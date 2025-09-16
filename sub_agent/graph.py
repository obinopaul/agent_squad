from langgraph.graph.state import StateGraph

from state import State
from node import sub_tools, subagent_call_model


def build_sub_agent():
    subgraph = StateGraph(State)
    subgraph.add_node("subagent_call_model", subagent_call_model)
    subgraph.add_node("sub_tools", sub_tools)
    subgraph.add_edge("__start__", "subagent_call_model")
    subgraph.add_edge("sub_tools", "subagent_call_model")

    return subgraph.compile()