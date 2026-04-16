from .implementation_state import ImplementationState
from implementation.architect.architect_graph import architect_node
from langgraph.graph import StateGraph, START, END
from typing import Literal
from utils import save_graph_visualization
from implementation.team.team import team_node
from config import settings
from state import State
from langchain_core.runnables import RunnableConfig

def route(state: ImplementationState) -> Literal["team", END]:
    if state["next_step"] == "team":
        return "team"
    else:
        return END

def prepare_graph():
    g = StateGraph(ImplementationState)
    g.add_node("architect", architect_node)
    g.add_node("team", team_node)
    g.add_edge(START, "architect")
    g.add_conditional_edges("architect", route)
    g.add_edge("team", "architect")
    
    graph = g.compile()
    if settings.generate_graphs:
        save_graph_visualization(
            graph.get_graph(),
            "implementation_graph.png"
        )
    return graph


graph = prepare_graph()

def process_implementation(state: State, config: RunnableConfig):
    state = ImplementationState(
        messages=[],
        documentation=state["documentation"],
    )
    implementation_config = {
        **config, 
        "recursion_limit": settings.implementation_recursion_limit 
    }
    result = graph.invoke(state,
        config=implementation_config
    )
    return result

