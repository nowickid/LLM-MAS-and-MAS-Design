from implementation.implementation import process_implementation

from state import State
from langgraph.graph import StateGraph, START, END
from config import settings
from utils import save_graph_visualization
from langchain_core.runnables import RunnableConfig

def run_without_gaia(initial_state: State, config: RunnableConfig):
    g = StateGraph(State)

    g.add_node('implementation', process_implementation)    
    
    g.add_edge(START, 'implementation')
    g.add_edge('implementation', END)
    
    graph = g.compile()
    
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), 'nongaia_strategy_graph.png')
        
    
    return graph.invoke(initial_state, config=config)