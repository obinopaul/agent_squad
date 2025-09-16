import os
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import Tool
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Interrupt
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.types import Send
from dotenv import load_dotenv

load_dotenv()

# --- Environment Setup ---
# Make sure to set your OPENAI_API_KEY and TAVILY_API_KEY environment variables
# For example:
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# --- Pydantic Schemas for Structured Data ---

class WeatherResponse(BaseModel):
    """The final response schema for a weather query."""
    conditions: str = Field(description="A brief description of the current weather conditions.")
    temperature_celsius: float = Field(description="The current temperature in Celsius.")
    city: str = Field(description="The city for which the weather is reported.")

class RequestHumanAssistance(BaseModel):
    """
    Schema for the tool that allows the agent to request human help.
    The agent can invoke this tool when it's stuck or needs clarification.
    """
    question: str = Field(..., description="The specific question or request for the human.")


class SearchToolInput(BaseModel):
    """Input schema for the Tavily Search Tool."""
    query: str = Field(..., description="The search query to look up.")

# --- Tool Definition ---

# Define the Tool
class TavilySearchTool:
    def __init__(self, max_results: int = 10):
        self.max_results = max_results

    def search(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Perform a web search using the Tavily search engine.
        """
        try:
            # Initialize the Tavily search tool with the configured max_results
            search_tool = TavilySearchResults(max_results=self.max_results)

            # Perform the search (synchronously)
            result = search_tool.invoke({"query": query})

            # Return the search results
            return result
        except Exception as e:
            return {"error": str(e)}

@tool
def request_human_assistance(question: str) -> str:
    """
    Use this tool when you need to ask the user for clarification, feedback, or help.
    The user's response will be returned as a string.
    """
    # The interrupt() function will pause the graph here. The main loop will
    # then prompt the user and resume execution with their response.
    print(f"\n--- AGENT REQUESTS ASSISTANCE ---\nAgent's Question: {question}")
    user_response = interrupt()
    return user_response


tavily_search_tool = Tool(
    name="Tavily_Search",
    func=TavilySearchTool().search,
    description="Performs web searches using the Tavily search engine, providing accurate and trusted results for general queries.",
    args_schema=SearchToolInput
)

tools = [tavily_search_tool, request_human_assistance]
tool_node = ToolNode(tools)

# --- Graph State Definition ---

class AgentState(TypedDict):
    """
    Represents the state of our agent. This state is passed between nodes in the graph.

    Attributes:
        messages: The history of messages in the conversation.
    """
    messages: Annotated[list, add_messages]


# --- Graph Nodes ---

def agent_node(state: AgentState, config: RunnableConfig) -> dict:
    """
    The core logic of the agent. It decides what action to take based on the current state.
    It can either call a tool, request human assistance, or respond directly to the user.
    """
    response = llm_with_tools.invoke(state["messages"], config)
    return {"messages": [response]}


if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    # Bind the tools to the LLM, making it aware of the functions it can call.
    llm_with_tools = llm.bind_tools(tools)

    # --- Build the Graph ---
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_edge(START, "agent")

    # Use the pre-built tools_condition to decide whether to call tools or end.
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,
        # If the agent decides to call a tool, route to the 'tools' node.
        # Otherwise, end the graph.
        {"tools": "tools", END: END},
    )

    graph_builder.add_edge("tools", "agent")

    # --- Compile the Graph ---
    memory = InMemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    # --- Run the Agent ---
    thread = {"configurable": {"thread_id": "1"}}
    print("Agent is running. Type 'exit' to quit.")

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        # Stream events from the graph.
        # The stream will pause if the `interrupt()` function is called.
        events = graph.stream(
            {"messages": [("user", user_input)]}, thread, stream_mode="values"
        )
        for event in events:
            last_message = event["messages"][-1]
            if last_message.type == 'ai':
                if last_message.tool_calls:
                    # The agent is calling a tool. We don't print this message
                    # as the tool's output will be more informative.
                    pass
                else:
                    # It's a final response from the agent.
                    print(f"Agent: {last_message.content}")

        # After the stream is exhausted, check if the graph is interrupted.
        snapshot = graph.get_state(thread)
        if snapshot.next:
            # If the graph is waiting for the next step, it means it was interrupted.
            # In our case, it's waiting for the human_assistance tool to get a response.
            user_feedback = input("Your Feedback: ")
            
            # Resume the graph by streaming the user's feedback.
            # The interrupt() call inside the tool will receive this value.
            resume_events = graph.stream(user_feedback, thread, stream_mode="values")
            for resume_event in resume_events:
                last_resume_message = resume_event["messages"][-1]
                if last_resume_message.type == 'ai' and not last_resume_message.tool_calls:
                     print(f"Agent: {last_resume_message.content}")

