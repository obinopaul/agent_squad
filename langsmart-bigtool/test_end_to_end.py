import inspect
import math
import os
import types
import uuid
from typing import Callable
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from a .env file if present

import pytest
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langsmart_bigtool import create_agent

# from langsmart_bigtool import create_agent
# Assuming the new utils file is in the correct path
from langsmart_bigtool.utils import convert_positional_only_function_to_tool

# --- Tool and Model Setup ---

# Set your OpenAI API key here.
# It's recommended to use environment variables for security.
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"
if not os.getenv("OPENAI_API_KEY"):
    # This is a placeholder and will not work.
    # Replace it with your actual OpenAI API key.
    os.environ["OPENAI_API_KEY"] = "sk-proj-..."

# Create a list of all the functions in the math module
all_names = dir(math)
math_functions = [
    getattr(math, name)
    for name in all_names
    if isinstance(getattr(math, name), types.BuiltinFunctionType)
]

# Convert to tools using the revised utility function
all_tools = []
for function in math_functions:
    if wrapper := convert_positional_only_function_to_tool(function):
        all_tools.append(wrapper)

# Store tool objects in a registry with unique IDs
tool_registry = {str(uuid.uuid4()): tool for tool in all_tools}


def _get_tool_id_by_name(tool_name: str) -> str:
    """Gets the unique ID of a tool by its registered name."""
    for tool_id, tool in tool_registry.items():
        if isinstance(tool, BaseTool) and tool.name == tool_name:
            return tool_id
    raise ValueError(f"Tool with name '{tool_name}' not found in the registry.")


@pytest.fixture(scope="module")
def llm():
    """Provides a reusable ChatOpenAI model instance for all tests."""
    # Using a powerful model is recommended for reliable tool selection
    return ChatOpenAI(model="gpt-4o", temperature=0)


@pytest.fixture(scope="module")
def agent(llm: LanguageModelLike):
    """Provides a compiled agent instance for all tests."""
    # The create_agent function returns a compiled graph directly.
    builder = create_agent(llm, llm, tool_registry)
    return builder


# --- Test Cases ---

def test_state_management_and_tool_use(agent):
    """
    Tests that the agent correctly selects a tool, executes it, and
    preserves the full message history.
    """
    acos_tool_id = _get_tool_id_by_name("acos")
    initial_query = "Calculate the arc cosine of 0.5"

    result = agent.invoke({"messages": [HumanMessage(content=initial_query)]})

    # 1. Verify that the original user message is preserved
    messages = result["messages"]
    assert any(
        isinstance(msg, HumanMessage) and initial_query in msg.content for msg in messages
    ), "Original user message should be preserved in the final state."

    # 2. Verify the correct tool was selected
    assert acos_tool_id in result["selected_tool_ids"], "The 'acos' tool should have been selected."

    # 3. Verify a tool message with the result is present
    assert any(
        isinstance(msg, ToolMessage) and "1.047" in msg.content for msg in messages
    ), "A ToolMessage with the approximate result of acos(0.5) should be present."

    # 4. Verify the final AI message contains the answer
    final_message = messages[-1]
    assert isinstance(final_message, AIMessage)
    assert "1.047" in final_message.content, "The final AI message should contain the calculated answer."


def test_reasoning_and_tool_selection_message(agent):
    """
    Tests that the agent's reasoning for tool selection is captured
    in an AIMessage.
    """
    query = "What is the factorial of 6?"
    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    messages = result["messages"]

    # Find the AIMessage that explains the tool selection
    reasoning_message = next(
        (msg for msg in messages if isinstance(msg, AIMessage) and "Selected tools:" in msg.content),
        None,
    )

    assert reasoning_message is not None, "A reasoning message for tool selection should be present."
    assert "factorial" in reasoning_message.content, "The reasoning should mention the selected 'factorial' tool."


def test_main_agent_uses_full_conversation_history(agent):
    """
    Tests that the main agent uses the context from a multi-turn conversation
    to resolve ambiguity and execute the correct tool.
    """
    initial_messages = [
        HumanMessage(content="My favorite number is 8."),
        AIMessage(content="Got it. Your favorite number is 8. How can I help you with it?"),
        HumanMessage(content="What is its square root?"),
    ]

    result = agent.invoke({"messages": initial_messages})
    final_message = result["messages"][-1]

    # The agent should use the context ("8") to calculate the square root
    assert isinstance(final_message, AIMessage)
    assert "2.828" in final_message.content, "The agent should have calculated the square root of 8 using conversation history."


def test_no_valid_tools_scenario(agent):
    """
    Tests that the agent responds conversationally without selecting a tool
    when the query does not match any available tools.
    """
    result = agent.invoke({"messages": [HumanMessage(content="What is the capital of France?")]})

    # No math tools should be selected for this query
    assert len(result["selected_tool_ids"]) == 0, "No tools should have been selected for a general knowledge question."

    final_message = result["messages"][-1]
    assert isinstance(final_message, AIMessage)
    assert "Paris" in final_message.content, "The agent should provide a direct answer without using a tool."


def test_multiple_tool_selection_and_execution(agent):
    """
    Tests the agent's ability to select and use multiple tools if implied by the query.
    Note: This depends on the agent's underlying logic. A simple query might only
    trigger one tool call at a time in many agent designs.
    """
    query = "What is the sine of 1.57 and the cosine of 0?"
    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    messages = result["messages"]

    # Verify that both tools were selected
    sin_tool_id = _get_tool_id_by_name("sin")
    cos_tool_id = _get_tool_id_by_name("cos")
    assert sin_tool_id in result["selected_tool_ids"]
    assert cos_tool_id in result["selected_tool_ids"]

    # Verify the final answer contains both results
    final_message = messages[-1]
    assert isinstance(final_message, AIMessage)
    assert "1.0" in final_message.content and "sine" in final_message.content.lower()
    assert "1.0" in final_message.content and "cosine" in final_message.content.lower()


@pytest.mark.asyncio
async def test_async_functionality(agent):
    """Tests the async `ainvoke` method for non-blocking execution."""
    sqrt_tool_id = _get_tool_id_by_name("sqrt")
    query = "What is the square root of 256?"

    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})

    assert sqrt_tool_id in result["selected_tool_ids"]
    final_message = result["messages"][-1]
    assert isinstance(final_message, AIMessage)
    assert "16" in final_message.content


def test_edge_case_empty_tool_selection(agent):
    """
    Tests the edge case where the LLM correctly determines that no tools are
    needed for a conversational query.
    """
    result = agent.invoke({"messages": [HumanMessage(content="Tell me a short poem about programming.")]})

    assert len(result["selected_tool_ids"]) == 0, "Tool selection should be empty for a creative request."

    # Check that a conversational response is given
    final_message = result["messages"][-1]
    assert isinstance(final_message, AIMessage)
    # A simple check to see if it tried to be poetic
    assert len(final_message.content.split()) > 5, "The final message should be a conversational, poetic response."


# --- Executable Example ---

if __name__ == "__main__":
    """
    This block demonstrates how to run the agent directly with a variety of
    test cases to showcase its different capabilities.
    
    You can execute this script from your terminal to see the agent in action.
    
    Example:
        python your_agent_file.py
    """
    print("--- Initializing Agent ---")
    # 1. Initialize the Language Model
    # Ensure your OPENAI_API_KEY is set as an environment variable
    try:
        # Using a powerful model is recommended for reliable tool selection
        main_llm = ChatOpenAI(model="gpt-4o", temperature=0)
    except ImportError as e:
        print(f"Error: Required packages might be missing. {e}")
        exit()
    except Exception as e:
        if "api_key" in str(e).lower():
            print("\n---")
            print("ERROR: OpenAI API key not found or invalid.")
            print("Please set the OPENAI_API_KEY environment variable.")
            print("---")
        else:
            print(f"An unexpected error occurred: {e}")
        exit()

    # 2. Create the agent instance
    # The create_agent function returns a compiled graph directly.
    agent_executable = create_agent(main_llm, main_llm, tool_registry)
    print("--- Agent Initialized Successfully ---\n")

    # 3. Define a list of demonstration cases to run
    demonstration_cases = [
        {
            "name": "SINGLE TOOL USE (FACTORIAL)",
            "conversation": [HumanMessage(content="What is the factorial of 6?")],
        },
        {
            "name": "CONVERSATIONAL HISTORY (SQUARE ROOT)",
            "conversation": [
                HumanMessage(content="My favorite number is 8."),
                AIMessage(content="Got it. Your favorite number is 8. How can I help?"),
                HumanMessage(content="What is its square root?"),
            ],
        },
        {
            "name": "MULTI-TOOL SELECTION (SINE & COSINE)",
            "conversation": [
                HumanMessage(content="What is the sine of 1.57 and the cosine of 0?")
            ],
        },
        {
             "name": "TWO-ARGUMENT TOOL (LOG)",
             "conversation": [HumanMessage(content="What is the log of 1024 with a base of 2?")]
        },
        {
            "name": "NO TOOL SCENARIO (GENERAL KNOWLEDGE)",
            "conversation": [
                HumanMessage(content="What is the capital of France?")
            ],
        },
        {
            "name": "EDGE CASE (CREATIVE REQUEST)",
            "conversation": [
                HumanMessage(content="Tell me a short poem about programming.")
            ],
        },
    ]

    # 4. Iterate through and run each demonstration case
    for i, case in enumerate(demonstration_cases):
        print(f"--- Running Demonstration Case {i+1}: {case['name']} ---")
        
        initial_messages = case["conversation"]
        
        print("\nInitial Conversation:")
        for msg in initial_messages:
            print(f"  {msg.type.upper()}: {msg.content}")
        print("--------------------------------------------------")

        # Invoke the agent with the messages
        final_result = agent_executable.invoke({"messages": initial_messages})

        # Print the full final state for review
        print("\nFinal Agent State:")
        print("  - Selected Tool IDs:")
        print(f"    {final_result['selected_tool_ids']}\n")
        
        print("  - Final Conversation History:")
        for msg in final_result["messages"]:
            content = msg.content
            # *** FIX STARTS HERE ***
            # Safely check if the message object has tool_calls and if they are present.
            # This prevents the AttributeError on HumanMessage, ToolMessage, etc.
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                # Format the tool calls for cleaner display
                calls = [f"{tc['name']}({tc['args']})" for tc in msg.tool_calls]
                content = f"Tool Calls: {', '.join(calls)}"
            # *** FIX ENDS HERE ***
            
            print(f"    {msg.type.upper()}: {content}")
        print("--------------------------------------------------\n")

