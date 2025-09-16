from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import os
from dotenv import load_dotenv
import pyowm
from langchain_community.tools.openweathermap.tool import OpenWeatherMapQueryRun

load_dotenv()


os.environ["OPENWEATHERMAP_API_KEY"] = "22bac1f7e8693517e2d902f9dbbdce9b"
weather_tool = OpenWeatherMapQueryRun(openweathermap_api_key=os.getenv("OPENWEATHERMAP_API_KEY"))

# Define a structured model for weather response
class WeatherResponse(BaseModel):
    """Structured response to present weather data"""
    temperature: float = Field(description="The temperature in fahrenheit")
    wind_direction: str = Field(description="The direction of the wind in abbreviated form")
    wind_speed: float = Field(description="The speed of the wind in km/h")


# Define AgentState class, which will handle messages and the final structured response
class AgentState(MessagesState):
    final_response: WeatherResponse
    

# Initialize the model and bind tools for use with the agent
tools = [weather_tool, WeatherResponse]
model = ChatAnthropic(model="claude-3-opus-20240229", api_key=os.getenv("ANTHROPIC_API_KEY"))
model_with_tools = model.bind_tools(tools, tool_choice="any")


def call_model(state: AgentState):
    """
    Calls the model to get the weather data.
    Uses the weather tool to fetch data and process the result.
    """
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def respond(state: AgentState):
    """
    Formats and responds to the user with the final structured response.
    Converts raw tool output into a structured WeatherResponse object.
    """
    # Extract the last tool call (weather tool call)
    weather_tool_call = state["messages"][-1].tool_calls[0]

    # Create a structured response using the weather data
    try:
        response = WeatherResponse(**weather_tool_call["args"])
    except Exception as e:
        return {"final_response": {"error": str(e)}, "messages": []}

    # Tool message indicating that structured output is ready
    tool_message = {
        "type": "tool",
        "content": "Here is your structured response",
        "tool_call_id": weather_tool_call["id"],
    }

    return {"final_response": response, "messages": [tool_message]}


def should_continue(state: AgentState):
    """
    Determines whether the agent should continue or respond based on tool call results.
    If the agent has made a valid weather tool call, it proceeds to respond to the user.
    """
    messages = state["messages"]
    last_message = messages[-1]

    if len(last_message.tool_calls) == 1 and last_message.tool_calls[0]["name"] == "WeatherResponse":
        return "respond"  # Respond with structured output
    else:
        return "continue"  # Continue to use the tool for more data


# Define the workflow for the agent
workflow = StateGraph(AgentState)

# Add nodes to the workflow
workflow.add_node("agent", call_model)
workflow.add_node("respond", respond)
workflow.add_node("tools", ToolNode(tools))

# Set the starting node as 'agent' for the workflow
workflow.set_entry_point("agent")

# Define the conditional edges for the graph
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",  # Continue using the tool
        "respond": "respond",  # Move to the response node
    },
)

# Add edges to cycle between nodes
workflow.add_edge("tools", "agent")
workflow.add_edge("respond", END)

# Compile the graph
graph = workflow.compile()


# Usage example:
answer = graph.invoke(input={"messages": [("human", "what's the weather in NYC, NY?")]})["final_response"]

# Output should be structured as WeatherResponse
print(answer)  # Expected output: WeatherResponse(temperature=80.0, wind_direction='W', wind_speed=6.0)
