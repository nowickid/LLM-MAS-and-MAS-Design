from ..implementation_state import ImplementationState
from .team_state import TeamState
from implementation.team.worker.worker import worker_node
from implementation.team.menager.menager_graph import menager_node
from langgraph.graph import StateGraph, START, END
from typing import Literal
from config import settings
from langchain_core.messages import HumanMessage
from utils import save_graph_visualization
from langchain_core.runnables import RunnableConfig

def route(state: TeamState) -> Literal["worker", END]:
    return "worker" if state["next_step"] == "worker" else END

def prepare_graph():
    graph = StateGraph(TeamState)
    graph.add_node("menager", menager_node)
    graph.add_node("worker", worker_node)
    graph.add_edge(START, "menager")
    graph.add_conditional_edges("menager", route)
    graph.add_edge("worker", "menager")
    team_process = graph.compile()
    if settings.generate_graphs:
        save_graph_visualization(
            team_process.get_graph(),
            "team_graph.png"
        )
    return team_process

team_process = prepare_graph()

def team_node(state: ImplementationState, config: RunnableConfig = None):
    team_state = TeamState(
        sprint_goal=state["sprint_goal"],
        project_context=state["project_context"],
        messages=[]
    )
    
    team_config = {
        **config,
        "recursion_limit": settings.team_recursion_limit
    }
    result = team_process.invoke(team_state,
        config=team_config
    )
    

    report = result.get("report", "No report generated.")  
    return {
        "messages": HumanMessage(content=f"Team completed the sprint with the following report:\n{report}")
    }