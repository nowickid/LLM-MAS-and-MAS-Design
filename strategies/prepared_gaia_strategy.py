from implementation.implementation import process_implementation

from state import State
from langgraph.graph import StateGraph, START, END
from config import settings
from utils import save_graph_visualization
from langchain_core.runnables import RunnableConfig
from gaia.documentation.generator import process_documentation
from gaia.analysis.analysis_structures import DefineRoles, InteractionModel
from gaia.design.design_structures import AgentModel, ServiceModel, AcquaintanceModel

#     roles: DefineRoles
#     interactions: InteractionModel
# #   second stages - design
#     agent_model: AgentModel
#     service_model: ServiceModel
#     acquaintance_model: AcquaintanceModel
def prepare_input(state: State, config: RunnableConfig):
    gaia_artifacts = config.get("configurable", {}).get("gaia_artifacts", {})
    return{
        "roles": DefineRoles(roles=gaia_artifacts.get("roles", [])),
        "interactions": InteractionModel(interactions=gaia_artifacts.get("interactions", [])),
        "agent_model": AgentModel(agent_types=gaia_artifacts.get("agent_model", [])),
        "service_model": ServiceModel(services=gaia_artifacts.get("service_model", [])),
        "acquaintance_model": AcquaintanceModel(acquaintances=gaia_artifacts.get("acquaintance_model", []))
    }
    

def run_with_prepared_gaia(initial_state: State, config: RunnableConfig):
    g = StateGraph(State)

    g.add_node('prepare_input', prepare_input)
    g.add_node('documentation', process_documentation)
    g.add_node('implementation', process_implementation)    
    
    g.add_edge(START, 'prepare_input')
    g.add_edge('prepare_input', 'documentation')
    # g.add_edge('documentation', END)
    g.add_edge('documentation', 'implementation')
    g.add_edge('implementation', END)
    
    graph = g.compile()
    
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), 'nongaia_strategy_graph.png')
        
    
    return graph.invoke(initial_state, config=config)