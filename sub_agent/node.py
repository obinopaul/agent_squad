from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from src.agent.state import State, Todo
from langchain_tavily.tavily_search import TavilySearch


@tool
def write_todo(todos: list[str], tool_call_id: Annotated[str, InjectedToolCallId]):
    """Tool for writing todos, can only be used once at the beginning. Use update_todo for subsequent updates.
    Arguments:
    todos: list[str], the list of todos to be written, each string represents a todo content.
    """
    return Command(
        update={
            "todo": [
                {"content": todo, "status": "pending" if index > 0 else "in_progress"}
                for index, todo in enumerate(todos)
            ],
            "messages": [
                ToolMessage(
                    content=f"Todo list written successfully, please execute the task {todos[0]} next (no need to modify its status to in_progress)",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def update_todo(
    update_todos: list[Todo],
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[State, InjectedState],
):
    """Tool for updating todos, can be used multiple times to update the todo list.
    Arguments:
    update_todos: list[Todo], the list of todos to update. It's a list of dictionaries where each dictionary contains:
    - content: str, todo content
    - status: str, todo status, can be either "pending", "in_progress", or "done". Only "in_progress" or "done" can be passed.

    Note: At least one todo with status "in_progress" and at least one with status "done" must be present in the update.
    """
    todo_list = state["todo"] if "todo" in state else []

    updated_todo_list = []

    for update_todo in update_todos:
        for todo in todo_list:
            if todo["content"] == update_todo["content"]:
                todo["status"] = update_todo["status"]
                updated_todo_list.append(todo)

    if len(updated_todo_list) < len(update_todos):
        raise ValueError(
            "The following todos were not found: "
            + ",".join([todo["content"] for todo in update_todos if todo not in updated_todo_list])
            + " Please check the todo list, the current todos are: "
            + "\n".join([todo["content"] for todo in todo_list if todo["status"] != "done"])
        )

    return Command(
        update={
            "todo": todo_list,
            "messages": [
                ToolMessage(content="Todo list updated successfully", tool_call_id=tool_call_id)
            ],
        }
    )


@tool
async def transfor_task_to_subagent(
    content: Annotated[
        str, "The content of the todo task to be executed, must match exactly with the content field of the todo list"
    ],
):
    """Tool for executing todo tasks.

    Arguments:
    content: str, the content of the todo task to be executed, must match exactly with the todo list.

    Example todo list:
    [
        {"content":"Task 1", "status":"done"},
        {"content":"Task 2", "status":"in_progress"},
        {"content":"Task 3", "status":"pending"}
    ]
    """
    return "Transform success!"


@tool
def write_note(
    file_name: Annotated[str, "Note name"],
    content: Annotated[str, "Note content"],
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[State, InjectedState],
):
    """Tool for writing notes.

    Arguments:
    content: str, the content of the note.
    """
    if file_name in state["note"] if "note" in state else {}:
        notes = state["note"] if "note" in state else {}
        file_name = file_name + "_" + str(len(notes[file_name]))

    return Command(
        update={
            "note": {file_name: content},
            "write_note_messages": [
                ToolMessage(
                    content=f"Note {file_name} written successfully, content is: {content}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def ls(state: Annotated[State, InjectedState]):
    """List notes.

    Returns:
    list[str], the list of note names.
    """
    notes = state["note"] if "note" in state else {}
    return list(notes.keys())


@tool
def query_note(file_name: str, state: Annotated[State, InjectedState]):
    """Query a note.

    Arguments:
    file_name: the name of the note.

    Returns:
    str, the content of the queried note.
    """
    notes = state["note"] if "note" in state else {}

    return notes.get(file_name, "Note not found")


@tool
def get_weather(city: str):
    """Query the weather.

    Arguments:
    city: name of the city.

    Returns:
    str, the weather information.
    """
    return f"The weather in {city} is sunny, with a temperature of 25°C."


tavily_search = TavilySearch(
    max_results=5,
    description="Internet search tool for retrieving the latest web information and materials. Note: To control context length and reduce costs, this tool can only be used once per task.",
)
