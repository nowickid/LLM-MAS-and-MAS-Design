from gaia.analysis.analysis import process_analize
from gaia.design.design import process_design
from gaia.documentation.generator import process_documentation
from implementation.implementation import process_implementation

from state import State
from langgraph.graph import StateGraph, START, END
from config import settings
from utils import save_graph_visualization
from langchain_core.runnables import RunnableConfig

def run_with_gaia(initial_state: State, config: RunnableConfig):
    g = StateGraph(State)
    
    g.add_node('analysis', process_analize)
    g.add_node('design', process_design)
    g.add_node('documentation', process_documentation)
    g.add_node('implementation', process_implementation)    
    
    g.add_edge(START, 'analysis')
    g.add_edge('analysis', 'design')
    g.add_edge('design', 'documentation')
    g.add_edge('documentation', 'implementation')
    g.add_edge('implementation', END)
    
    graph = g.compile()
    
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), 'gaia_strategy_graph.png')
        
    
    return graph.invoke(initial_state, config=config)