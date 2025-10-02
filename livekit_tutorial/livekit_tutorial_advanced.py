# LiveKit Advanced Agent Cheat Sheet
# A guide to building complex, real-time, and multimodal voice agents.
# This cheat sheet covers advanced topics including tool calling, vision,
# state management, multi-agent systems, and more.
#
# Created by Gemini based on LiveKit documentation and examples.
#
# ==============================================================================
# I. ADVANCED TOOL CALLING & DYNAMIC FUNCTIONS
# ==============================================================================

# Tool calling allows your agent to interact with external systems, APIs, or databases.
# This section covers creating, updating, and managing these tools at runtime.

# 1.1: Basic Function Tool with Parameters and Context
# -----------------------------------------------------
# # The `@function_tool` decorator registers a method with the LLM.
# # The `RunContext` parameter provides access to the agent's session and shared
# # `userdata`, which is essential for stateful operations.

from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, RunContext
from dataclasses import dataclass

# Example UserData for state management
@dataclass
class MySessionData:
    call_id: str
    user_name: str
    items_in_cart: list[str]

class BasicFunctionAgent(Agent):
    @function_tool
    async def add_item_to_cart(self, context: RunContext[MySessionData], item_name: str, quantity: int):
        """Adds a specified quantity of an item to the user's shopping cart."""
        # Access shared session data
        userdata = context.userdata
        userdata.items_in_cart.extend([item_name] * quantity)
        print(f"Added {quantity}x {item_name} to cart for user {userdata.user_name}.")
        # The second element of the tuple is the verbal response to the user
        return None, f"Okay, I've added {quantity} of {item_name} to your cart."

# 1.2: Updating Tools at Runtime
# -------------------------------
# # You can dynamically add new tools to an agent after it has been initialized.
# # This is useful for enabling or disabling capabilities based on context.

import random
from livekit.agents import JobContext

async def update_tools_entrypoint(ctx: JobContext):
    agent = BasicFunctionAgent()

    # Define an external function to be added as a tool
    async def _get_random_number() -> int:
        """Generates a random number between 0 and 100."""
        num = random.randint(0, 100)
        print(f"Generated random number: {num}")
        return num

    # Use `update_tools` to add the new function dynamically
    await agent.update_tools(
        agent.tools + [
            function_tool(
                _get_random_number,
                name="get_random_number",
                description="Get a random number."
            )
        ]
    )
    print("Agent tools have been dynamically updated.")
    # Now the agent can use the `get_random_number` tool.

# 1.3: Browser Agents (Conceptual)
# ---------------------------------
# # A "browser agent" is an advanced form of tool calling where the agent's tools
# # can control a web browser to perform tasks like searching, filling forms, or
# # scraping data.
# #
# # Implementation:
# # 1.  Use a browser automation library like `Playwright` or `Selenium`.
# # 2.  Create function tools that wrap browser actions (e.g., `Maps_to_url`,
# #     `search_for_product`, `get_page_summary`).
# # 3.  The agent can then reason about which browser actions to take to fulfill a
# #     user's request, effectively using the web as a knowledge source and action space.

# ==============================================================================
# II. REAL-TIME & PIPELINED PROCESSING
# ==============================================================================

# # Real-time models offer the lowest latency by processing audio streams as they
# # arrive, enabling more natural, back-and-forth conversation. Pipelining involves
# # chaining different components (STT, LLM, TTS) to perform complex tasks like translation.

# 2.1: Real-Time LLM Agents
# --------------------------
# # LiveKit plugins for models like OpenAI Realtime, AWS Bedrock, and Google Gemini
# # are optimized for low-latency voice interactions.

from livekit import agents
from livekit.agents.voice import AgentSession
from livekit.plugins import openai, aws, google, silero

async def openai_realtime_entrypoint(ctx: agents.JobContext):
    # This example uses OpenAI's Realtime model with extensive function tools.
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-realtime-preview-2025-06-03"
        ),
        vad=silero.VAD.load(),
    )
    # ... start session with an agent that has many function tools ...

async def aws_realtime_entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=aws.realtime.RealtimeModel(), # Uses AWS Bedrock Nova
        vad=silero.VAD.load()
    )
    # ... start session ...

async def gemini_realtime_entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025"
        ),
        vad=silero.VAD.load()
    )
    # ... start session ...

# 2.2: Pipelined Agents for Specific Tasks (e.g., Translation)
# ------------------------------------------------------------
# # You can construct a pipeline to perform a specific task, such as real-time
# # voice translation. The user speaks in one language, and the agent responds
# # in another.

from livekit.plugins import deepgram, elevenlabs

class TranslationAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Do not respond with anything else but the translation.
            """,
            stt=deepgram.STT(), # Input STT
            llm=openai.LLM(model="gpt-4o"), # LLM for translation
            tts=elevenlabs.TTS(model="eleven_multilingual_v2"), # Multilingual TTS for output
            vad=silero.VAD.load()
        )

# ==============================================================================
# III. VISION & MULTIMODALITY
# ==============================================================================

# # LiveKit agents can process video streams, allowing them to "see" what the user
# # is showing them. This enables a new class of multimodal interactions.

# 3.1: Processing Video Streams
# -----------------------------
# # The core pattern is to subscribe to a participant's video track, create a
# # `rtc.VideoStream`, and buffer the latest frame. When the user speaks, this
# # frame is injected into the LLM context.

import asyncio
from livekit import rtc
from livekit.agents import get_job_context
from livekit.agents.llm import ImageContent, ChatContext, ChatMessage

class VisionAgent(Agent):
    def __init__(self) -> None:
        self._latest_frame: rtc.VideoFrame | None = None
        self._video_stream: rtc.VideoStream | None = None
        self._tasks: list[asyncio.Task] = []
        super().__init__(
            instructions="You are an assistant with vision capabilities. You can see what the user shows you.",
            # Use an LLM that supports vision, e.g., OpenAI's Grok-2 Vision
            llm=openai.LLM.with_x_ai(model="grok-2-vision"),
            # ... other components ...
        )

    async def on_enter(self):
        # When the agent enters the room, look for video tracks to subscribe to.
        room = get_job_context().room
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, *args):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)

    def _create_video_stream(self, track: rtc.Track):
        # Helper to create a task that reads from the video stream
        if self._video_stream:
            self._video_stream.close()
        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                self._latest_frame = event.frame # Buffer the latest frame
        task = asyncio.create_task(read_stream())
        self._tasks.append(task)

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # When the user finishes speaking, inject the latest captured frame into the message.
        if self._latest_frame:
            new_message.content.append(ImageContent(image=self._latest_frame))
            self._latest_frame = None # Clear the frame after use

# 3.2: Vision with Non-Vision LLMs
# ---------------------------------
# # If your LLM doesn't have native vision, you can use an external vision model
# # (like Moondream) to generate a text description of the image and then pass
# # that description to your LLM.
#
# # See the `moondream_vision_agent.py` example for an implementation of this pattern.
# # It captures a frame, sends it to the Moondream API to get a caption, and then
# # adds `[Image description: {caption}]` to the LLM prompt.

# ==============================================================================
# IV. STATE MANAGEMENT & COMPLEX AGENTS
# ==============================================================================

# # For complex tasks, agents need to manage state, interact with databases,
# # and even transfer users between different specialized agents.

# 4.1: RPC for State & Frontend Communication
# -------------------------------------------
# # Remote Procedure Calls (RPC) allow the agent to communicate with the frontend
# # or other services. This is useful for updating a UI, managing state, or
# # receiving commands.

import json
from livekit.agents import RoomOutputOptions

async def rpc_entrypoint(ctx: JobContext):
    # ... setup agent and session ...

    async def handle_client_rpc(rpc_data):
        # Handler for incoming RPC calls from the client
        payload_str = rpc_data.payload
        payload = json.loads(payload_str)
        operation = payload.get("operation")
        # ... process CRUD operations (create, read, update, delete) on your state ...
        return json.dumps({"status": "success", "message": f"Processed {operation}"})

    # Register the RPC method with a specific name
    ctx.room.local_participant.register_rpc_method("agent.state", handle_client_rpc)

    # Agent can also send RPC calls to the client
    await ctx.room.local_participant.perform_rpc(
        destination_identity="client_identity",
        method="ui.update",
        payload=json.dumps({"status": "processing"})
    )

# 4.2: Persistent State with Databases
# ------------------------------------
# # For long-term memory, agents can connect to a database. To avoid blocking the
# # async event loop, database operations should be run in a separate thread.

import sqlite3
from concurrent.futures import ThreadPoolExecutor

db_executor = ThreadPoolExecutor(max_workers=1) # Thread pool for DB operations

def _insert_record_sync(data):
    # This synchronous function runs in the thread pool
    conn = sqlite3.connect("my_app.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO records (data) VALUES (?)", (data,))
    conn.commit()
    conn.close()

class DatabaseAgent(Agent):
    @function_tool
    async def save_data(self, data: str):
        """Saves data to the database."""
        loop = asyncio.get_event_loop()
        # Run the synchronous DB operation in the executor to avoid blocking
        await loop.run_in_executor(db_executor, _insert_record_sync, data)
        return None, "I've saved the data."

# 4.3: Multi-Agent Systems (e.g., Personal Shopper)
# -------------------------------------------------
# # For complex workflows, you can create a system of specialized agents (e.g., Triage,
# # Sales, Returns) and transfer the user between them while preserving context.

@dataclass
class CallUserData:
    # Shared data across all agents in the session
    personas: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Agent | None = None
    customer_id: str | None = None

class BaseAgent(Agent):
    async def _transfer_to_agent(self, name: str, context: RunContext[CallUserData]) -> Agent:
        """Transfers the user to another agent."""
        userdata = context.userdata
        userdata.prev_agent = context.session.current_agent # Store current agent
        next_agent = userdata.personas[name] # Get the next agent
        # The session will automatically switch to the new agent returned by the tool
        return next_agent

class TriageAgent(BaseAgent):
    @function_tool
    async def transfer_to_sales(self, context: RunContext[CallUserData]) -> Agent:
        """Transfers the user to the sales department."""
        await self.session.say("Okay, transferring you to sales.")
        return await self._transfer_to_agent("sales", context)

class SalesAgent(BaseAgent):
    # ... sales-specific tools ...
    pass

async def multi_agent_entrypoint(ctx: JobContext):
    userdata = CallUserData()
    # Create and register all agent personas
    userdata.personas["triage"] = TriageAgent()
    userdata.personas["sales"] = SalesAgent()

    session = AgentSession[CallUserData](userdata=userdata)
    await session.start(
        agent=userdata.personas["triage"], # Start with the Triage agent
        room=ctx.room
    )


# ==============================================================================
# V. ADVANCED INTEGRATIONS & CONCEPTS
# ==============================================================================

# 5.1: MCP (Media Control Plane)
# ------------------------------
# # MCP allows external systems to control and interact with LiveKit rooms and agents.
# # You can build an MCP server with tools to manage rooms, or an MCP client agent
# # that can access data and functions from an MCP server.

from livekit.agents import mcp

# An agent acting as an MCP client
async def mcp_client_entrypoint(ctx: JobContext):
    session = AgentSession(
        # Connect the session to one or more MCP servers
        mcp_servers=[mcp.MCPServerHTTP(url="https://your-mcp-server.com/mcp")],
        # ... other components ...
    )
    # The LLM can now call tools exposed by the MCP server.

# An MCP server exposing tools to control LiveKit
from mcp.server.fastmcp import FastMCP
from livekit import api

mcp_server = FastMCP("MyLiveKitController")

@mcp_server.tool()
def generate_livekit_token(identity: str, room: str) -> str:
    """Generates a JWT token for a user to join a LiveKit room."""
    # ... implementation to create and return a LiveKit token ...
    return "generated_token"

# To run the server:
# if __name__ == "__main__":
#     mcp_server.run()

# 5.2: RAG (Retrieval-Augmented Generation) - Conceptual
# ------------------------------------------------------
# # RAG enhances your agent's knowledge by allowing it to retrieve information
# # from a knowledge base (e.g., a vector database) and use that information
# # to form a more accurate and context-aware response.
#
# # Implementation Pattern:
# # 1.  Create a function tool, e.g., `query_knowledge_base(query: str)`.
# # 2.  Inside this tool, use a library like `langchain`, `llama-index`, or a
# #     vector DB client (`pinecone`, `weaviate`) to perform a similarity search.
# # 3.  The tool returns the retrieved documents/text chunks.
# # 4.  The LLM automatically incorporates this retrieved context into its final
# #     answer to the user.
# # 5.  Your agent's instructions should guide it on when and how to use this tool,
# #     e.g., "If the user asks a question about our product policies, use the
# #     `query_knowledge_base` tool to find the relevant information."

# 5.3: LangGraph Integration (Conceptual)
# ---------------------------------------
# # For building highly complex, stateful, and cyclic conversational flows, you
# # can integrate a LiveKit agent with a state machine framework like LangGraph.
# #
# # Integration Pattern:
# # 1.  **LiveKit as the I/O Layer:** The LiveKit agent serves as the "ears and mouth"
# #     of the LangGraph application. It handles the real-time audio input (STT) and
# #     output (TTS).
# # 2.  **State Machine Orchestration:** The core logic resides in your LangGraph graph.
# #     The graph defines the states, transitions, and tool-calling nodes.
# # 3.  **Communication Bridge:**
# #     - When the LiveKit agent gets a user transcript, it sends the text to the
# #       LangGraph application (e.g., via an API call or a message queue).
# #     - The LangGraph graph processes the input, moves through its states, and
# #       eventually produces a text response.
# #     - This response is sent back to the LiveKit agent.
# #     - The LiveKit agent uses `session.say()` to speak the response to the user.
# # This architecture separates the real-time communication layer (LiveKit) from the
# # complex conversational logic layer (LangGraph), creating a powerful and scalable system.

# ==============================================================================
# VI. AGENT PIPELINES & ADVANCED FLOWS
# ==============================================================================

# A "pipeline" in this context refers to modifying the standard STT -> LLM -> TTS
# data flow. By overriding the agent's `stt_node`, `llm_node`, or `tts_node`, you
# can intercept, analyze, and manipulate data at each stage to create highly
# customized behaviors.

# 6.1: STT Pipelines (Input Processing)
# -------------------------------------
# # Modify the STT pipeline to analyze or enrich incoming user speech.

# ### Keyword Detection
# # This agent inspects the final transcript for specific keywords without altering
# # the data sent to the LLM. It's useful for command detection or analytics.
class KeywordDetectionAgent(Agent):
    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        keywords = ["Shane", "hello", "thanks", "bye"]
        parent_stream = super().stt_node(text, model_settings)

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    for keyword in keywords:
                        if keyword.lower() in transcript.lower():
                            print(f"Keyword detected: '{keyword}'")
                yield event
        return process_stream()

# ### Diarization (Speaker Labeling)
# # When using an STT that supports diarization (like Speechmatics), you can
# # prepend speaker labels to transcripts to give the LLM context on who said what.
class DiarizationAgent(Agent):
    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)
        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    speaker_id = event.alternatives[0].speaker_id
                    # Look up the speaker's name from userdata
                    speaker_name = self.session.userdata.speaker_names.get(speaker_id, speaker_id)
                    # Prepend the name to the transcript
                    event.alternatives[0].text = f"{speaker_name}: {transcript}"
                yield event
        return process_stream()

# 6.2: LLM Pipelines (Logic & Context Processing)
# -----------------------------------------------
# # Modify the LLM pipeline to inject large amounts of context or to process the
# # model's output stream before it reaches the TTS.

# ### Large Context Injection (Static RAG)
# # For tasks requiring deep knowledge of a specific document, you can load the entire
# # text into the agent's initial instructions. This is effective for models with
# # very large context windows, like Gemini 2.0 Flash.
class WarAndPeaceAgent(Agent):
    def __init__(self) -> None:
        book_path = Path(__file__).parent / "lib" / "war_and_peace.txt"
        with open(book_path, "r", encoding="utf-8") as f:
            war_and_peace_text = f.read()

        super().__init__(
            instructions=f"""
                You are a War and Peace book club assistant.
                Here is the complete text of the book:
                {war_and_peace_text}
            """,
            llm=google.LLM(model="gemini-2.0-flash"),
            # ... other components
        )

# ### LLM Output Stream Manipulation
# # Override `llm_node` to process the raw output from the LLM in real-time. This is
# # useful for filtering, censoring, or transforming model-specific syntax (like
# # "thinking" tags) into user-friendly output.
class LLMOutputReplacementAgent(Agent):
    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            async with self.llm.chat(chat_ctx=chat_ctx, tools=tools) as stream:
                async for chunk in stream:
                    content = getattr(chunk.delta, 'content', None)
                    if content is not None:
                        # Replace model's thinking tags with a friendly message
                        processed_content = content.replace("<think>", "").replace("</think>", "Okay, I'm ready to respond.")
                        chunk.delta.content = processed_content
                    yield chunk
        return process_stream()


# 6.3: TTS Pipelines (Output Processing)
# --------------------------------------
# # Modify the TTS pipeline to change the text before synthesis or to implement
# # flow control based on the length of the agent's response.

# ### TTS Output Text Manipulation
# # Override `tts_node` to perform text replacements. This can be used to add
# # emphasis, pauses, or vocal effects using SSML-like tags if the TTS supports it.
class TTSNodeOverrideAgent(Agent):
    async def tts_node(self, text: AsyncIterable[str], model_settings):
        async def process_text():
            async for chunk in text:
                # Replace "lol" with a tag that the TTS might interpret as laughter
                yield chunk.replace("lol", "<laugh>").replace("LOL", "<laugh>")
        return Agent.default.tts_node(self, process_text(), model_settings)

# ### Flow Control based on Response Length
# # This agent interrupts itself if its response becomes too long, ensuring a better
# # user experience by avoiding lengthy monologues.
class ShortRepliesOnlyAgent(Agent):
    async def tts_node(self, text: AsyncIterable[str], model_settings):
        MAX_CHUNKS = 20
        chunk_count = 0
        async def process_text():
            nonlocal chunk_count
            async for chunk in text:
                chunk_count += 1
                if chunk_count > MAX_CHUNKS:
                    self.session.interrupt() # Stop the current TTS playback
                    self.session.say("I'm sorry, that will take too long to say.")
                    break # Stop processing further chunks
                yield chunk
        return Agent.default.tts_node(self, process_text(), model_settings)

# 6.4: RAG Pipelines (Dynamic Knowledge Retrieval)
# ------------------------------------------------
# # Retrieval-Augmented Generation (RAG) is a powerful pipeline where the agent
# # dynamically fetches information from a knowledge base to answer questions.
# # This is typically implemented using a function tool that queries a vector database.

class RAGEnrichedAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an expert on LiveKit. Use the `livekit_docs_search` tool to answer questions.",
            # ... other components ...
        )
        # ... initialize AnnoyIndex and load data ...
        self._annoy_index = AnnoyIndex.load("path/to/index")

    @function_tool
    async def livekit_docs_search(self, query: str):
        """Lookup information in the LiveKit docs database."""
        # 1. Generate embeddings for the user's query
        query_embedding = await openai.create_embeddings(input=[query], model="text-embedding-3-small")
        # 2. Query the vector database (AnnoyIndex) for relevant documents
        results = self._annoy_index.query(query_embedding[0].embedding, n=2)
        # 3. Format and return the retrieved text chunks
        # The LLM will then use this returned context to formulate its final answer.
        retrieved_context = " ".join([res.userdata for res in results])
        return retrieved_context


# 6.5: Telephony & Calling Pipelines
# ----------------------------------
# # Agents can be used to make and receive phone calls via SIP integration. This
# # creates complex pipelines involving call setup, management, and teardown.

from livekit import api

# ### Outbound Calling
# # An external script initiates a call and connects a user to an agent in a room.
async def make_outbound_call(phone_number: str):
    lkapi = api.LiveKitAPI()
    # 1. Create an agent dispatch to tell LiveKit which agent to run in a specific room.
    await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(agent_name="survey-agent", room="survey-room-123")
    )
    # 2. Create a SIP participant to dial the phone number and join the same room.
    await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name="survey-room-123",
            sip_trunk_id="ST_...",
            sip_call_to=phone_number
        )
    )
    await lkapi.aclose()

# ### Warm Handoff (Agent to Human)
# # A common telephony pattern is transferring a call from an AI agent to a human.
# # This is done by adding another SIP participant (the human agent) to the call.
class WarmHandoffAgent(Agent):
    @function_tool
    async def transfer_call_to_human(self, context: RunContext, phone_number: str):
        """Transfers the call to a human agent at the specified number."""
        room_name = context.room.name
        # The agent stays in the call while a new participant (the human) is added.
        await context.job_context.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id="ST_...",
                sip_call_to=phone_number,
                participant_name="Human Agent"
            )
        )
        return None, f"I am now transferring you to a human agent at {phone_number}. Please hold."

# 6.6: LangGraph Integration Pipeline
# -----------------------------------
# # For the most complex, stateful conversations, you can replace the standard LLM
# # with a LangGraph state machine. The `langchain.LLMAdapter` serves as the bridge.

from livekit.plugins import langchain
from langgraph.graph import StateGraph, START, END

# Define your LangGraph state and nodes
class MyLangGraphState(TypedDict):
    messages: Annotated[list, add_messages]

def my_chat_node(state: MyLangGraphState):
    # ... logic for this node ...
    return state

# Create the graph
graph_builder = StateGraph(MyLangGraphState)
graph_builder.add_node("chat", my_chat_node)
graph_builder.add_edge(START, "chat")
graph_builder.add_edge("chat", END)
workflow = graph_builder.compile()

# Use the graph in your AgentSession
async def langgraph_entrypoint(ctx: JobContext):
    session = AgentSession(
        # The LLMAdapter wraps the LangGraph workflow
        llm=langchain.LLMAdapter(graph=workflow),
        # ... other components ...
    )
    # ... start session ...