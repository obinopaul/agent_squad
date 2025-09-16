import logging
from pathlib import Path
import wave
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, openai, silero
from livekit import rtc

logger = logging.getLogger("function-calling")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class FunctionAgent(Agent):
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
        audio_path = Path(__file__).parent / "audio.wav"
        
        with wave.open(str(audio_path), 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
        
        audio_frame = rtc.AudioFrame(
            data=frames,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=wav_file.getnframes()
        )
        
        async def audio_generator():
            yield audio_frame
        
        await self.session.say("Playing audio file", audio=audio_generator())
        
        return None, "I've played the audio file for you."

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=FunctionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))