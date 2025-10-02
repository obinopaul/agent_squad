# LiveKit Voice Agent Cheat Sheet
# A comprehensive guide to building voice agents with LiveKit, including core concepts,
# basic to advanced implementations, and integration patterns.
#
# Created by Gemini based on LiveKit documentation and examples.
#
# ==============================================================================
# I. CORE LIVEKIT CONCEPTS & ARCHITECTURE
# ==============================================================================

# LiveKit is designed for real-time communication (RTC) applications, and its architecture
# revolves around the concept of "Rooms" to facilitate interactive voice and video experiences.

# Why Rooms?
# -----------
# LiveKit's architecture is built upon the idea of "rooms" for several key reasons,
# which provide a robust and scalable foundation for real-time communication:
#
# 1.  **Multi-party Communication:** Rooms act as virtual meeting spaces where multiple
#     participants (users, agents) can connect and interact. This is crucial for
#     conversational AI, where an agent might need to speak to one or more users.
#
# 2.  **Media Routing & Management:** Instead of point-to-point connections, LiveKit
#     servers (often called a "media server" or "SFU - Selective Forwarding Unit")
#     within a room handle the efficient routing of audio and video streams between
#     participants. This offloads the complexity of direct peer connections from
#     your application and ensures optimal performance, especially with many participants.
#
# 3.  **Signaling:** Rooms provide a structured way for participants to exchange
#     signaling messages (e.g., joining/leaving, publishing/subscribing to tracks,
#     negotiating connections). This ensures that all participants are aware of
#     each other's status and media capabilities.
#
# 4.  **Scalability:** Rooms are designed to scale. LiveKit can manage many rooms
#     concurrently, each with varying numbers of participants, allowing for flexible
#     deployment of voice agents across numerous simultaneous conversations.
#
# 5.  **State Management:** The room maintains the state of all participants and
#     their published media tracks, simplifying the logic for agents and clients.
#
# 6.  **ACLs (Access Control Lists) & Permissions:** Rooms allow for granular
#     control over who can join, what they can do (e.g., publish audio, subscribe
#     to video), enhancing security and privacy.
#
# In essence, while you could technically integrate STT, TTS, LLM, and VAD components
# standalone, a LiveKit room provides the entire real-time communication infrastructure
# needed to connect these components to actual users over a network, manage their
# interactions, and scale the solution effectively. Without rooms, you'd be
# reinventing a significant portion of a WebRTC stack.

# What is RTC (Real-Time Communication)?
# ---------------------------------------
# # RTC refers to technologies that enable live, interactive communication between
# # users over a network with minimal delay. This includes voice calls, video calls,
# # and live streaming. LiveKit is built on WebRTC, a widely used open standard
# # for RTC.
# 
#
# What are WebSockets?
# --------------------
# # WebSockets provide a full-duplex communication channel over a single TCP connection.
# # Unlike traditional HTTP, where the client initiates a request and waits for a response,
# # WebSockets allow for persistent, two-way communication, making them ideal for
# # real-time applications where both the client and server need to send data
# # asynchronously. LiveKit uses WebSockets for signaling messages between clients
# # (including agents) and the LiveKit server.
#
# # ==============================================================================
# # II. BASIC LIVEKIT AGENT ARCHITECTURE IN PYTHON
# # ==============================================================================

# # LiveKit agents are typically run within a `JobContext` and interact with a `Room`
# # via an `AgentSession`. This section covers the fundamental building blocks.

import logging
import os
import asyncio
import re
import wave
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, ConversationItemAddedEvent
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext, room_io
from livekit.agents.vad import VADEventType
from livekit.plugins import openai, silero, deepgram, inworld, noise_cancellation

# Load environment variables (API keys, LiveKit URL/API credentials)
# Ensure your .env file is in the parent directory, e.g.:
# LIVEKIT_URL=ws://localhost:7880
# LIVEKIT_API_KEY=devkey
# LIVEKIT_API_SECRET=secret
# OPENAI_API_KEY=sk-...
# DEEPGRAM_API_KEY=...
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Basic Logging Setup
logger = logging.getLogger("livekit-cheat-sheet")
logger.setLevel(logging.INFO)

# 2.1: The Most Basic Listen and Respond Agent
# --------------------------------------------
# # This is the foundational agent capable of listening to user speech, processing it
# # with an LLM, and responding via TTS.

# # `Agent` Class: The core class for defining your agent's behavior and integrating
# # various voice components.
# # `AgentSession`: Manages the agent's connection and interaction within a LiveKit room.
# # `JobContext`: Provides access to the room and other job-related information.

class BasicListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            # `instructions`: The system prompt for your LLM, defining the agent's persona and role.
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            # `stt`: Speech-to-Text component. Deepgram is used here.
            stt=deepgram.STT(),
            # `llm`: Large Language Model component. OpenAI's GPT-4o is used.
            llm=openai.LLM(model="gpt-4o"),
            # `tts`: Text-to-Speech component. OpenAI's TTS is used.
            tts=openai.TTS(),
            # `vad`: Voice Activity Detection component. Silero VAD helps detect speech boundaries.
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        # `on_enter`: This method is called automatically when the agent successfully
        # joins the LiveKit room and is ready to start.
        # It's a common place to initiate the first greeting or action.
        self.session.generate_reply()
        # `generate_reply()`: Instructs the LLM to generate a response based on the
        # current conversation history and agent instructions, then synthesizes it
        # via TTS and speaks it in the room.

async def basic_entrypoint(ctx: JobContext):
    # `entrypoint`: The main function that LiveKit's CLI or worker calls to start an agent job.
    # `JobContext`: Provides access to the LiveKit room the agent will join.
    session = AgentSession()
    # `AgentSession`: An instance of the agent's session, which connects to the room.

    await session.start(
        agent=BasicListenAndRespondAgent(), # Your custom agent instance
        room=ctx.room                      # The LiveKit room to connect to
    )

# How to run this agent (from your terminal, after saving as e.g., `basic_agent.py`):
# python basic_agent.py dev
#
# Explanation of `WorkerOptions` and `cli.run_app`:
# `WorkerOptions`: Configures how the agent job should be run (e.g., its entrypoint function).
# `cli.run_app`: The utility to start the LiveKit agent worker, which manages job distribution
# and execution. This is for local development or for deploying as a worker service.
#
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=basic_entrypoint))

# ==============================================================================
# III. AGENT CUSTOMIZATION & CONTROL
# ==============================================================================

# LiveKit agents offer various ways to customize their behavior, respond to events,
# and interact with the user beyond simple listen-and-respond.

# 3.1: Changing Agent Instructions Dynamically
# --------------------------------------------
# # You can update the LLM instructions after the agent has started, allowing for
# # context-aware persona changes.

class ChangeInstructionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        # Example: Change instructions if the participant name starts with "sip" (e.g., a phone call)
        if self.session.participant.name.startswith("sip"):
            self.update_instructions("""
                You are a helpful agent speaking on the phone.
                Your primary goal is to assist the caller with their inquiry.
            """)
            logger.info("Instructions updated for phone call context.")
        self.session.generate_reply()

async def change_instructions_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=ChangeInstructionsAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=change_instructions_entrypoint))

# 3.2: Context Variables - Providing User-Specific Information
# -----------------------------------------------------------
# # Inject dynamic variables into your agent's instructions to give it context
# # about the user or situation.

class ContextAgent(Agent):
    def __init__(self, context_vars=None) -> None:
        instructions = """
            You are a helpful agent. The user's name is {name}.
            They are {age} years old and live in {city}.
            Speak to them as if you know these details.
        """

        if context_vars:
            # Format the instructions string with provided context variables
            instructions = instructions.format(**context_vars)

        super().__init__(
            instructions=instructions,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

async def context_variables_entrypoint(ctx: JobContext):
    context_variables = {
        "name": "Shayne",
        "age": 35,
        "city": "Toronto"
    }

    session = AgentSession()
    await session.start(
        agent=ContextAgent(context_vars=context_variables),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=context_variables_entrypoint))

# 3.3: Exit Messages - Performing Actions on Agent Exit
# ----------------------------------------------------
# # The `on_exit` method allows you to execute code when the agent is about to
# # disconnect from the room, e.g., sending a goodbye message.

class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        # `drain()`: Ensures any pending messages are sent before closing.
        await self.session.drain()
        # `aclose()`: Closes the agent session.
        await self.session.aclose()
        # You would typically return a success message here for the LLM to convey.
        return None, "I've ended our session. Goodbye!"

    async def on_exit(self):
        # This method is called just before the agent completely exits the room.
        await self.session.say("Goodbye!")
        logger.info("Agent said goodbye on exit.")

async def exit_message_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=GoodbyeAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=exit_message_entrypoint))

# 3.4: Interrupting Users / Uninterruptible Speech
# ------------------------------------------------
# # Control whether your agent can be interrupted while speaking, or define logic
# # to interrupt the user.

# # `allow_interruptions=False`: Makes the agent speak its entire response without
# # being cut off by user speech. User input is buffered until the agent finishes.

class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
                You will speak your full response regardless of user interruptions.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            allow_interruptions=False # <--- Key setting for uninterruptible speech
        )

    async def on_enter(self):
        # Agent initiates a long response to demonstrate non-interruptible behavior.
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable. For example, recite a paragraph from a book or explain a complex concept in detail.")

async def uninterruptable_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=UninterruptableAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=uninterruptable_entrypoint))

# # Interrupting the User:
# # This example shows how to detect when a user has spoken more than one sentence
# # and interrupt them. This involves overriding `stt_node` to process transcript
# # events in real-time.

class InterruptUserAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who will interrupt the user if they try to say more than one sentence.
                Your goal is to ensure the user speaks one sentence at a time.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            # It's set to False here because we want to control interruptions manually
            # and prevent the agent from being interrupted while it's telling the user to stop.
            allow_interruptions=False
        )
        self.text_buffer = ""

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        # `stt_node` allows you to intercept and process the raw audio or text stream
        # before it goes to the STT plugin or after it comes out.
        parent_stream = super().stt_node(text, model_settings)

        if parent_stream is None:
            return None

        async def replay_user_input(sentence_text: str):
            # The agent speaks immediately to interrupt the user.
            await self.session.say("Let me stop you there. You just said: " + sentence_text + ". Please try to speak one sentence at a time.")

        async def process_stream():
            async for event in parent_stream:
                # We're interested in final transcripts from the STT.
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text

                    self.text_buffer += " " + transcript
                    self.text_buffer = self.text_buffer.strip()

                    # Simple sentence detection (can be improved for complex cases)
                    sentence_pattern = r'[.!?]+'
                    if re.search(sentence_pattern, self.text_buffer):
                        sentences = re.split(sentence_pattern, self.text_buffer)

                        if len(sentences) > 1: # If more than one sentence is detected
                            for i in range(len(sentences) - 1):
                                if sentences[i].strip():
                                    logger.info(f"Complete sentence detected and user interrupted: '{sentences[i].strip()}'")
                                    await replay_user_input(sentences[i].strip())
                            # Keep the last (incomplete or next) sentence in the buffer
                            self.text_buffer = sentences[-1].strip()

                yield event # Pass the original event upstream to other agent components

        return process_stream()

    async def on_enter(self):
        self.session.say("I'll interrupt you if you speak more than one sentence at a time. Go ahead and try!")

async def interrupt_user_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=InterruptUserAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=interrupt_user_entrypoint))

# 3.5: Playing Audio from a File
# -------------------------------
# # Agents can play pre-recorded audio files, which is useful for specific sound effects,
# # jingles, or canned responses.

class AudioPlayerAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                If asked to play audio, use the `play_audio_file` function.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def play_audio_file(self, context: RunContext):
        """When asked, use this function to play a pre-recorded audio file."""
        # Ensure you have an 'audio.wav' file in the same directory as your agent script.
        # This example assumes a simple WAV file. For more complex audio, consider libraries
        # like pydub or soundfile for better handling.
        audio_path = Path(__file__).parent / "audio.wav"

        if not audio_path.exists():
            return None, "Error: Audio file 'audio.wav' not found."

        try:
            with wave.open(str(audio_path), 'rb') as wav_file:
                num_channels = wav_file.getnchannels()
                sample_rate = wav_file.getframerate()
                # Read all frames at once. For very long files, consider streaming.
                frames = wav_file.readframes(wav_file.getnframes())

            audio_frame = rtc.AudioFrame(
                data=frames,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=wav_file.getnframes() # Total samples = frames * num_channels
            )

            async def audio_generator():
                # Yield the audio frame. You can yield multiple frames for longer audio.
                yield audio_frame

            # `self.session.say` can take an `audio` argument which is an AsyncIterable of AudioFrame
            await self.session.say("Playing audio file now.", audio=audio_generator())
            logger.info("Played audio file.")
            return None, "I've played the audio file for you."
        except Exception as e:
            logger.error(f"Failed to play audio file: {e}")
            return None, f"I encountered an error trying to play the audio file: {e}"

    async def on_enter(self):
        self.session.generate_reply()

async def playing_audio_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=AudioPlayerAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=playing_audio_entrypoint))


# 3.6: Echo Transcriber - Transcribing and Echoing Audio
# ----------------------------------------------------
# # This agent demonstrates advanced audio processing by intercepting the incoming
# # audio, transcribing it, and then echoing the buffered audio back to the user.
# # It uses a custom VAD to detect speech segments for accurate echoing.

class EchoTranscriberAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an echo transcriber that listens and repeats audio.",
            stt=deepgram.STT(),
            vad=None, # We use a custom VAD, so set this to None
            allow_interruptions=False # Prevent agent interruption during echo
        )

        self.audio_source: Optional[rtc.AudioSource] = None
        self.echo_track: Optional[rtc.LocalAudioTrack] = None
        self.ctx: Optional[JobContext] = None
        self.audio_buffer: list[rtc.AudioFrame] = []
        # Custom VAD for fine-grained control over speech detection
        self.custom_vad = silero.VAD.load(
            min_speech_duration=0.2, # Minimum speech duration to consider it valid
            min_silence_duration=0.6, # Minimum silence duration to mark end of speech
        )
        self.vad_stream = self.custom_vad.stream() # Stream for VAD events
        self.is_speaking = False # Flag to track if user is speaking
        self.is_echoing = False # Flag to track if agent is currently echoing
        self.audio_format_set = False # Flag to ensure audio output setup once

    async def on_enter(self):
        # Override to prevent default TTS greeting, as we are echoing.
        pass

    def set_context(self, ctx: JobContext):
        # A helper to pass JobContext to the agent instance
        self.ctx = ctx

    async def setup_audio_output(self):
        # Only set up audio output once
        if self.audio_format_set:
            return

        # Create an AudioSource that the agent can write to
        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        # Create a LocalAudioTrack from the source
        self.echo_track = rtc.LocalAudioTrack.create_audio_track("echo", self.audio_source)
        # Publish this track to the room so others (including the user) can hear it
        if self.ctx and self.ctx.room:
            await self.ctx.room.local_participant.publish_track(
                self.echo_track,
                rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
            )
        self.audio_format_set = True

    async def stt_node(self, audio: AsyncIterable[rtc.AudioFrame], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[str]]:
        """Intercept audio frames before STT processing for buffering and VAD."""

        async def audio_with_buffer():
            """Pass through audio while processing with VAD and buffering."""
            first_frame = True
            async for frame in audio:
                if first_frame:
                    await self.setup_audio_output() # Setup audio output when first audio frame arrives
                    first_frame = False

                if not self.is_echoing: # Only buffer if not currently echoing
                    self.vad_stream.push_frame(frame) # Push frame to custom VAD
                    self.audio_buffer.append(frame) # Buffer the audio frame

                    # Simple buffer management to prevent excessive memory usage
                    if len(self.audio_buffer) > 1000: # Approx 10 seconds of 48kHz audio (1 frame = 10ms)
                        self.audio_buffer.pop(0)

                yield frame # Pass the frame to the STT component

        # Call the super method with our wrapped audio stream
        return super().stt_node(audio_with_buffer(), model_settings)

async def echo_transcriber_entrypoint(ctx: JobContext):
    # Set agent state to 'listening' for front-end integration (optional)
    await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    session = AgentSession()
    agent = EchoTranscriberAgent()
    agent.set_context(ctx) # Pass context to the agent instance

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        # Log final transcripts from the user
        if transcript.is_final:
            logger.info(f"Transcribed: {transcript.transcript}")

    async def process_vad_events():
        """Asynchronously process VAD events to detect speech boundaries and trigger echoing."""
        async for vad_event in agent.vad_stream:
            if agent.is_echoing:
                continue # Don't process VAD during echoing

            if vad_event.type == VADEventType.START_OF_SPEECH:
                agent.is_speaking = True
                logger.info("VAD: Start of speech detected")
                # Keep only a recent portion of the buffer to avoid echoing old noise
                if len(agent.audio_buffer) > 100: # Keep ~1 second before speech start
                    agent.audio_buffer = agent.audio_buffer[-100:]

            elif vad_event.type == VADEventType.END_OF_SPEECH:
                agent.is_speaking = False
                agent.is_echoing = True # Set flag to prevent buffering during echo
                buffer_size = len(agent.audio_buffer)
                logger.info(f"VAD: End of speech, echoing {buffer_size} frames")

                await ctx.room.local_participant.set_attributes({"lk.agent.state": "speaking"})

                frames_to_play = agent.audio_buffer.copy() # Copy buffer to avoid race conditions
                agent.audio_buffer.clear() # Clear buffer for next speech segment

                # Play back all buffered audio frames
                if agent.audio_source:
                    for frame in frames_to_play:
                        await agent.audio_source.capture_frame(frame)
                else:
                    logger.error("Audio source not initialized, cannot echo.")

                agent.is_echoing = False # Reset flag after echoing
                logger.info("Finished echoing.")
                await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    # Start the VAD event processing in a separate task
    vad_task = asyncio.create_task(process_vad_events())

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            # Enable noise cancellation for cleaner input audio
            noise_cancellation=noise_cancellation.BVC(),
            audio_sample_rate=48000,
            audio_num_channels=1,
        )
    )

    # Keep the VAD task running until the session ends
    await vad_task

# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=echo_transcriber_entrypoint))


# 3.7: Repeater Agent - Repeating User Input
# ------------------------------------------
# # A simple agent that demonstrates how to listen for user input and immediately
# # repeat it back using the `on_user_input_transcribed` event.

async def repeater_entrypoint(ctx: JobContext):
    session = AgentSession()

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        # `transcript.is_final` ensures we only act on complete transcriptions.
        if transcript.is_final:
            logger.info(f"User said: {transcript.transcript}")
            # `session.say()` is used to make the agent speak the given text.
            session.say(transcript.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that repeats what the user says.",
            stt=deepgram.STT(),
            tts=openai.TTS(),
            allow_interruptions=False # Ensure the agent finishes repeating
        ),
        room=ctx.room
    )

# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=repeater_entrypoint))


# 3.8: Label Messages / Conversation Event Monitoring
# ----------------------------------------------------
# # LiveKit agents can emit `ConversationItemAddedEvent`s, which are useful for
# # monitoring the flow of conversation, logging, and debugging.

class LabelMessagesAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

async def label_messages_entrypoint(ctx: JobContext):
    # Connect to the room (optional, session.start will also connect)
    await ctx.connect()

    session = AgentSession()

    @session.on("conversation_item_added")
    def conversation_item_added(item: ConversationItemAddedEvent):
        # This event is fired whenever a new conversational turn (user speech, agent reply) occurs.
        # It contains details like the participant who spoke, the text, and timestamps.
        print(f"Conversation Event: {item}")
        logger.info(f"Conversation Item Added - Participant: {item.participant_identity}, Text: {item.text}, Type: {item.item_type}")

    await session.start(
        agent=LabelMessagesAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=label_messages_entrypoint))

# 3.9: Entry Points
# ------------------
# # In LiveKit, the `entrypoint` function is the initial function invoked when an
# # agent job starts. It receives a `JobContext` and is responsible for setting
# # up and starting the `AgentSession`. It acts as the main orchestrator for your agent's lifecycle.
# # (Refer back to `basic_entrypoint` for a concrete example).

# # 3.10: Pre-Warm (Conceptual)
# # ----------------------------
# # # While not directly shown in the provided examples, "pre-warming" refers to
# # # loading and initializing resources (like LLM models, VAD models, etc.) *before*
# # # they are first needed in the `on_enter` method or during a conversation.
# # # This can significantly reduce latency for the first interaction.
# # #
# # # In the provided examples, `silero.VAD.load()` and `openai.LLM()` are called
# # # in `__init__`, which effectively "pre-warms" these components when the agent
# # # object is created, often before the `on_enter` method is called or the first
# # # user interaction occurs.
# # # For larger models or external services, you might explicitly call them once
# # # during agent initialization or even at the worker startup phase.

# # ==============================================================================
# # IV. ADVANCED LIVEKIT AGENT FEATURES & INTEGRATIONS
# # ==============================================================================

# # LiveKit agents can go beyond basic conversation, integrating with external tools,
# # handling complex call flows, and incorporating multimodal inputs like vision.

# 4.1: Tool Calling with LLMs
# ---------------------------
# # Modern LLMs can be augmented with "tool calling" capabilities, allowing them to
# # invoke functions or interact with external systems based on user intent. LiveKit
# # integrates this by allowing you to define functions as `@function_tool`s.

class ToolCallingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
                Always respond politely after performing an action.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"), # Ensure your LLM supports tool calling (e.g., GPT-4o)
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool # Decorator to mark a method as an LLM tool
    async def print_to_console(self, context: RunContext) -> tuple[None, str]:
        """When the user asks you to print something, or specifically says "print to console", use this function to print a message to the agent's console."""
        # The `context: RunContext` parameter provides access to the agent's session and other runtime info.
        print("Console Print Success!")
        logger.info("Function tool 'print_to_console' executed.")
        # Return `None` for internal action, and a string for the LLM's response to the user.
        return None, "I've printed a success message to the console."

    async def on_enter(self):
        self.session.generate_reply()

async def tool_calling_entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(
        agent=ToolCallingAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=tool_calling_entrypoint))


# 4.2: Two-Calling with LiveKit (Conceptual)
# ------------------------------------------
# # "Two-calling" in LiveKit refers to scenarios where an agent facilitates a call
# # between two other parties, or acts as an intermediary, potentially bridging
# # different communication channels (e.g., WebRTC to SIP).
# #
# # **How it works conceptually:**
# # 1.  **Agent as a Router/Bridge:** The LiveKit agent itself can join multiple
# #     LiveKit rooms or manage connections to different endpoints. For example,
# #     it could join a WebRTC room with user A, and simultaneously join another
# #     room with user B (or a SIP trunk for an external phone call).
# # 2.  **Media Forwarding:** The agent would then receive audio/video streams
# #     from one participant and forward them to the other, potentially applying
# #     transcription, translation, or LLM processing in between.
# # 3.  **Example Use Case:** A virtual receptionist agent could receive a call,
# #     ask who the user wants to speak to, and then "transfer" or "bridge" the
# #     call to the appropriate human agent in another LiveKit room.
# #
# # **Implementation Notes:**
# # * This would involve using LiveKit's low-level `rtc` APIs (`LocalAudioTrack`,
# #     `RemoteAudioTrack`, `AudioSource`, `AudioSink`, etc.) to explicitly
# #     manage media streams between different connections.
# # * You might have an agent connecting to multiple `AgentSession` instances
# #     or even direct `rtc.Room` instances to manage diverse connections.
# # * This is a more advanced pattern and would require careful handling of
# #     media pipelines and signaling.

# # 4.3: Connecting with LangGraph (Conceptual)
# # -------------------------------------------
# # LangGraph is a library built on LangChain for building stateful, multi-actor
# # applications with LLMs. Integrating LiveKit agents with LangGraph allows
# # for highly complex, multi-turn conversational flows and agentic behavior.
# #
# # **How it works conceptually:**
# # 1.  **LiveKit Agent as an I/O Layer:** The LiveKit agent acts as the real-time
# #     audio input (STT) and audio output (TTS) layer for your LangGraph application.
# # 2.  **Transcript to LangGraph:** When the LiveKit agent receives a final
# #     transcript from the user (e.g., via `on_user_input_transcribed`), it
# #     sends this text input to your running LangGraph application.
# # 3.  **LangGraph Processes:** LangGraph orchestrates the various LLM calls, tool
# #     invocations, and state transitions based on the user's input.
# # 4.  **LangGraph Response to LiveKit:** Once LangGraph determines a response
# #     (text, or instructions for a tool), it sends this back to the LiveKit agent.
# # 5.  **LiveKit Agent Speaks:** The LiveKit agent receives the text response
# #     from LangGraph and uses its TTS component (`session.say()`) to speak
# #     the reply to the user.
# #
# # **Implementation Notes:**
# # * You would typically have your LangGraph application running as a separate
# #     service or within the same worker process.
# # * Communication between the LiveKit agent and LangGraph could be via
# #     direct function calls (if co-located), message queues, or HTTP APIs.
# # * The LiveKit agent would essentially be a specialized "tool" for LangGraph,
# #     handling real-time voice I/O.


# 4.4: Vision and Audio (Multimodal Agents - Conceptual)
# ------------------------------------------------------
# # LiveKit fully supports video streams, enabling the creation of multimodal
# # agents that can process both audio and visual information.
# #
# # **How it works conceptually:**
# # 1.  **Video Input:** A user's camera stream is published to the LiveKit room
# #     as a `rtc.LocalVideoTrack`. The agent can then subscribe to this track.
# # 2.  **Frame Processing:** The agent would receive `rtc.VideoFrame` objects
# #     from the subscribed video track. These frames can be processed:
# #     * **Computer Vision Models:** Send frames to external computer vision
# #         models (e.g., for object detection, facial recognition, gesture
# #         analysis).
# #     * **Multimodal LLMs:** For LLMs that accept image input (like GPT-4o Vision,
# #         Google Gemini Vision), you would convert the `rtc.VideoFrame` into
# #         an image format (e.g., JPEG, PNG) and send it along with the audio transcript
# #         to the multimodal LLM.
# # 3.  **Audio Processing:** Simultaneously, the agent continues to process
# #     audio (STT, LLM, TTS) as described in previous sections.
# # 4.  **Synchronized Understanding:** The challenge lies in synchronizing the
# #     visual context with the auditory context to build a coherent understanding
# #     of the user's intent or the environment.
# # 5.  **Video Output (Optional):** An agent could also publish its own video
# #     track, for example, to display a virtual avatar or visual feedback.
# #
# # **Implementation Notes:**
# # * You would use `session.room.on("track_subscribed")` to detect when a
# #     user publishes a video track.
# # * Then, you would use `rtc.VideoSource` and `rtc.VideoFrame` to read
# #     and potentially process video data.
# # * This typically requires external computer vision libraries (e.g., OpenCV, PIL)
# #     and APIs for multimodal LLMs.

# # Example Snippet (Conceptual - not fully runnable without video processing logic):
# # async def process_video_track(track: rtc.RemoteVideoTrack):
# #     video_stream = rtc.VideoStream(track)
# #     async for frame in video_stream:
# #         # `frame` is an rtc.VideoFrame object
# #         # Convert to image format (e.g., Pillow image)
# #         # image = convert_video_frame_to_pil_image(frame)
# #         # Send image to a vision model or multimodal LLM
# #         # await send_to_vision_llm(image, current_transcript)
# #         pass

# # @session.on("track_subscribed")
# # def on_track_subscribed(track: rtc.RemoteTrack, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
# #     if track.kind == rtc.TrackKind.KIND_VIDEO:
# #         asyncio.create_task(process_video_track(track))
# #         logger.info(f"Subscribed to video track from {participant.identity}")

# # 4.5: Say in Voice / Dynamic TTS Voice Switching
# # ------------------------------------------------
# # LiveKit agents can dynamically switch the Text-to-Speech voice, allowing for
# # more expressive or persona-specific responses. This is often done using
# # function tools.

class SayPhraseInVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are an agent that can say phrases in different voices.
                When the user asks you to say a phrase in a specific voice (e.g., "say hello in Hades voice"),
                use the `say_phrase_in_voice_tool` function.
                Available voices include 'Ashley', 'Hades', 'Elijah'. Default voice is Ashley.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            # Initialize with a default TTS voice (e.g., Inworld's Ashley)
            tts=inworld.TTS(voice="Ashley"),
            vad=silero.VAD.load()
        )
        self._default_voice = "Ashley" # Store the default voice

    async def say_phrase_in_voice(self, phrase: str, voice: str):
        # Update the TTS component's options to switch the voice
        self.tts.update_options(voice=voice)
        await self.session.say(phrase) # Speak the phrase in the new voice
        self.tts.update_options(voice=self._default_voice) # Revert to default voice
        logger.info(f"Said '{phrase}' in voice '{voice}'. Reverted to default voice.")

    @function_tool
    async def say_phrase_in_voice_tool(self, phrase: str, voice: str = "Ashley") -> tuple[None, str]:
        """Say a phrase in a specific voice.
        
        Args:
            phrase: The text phrase to be spoken.
            voice: The name of the voice to use (e.g., 'Ashley', 'Hades', 'Elijah'). Defaults to 'Ashley'.
        """
        valid_voices = ['Ashley', 'Hades', 'Elijah'] # Example valid voices
        if voice not in valid_voices:
            return None, f"I cannot use the voice '{voice}'. Please choose from: {', '.join(valid_voices)}."

        await self.say_phrase_in_voice(phrase, voice)
        return None, f"I've said '{phrase}' in the {voice} voice for you."

    async def on_enter(self):
        self.session.generate_reply()

async def say_in_voice_entrypoint(ctx: JobContext):
    await ctx.connect() # Ensure connection

    session = AgentSession()
    await session.start(
        agent=SayPhraseInVoiceAgent(),
        room=ctx.room
    )
# if __name__ == "__main__":
#     cli.run_app(WorkerOptions(entrypoint_fnc=say_in_voice_entrypoint))