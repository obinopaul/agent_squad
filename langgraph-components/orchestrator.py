# orchestrator.py

import os
import asyncio
import logging
from functools import partial
from typing import TypedDict, Dict, Type, Any, Callable, Literal, AsyncIterator, AsyncGenerator, Optional, Annotated
import operator

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.tools.openweathermap.tool import OpenWeatherMapQueryRun

# --- Environment Setup ---
load_dotenv()

# Suppress noisy httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

# Ensure required environment variables are set
required_env_vars = ["OPENWEATHERMAP_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY"]
for var in required_env_vars:
    if var not in os.environ or not os.getenv(var):
        raise EnvironmentError(f"{var} environment variable not set.")

weather_tool = OpenWeatherMapQueryRun()


# -----------------------------------------------------------------------------
# 1. ROUTER MODEL FACTORY (FIXED)
# -----------------------------------------------------------------------------

def create_router_model(agent_names: list[str]) -> Type[BaseModel]:
    """Dynamically creates the Router Pydantic model with the available agent names."""
    RouteOptions = Literal[*agent_names]

    class Router(BaseModel):
        """Routes the user's request to the most appropriate sub-agent."""
        next: RouteOptions = Field(
            description="The name of the sub-agent to route the user's request to."
        )

    # FIX: Use a short, static name to avoid exceeding the API's character limit.
    Router.__name__ = "RouteToAgent"
    return Router

def sanitize_output(output):
    """Recursively converts Pydantic models in the output to dictionaries."""
    if hasattr(output, "model_dump"):
        return output.model_dump()
    if isinstance(output, dict):
        return {k: sanitize_output(v) for k, v in output.items()}
    if isinstance(output, list):
        return [sanitize_output(i) for i in output]
    return output

def wrap_node_with_sanitizer(node_fn):
    """Decorator to sanitize the output of a node function."""
    async def wrapped(state):
        result = await node_fn(state)
        return sanitize_output(result)
    return wrapped

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT
# -----------------------------------------------------------------------------

class AgentState(TypedDict):
    """
    Defines the shared state for the graph.
    `messages` is the conversation history, and it's append-only.
    `next_node` directs the graph to the next agent to call.
    """
    messages: Annotated[list[BaseMessage], operator.add]
    next_node: str

# -----------------------------------------------------------------------------
# 3. CLASSIFIER AGENT FRAMEWORK
# -----------------------------------------------------------------------------

class LangGraphClassifier:
    """
    A robust classifier agent framework that routes user requests to specialized
    sub-agents. It supports asynchronous streaming of responses.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        sub_agents: Dict[str, Callable],
        fallback_agent: Callable,
        checkpointer: Optional[MemorySaver] = None,
    ):
        if not sub_agents:
            raise ValueError("At least one sub-agent must be provided.")

        self.llm = llm
        self.sub_agents = sub_agents
        self.fallback_agent = fallback_agent
        self.all_agent_names = list(sub_agents.keys()) + ["fallback"]
        self.checkpointer = checkpointer
        
        self.runnable = self._build_graph()

    def _build_router_context(self) -> str:
        """
        Returns a string describing all available agents and their descriptions.
        """
        descriptions = []
        for name, agent in self.sub_agents.items():
            # Use the agent's prompt for a more detailed description if available
            desc = "No description available."
            if hasattr(agent, "runnable") and hasattr(agent.runnable, "prompt"):
                desc = agent.runnable.prompt.template
            elif hasattr(agent, "prompt"):
                desc = agent.prompt.template
            descriptions.append(f"- {name}: {desc}")
        descriptions.append("- fallback: Default fallback agent for unrecognized queries.")
        return "Available agents:\n" + "\n".join(descriptions) + "\n\n"

    def _create_router_tool(self) -> Callable:
        """Creates a Pydantic model for routing and binds it to the LLM."""
        RouterModel = create_router_model(self.all_agent_names)
        return self.llm.with_structured_output(RouterModel)
    
    async def _router_node(self, state: AgentState) -> Dict[str, str]:
        """Determines the next agent to route to based on the conversation history."""
        try:
            if not state.get("messages"):
                raise ValueError("State 'messages' must be a non-empty list.")
                
            router_tool = self._create_router_tool()
            router_context = self._build_router_context()
            # Combine the context with the actual message history
            messages_with_context = [HumanMessage(content=router_context)] + state["messages"]
            
            route = await router_tool.ainvoke(messages_with_context)
            
            route_dict = route.model_dump()
            
            next_node = route_dict.get("next")
            if next_node not in self.all_agent_names:
                logging.warning(f"Router returned unknown next_node '{next_node}', falling back.")
                next_node = "fallback"
            
            return {"next_node": next_node}
        except Exception as e:
            logging.error(f"Router node error: {e}")
            return {"next_node": "fallback"}
        

    # async def _sub_agent_node(
    #     self, state: AgentState, agent_name: str, agent_runnable: Callable
    # ) -> AsyncGenerator[Dict[str, Any], None]:
    #     """Executes a sub-agent and streams its output."""
    #     try:
    #         async for chunk in agent_runnable.astream({"messages": state["messages"]}):
    #             if isinstance(chunk, BaseMessage):
    #                 yield {"messages": [chunk]}
    #             elif isinstance(chunk, dict) and "messages" in chunk:
    #                 yield chunk
    #             else:
    #                 # Fallback for unexpected chunk types
    #                 yield {"messages": [AIMessageChunk(content=str(chunk))]}
    #     except Exception as e:
    #         logging.error(f"Error in sub-agent '{agent_name}': {e}")
    #         yield {"messages": [AIMessage(content=f"Error in agent '{agent_name}': {e}")]}


    async def _sub_agent_node(self, state: AgentState, agent_name: str, agent_runnable: Callable) -> AsyncGenerator[Dict[str, Any], None]:
        """Executes a sub-agent and streams its output, ignoring internal state chunks."""
        try:
            config = {"callbacks": []}
            async for chunk in agent_runnable.astream({"messages": state["messages"]}, config=config):
                if isinstance(chunk, BaseMessage):
                    yield {"messages": [chunk]}
                elif isinstance(chunk, dict) and "messages" in chunk:
                    yield chunk
                else:
                    # FIX: Ignore any other chunk types (like raw state dicts)
                    # which were being improperly converted to strings and printed.
                    continue
        except Exception as e:
            logging.error(f"Error in sub-agent '{agent_name}': {e}")
            yield {"messages": [AIMessage(content=f"Error in agent '{agent_name}': {e}")]}

    
    
    def _build_graph(self) -> Callable:
        """Builds and compiles the LangGraph StateGraph."""
        graph = StateGraph(AgentState)
        
        # The router is a single-output node, so wrapping it to sanitize is safe.
        graph.add_node("router", wrap_node_with_sanitizer(self._router_node))

        # Sub-agent nodes are streaming generators; do not wrap them.
        for name, agent in self.sub_agents.items():
            node_fn = partial(self._sub_agent_node, agent_name=name, agent_runnable=agent)
            graph.add_node(name, node_fn)
            graph.add_edge(name, END)
            
        fallback_node_fn = partial(self._sub_agent_node, agent_name="fallback", agent_runnable=self.fallback_agent)
        graph.add_node("fallback", fallback_node_fn)
        graph.add_edge("fallback", END)
        
        graph.add_edge(START, "router")
        graph.add_conditional_edges(
            "router",
            lambda state: state["next_node"],
            {name: name for name in self.all_agent_names},
        )
        return graph.compile(checkpointer=self.checkpointer)


    # --- START OF FIXED CODE ---
    async def stream_full_response(self, query: str, thread_id: str):
        """
        Invokes the main graph to stream a response with clean terminal output,
        showing routing, tool calls, and the final AI message.
        """
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=query)]}
        
        agent_prompt_printed = False
        tool_calls_announced = set()

        async for event in self.runnable.astream_events(inputs, config=config, version="v1"):
            kind = event["event"]
            
            if kind == "on_chain_end":
                if event["name"] == "router":
                    routing_decision = event["data"]["output"]["next_node"]
                    print(f"[Routing to agent: {routing_decision}]", flush=True)

            elif kind == "on_chain_stream":
                chunk = event["data"].get("chunk")
                               
                if not chunk:
                    continue

                message_chunk = None
                
                # Intelligent parsing of different chunk structures from sub-agents
                if isinstance(chunk, dict):
                    # ReAct agent state updates look like: {'agent': {'messages': [...]}}
                    if 'agent' in chunk and isinstance(chunk['agent'], dict):
                        messages = chunk['agent'].get('messages', [])
                        if messages and isinstance(messages[0], (AIMessage, AIMessageChunk)):
                            message_chunk = messages[0]
                    # Simple agent state updates look like: {'messages': [...]}
                    elif 'messages' in chunk:
                        messages = chunk.get('messages', [])
                        if messages and isinstance(messages[0], (AIMessage, AIMessageChunk)):
                            message_chunk = messages[0]
                
                if not message_chunk:
                    continue # Skip events that don't contain a printable message (e.g., tool results)

                # --- FIX #2: Announce tool calls as they happen ---
                # Check for tool call chunks (streaming)
                if hasattr(message_chunk, 'tool_call_chunks') and message_chunk.tool_call_chunks:
                    for tc_chunk in message_chunk.tool_call_chunks:
                        tool_name = tc_chunk.get("name")
                        if tool_name and tool_name not in tool_calls_announced:
                            print(f"\n[Calling tool: {tool_name}]\n", flush=True)
                            tool_calls_announced.add(tool_name)

                # Check for final tool calls in a complete AIMessage
                if hasattr(message_chunk, 'tool_calls') and message_chunk.tool_calls:
                    for tool_call in message_chunk.tool_calls:
                        tool_name = tool_call.get("name")
                        if tool_name and tool_name not in tool_calls_announced:
                            print(f"\n[Calling tool: {tool_name}]\n", flush=True)
                            tool_calls_announced.add(tool_name)
                
                # --- FIX #1: Extract and print only the text content ---
                text_to_print = ""
                if isinstance(message_chunk.content, str):
                    text_to_print = message_chunk.content
                elif isinstance(message_chunk.content, list):
                    for item in message_chunk.content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_to_print += item.get("text", "")
                
                if text_to_print:
                    if not agent_prompt_printed:
                        print(f"\nAgent > ", end="", flush=True)
                        agent_prompt_printed = True
                    print(text_to_print, end="", flush=True)
    # --- END OF FIXED CODE ---


    async def stream_agent_response(self, agent_name: str, query: str, thread_id: Optional[str] = None):
        """
        Handles the streaming of the agent's response, printing only the text content.
        """
        if thread_id is None:
            thread_id = "default_thread"  # fallback thread id

        config = {"configurable": {"thread_id": thread_id}}
        
        # Get the latest state snapshot from the graph
        state_snapshot = self.runnable.get_state(config)
        messages = state_snapshot.values.get("messages", []) if state_snapshot else []

        # Append current user message
        full_history = list(messages) + [HumanMessage(content=query)]
            
        agent_runnable = (
            self.sub_agents.get(agent_name)
            if agent_name != "fallback"
            else self.fallback_agent
        )
        tool_calls_in_progress = set()

        async for chunk in agent_runnable.astream(
            {"messages": full_history},
            stream_mode="messages",
            config=config   
        ):
            # Unpack the chunk safely; it can be a tuple or a direct message object
            if isinstance(chunk, tuple) and len(chunk) == 2:
                message_chunk, _ = chunk
            else:
                message_chunk = chunk

            # We only want to process AIMessageChunks or AIMessage for streaming text output.
            if not isinstance(message_chunk, (AIMessageChunk, AIMessage)):
                continue

            # Announce tool calls when the AI first decides to use them
            tool_call_chunks = getattr(message_chunk, "tool_call_chunks", None)
            if tool_call_chunks:
                for tool_call in tool_call_chunks:
                    tool_name = tool_call.get("name")
                    if tool_name and tool_name not in tool_calls_in_progress:
                        print(f"\n[Calling tool: {tool_name}]\n")
                        tool_calls_in_progress.add(tool_name)

            # Process the content to extract and stream only the text
            content = message_chunk.content
            text_to_print = ""

            if isinstance(content, str):
                # Handles models that stream simple strings
                text_to_print = content
            elif isinstance(content, list):
                # Handles models like Anthropic that stream a list of content blocks
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_to_print += item.get("text", "")

            # Print the extracted text immediately for a live streaming effect
            if text_to_print:
                print(text_to_print, end="", flush=True)

    def astream(self, query: str, stream_mode="messages") -> AsyncIterator[Any]:
        return self.runnable.astream(
            {"messages": [HumanMessage(content=query)]},
            stream_mode=stream_mode,
        )

# -----------------------------------------------------------------------------
# 4. EXAMPLE USAGE
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    
    from tavily import AsyncTavilyClient
    import uuid
    
    # Create an in-memory checkpointer (for production, consider PostgresSaver or MongoDBSaver)
    memory_checkpointer = MemorySaver()
    
    # 1. Initialize the async client for the tool
    tavily_async_client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    # 2. Define an async tool for the agent to use
    async def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
    ) -> list[dict[str, Any]]:
        """Run an async web search using Tavily."""
        print(f"\n🔎 Searching for: '{query}'...")
        return await tavily_async_client.search(
            query,
            max_results=max_results,
            search_depth="advanced",
            topic=topic,
        )

    # --- Initialize LLM and Agents ---
    # llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=os.getenv("ANTHROPIC_API_KEY"))
    llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    
    # 1. A ReAct agent with tools (this is itself a compiled LangGraph)
    weatherAgent = create_react_agent(llm, tools=[weather_tool, internet_search])
    basicAgent1 = create_react_agent(llm, tools=[weather_tool, internet_search])
    # basicAgent2 = create_react_agent(llm, tools=[weather_tool, internet_search])
    # basicAgent3 = create_react_agent(llm, tools=[weather_tool, internet_search])

    # 2. Simple agents created using idiomatic LCEL (Prompt | LLM)
    story_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a master storyteller. Your stories are brief, whimsical, and captivating."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    storyAgent = story_prompt | llm

    summarizer_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert summarizer. Provide a concise, one-sentence summary of the user's text."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    summarizationAgent = summarizer_prompt | llm

    # 3. A fallback agent for when no other agent is suitable
    fallback_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. The user's request could not be routed to a specialized agent. Politely ask for clarification or a different request."),
        MessagesPlaceholder(variable_name="messages"),
    ])
    fallback_agent = fallback_prompt | llm

    # --- Instantiate and Run the Classifier ---
    classifier = LangGraphClassifier(
        llm=llm,
        sub_agents={
            "weatherAgent": weatherAgent,
            "basicAgent1": basicAgent1,
            # "basicAgent2": basicAgent2,
            # "basicAgent3": basicAgent3,
            "storyAgent": storyAgent,
            "summarizationAgent": summarizationAgent,
        },
        fallback_agent=fallback_agent,
        checkpointer=memory_checkpointer,  # pass it here
    )

    async def main():
        """Main loop to interact with the classifier agent."""
        print("🚀 Classifier Agent Framework running. Type 'exit' to quit.")
        print("-" * 50)
        # Create a persistent thread_id for the entire session
        thread_id = str(uuid.uuid4())
        
        while True:
            user_input = input("User > ")
            if user_input.lower() == "exit":
                break

            try:
                # This is the ONLY call you need. 
                # It handles routing and streaming in one step.
                await classifier.stream_full_response(user_input, thread_id=thread_id)
                
                # Add a newline after the full response is streamed.
                print() 
                    
            except Exception as e:
                logging.error(f"Error during streaming: {e}")
                print("\n[An error occurred during response streaming]")

            print("\n" + "-" * 50)

    # Run the asynchronous main function
    asyncio.run(main())
