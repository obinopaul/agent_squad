# ##############################################################################
# #                                                                            #
# #        LANGGRAPH STREAMING: THE ULTIMATE CHEAT SHEET & GUIDE               #
# #                                                                            #
# ##############################################################################
#
"""
This Python file serves as a detailed, runnable documentation and cheat sheet
for understanding and using Streaming in LangGraph.

Streaming is essential for building responsive AI applications, providing real-time
updates as a graph executes. This guide covers everything from basic stream modes
to advanced topics like durable execution and human-in-the-loop patterns.

To run the code snippets, you'll need LangGraph and its dependencies installed:
pip install langgraph langchain_openai
"""

# --- Imports & Initial Setup ---
import uuid
from typing import TypedDict, Annotated, NotRequired
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphInterrupt
from langgraph.graph.message import add_messages

# We'll use a placeholder LLM to demonstrate streaming mechanics without API calls.
class FakeStreamingLLM:
    """A fake LLM that 'streams' a predefined response token by token."""
    def __init__(self, response: str, tags: list = None):
        self.response = response
        self.tags = tags or []

    def stream(self, messages, **kwargs):
        # Simulate receiving config with tags
        if 'config' in kwargs and 'tags' in kwargs['config']:
            self.tags.extend(kwargs['config']['tags'])
        
        for char in self.response:
            yield AIMessage(content=char)

    def with_config(self, config):
        # Allow adding tags for filtering demonstrations
        if 'tags' in config:
            self.tags.extend(config['tags'])
        return self

# ##############################################################################
# # 1. CORE CONCEPTS: WHY STREAM AND HOW?                                      #
# ##############################################################################

# LangGraph's streaming system provides real-time updates as your graph runs.
# This is crucial for good user experience, especially with slow LLM calls.

# The primary methods are:
# - `.stream()`: For synchronous, iterator-based streaming.
# - `.astream()`: For asynchronous streaming.

# You control WHAT you stream using the `stream_mode` parameter.

# ##############################################################################
# # 2. THE FIVE STREAM MODES: CHOOSING YOUR OUTPUT                             #
# ##############################################################################

# Let's define a simple graph to demonstrate the different modes.
class BasicState(TypedDict):
    topic: str
    joke: NotRequired[str]

def generate_joke(state: BasicState):
    return {"joke": f"Why did the {state['topic']} cross the road? To get to the other side!"}

def refine_topic(state: BasicState):
    return {"topic": f"silly {state['topic']}"}

builder = StateGraph(BasicState)
builder.add_node("refine_topic", refine_topic)
builder.add_node("generate_joke", generate_joke)
builder.add_edge(START, "refine_topic")
builder.add_edge("refine_topic", "generate_joke")
builder.add_edge("generate_joke", END)
basic_graph = builder.compile()

inputs = {"topic": "chicken"}

# ## 2.1. `updates` mode: See What Changed
# Streams only the *changes* (deltas) to the state after each node runs.
# This is lightweight and tells you exactly which node produced what output.
# Output format: `dict[str, Any]` where the key is the node name.

print("\n--- 2.1. stream_mode='updates' ---")
for chunk in basic_graph.stream(inputs, stream_mode="updates"):
    print(chunk)
# Expected Output:
# {'refine_topic': {'topic': 'silly chicken'}}
# {'generate_joke': {'joke': 'Why did the silly chicken cross the road? To get to the other side!'}}

# ## 2.2. `values` mode: See the Full Picture
# Streams the *entire state object* after each node completes.
# This is useful if you need the full context at every step.
# Output format: `State` (your TypedDict or class).

print("\n--- 2.2. stream_mode='values' ---")
for chunk in basic_graph.stream(inputs, stream_mode="values"):
    print(chunk)
# Expected Output:
# {'topic': 'silly chicken'}
# {'topic': 'silly chicken', 'joke': 'Why did the silly chicken...'}

# ## 2.3. `debug` mode: See Everything
# The most verbose mode. Streams detailed information about the graph's execution,
# including task details, inputs, outputs, and the full state. Great for debugging.
# Output format: `list[dict]` containing detailed trace information.

print("\n--- 2.3. stream_mode='debug' ---")
for chunk in basic_graph.stream(inputs, stream_mode="debug", stream_options={"include_types": False}):
    # Limiting output for clarity
    if chunk[0]['type'] == 'task':
        print(f"Executing Node: {chunk[0]['name']}")
        print(f"  - State After: {chunk[0]['output']}")


# ## 2.4. Streaming Multiple Modes
# You can request multiple modes at once by passing a list.
# The output is a tuple: `(mode_name: str, chunk: Any)`.

print("\n--- 2.4. Streaming Multiple Modes ['updates', 'values'] ---")
for mode, chunk in basic_graph.stream(inputs, stream_mode=["updates", "values"]):
    print(f"Mode: {mode} | Chunk: {chunk}")


# ##############################################################################
# # 3. STREAMING LLM TOKENS (`messages` mode)                                  #
# ##############################################################################

# The `messages` mode is specifically for streaming token-by-token LLM outputs.
# It works automatically with any LangChain-compatible LLM.

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

def call_llm(state: ChatState):
    llm = FakeStreamingLLM("This is a streamed joke about cats!")
    response = llm.stream(state["messages"])
    return {"messages": list(response)} # Collect chunks into a final message

llm_builder = StateGraph(ChatState)
llm_builder.add_node("call_llm", call_llm)
llm_builder.add_edge(START, "call_llm")
llm_builder.add_edge("call_llm", END)
llm_graph = llm_builder.compile()

# ## 3.1. Basic Token Streaming
# The output is a tuple: `(message_chunk: BaseMessageChunk, metadata: dict)`.
print("\n--- 3.1. Basic LLM Token Streaming ('messages' mode) ---")
final_message = ""
for chunk, metadata in llm_graph.stream([HumanMessage("Tell me a joke")], stream_mode="messages"):
    if chunk.content:
        print(chunk.content, end="", flush=True)
        final_message += chunk.content
print("\n")

# ## 3.2. Filtering Streamed Tokens by Node
# The `metadata` dictionary contains the node name that triggered the LLM call.
print("\n--- 3.2. Filtering Tokens by Node Name ---")
for chunk, metadata in llm_graph.stream([HumanMessage("Tell me a joke")], stream_mode="messages"):
    if metadata.get("langgraph_node") == "call_llm" and chunk.content:
        print(chunk.content, end="", flush=True)
print("\n")

# ## 3.3. Filtering Streamed Tokens by Invocation (Tags)
# You can "tag" LLM invocations to distinguish between them in a single node.
def multi_llm_node(state: ChatState):
    joke_llm = FakeStreamingLLM("Why don't scientists trust atoms? Because they make up everything!").with_config({"tags": ["joke_llm"]})
    poem_llm = FakeStreamingLLM("Roses are red, violets are blue...").with_config({"tags": ["poem_llm"]})
    
    # These would typically run in parallel
    _ = list(joke_llm.stream(state["messages"]))
    _ = list(poem_llm.stream(state["messages"]))
    return {"messages": []}

multi_llm_builder = StateGraph(ChatState)
multi_llm_builder.add_node("multi_llm_node", multi_llm_node)
multi_llm_builder.add_edge(START, "multi_llm_node")
multi_llm_builder.add_edge("multi_llm_node", END)
multi_llm_graph = multi_llm_builder.compile()

print("\n--- 3.3. Filtering Tokens by Tags (Streaming only the joke) ---")
for chunk, metadata in multi_llm_graph.stream([HumanMessage("Generate")], stream_mode="messages"):
    if "joke_llm" in metadata.get("tags", []) and chunk.content:
        print(chunk.content, end="", flush=True)
print("\n")


# ##############################################################################
# # 4. STREAMING CUSTOM DATA (`custom` mode)                                   #
# ##############################################################################
# Use this mode to send arbitrary data from inside your nodes, like progress
# updates or outputs from non-LangChain tools.

from langgraph.config import get_stream_writer

class CustomState(TypedDict):
    input: str

def custom_node(state: CustomState):
    # 1. Get the stream writer
    writer = get_stream_writer()

    # 2. Emit custom data at any point
    writer.emit({"progress": 25, "status": "Starting analysis..."})
    # ... some work ...
    writer.emit({"progress": 75, "status": "Generating report..."})

    return {} # Node can still return state updates

custom_builder = StateGraph(CustomState)
custom_builder.add_node("custom_node", custom_node)
custom_builder.add_edge(START, "custom_node")
custom_builder.add_edge("custom_node", END)
custom_graph = custom_builder.compile()

print("\n--- 4. Streaming Custom Progress Updates ('custom' mode) ---")
for chunk in custom_graph.stream({"input": "test"}, stream_mode="custom"):
    print(chunk)
# Expected Output:
# {'custom_key': {'progress': 25, 'status': 'Starting analysis...'}}
# {'custom_key': {'progress': 75, 'status': 'Generating report...'}}


# ##############################################################################
# # 5. DURABLE EXECUTION & STREAMING                                           #
# ##############################################################################
# Durable execution saves the graph's state at each step, allowing you to pause,
# resume, and handle failures. This is enabled by adding a `checkpointer`.

# ## 5.1. Setup with a Checkpointer
# You need two things: a checkpointer and a unique `thread_id` for each run.
checkpointer = InMemorySaver()

durable_graph = builder.compile(checkpointer=checkpointer)
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# ## 5.2. Human-in-the-Loop: Pausing and Resuming a Stream
# You can interrupt a graph before a specific node to wait for user input.

# Recompile the graph to interrupt BEFORE the 'generate_joke' node
interrupting_graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["generate_joke"]
)

print("\n--- 5.2. Pausing a stream for human input ---")
# The stream will run and then stop, raising a GraphInterrupt.
try:
    for chunk in interrupting_graph.stream(inputs, config=config):
        print(f"Streamed before interrupt: {chunk}")
except GraphInterrupt:
    print("\n--- Graph execution paused as expected! ---")

# You can inspect the state where it paused
paused_state = interrupting_graph.get_state(config)
print(f"State at pause: {paused_state.values}")

# Now, let's resume the stream. We call `.stream()` again with the SAME config.
# Passing `None` as input tells the graph to continue from its last saved state.
print("\n--- Resuming the stream ---")
for chunk in interrupting_graph.stream(None, config=config):
    print(f"Streamed after resume: {chunk}")

# ## 5.3. Durability Modes
# Controls when the state is saved.
# - "exit": (Default) Saves only at the end. Fastest, but no mid-run recovery.
# - "async": Saves state in the background. Good balance of speed and safety.
# - "sync": Waits for the save to complete before continuing. Safest, but slower.

# Example of using 'sync' for maximum durability
print("\n--- 5.3. Using 'sync' durability mode ---")
sync_config = {"configurable": {"thread_id": "sync_thread_example"}}
for chunk in durable_graph.stream(inputs, config=sync_config, durability="sync"):
    print(chunk)
print("--- 'sync' durability stream complete. ---")

print("\n--- End of LangGraph Streaming Cheat Sheet ---")