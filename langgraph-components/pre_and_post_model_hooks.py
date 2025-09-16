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
from typing import Sequence
from langgraph.types import interrupt
from langgraph.graph.message import RemoveMessage
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langchain_core.messages import ToolMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.types import Send
from dotenv import load_dotenv

load_dotenv()

# The pre- and post-model hooks in the create_react_agent function are powerful tools that allow you to modify the agent's behavior before and after the LLM call. These hooks are essential for customizing the agent's interactions with the model, ensuring that it behaves according to your specific needs.

# Pre-Model Hook:
    # The pre-model hook runs before the LLM call and is useful for modifying or condensing the messages before they are sent to the model. It allows you to manipulate the state or perform tasks like:
    # Trimming or summarizing message history to make the input more efficient.
    # Injecting custom system messages to guide the LLM’s behavior.
    # Manipulating inputs by, for instance, adding context, changing formats, or preprocessing data.


# Memory Summarization with Threshold

    # Trimming or summarizing message history to make the input more efficient.
    # 1. Models for the agent and the summarizer
    main_llm = ChatOpenAI(model="gpt-4o")
    summarizer_llm = ChatOpenAI(model="gpt-3.5-turbo")

    # 2. The Production-Grade Pre-Model Hook for Memory Summarization
    MEMORY_THRESHOLD = 10  # Summarize when history exceeds 10 messages

    def condense_messages_hook(state: dict) -> dict:
        """
        A pre-model hook to manage conversation history. If the number of messages
        exceeds a threshold, it summarizes the middle part of the conversation.
        """
        messages: Sequence[BaseMessage] = state["messages"]

        if len(messages) <= MEMORY_THRESHOLD:
            return {}

        print(f"⚠️ Condensing message history from {len(messages)} messages.")

        # 1. Identify which messages to keep and which to summarize
        system_prompt = next((msg for msg in messages if isinstance(msg, SystemMessage)), None)
        messages_to_summarize = messages[1:-4]  # Summarize all but the first (system) and last 4
        last_four_messages = messages[-4:]

        # 2. Create the summarization prompt
        summarization_prompt = (
            "Your task is to create a concise summary of the following conversation. "
            "This summary will be used as context for a helpful AI assistant. "
            "Include all key details, decisions, and topics discussed.\n\n"
            "--- CONVERSATION --- \n"
            f"{messages_to_summarize}"
        )

        # 3. Call the summarizer LLM
        summary_message_content = summarizer_llm.invoke(summarization_prompt).content
        summary_message = AIMessage(content=f"Summary of earlier conversation: {summary_message_content}")

        # 4. Construct the new message list
        new_messages = []
        if system_prompt:
            new_messages.append(system_prompt)
        new_messages.extend([summary_message] + last_four_messages)

        print(f"✅ History condensed to {len(new_messages)} messages.")

        # 5. Return the state update
        return {
            "messages": [RemoveMessage(id=[m.id for m in messages])] + new_messages
        }

    # 3. Create the agent with the hook
    tools = [lambda flight_number: f"Flight {flight_number} status is on time."]
    agent_executor = create_react_agent(
        model=main_llm,
        tools=tools,
        pre_model_hook=condense_messages_hook,
        prompt=SystemMessage(content="You are a helpful flight assistant."),
    )



# Context Injection (Dynamic System Messages)

    def inject_dynamic_system_message(state: dict) -> dict:
        """
        Dynamically injects a system message depending on the current conversation.
        """
        messages = state["messages"]

        # If the conversation is about flights, we use a specific system message
        if any("flight" in msg.content.lower() for msg in messages):
            system_msg = SystemMessage(content="You are a flight booking assistant.")
        else:
            system_msg = SystemMessage(content="You are a general assistant.")
        
        print(f"Injecting system message: {system_msg.content}")

        return {
            "messages": [system_msg] + messages
        }

    # Use it in the agent
    agent_executor_with_dynamic_message = create_react_agent(
        model=main_llm,
        tools=tools,
        pre_model_hook=inject_dynamic_system_message,
        prompt=SystemMessage(content="You are a helpful assistant."),
)





# Post-Model Hook
    # The post-model hook runs after the LLM call and can be used to handle post-processing, such as:
    # Logging or modifying the model's response.
    # Implementing guardrails like content filtering, validation, or human-in-the-loop processes.
    # Injecting additional processing like feedback loops or altering the output based on certain criteria.
    
    

# Guardrails for Content Moderation
    import re

    def content_moderation_guardrails(response: AIMessage, config: dict) -> AIMessage:
        """
        Post-model hook to enforce guardrails and check if the model's response contains harmful content.
        """
        harmful_keywords = ["violence", "hate", "discrimination"]
        
        # Check if the response contains harmful keywords
        for keyword in harmful_keywords:
            if re.search(rf"\b{keyword}\b", response.content, re.IGNORECASE):
                print(f"⚠️ Harmful content detected: {keyword}")
                # Replace harmful content with a neutral response
                response.content = "I'm sorry, I cannot assist with that topic."
        
        print(f"✅ Response after moderation: {response.content}")
        
        return response

    # Using it in the agent
    agent_with_moderation = create_react_agent(
        model=main_llm,
        tools=tools,
        post_model_hook=content_moderation_guardrails,
        prompt=SystemMessage(content="You are a responsible assistant."),
    )


# Logging and Feedback Loop for Continuous Improvement

    def log_and_feedback_hook(response: AIMessage, config: dict) -> AIMessage:
        """
        Post-model hook for logging and creating a feedback loop for model performance improvement.
        """
        # Log the model's response
        with open("model_responses.log", "a") as log_file:
            log_file.write(f"Model Response: {response.content}\n")
        
        # Example of a feedback loop: If the response mentions "weather", we collect user feedback
        if "weather" in response.content.lower():
            print("Prompting user for feedback on weather-related response.")
            response.content += "\nWas this information helpful? Please provide feedback."

        return response

    # Using it in the agent
    agent_with_logging = create_react_agent(
        model=main_llm,
        tools=tools,
        post_model_hook=log_and_feedback_hook,
        prompt=SystemMessage(content="You are a helpful assistant."),
    )
