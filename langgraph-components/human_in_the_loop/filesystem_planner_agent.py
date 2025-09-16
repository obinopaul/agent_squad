"""
Filesystem Planner Agent

This agent creates and manages todo.md files with structured plans, then executes tasks
while updating the plan. It can work with actual filesystem operations or manage plans
in state variables for flexibility.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Annotated, Sequence, TypedDict, Optional
import operator
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from utils import get_model, AgentState, create_agent_prompt, PLANNER_PROMPT


# Define the state for the filesystem planner agent
class FilesystemPlannerState(TypedDict):
    """State for filesystem planner agent workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_plan: str  # The todo.md content or plan state
    plan_file_path: Optional[str]  # Path to the todo.md file if using filesystem
    completed_tasks: List[str]
    current_task: Optional[str]
    task_history: List[Dict[str, Any]]
    use_filesystem: bool  # Whether to use actual files or state variables
    workspace_path: str  # Working directory path


class FileSystemTool(BaseTool):
    """Tool for basic filesystem operations."""
    
    name: str = "filesystem_operation"
    description: str = """Perform filesystem operations like creating directories, listing files, reading/writing files.
    Operations: create_dir, list_files, read_file, write_file, delete_file, file_exists
    """
    
    def _run(self, operation: str, path: str, content: str = "", **kwargs) -> str:
        """Execute filesystem operations."""
        try:
            path_obj = Path(path)
            
            if operation == "create_dir":
                path_obj.mkdir(parents=True, exist_ok=True)
                return f"Directory created: {path}"
            
            elif operation == "list_files":
                if path_obj.is_dir():
                    files = [str(f) for f in path_obj.iterdir()]
                    return f"Files in {path}: {files}"
                else:
                    return f"Path {path} is not a directory"
            
            elif operation == "read_file":
                if path_obj.exists():
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return f"Content of {path}:\n{content}"
                else:
                    return f"File {path} does not exist"
            
            elif operation == "write_file":
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(path_obj, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File written successfully: {path}"
            
            elif operation == "delete_file":
                if path_obj.exists():
                    if path_obj.is_file():
                        path_obj.unlink()
                        return f"File deleted: {path}"
                    else:
                        return f"Path {path} is not a file"
                else:
                    return f"File {path} does not exist"
            
            elif operation == "file_exists":
                exists = path_obj.exists()
                return f"File {path} exists: {exists}"
            
            else:
                return f"Unknown operation: {operation}"
                
        except Exception as e:
            return f"Error performing {operation} on {path}: {str(e)}"


class TodoManagerTool(BaseTool):
    """Tool for managing todo.md files and plan structures."""
    
    name: str = "todo_manager"
    description: str = """Manage todo.md files and plan structures.
    Operations: create_plan, update_plan, mark_completed, add_task, get_current_task, get_plan_status
    """
    
    def _run(self, operation: str, plan_content: str = "", task: str = "", 
             file_path: str = "", use_filesystem: bool = True, **kwargs) -> str:
        """Manage todo plans."""
        try:
            if operation == "create_plan":
                # Create a structured todo.md plan
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                plan_template = f"""# Todo Plan
Created: {timestamp}

## Overview
{plan_content}

## Tasks
- [ ] Task 1: [To be defined]
- [ ] Task 2: [To be defined]
- [ ] Task 3: [To be defined]

## Completed Tasks
(None yet)

## Notes
- Plan created by Filesystem Planner Agent
- Tasks will be updated as work progresses
"""
                
                if use_filesystem and file_path:
                    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(plan_template)
                    return f"Todo plan created at: {file_path}"
                else:
                    return plan_template
            
            elif operation == "update_plan":
                # Update existing plan with new content
                if use_filesystem and file_path and Path(file_path).exists():
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(plan_content)
                    return f"Plan updated at: {file_path}"
                else:
                    return plan_content
            
            elif operation == "mark_completed":
                # Mark a task as completed in the plan
                if use_filesystem and file_path and Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Simple task completion marking
                    updated_content = content.replace(f"- [ ] {task}", f"- [x] {task}")
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    return f"Task marked as completed: {task}"
                else:
                    # Return updated content for state management
                    updated_content = plan_content.replace(f"- [ ] {task}", f"- [x] {task}")
                    return updated_content
            
            elif operation == "add_task":
                # Add a new task to the plan
                new_task_line = f"- [ ] {task}"
                
                if use_filesystem and file_path and Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add task under the Tasks section
                    if "## Tasks" in content:
                        content = content.replace("## Tasks", f"## Tasks\n{new_task_line}")
                    else:
                        content += f"\n{new_task_line}"
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    return f"Task added: {task}"
                else:
                    return f"{plan_content}\n{new_task_line}"
            
            elif operation == "get_current_task":
                # Get the next uncompleted task
                content = plan_content
                if use_filesystem and file_path and Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                # Find first uncompleted task
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('- [ ]'):
                        task_text = line.strip()[5:].strip()  # Remove "- [ ] "
                        return f"Current task: {task_text}"
                
                return "No uncompleted tasks found"
            
            elif operation == "get_plan_status":
                # Get overall plan status
                content = plan_content
                if use_filesystem and file_path and Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                total_tasks = content.count('- [ ]') + content.count('- [x]')
                completed_tasks = content.count('- [x]')
                
                return f"Plan status: {completed_tasks}/{total_tasks} tasks completed"
            
            else:
                return f"Unknown todo operation: {operation}"
                
        except Exception as e:
            return f"Error in todo manager operation {operation}: {str(e)}"


class PlanUpdateTool(BaseTool):
    """Tool for updating and refining plans based on progress."""
    
    name: str = "plan_updater"
    description: str = """Update and refine plans based on task progress and new requirements.
    Operations: refine_plan, add_subtasks, reorganize_tasks, update_priorities
    """
    
    def _run(self, operation: str, current_plan: str = "", updates: str = "", 
             file_path: str = "", use_filesystem: bool = True, **kwargs) -> str:
        """Update and refine plans."""
        try:
            if operation == "refine_plan":
                # Refine the plan based on new information
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                refined_plan = f"{current_plan}\n\n## Plan Refinement ({timestamp})\n{updates}\n"
                
                if use_filesystem and file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(refined_plan)
                    return f"Plan refined and saved to: {file_path}"
                else:
                    return refined_plan
            
            elif operation == "add_subtasks":
                # Add subtasks to existing tasks
                subtask_section = f"\n### Subtasks\n{updates}\n"
                updated_plan = current_plan + subtask_section
                
                if use_filesystem and file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_plan)
                    return f"Subtasks added to plan"
                else:
                    return updated_plan
            
            elif operation == "reorganize_tasks":
                # Reorganize tasks based on priorities or dependencies
                reorganized_plan = f"{current_plan}\n\n## Task Reorganization\n{updates}\n"
                
                if use_filesystem and file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(reorganized_plan)
                    return f"Tasks reorganized"
                else:
                    return reorganized_plan
            
            elif operation == "update_priorities":
                # Update task priorities
                priority_update = f"{current_plan}\n\n## Priority Updates\n{updates}\n"
                
                if use_filesystem and file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(priority_update)
                    return f"Priorities updated"
                else:
                    return priority_update
            
            else:
                return f"Unknown plan update operation: {operation}"
                
        except Exception as e:
            return f"Error in plan update operation {operation}: {str(e)}"


def get_filesystem_tools() -> List[BaseTool]:
    """Get all filesystem and planning tools."""
    return [
        FileSystemTool(),
        TodoManagerTool(),
        PlanUpdateTool()
    ]


# Extended system prompt for filesystem planner
FILESYSTEM_PLANNER_PROMPT = f"""{PLANNER_PROMPT}

You are an advanced filesystem planner agent that specializes in creating, managing, and executing structured plans using todo.md files and filesystem operations.

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

Always start by creating a comprehensive plan, then execute it systematically while keeping the plan updated."""


def create_filesystem_planner_agent():
    """Create a ReAct agent for filesystem planning and execution."""
    
    # Get the language model
    llm = get_model()
    
    # Get filesystem and planning tools
    tools = get_filesystem_tools()
    
    # Create the ReAct agent with filesystem tools
    agent = create_react_agent(
        llm,
        tools,
        state_modifier=FILESYSTEM_PLANNER_PROMPT
    )
    
    return agent


# Node functions for the workflow
def initialize_workspace(state: FilesystemPlannerState) -> Dict[str, Any]:
    """Initialize the workspace and determine filesystem usage."""
    
    # Set up workspace path
    workspace_path = state.get("workspace_path", "./planner_workspace")
    use_filesystem = state.get("use_filesystem", True)
    
    if use_filesystem:
        # Create workspace directory
        Path(workspace_path).mkdir(parents=True, exist_ok=True)
        plan_file_path = os.path.join(workspace_path, "todo.md")
    else:
        plan_file_path = None
    
    return {
        "messages": [AIMessage(content=f"Workspace initialized at: {workspace_path}")],
        "workspace_path": workspace_path,
        "plan_file_path": plan_file_path,
        "use_filesystem": use_filesystem
    }


def create_initial_plan(state: FilesystemPlannerState) -> Dict[str, Any]:
    """Create the initial todo.md plan."""
    
    # Create the filesystem planner agent
    agent = create_filesystem_planner_agent()
    
    # Get the user's request
    user_message = state["messages"][-1].content if state["messages"] else ""
    
    # Create planning prompt
    planning_prompt = f"""Create a comprehensive todo.md plan for this request: {user_message}

Please use the todo_manager tool to create a structured plan with:
1. Clear overview of the task
2. Broken down subtasks with checkboxes
3. Proper organization and priorities
4. Timestamps and notes

Workspace path: {state.get('workspace_path', './planner_workspace')}
Use filesystem: {state.get('use_filesystem', True)}
"""
    
    try:
        response = agent.invoke({
            "messages": [HumanMessage(content=planning_prompt)]
        })
        
        # Extract the agent's response
        agent_messages = response.get("messages", [])
        final_message = agent_messages[-1] if agent_messages else AIMessage(content="Plan creation failed")
        
        # Update the current plan (this would be extracted from the agent's tool usage)
        current_plan = "# Initial Plan Created\nPlan details will be populated by the agent's tool usage."
        
        return {
            "messages": [final_message],
            "current_plan": current_plan
        }
        
    except Exception as e:
        error_message = f"Error creating initial plan: {str(e)}"
        return {
            "messages": [AIMessage(content=error_message)],
            "current_plan": f"# Error in Plan Creation\n{error_message}"
        }


def execute_plan_tasks(state: FilesystemPlannerState) -> Dict[str, Any]:
    """Execute tasks from the plan systematically."""
    
    # Create the filesystem planner agent
    agent = create_filesystem_planner_agent()
    
    # Create execution prompt
    execution_prompt = f"""Now execute the tasks from the plan systematically:

Current plan: {state.get('current_plan', 'No plan available')}
Workspace: {state.get('workspace_path', './planner_workspace')}

Please:
1. Get the current task using todo_manager
2. Execute the task step by step
3. Mark completed tasks
4. Update the plan as needed
5. Move to the next task

Continue until all tasks are completed or you need user input."""
    
    try:
        response = agent.invoke({
            "messages": [HumanMessage(content=execution_prompt)]
        })
        
        # Extract the agent's response
        agent_messages = response.get("messages", [])
        final_message = agent_messages[-1] if agent_messages else AIMessage(content="Task execution completed")
        
        # Update task history
        task_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "task_execution",
            "status": "completed"
        }
        
        updated_history = state.get("task_history", []) + [task_entry]
        
        return {
            "messages": [final_message],
            "task_history": updated_history
        }
        
    except Exception as e:
        error_message = f"Error executing plan tasks: {str(e)}"
        return {
            "messages": [AIMessage(content=error_message)]
        }


def finalize_plan(state: FilesystemPlannerState) -> Dict[str, Any]:
    """Finalize the plan and provide summary."""
    
    # Create summary of completed work
    workspace_path = state.get("workspace_path", "./planner_workspace")
    plan_file_path = state.get("plan_file_path")
    task_history = state.get("task_history", [])
    
    summary = f"""Plan execution completed!

Workspace: {workspace_path}
Plan file: {plan_file_path if plan_file_path else 'State-based plan'}
Tasks executed: {len(task_history)}

The filesystem planner agent has successfully:
1. Created a structured todo.md plan
2. Executed tasks systematically
3. Updated progress throughout the process
4. Maintained organized workspace

Check the workspace directory for all created files and the updated todo.md plan."""
    
    return {
        "messages": [AIMessage(content=summary)]
    }


def create_filesystem_planner_workflow():
    """Create the filesystem planner agent workflow."""
    
    # Create the state graph
    workflow = StateGraph(FilesystemPlannerState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_workspace)
    workflow.add_node("create_plan", create_initial_plan)
    workflow.add_node("execute_tasks", execute_plan_tasks)
    workflow.add_node("finalize", finalize_plan)
    
    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "create_plan")
    workflow.add_edge("create_plan", "execute_tasks")
    workflow.add_edge("execute_tasks", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile the workflow
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app


def run_filesystem_planner_example(query: str, use_filesystem: bool = True, 
                                 workspace_path: str = "./planner_workspace") -> Dict[str, Any]:
    """Run an example with the filesystem planner agent."""
    
    print(f"📁 Filesystem Planner Agent Processing: {query}")
    print(f"📂 Workspace: {workspace_path}")
    print(f"💾 Using filesystem: {use_filesystem}")
    
    # Create the workflow
    app = create_filesystem_planner_workflow()
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "current_plan": "",
        "plan_file_path": None,
        "completed_tasks": [],
        "current_task": None,
        "task_history": [],
        "use_filesystem": use_filesystem,
        "workspace_path": workspace_path
    }
    
    # Run the workflow
    try:
        config = {"configurable": {"thread_id": "filesystem_planner_thread"}}
        final_state = app.invoke(initial_state, config)
        
        # Extract the final response
        final_messages = final_state.get("messages", [])
        final_response = final_messages[-1].content if final_messages else "No response generated"
        
        print(f"✅ Filesystem Planner Agent Response: {final_response}")
        
        return {
            "final_response": final_response,
            "current_plan": final_state.get("current_plan", ""),
            "workspace_path": final_state.get("workspace_path", ""),
            "plan_file_path": final_state.get("plan_file_path"),
            "completed_tasks": final_state.get("completed_tasks", []),
            "task_history": final_state.get("task_history", []),
            "use_filesystem": final_state.get("use_filesystem", True)
        }
        
    except Exception as e:
        error_message = f"Error in filesystem planner workflow: {str(e)}"
        print(f"❌ Error: {error_message}")
        
        return {
            "final_response": error_message,
            "current_plan": "",
            "workspace_path": workspace_path,
            "plan_file_path": None,
            "completed_tasks": [],
            "task_history": [],
            "use_filesystem": use_filesystem
        }


# Example usage and testing
if __name__ == "__main__":
    # Test queries for the filesystem planner agent
    test_queries = [
        "Create a Python web scraping project with proper structure and documentation",
        "Plan and implement a data analysis pipeline for CSV files",
        "Set up a machine learning project with model training and evaluation",
        "Create a REST API with authentication and database integration"
    ]
    
    print("🚀 Testing Filesystem Planner Agent")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        # Test with filesystem
        result_fs = run_filesystem_planner_example(
            query, 
            use_filesystem=True, 
            workspace_path=f"./test_workspace_{i}"
        )
        
        print(f"📊 Plan Status: {'Created' if result_fs['current_plan'] else 'Failed'}")
        print(f"📁 Workspace: {result_fs['workspace_path']}")
        print(f"📄 Plan File: {result_fs['plan_file_path']}")
        print(f"✅ Completed Tasks: {len(result_fs['completed_tasks'])}")
        print(f"📋 Task History: {len(result_fs['task_history'])}")
        
        print("\n" + "=" * 60)