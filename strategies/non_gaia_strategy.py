from implementation.implementation import process_implementation

from state import State
from langgraph.graph import StateGraph, START, END
from config import settings
from utils import save_graph_visualization
from langchain_core.runnables import RunnableConfig


def prepare_requirements_as_input(state: State, config: RunnableConfig):
    requirements = state["functional_requirements"]
    
    documenation_str = "Functional requirements:\n" + "\n".join(f"- {req}" for req in requirements)
    return State(
        documentation=documenation_str
    )
    
def run_without_gaia(initial_state: State, config: RunnableConfig):
    g = StateGraph(State)

    g.add_node('prepare_requirements', prepare_requirements_as_input)
    g.add_node('implementation', process_implementation)    
    
    g.add_edge(START, 'prepare_requirements')
    g.add_edge('prepare_requirements', 'implementation')
    g.add_edge('implementation', END)
    
    graph = g.compile()
    
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), 'nongaia_strategy_graph.png')
        
    
    return graph.invoke(initial_state, config=config)