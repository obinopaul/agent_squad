# ==============================================================================
# Advanced LangGraph Agent with Structured Output: A Comprehensive Cheat Sheet
# ==============================================================================
# This guide breaks down the process of creating a robust LangGraph agent that
# returns structured, validated data. We will explore Pydantic for schema
# definition, advanced tool creation, and sophisticated error handling strategies.
# ==============================================================================

# --- Section 0: Setup and Imports ---
# Here, we import all the necessary libraries and load our environment variables.

import os
from typing import List, Dict, Any, Literal, Union
from dotenv import load_dotenv

# Pydantic is crucial for defining our desired output schema.
from pydantic import BaseModel, Field, validator

# LangChain and LangGraph components for building the agent.
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# These are specific components for advanced structured output control.
from langgraph.agents.structured_output import ToolStrategy
from langgraph.errors import StructuredOutputValidationError, MultipleStructuredOutputsError

# Load API keys and other environment variables from a .env file.
load_dotenv()

# ==============================================================================
# --- Section 1: Defining the Structured Output Schema ---
# ==============================================================================
# The schema is the blueprint for our desired output. Using a Pydantic BaseModel
# is the recommended approach because it allows for type validation, descriptions,
# and custom logic, which helps the agent produce accurate results.

class WeatherReport(BaseModel):
    """
    A detailed, structured report of the weather for a specific location.
    The docstring itself provides context to the LLM about the purpose of this schema.
    """
    # The `Field` function allows us to add a description, which is passed
    # directly to the model, guiding it on what data to populate.
    location: str = Field(..., description="The city and state/country of the weather report, e.g., 'San Francisco, CA'.")
    temperature_celsius: float = Field(..., description="The current temperature, converted to Celsius.")
    conditions: str = Field(..., description="A brief, one-sentence description of the current weather conditions (e.g., 'Clear skies and sunny').")
    
    # Using `Literal` gives the model specific choices.
    sentiment: Literal["positive", "neutral", "negative"] = Field(description="The overall sentiment of the weather report.")

    # We can even include complex types like lists.
    key_points: List[str] = Field(description="A list of 2-3 key takeaways from the weather report, in lowercase.")

    # Custom validators allow us to enforce our own logic. If validation fails,
    # the error handling strategy (defined in Section 4) will be triggered,
    # prompting the agent to self-correct.
    @validator('temperature_celsius')
    def temperature_must_be_realistic(cls, v):
        if not -100 < v < 100:
            # This error message can be passed back to the model.
            raise ValueError("Temperature is unrealistic. The value must be between -100 and 100 Celsius.")
        return v

# ==============================================================================
# --- Section 2: Defining Tools for the Agent ---
# ==============================================================================
# Tools give the agent capabilities to interact with the outside world, like
# searching the web or accessing a database. The `@tool` decorator is the
# modern, recommended way to define them.

@tool
def tavily_web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Performs a web search using the Tavily search engine to find up-to-date
    information based on the user's query.
    The tool's docstring is crucial as it tells the agent WHEN to use this tool.
    """
    try:
        search_tool = TavilySearchResults(max_results=max_results)
        return search_tool.invoke({"query": query})
    except Exception as e:
        return [{"error": f"An error occurred during the search: {str(e)}"}]


checkpointer = InMemorySaver()
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

# ==============================================================================
# --- Section 3: Choosing a Structured Output Strategy ---
# ==============================================================================
# LangGraph offers different strategies to enforce structured output. Choosing
# the right one depends on your model's capabilities and your need for control.

# --- Option A: ProviderStrategy (Simple & Reliable) ---
# If your model (like GPT-4o, Claude 3, Grok) supports native structured output
# (also called JSON mode or tool calling), LangGraph automatically uses this
# strategy. It's the most reliable method. You would simply pass the class:
#
# response_format=WeatherReport
agent = create_react_agent(
    model=llm,
    tools=[tavily_web_search],
    checkpointer=checkpointer,
    response_format=WeatherReport,  # We pass our advanced strategy here
)
# LangGraph handles the rest. This is functionally equivalent to:
# from langgraph.agents.structured_output import ProviderStrategy
# response_format=ProviderStrategy(WeatherReport)



# --- Option B: ToolStrategy (Advanced Control & Compatibility) ---
# This strategy works with any model that supports tool calling, even if it
# doesn't have a native "JSON mode". It gives you fine-grained control over
# error handling and messaging, making it ideal for building robust applications.
# We will use this strategy for our cheat sheet.

# ==============================================================================
# --- Section 4: Advanced Error Handling with ToolStrategy ---
# ==============================================================================
# Models can make mistakes. A robust error handling strategy is key to building
# reliable agents that can self-correct.

def custom_error_handler(error: Exception) -> str:
    """
    A custom function to generate specific, helpful error messages for the model.
    This function is a 'Callable' that takes the exception and returns a string.
    """
    # This gives us visibility into what kind of error occurred.
    print(f"--- Encountered validation error: {type(error).__name__} ---")
    
    if isinstance(error, StructuredOutputValidationError):
        # This error occurs when the model's output doesn't match the Pydantic schema.
        # We can provide detailed feedback to help it fix the output.
        return f"Validation Error: The generated output is not in the correct format. Details from Pydantic: {error}. Please correct your output to match the `WeatherReport` schema."
    
    elif isinstance(error, MultipleStructuredOutputsError):
        # This error occurs if the model tries to return more than one structured response.
        return "You have returned multiple structured outputs. Please consolidate them into a single, valid `WeatherReport` object."
        
    else:
        # A fallback for any other unexpected errors.
        return f"An unexpected error occurred: {str(error)}. Please review your output and try again."

# Now, we configure the ToolStrategy with our schema and custom error handler.
structured_output_strategy = ToolStrategy(
    schema=WeatherReport,
    handle_errors=custom_error_handler, # The most robust option.
    tool_message_content="Weather report successfully generated and validated. The user can now see the result." # Custom message for the trace.
)

# ==============================================================================
# --- Section 5: Assembling and Running the Agent ---
# ==============================================================================

# 1. Initialize the LLM
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o", temperature=0)

# 2. Setup memory to persist conversation state
checkpointer = InMemorySaver()

# 3. Create the agent using the prebuilt `create_react_agent`
agent = create_react_agent(
    model=llm,
    tools=[tavily_web_search],
    checkpointer=checkpointer,
    response_format=structured_output_strategy,  # We pass our advanced strategy here
)

# 4. Define the agent invocation configuration
# The `thread_id` ensures that we can have separate, stateful conversations.
config = {"configurable": {"thread_id": "weather_session_1"}}

# 5. Define the user's input
user_input = "What is the weather in Norman, Oklahoma right now? Also, what's the sentiment of the weather?"

# 6. Invoke the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": user_input}]},
    config
)

# ==============================================================================
# --- Section 6: Interpreting the Results ---
# ==============================================================================

# The final, validated Pydantic object is in the 'structured_response' key.
print("\n" + "="*50)
print("✅ Final Structured Response:")
print("="*50)
final_report: WeatherReport = response.get("structured_response")

if final_report:
    # `model_dump_json` provides a clean JSON representation.
    print(final_report.model_dump_json(indent=2))
else:
    print("No structured response was generated. Check the trace for errors.")
    print("Final message content:", response['messages'][-1].content)


# It's crucial to inspect the full trace to understand the agent's reasoning.
print("\n" + "="*50)
print("🔎 Full Conversation Trace:")
print("="*50)
for message in response['messages']:
    # `pretty_print` gives a readable view of each step in the agent's process.
    message.pretty_print()
    print("-" * 30)
