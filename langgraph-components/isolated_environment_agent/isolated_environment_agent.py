"""
Isolated Environment Agent with Daytona Integration

This agent provides secure code execution capabilities using Daytona sandboxes.
It can create isolated environments, execute code safely, and manage files
within sandboxed environments.
"""

import asyncio
from typing import Dict, List, Any, Annotated, Sequence, TypedDict, Optional
import operator
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from utils import get_model, AgentState, create_agent_prompt
from daytona_tools import get_daytona_tools, DaytonaSandboxManager


# Define the state for the isolated environment agent
class IsolatedEnvironmentState(TypedDict):
    """State for isolated environment agent workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_sandbox: Optional[str]
    sandbox_status: str
    execution_history: List[Dict[str, Any]]
    files_created: List[str]
    error_log: List[str]


# System prompt for the isolated environment agent
CODE_EXECUTOR_PROMPT = """You are an advanced code execution agent that specializes in running code in secure, isolated environments using Daytona sandboxes.

Your capabilities include:
- Creating and managing Daytona sandboxes for isolated code execution
- Executing Python code and shell commands safely in sandboxed environments
- Managing files within sandboxes (upload, download, create, modify)
- Cloning Git repositories into sandboxes
- Providing detailed execution results with stdout, stderr, and exit codes

Key principles:
1. ALWAYS create a sandbox before executing any code
2. Provide clear feedback about sandbox status and operations
3. Handle errors gracefully and provide helpful debugging information
4. Clean up resources when tasks are complete
5. Ensure code execution is secure and isolated from the host system

When a user asks you to run code:
1. First check if a sandbox exists, create one if needed
2. Execute the code in the isolated environment
3. Return the results with clear formatting
4. Offer to save any generated files or outputs

Available tools:
- create_daytona_sandbox: Create a new isolated sandbox
- destroy_daytona_sandbox: Remove a sandbox when done
- execute_python_code: Run Python code in the sandbox
- execute_command_in_sandbox: Run shell commands in the sandbox
- upload_file_to_sandbox: Upload files to the sandbox
- download_file_from_sandbox: Download files from the sandbox
- list_daytona_sandboxes: List available sandboxes
- git_clone_in_sandbox: Clone repositories into the sandbox

Always prioritize security and isolation. Never execute potentially harmful code on the host system."""


def inject_system_prompt(state: dict) -> dict:
    """
    Pre-model hook to inject the system prompt as the first message.
    """
    messages = state.get("messages", [])
    # Only inject if not already present
    if not messages or not (isinstance(messages[0], SystemMessage) and messages[0].content == CODE_EXECUTOR_PROMPT):
        new_messages = [SystemMessage(content=CODE_EXECUTOR_PROMPT)] + messages
        return {"messages": new_messages}
    return {}


def create_isolated_environment_agent():
    """Create a ReAct agent for isolated code execution with Daytona."""
    
    # Get the language model
    llm = get_model()
    
    # Get Daytona tools
    tools = get_daytona_tools()
    
    # Create the ReAct agent with Daytona tools
    agent = create_react_agent(
        llm,
        tools,
        # state_modifier=CODE_EXECUTOR_PROMPT
        pre_model_hook=inject_system_prompt
    )
    
    return agent


# Node functions for the workflow
def initialize_sandbox(state: IsolatedEnvironmentState) -> Dict[str, Any]:
    """Initialize the sandbox environment if needed."""
    
    # Check if we already have an active sandbox
    if state.get("current_sandbox") and state.get("sandbox_status") == "active":
        return {
            "messages": [AIMessage(content="Sandbox is already active and ready for code execution.")],
            "sandbox_status": "active"
        }
    
    # Initialize sandbox manager
    sandbox_manager = DaytonaSandboxManager()
    
    # Check authentication
    auth_result = sandbox_manager.authenticate()
    if auth_result["status"] == "error":
        return {
            "messages": [AIMessage(content=f"Authentication required: {auth_result['message']}")],
            "sandbox_status": "authentication_required",
            "error_log": [auth_result["message"]]
        }
    
    return {
        "messages": [AIMessage(content="Ready to create sandbox for code execution.")],
        "sandbox_status": "ready"
    }


def execute_code_task(state: IsolatedEnvironmentState) -> Dict[str, Any]:
    """Execute the main code execution task using the ReAct agent."""
    
    # Create the isolated environment agent
    agent = create_isolated_environment_agent()
    
    # Get the latest user message
    user_message = state["messages"][-1].content if state["messages"] else ""
    
    # Execute the agent
    try:
        response = agent.invoke({
            "messages": [HumanMessage(content=user_message)]
        })
        
        # Extract the agent's response
        agent_messages = response.get("messages", [])
        final_message = agent_messages[-1] if agent_messages else AIMessage(content="No response from agent")
        
        # Update execution history
        execution_entry = {
            "user_input": user_message,
            "agent_response": final_message.content,
            "timestamp": "now"  # In a real implementation, use proper timestamp
        }
        
        updated_history = state.get("execution_history", []) + [execution_entry]
        
        return {
            "messages": [final_message],
            "execution_history": updated_history,
            "sandbox_status": "active"
        }
        
    except Exception as e:
        error_message = f"Error executing code task: {str(e)}"
        return {
            "messages": [AIMessage(content=error_message)],
            "error_log": state.get("error_log", []) + [error_message],
            "sandbox_status": "error"
        }


def cleanup_sandbox(state: IsolatedEnvironmentState) -> Dict[str, Any]:
    """Clean up sandbox resources if requested."""
    
    # Check if cleanup is requested in the user message
    user_message = state["messages"][-1].content.lower() if state["messages"] else ""
    
    if "cleanup" in user_message or "destroy" in user_message or "remove sandbox" in user_message:
        return {
            "messages": [AIMessage(content="Sandbox cleanup requested. Use the destroy_daytona_sandbox tool to remove the sandbox when you're done.")],
            "sandbox_status": "cleanup_requested"
        }
    
    return {
        "messages": [AIMessage(content="Sandbox remains active for further code execution.")],
        "sandbox_status": state.get("sandbox_status", "active")
    }


def create_isolated_environment_workflow():
    """Create the isolated environment agent workflow."""
    
    # Create the state graph
    workflow = StateGraph(IsolatedEnvironmentState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_sandbox)
    workflow.add_node("execute", execute_code_task)
    workflow.add_node("cleanup", cleanup_sandbox)
    
    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "execute")
    workflow.add_edge("execute", "cleanup")
    workflow.add_edge("cleanup", END)
    
    # Compile the workflow
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def run_isolated_environment_example(query: str) -> Dict[str, Any]:
    """Run an example with the isolated environment agent."""
    
    print(f"🔒 Isolated Environment Agent Processing: {query}")
    
    # Create the workflow
    app = create_isolated_environment_workflow()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "current_sandbox": None,
        "sandbox_status": "not_initialized",
        "execution_history": [],
        "files_created": [],
        "error_log": []
    }
    
    # Run the workflow
    try:
        config = {"configurable": {"thread_id": "isolated_env_thread"}}
        final_state = app.invoke(initial_state, config)
        
        # Extract the final response
        final_messages = final_state.get("messages", [])
        final_response = final_messages[-1].content if final_messages else "No response generated"
        
        print(f"✅ Isolated Environment Agent Response: {final_response}")
        
        return {
            "final_response": final_response,
            "sandbox_status": final_state.get("sandbox_status", "unknown"),
            "execution_history": final_state.get("execution_history", []),
            "files_created": final_state.get("files_created", []),
            "error_log": final_state.get("error_log", [])
        }
        
    except Exception as e:
        error_message = f"Error in isolated environment workflow: {str(e)}"
        print(f"❌ Error: {error_message}")
        
        return {
            "final_response": error_message,
            "sandbox_status": "error",
            "execution_history": [],
            "files_created": [],
            "error_log": [error_message]
        }


# Example usage and testing
if __name__ == "__main__":
    # Test queries for the isolated environment agent
    test_queries = [
        "Create a sandbox and execute this Python code: print('Hello from isolated environment!')",
        "Write a Python script that calculates the factorial of 10 and save it to a file",
        "Clone a simple Python repository and run its tests in the sandbox",
        "Create a data analysis script that generates a simple plot and save the results"
    ]
    
    print("🚀 Testing Isolated Environment Agent with Daytona Integration")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        result = run_isolated_environment_example(query)
        
        print(f"📊 Sandbox Status: {result['sandbox_status']}")
        print(f"📁 Files Created: {len(result['files_created'])}")
        print(f"⚠️  Errors: {len(result['error_log'])}")
        
        if result['error_log']:
            print("🔍 Error Details:")
            for error in result['error_log']:
                print(f"   - {error}")
        
        print("\n" + "=" * 60)