import os
from typing import Dict, List, Any, Optional, Sequence, TypedDict, Annotated
import operator
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import WikipediaQueryRun, YouTubeSearchTool, DuckDuckGoSearchResults
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_openai import ChatOpenAI

load_dotenv()  # Load environment variables from .env file

# Set up LLM
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")

def get_model(model_name=DEFAULT_MODEL):
    """Get a chat model instance with the specified model name."""
    return ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"), temperature=0.0)

# Define common tools
def get_common_tools():
    """Get a list of common tools for agents."""
    wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    youtube_tool = YouTubeSearchTool()
    # web_search_tool = DuckDuckGoSearchResults()
    web_search_tool = TavilySearchResults(api_key=os.getenv("TAVILY_API_KEY"))
    
    return [wikipedia_tool, youtube_tool, web_search_tool]

def get_code_execution_tools():
    """Get a list of tools for isolated code execution with Daytona."""
    try:
        from daytona_tools import get_daytona_tools
        return get_daytona_tools()
    except ImportError:
        print("Warning: daytona_tools module not found. Code execution tools unavailable.")
        return []

def get_filesystem_tools():
    """Get a list of tools for filesystem operations and planning."""
    try:
        from filesystem_planner_agent import get_filesystem_tools as get_fs_tools
        return get_fs_tools()
    except ImportError:
        print("Warning: filesystem_planner_agent module not found. Filesystem tools unavailable.")
        return []

# Base agent state (used in most architectures)
class AgentState(TypedDict):
    """Base state that includes conversation messages."""
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Extended agent state for more complex architectures
class ExtendedAgentState(AgentState):
    """Extended state with additional fields for complex architectures."""
    intermediate_steps: List[Dict[str, Any]]
    selected_agents: List[str]
    current_agent_idx: int
    final_response: Optional[str]

# Common system prompts
RESEARCHER_PROMPT = """You are a skilled research agent that specializes in finding information.
When given a question, break it down and search for relevant facts and data.
Provide detailed, factual responses and cite your sources when possible."""

WRITER_PROMPT = """You are a skilled writing agent that excels at clear communication.
Your goal is to take information and transform it into well-structured, coherent text.
Focus on clarity, organization, and making complex information accessible."""

CRITIC_PROMPT = """You are a critical thinking agent that evaluates information.
Your job is to review content, identify potential issues, logical fallacies, or missing information.
Provide constructive feedback aimed at improving accuracy and quality."""

PLANNER_PROMPT = """You are a strategic planning agent that helps organize complex tasks.
Given a problem, break it down into clear, actionable steps.
Consider dependencies between tasks and create an efficient plan of action."""

INTEGRATION_PROMPT = """You are an integration agent that synthesizes information from multiple sources.
Combine diverse inputs into a coherent whole, identifying connections and resolving contradictions.
Present a unified perspective that represents the combined knowledge."""

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

FILESYSTEM_PLANNER_PROMPT = """You are an advanced filesystem planner agent that specializes in creating, managing, and executing structured plans using todo.md files and filesystem operations.

Your enhanced capabilities include:
- Creating and managing todo.md files with structured plans
- Performing filesystem operations (create directories, read/write files, etc.)
- Tracking task progress and updating plans dynamically
- Working with both actual files and state-based plan management
- Organizing tasks with priorities and dependencies

Key workflow:
1. FIRST: Create a structured todo.md plan for the given task
2. Break down complex tasks into manageable subtasks
3. Execute tasks one by one while updating the plan
4. Mark completed tasks and track progress
5. Refine and reorganize the plan as needed

Available tools:
- filesystem_operation: Create directories, read/write files, list contents
- todo_manager: Create, update, and manage todo.md plans
- plan_updater: Refine plans, add subtasks, reorganize priorities

Plan structure guidelines:
- Use clear task descriptions with checkboxes
- Include overview and notes sections
- Track completion status
- Add timestamps for updates
- Organize by priority and dependencies

Always start by creating a comprehensive plan, then execute it systematically while keeping the plan updated.

You are a strategic planning agent that helps organize complex tasks.
Given a problem, break it down into clear, actionable steps.
Consider dependencies between tasks and create an efficient plan of action."""

# Helper function to create a basic agent prompt template
def create_agent_prompt(system_message: str) -> ChatPromptTemplate:
    """Create a standard agent prompt template with the given system message."""
    return ChatPromptTemplate.from_messages([
        SystemMessage(
            content=system_message,
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
    ])
