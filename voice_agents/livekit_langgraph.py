from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    WorkerOptions,
    cli,
    RoomInputOptions
)
from livekit.plugins import elevenlabs, noise_cancellation, silero, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import langchain
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from langgraph.graph.message import add_messages,AnyMessage
from langgraph.graph import START, END, StateGraph

load_dotenv()

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def chat_node(state: State) -> State:
    model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7)
    state["messages"] = model.invoke(state["messages"])
    return state

def create_workflow():
    graph_builder = StateGraph(State)
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_edge(START, "chat_node")
    graph_builder.add_edge("chat_node", END)
    graph = graph_builder.compile()
    return graph  



class Assistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful assistant.")

async def entrypoint(ctx: JobContext):
    
    session = AgentSession(
        llm=langchain.LLMAdapter(
            graph=create_workflow() 
        ),
        stt=openai.STT(model="whisper-1",detect_language=True),
        tts=elevenlabs.TTS(model="eleven_flash_v2_5",voice_id="yj30vwTGJxSHezdAGsv9"),
        turn_detection=MultilingualModel(), 
        vad=silero.VAD.load(),
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))