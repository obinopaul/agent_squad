from typing import Annotated, Callable, List, Tuple
import json
import asyncio

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

# Try to import TrustCall, fallback to structured output if not available
try:
    from trustcall import create_extractor
    TRUSTCALL_AVAILABLE = True
except ImportError:
    TRUSTCALL_AVAILABLE = False

# Define a utility function to add new items to a list while avoiding duplicates
def _add_new(left: list, right: list) -> list:
    """Extend left list with new items from right list."""
    return left + [item for item in right if item not in set(left)]


# Define the state for the agent, which includes selected tool IDs
class State(MessagesState):
    selected_tool_ids: Annotated[list[str], _add_new]

# Define a structured response model for tool selection
class ToolSelectionResponse(BaseModel):
    """Structured response for tool selection."""
    tool_ids: List[str] = Field(
        description="List of tool IDs selected for the task"
    )
    reasoning: str = Field(
        description="Brief explanation of why these tools were selected"
    )

# Define a function to create an agent with LLM-driven tool selection
def create_agent(
    selector_llm: LanguageModelLike,
    main_llm: LanguageModelLike,
    tool_registry: dict[str, BaseTool | Callable],
    tool_selection_limit: int = 10,
    prompt: ChatPromptTemplate | None = None,
) -> StateGraph:
    """Create an agent with LLM-driven tool selection.

    The agent uses a two-node architecture:
    1. Tool Selector: A fast LLM that selects relevant tools from the registry
    2. Main Agent: A ReAct agent that uses only the selected tools

    Args:
        selector_llm: Fast language model for tool selection.
        main_llm: Language model for the main agent execution.
        tool_registry: Dict mapping string IDs to tools or callables.
        tool_selection_limit: The maximum number of tools to select.
    """
    
    # === 1. DEFINE THE PROMPT FOR THE MAIN AGENT ===
    # If a custom prompt is not provided, use this robust default.
    if prompt is None:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a powerful and helpful assistant. Your goal is to use a pre-selected set of tools to answer the user's query accurately.

            **Operational Principles:**

            1.  **Analyze the Goal:** Carefully examine the user's latest query and the conversation history to understand the objective.
            2.  **Use Your Tools:** You have been provided with a specific, curated set of tools that are deemed relevant for this task. Your primary job is to use them effectively.
            3.  **ReAct Workflow:** Follow a "Reason-Act" loop to solve the problem:
                - **Thought:** Explain your reasoning. What are you trying to achieve, and which tool will you use to do it?
                - **Action:** State the exact tool and input you are using.
                - **Observation:** After a tool is used, you will see the result.
                - **Thought:** Analyze the result. Do you have the final answer, or do you need to use another tool? Repeat until you can answer the user's query.
            4.  **Final Answer:** Once you have sufficient information from your tools, provide a clear, concise, and final answer to the user. Do not explain your internal tool-use process in the final answer.
            """,
                            ),
                            MessagesPlaceholder(variable_name="messages"),
                            # MessagesPlaceholder(variable_name="agent_scratchpad"),
                        ]
                    )

    # === 2. DEFINE THE TOOL SELECTION LOGIC ===
    # This part remains as it was, responsible for the first node's logic.
    
    def _create_tool_manifest(tool_registry: dict[str, BaseTool | Callable]) -> str:
        """Create a structured manifest of all available tools."""
        manifest_lines = ["# Available Tools\n"]
        
        for tool_id, tool in tool_registry.items():
            if isinstance(tool, BaseTool):
                name = tool.name
                description = tool.description
            else:
                name = tool.__name__
                description = tool.__doc__ or "No description available"
            
            manifest_lines.append(f"## {name}")
            manifest_lines.append(f"- **ID**: {tool_id}")
            manifest_lines.append(f"- **Description**: {description}")
            manifest_lines.append("")
        
        return "\n".join(manifest_lines)

    def _get_selection_prompt(user_query: str, tool_manifest: str) -> str:
        """Generate the system prompt for the tool selector."""
        return f"""You are a tool selection expert. Your task is to analyze a user's query and select the most relevant tools from the available tool registry.

{tool_manifest}

Instructions:
1. Analyze the user's query carefully.
2. Select 1-{tool_selection_limit} of the most relevant tools that could help answer the query.
3. Provide the tool IDs (not names) in your response.
4. If no tools are relevant to the query, return an empty list.
5. Explain your reasoning briefly.

User Query: {user_query}"""

    if TRUSTCALL_AVAILABLE:
        tool_selector_extractor = create_extractor(
            selector_llm,
            tools=[ToolSelectionResponse],
            tool_choice="ToolSelectionResponse"
        )
        
        def _invoke_tool_selector(sample_prompt: str) -> ToolSelectionResponse:
            result = tool_selector_extractor.invoke({
                "messages": [{"role": "user", "content": f"Select the most relevant tools for this query:\n{sample_prompt}"}]
            })
            return result["responses"][0]

        async def _ainvoke_tool_selector(sample_prompt: str) -> ToolSelectionResponse:
            # TrustCall doesn't have async invoke yet, run sync in executor
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _invoke_tool_selector, sample_prompt)

    else:
        selector_with_structured_output = selector_llm.with_structured_output(ToolSelectionResponse)
        
        def _invoke_tool_selector(sample_prompt: str) -> ToolSelectionResponse:
            return selector_with_structured_output.invoke([SystemMessage(content=sample_prompt)])

        async def _ainvoke_tool_selector(sample_prompt: str) -> ToolSelectionResponse:
            return await selector_with_structured_output.ainvoke([SystemMessage(content=sample_prompt)])

    def tool_selector(state: State, config: RunnableConfig) -> dict:
        """Selects relevant tools based on the user's query."""
        messages = state["messages"]
        # Improved logic to find the last human message
        user_query = ""
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                # Found the last human message, so we extract its content
                user_query = message.content
                break
        
        # user_query = messages[-1].content if messages else ""
        tool_manifest = _create_tool_manifest(tool_registry)
        system_prompt = _get_selection_prompt(user_query, tool_manifest)
        
        tool_selection = _invoke_tool_selector(system_prompt)
        
        return {
            "selected_tool_ids": tool_selection.tool_ids,
            "messages": [
                AIMessage(
                    content=f"Selected tools: {tool_selection.tool_ids}. Reasoning: {tool_selection.reasoning}"
                )
            ],
        }

    async def atool_selector(state: State, config: RunnableConfig) -> dict:
        """Async version of tool selector."""
        messages = state["messages"]
        user_query = ""
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                # Found the last human message, so we extract its content
                user_query = message.content
                break
        # user_query = messages[-1].content if messages else ""
        tool_manifest = _create_tool_manifest(tool_registry)
        system_prompt = _get_selection_prompt(user_query, tool_manifest)

        tool_selection = await _ainvoke_tool_selector(system_prompt)
        
        return {
            "selected_tool_ids": tool_selection.tool_ids,
            "messages": [
                AIMessage(
                    content=f"Selected tools: {tool_selection.tool_ids}. Reasoning: {tool_selection.reasoning}"
                )
            ],
        }

    # === 3. DEFINE THE MAIN AGENT LOGIC (REWRITTEN) ===
    # This node is now a true, configurable ReAct agent.
    
    def main_agent(state: State, config: RunnableConfig) -> dict:
        """Main ReAct agent that uses only the selected tools and a dedicated prompt."""
        selected_tools = [
            tool_registry[tool_id] for tool_id in state.get("selected_tool_ids", [])
            if tool_id in tool_registry
        ]
        
        # Dynamically create the agent with the right tools and prompt
        agent_executor = create_react_agent(
            model=main_llm, 
            tools=selected_tools, 
            prompt=prompt
        )
        
        # Invoke the agent. It will handle the ReAct loop internally for this one step.
        response = agent_executor.invoke({"messages": state["messages"]})
        
        # Return the message(s) from the agent to be added to the state.
        # This could be a final answer or a new tool call.
        return {"messages": response["messages"]}

    async def amain_agent(state: State, config: RunnableConfig) -> dict:
        """Async version of the main ReAct agent."""
        selected_tools = [
            tool_registry[tool_id] for tool_id in state.get("selected_tool_ids", [])
            if tool_id in tool_registry
        ]
        
        agent_executor = create_react_agent(
            model=main_llm, 
            tools=selected_tools, 
            prompt=prompt
        )
        
        response = await agent_executor.ainvoke({"messages": state["messages"]})
        return {"messages": response["messages"]}

    # === 4. DEFINE THE GRAPH STRUCTURE AND FLOW ===

    # The ToolNode is the "hands" that executes tool calls requested by the main agent.
    # It must be initialized with *all* possible tools from the registry.
    tool_node = ToolNode(
        [tool for tool in tool_registry.values() if isinstance(tool, (BaseTool, Callable))]
    )

    def should_continue(state: State) -> str:
        """Determines if the agent should continue, call tools, or end."""
        last_message = state["messages"][-1]
        
        # If the agent made a tool call, route to the 'tools' node.
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, the agent has finished, so we end the graph.
        return END

    # Build the graph
    builder = StateGraph(State)
    
    # Add nodes to the graph
    builder.add_node("tool_selector", tool_selector)
    builder.add_node("main_agent", main_agent) # The new, improved main_agent
    builder.add_node("tools", tool_node) # The node that executes tool calls
    
    # Define the graph's flow
    builder.set_entry_point("tool_selector")
    builder.add_edge("tool_selector", "main_agent")
    
    # This is the agentic loop: main_agent -> should_continue -> (tools or END)
    builder.add_conditional_edges(
        "main_agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    # After tools are executed, the result is sent back to the main_agent to continue reasoning.
    builder.add_edge("tools", "main_agent")
    
    # Compile the graph into a runnable object
    return builder.compile()