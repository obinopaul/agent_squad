# ##############################################################################
# #                                                                            #
# #         LANGGRAPH MESSAGES: THE ULTIMATE CHEAT SHEET & GUIDE               #
# #                                                                            #
# ##############################################################################
#
"""
This Python file serves as a detailed, runnable documentation and cheat sheet
for understanding and using Messages in LangChain and LangGraph.

Messages are the fundamental unit of context for models. They represent the
input and output, carrying content and metadata for conversations with LLMs.

To run the code snippets, you'll need LangChain installed and an LLM provider
configured (e.g., by setting the OPENAI_API_KEY environment variable).

pip install langchain langchain_openai
"""

# --- Imports & Initial Setup ---
# We'll use placeholder models and data for some examples to ensure the script
# runs without real API calls unless explicitly intended.

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool

# Let's define a dummy model for syntax demonstration purposes.
# In a real application, you would initialize your actual chat model like this:
# from langchain_openai import ChatOpenAI
# model = ChatOpenAI(model="gpt-4o")

class FakeChatModel:
    """A fake model to demonstrate message structures without API calls."""
    def invoke(self, messages, **kwargs):
        print("\n--- Model Invoked With: ---")
        if isinstance(messages, str): # Handle simple string prompts
            messages = [HumanMessage(content=messages)]
        for msg in messages:
            print(f"  - Role: {msg.type}, Content: '{msg.content}'")
        print("---------------------------\n")
        return AIMessage(content="This is a simulated response from the AI.")

    def stream(self, messages, **kwargs):
        """Simulates a streaming response."""
        print("\n--- Model Streaming ---")
        chunks = ["This ", "is ", "a ", "streamed ", "AI ", "response."]
        for chunk_text in chunks:
            yield AIMessageChunk(content=chunk_text)
        print("-----------------------\n")

    def bind_tools(self, tools):
        """Simulates binding tools to the model."""
        print(f"\n--- Tools Bound to Model: {[t.name for t in tools]} ---")
        class ModelWithTools(self.__class__):
            def invoke(self, messages, **kwargs):
                super().invoke(messages, **kwargs)
                return AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "get_weather",
                            "args": {"location": "Oklahoma City"},
                            "id": "tool_call_12345"
                        }
                    ]
                )
        return ModelWithTools()

model = FakeChatModel()

# Define a sample tool for demonstration
@tool
def get_weather(location: str) -> str:
    """Gets the weather for a specific location."""
    if "Oklahoma" in location:
        return "It's 75°F and sunny in Oklahoma City."
    return "It's 80°F and partly cloudy."

# ##############################################################################
# # 1. CORE CONCEPTS: WHAT IS A MESSAGE?                                       #
# ##############################################################################

# A Message is an object with three main components:
#
# 1. **role**: The source of the message (e.g., 'system', 'human', 'ai', 'tool').
# 2. **content**: The payload of the message (text, images, documents, etc.).
# 3. **metadata**: Optional extra information like message IDs, tool calls, or token usage.
#
# LangChain provides four primary message types that standardize interactions
# across all Large Language Models (LLMs).

# ##############################################################################
# # 2. THE FOUR MAIN MESSAGE TYPES                                             #
# ##############################################################################

# ## 2.1. SystemMessage
# Purpose: Sets the context, instructions, or persona for the AI. It tells the
# model *how* to behave throughout the conversation.
# Analogy: It's like giving a stage actor their character notes before a play begins.

print("--- 2.1. SystemMessage Example ---")
system_message = SystemMessage(
    content="You are a helpful assistant that translates English to French."
)
print(system_message)
print("-" * 20)

# ## 2.2. HumanMessage
# Purpose: Represents input from the end-user. This is what a person
# types or provides to the model.
# Analogy: It's the user's side of a text message conversation.

print("--- 2.2. HumanMessage Example ---")
human_message = HumanMessage(
    content="Hello, how are you?"
)
print(human_message)
print("-" * 20)

# ## 2.3. AIMessage
# Purpose: Represents the output *from* the model. This includes text responses,
# decisions to use tools, and other metadata from the AI.
# Analogy: It's the AI's reply in the text message conversation.

print("--- 2.3. AIMessage Example ---")
ai_message = AIMessage(
    content="Bonjour! Comment ça va?"
)
print(ai_message)
print("-" * 20)

# ## 2.4. ToolMessage
# Purpose: Provides the *result* of a tool's execution back to the model.
# After an AIMessage requests a tool call, a ToolMessage is used to give the
# model the information it asked for.
# Analogy: If the AI asks its assistant (a tool) for a file, this is the
# message containing the file's contents.

print("--- 2.4. ToolMessage Example ---")
tool_message = ToolMessage(
    content="The tool execution returned: 'San Francisco is sunny and 70°F'",
    tool_call_id="some_unique_tool_call_id_123" # Must match the ID from the AIMessage's tool_call
)
print(tool_message)
print("-" * 20)

# ##############################################################################
# # 3. BASIC USAGE: INVOKING A MODEL                                           #
# ##############################################################################

# There are three primary ways to pass input to a model.

# ## 3.1. Simple Text Prompt (String)
# The simplest way. LangChain automatically converts the string into a HumanMessage.
# **Best for**: Single, one-off requests where conversation history isn't needed.

print("\n--- 3.1. Invoking with a simple string ---")
# This is internally converted to: model.invoke([HumanMessage(content="Write a haiku...")])
response_from_string = model.invoke("Write a haiku about fall.")
print(f"Response from string input: {response_from_string}")

# ## 3.2. List of Message Objects
# This is the standard and most powerful way to interact with chat models.
# You pass a list of messages to maintain conversational context.
# **Best for**: Multi-turn conversations, including system instructions, or multimodal input.

print("\n--- 3.2. Invoking with a list of Message objects ---")
conversation_history = [
    SystemMessage(content="You are a poetry expert."),
    HumanMessage(content="Write a haiku about spring."),
    AIMessage(content="Green shoots reach for sun,\nCherry blossoms start to bloom,\nSpring's gentle rebirth."),
    HumanMessage(content="Now, one about winter.")
]
response_from_messages = model.invoke(conversation_history)
print(f"Response from message list: {response_from_messages}")

# ## 3.3. List of Dictionaries
# You can also use the OpenAI dictionary format, which LangChain understands.
# This can be useful for compatibility or when working with data from other systems.

print("\n--- 3.3. Invoking with a list of dictionaries ---")
dict_messages = [
    {"role": "system", "content": "You are a poetry expert."},
    {"role": "user", "content": "Write a haiku about summer."},
]
response_from_dicts = model.invoke(dict_messages)
print(f"Response from dict list: {response_from_dicts}")


# ##############################################################################
# # 4. ADVANCED MESSAGE FEATURES & ATTRIBUTES                                  #
# ##############################################################################

# ## 4.1. HumanMessage with Metadata
# You can add optional metadata to messages for tracing or multi-user chats.
# **`id`**: A unique identifier for the message. Useful for logging and debugging.
# **`name`**: Identifies the user. Some models use this to distinguish between
#         different speakers in a group chat.

print("\n--- 4.1. HumanMessage with Metadata ---")
human_msg_with_meta = HumanMessage(
    content="Can you help me plan a trip?",
    id="message_uuid_v4_12345",  # For tracing
    name="Alice"                 # To identify the user
)
print(human_msg_with_meta)

# ## 4.2. AIMessage Attributes (Outputs)
# The AIMessage returned by a model is rich with information beyond just text.

# Let's simulate a response that has more attributes
simulated_ai_response = AIMessage(
    content="Of course! To start, I need to know the weather in your destination.",
    id="ai_response_uuid_67890",
    response_metadata={
        'finish_reason': 'tool_calls',
        'logprobs': None
    },
    tool_calls=[
        {
            'name': 'get_weather',
            'args': {'location': 'Paris'},
            'id': 'tool_call_abcde'
        }
    ],
    usage_metadata={
        'input_tokens': 50,
        'output_tokens': 25,
        'total_tokens': 75
    }
)

print("\n--- 4.2. Exploring AIMessage Attributes ---")
print(f"Content: {simulated_ai_response.content}")
print(f"ID: {simulated_ai_response.id}")
print(f"Tool Calls: {simulated_ai_response.tool_calls}")
print(f"Usage Metadata (Tokens): {simulated_ai_response.usage_metadata}")
print(f"Response Metadata (from provider): {simulated_ai_response.response_metadata}")

# ### Key AIMessage Attributes:
# - **`.content`**: The primary text content.
# - **`.tool_calls`**: A list of tools the model wants to execute. This is the core of agentic behavior.
# - **`.id`**: A unique ID for the AI's response message.
# - **`.usage_metadata`**: Contains token counts, if provided by the model. Essential for cost tracking.
# - **`.response_metadata`**: Raw, provider-specific information (e.g., finish reason, safety ratings).

# ## 4.3. Streaming and AIMessageChunk
# When you `.stream()` a model, you don't get a single AIMessage. Instead, you
# get a stream of `AIMessageChunk` objects. Each chunk contains a piece of the
# final message. They can be added together to reconstruct the full AIMessage.

print("\n--- 4.3. Streaming with AIMessageChunk ---")
full_response = None
for chunk in model.stream([HumanMessage(content="Tell me a very short story.")]):
    print(f"Received Chunk: '{chunk.content}' | Type: {type(chunk)}")
    if full_response is None:
        full_response = chunk
    else:
        full_response += chunk  # Chunks can be added together!

print("\n--- Reconstructed Full Message from Chunks ---")
print(f"Full Content: {full_response.content}")
print(f"Full Message Type: {type(full_response)}") # Note: it becomes an AIMessage

# ##############################################################################
# # 5. TOOL CALLING WORKFLOW (The Agentic Loop)                              #
# ##############################################################################

# This is the fundamental cycle for building agents. It uses Human, AI, and Tool messages.

print("\n--- 5. Tool Calling Full Workflow ---")

# **Step 1: User asks a question that requires a tool.**
user_question = HumanMessage(content="What's the weather like in Oklahoma City?")
print(f"Step 1: User asks -> '{user_question.content}'")

# **Step 2: Bind tools to the model and invoke it.**
# The model's response will be an AIMessage containing a `tool_calls` request.
model_with_tools = model.bind_tools([get_weather])
ai_tool_request = model_with_tools.invoke([user_question])

print(f"Step 2: AI responds with a tool call request.")
print(f"   -> Tool Call Details: {ai_tool_request.tool_calls}")

# **Step 3: Parse the AI's response and execute the requested tool.**
# In a real app, you'd have a router to call the correct function.
tool_call_request = ai_tool_request.tool_calls[0]
tool_name = tool_call_request['name']
tool_args = tool_call_request['args']
tool_call_id = tool_call_request['id']

if tool_name == "get_weather":
    tool_output = get_weather.invoke(tool_args)
    print(f"Step 3: Executing tool '{tool_name}' with args {tool_args}.")
    print(f"   -> Tool Output: '{tool_output}'")
else:
    tool_output = "Error: Tool not found."

# **Step 4: Create a ToolMessage with the result and the `tool_call_id`.**
# This ID is crucial; it tells the model which request this result is for.
tool_response_message = ToolMessage(
    content=str(tool_output),
    tool_call_id=tool_call_id
)
print(f"Step 4: Creating ToolMessage with result and ID '{tool_call_id}'.")

# **Step 5: Continue the conversation by sending the full history back to the model.**
# This includes the original question, the AI's tool request, and your tool's response.
conversation_history_for_final_answer = [
    user_question,         # Original question
    ai_tool_request,       # AI's request to use a tool
    tool_response_message  # The result of that tool call
]

final_answer = model.invoke(conversation_history_for_final_answer)
print(f"Step 5: Model receives tool result and generates the final answer.")
print(f"   -> Final AI Answer: {final_answer.content}")


# ##############################################################################
# # 6. DEEP DIVE: CONTENT BLOCKS (MULTIMODALITY & STANDARDIZATION)             #
# ##############################################################################

# A message's `.content` attribute is powerful but can be provider-specific.
# To solve this, LangChain introduced `.content_blocks`, a standardized,
# type-safe way to access a message's payload.

# ## 6.1. The "Why": .content vs. .content_blocks
#
# - **`.content`**: This is the raw payload. It can be a simple string or a list
#   of provider-native dictionaries (e.g., OpenAI's format vs. Anthropic's).
#   It's flexible but can lead to provider-specific parsing logic in your code.
#
# - **`.content_blocks`**: This is a **read-only property** that **lazily parses**
#   `.content` into a list of standardized, LangChain-defined dictionaries.
#   This allows you to write universal code that handles text, images, tool calls,
#   and reasoning steps the same way, regardless of the model provider.

print("\n--- 6.1. Example: Standardization in Action ---")
# Imagine an AI response from a provider (like Anthropic) that includes
# a "thinking" step before its final answer.
provider_specific_content = [
    {"type": "thinking", "thinking": "The user wants a list. I will start with item one."},
    {"type": "text", "text": "1. First, peel the potatoes."},
]

ai_message_from_provider = AIMessage(content=provider_specific_content)

print(f"Raw `.content` from the provider's API:\n{ai_message_from_provider.content}\n")

# Now, access the standardized `.content_blocks` property.
# LangChain automatically converts the proprietary "thinking" block into its
# standard "reasoning" block.
standardized_blocks = ai_message_from_provider.content_blocks
print(f"Standardized `.content_blocks` from LangChain:\n{standardized_blocks}")

# This means you can reliably check for `block['type'] == 'reasoning'` in your
# code without worrying about the underlying model provider.

# ## 6.2. Common Standard Content Block Types

# ### TextContentBlock
# The most common block type for text.
text_block = {"type": "text", "text": "Hello, world!"}
print(f"\n--- 6.2.1. Text Block ---\n{text_block}")

# ### ImageContentBlock
# For including images. You can use a URL or base64-encoded data.
image_block_url = {
    "type": "image_url",
    "image_url": {"url": "https://example.com/image.jpg"}
}

# You would get base64 data like this:
# import base64
# with open("path/to/image.png", "rb") as image_file:
#     b64_string = base64.b64encode(image_file.read()).decode("utf-8")
image_block_b64 = {
    "type": "image_url",
    "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..." # truncated for brevity
}
print(f"\n--- 6.2.2. Image Block (URL) ---\n{image_block_url}")

# ### ToolUseBlock
# When a model decides to use a tool, its AIMessage content will contain this block.
# Note: The `.tool_calls` attribute is often an easier way to access this info,
# but it's good to know it exists in block form too.
tool_use_block = {
    "type": "tool_use",
    "id": "tool_call_12345",
    "name": "get_weather",
    "input": {"location": "Oklahoma City"},
}
print(f"\n--- 6.2.3. Tool Use Block ---\n{tool_use_block}")


# ## 6.3. Constructing Messages with Content Blocks
# You can also construct `HumanMessage` objects using the standardized block
# format directly. This is the modern way to handle multimodal input.

print("\n--- 6.3. Creating a Multimodal Message ---")

# Let's create a message that asks a question about an image.
multimodal_human_message = HumanMessage(
    content=[
        {
            "type": "text",
            "text": "How many logos are in this image?"
        },
        {
            "type": "image_url",
            "image_url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
        }
    ]
)

print(f"Constructed Multimodal Message:")
print(f"  Type: {multimodal_human_message.type}")
print(f"  Content Payload: {multimodal_human_message.content}")

# Note that when you create a message this way, the `.content` attribute is
# populated with the list of blocks you provided. This is the correct format
# for sending to a modern multimodal model.

# ## 6.4. Serializing with Standard Blocks (output_version)
# By default, for backward compatibility, some models might not serialize their
# output using the standard block format. If you need to ensure the output
# `.content` IS in the standard format (e.g., for sending to another system),
# you can set `output_version="v1"` when initializing the model.
#
# from langchain_openai import ChatOpenAI
# model_v1 = ChatOpenAI(model="gpt-4o", output_version="v1")
#
# This tells LangChain to populate the `.content` field with the standardized
# list of blocks directly, not just make it available via `.content_blocks`.



# ##############################################################################
# # 7. ADVANCED CONTENT: MULTIMODALITY AND CONTENT BLOCKS                      #
# ##############################################################################

# A message's `.content` is not limited to strings. It can be a list of
# typed "content blocks" for multimodal inputs like images.

# ## 6.1. Multimodal Input (Text and Image)
# You can pass a list of dictionaries as the content for a HumanMessage.
# Each dictionary represents a "block" of content.

print("\n--- 6.1. Multimodal Input Example ---")

# This is how you would structure a message to send both text and an image.
# NOTE: The fake model won't process this, but this is the correct syntax for
#       a real multimodal model like GPT-4o or Claude 3.
multimodal_message = HumanMessage(
    content=[
        # A text block
        {
            "type": "text",
            "text": "What is in this image?"
        },
        # An image block (can be a URL or base64 data)
        {
            "type": "image_url",
            "image_url": {
                "url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
            },
        }
    ]
)

print(f"Constructed Multimodal Message:")
print(f"  Type: {multimodal_message.type}")
print(f"  Content: {multimodal_message.content}")

# ## 6.2. Content vs. Content Blocks
# - **`.content`**: The raw payload sent to the model. It can be a string or a list
#   of provider-native dictionaries (like the example above).
#
# - **`.content_blocks`**: A *standardized*, type-safe property that LangChain provides.
#   It lazily parses the `.content` into a consistent format, regardless of the
#   model provider. This is incredibly useful for parsing model outputs.

# Example: An AI response might include "reasoning" steps before the text.
# The raw `.content` might be specific to Anthropic or OpenAI, but
# `.content_blocks` standardizes it.

simulated_anthropic_response = AIMessage(
    content=[
        # This is a provider-specific format
        {"type": "thinking", "thinking": "The user is asking for a code example... I should prepare one."},
        {"type": "text", "text": "Here is a Python code snippet for you."},
    ]
)

print("\n--- 6.2. Comparing .content and .content_blocks ---")
print(f"Raw .content from model:\n{simulated_anthropic_response.content}")
print(f"\nStandardized .content_blocks property:\n{simulated_anthropic_response.content_blocks}")

# Notice how `{"type": "thinking"}` was parsed into `{'type': 'reasoning'}`.
# This allows you to write code that handles model reasoning steps consistently
# across different LLM providers without changing your parsing logic.

# ##############################################################################
# # 8. EXAMPLE APPLICATION: A SIMPLE CONVERSATIONAL CHATBOT                    #
# ##############################################################################

# This example ties everything together in a basic interactive loop.

def run_chatbot():
    """A simple command-line chatbot to demonstrate message history management."""
    print("\n--- 7. Starting Simple Chatbot (type 'quit' to exit) ---")

    # 1. Start with a System Message to set the AI's persona
    message_history = [
        SystemMessage("You are a helpful, friendly assistant.")
    ]

    # Use a real model for this interactive part if you have an API key set
    try:
        from langchain_openai import ChatOpenAI
        # Make sure your OPENAI_API_KEY is set in your environment
        chat_model = ChatOpenAI(model="gpt-3.5-turbo")
        print("(Using real OpenAI model for chat.)")
    except (ImportError, Exception):
        print("(Falling back to FakeChatModel for demonstration.)")
        chat_model = FakeChatModel()


    while True:
        # 2. Get user input
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            print("Chatbot session ended. Goodbye!")
            break

        # 3. Append the user's message to the history
        message_history.append(HumanMessage(content=user_input))

        # 4. Invoke the model with the entire conversation history
        ai_response = chat_model.invoke(message_history)

        # 5. Append the AI's response to the history for the next turn
        message_history.append(ai_response)

        # 6. Print the AI's response
        print(f"Assistant: {ai_response.content}")

# To run the interactive chatbot, uncomment the line below.
# Make sure your OpenAI API key is set as an environment variable.
# run_chatbot()

print("\n--- End of LangGraph Messages Cheat Sheet ---")