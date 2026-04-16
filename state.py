from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage

from gaia.analysis.analysis_structures import DefineRoles, InteractionModel
from gaia.design.design_structures import ServiceModel, AgentModel, AcquaintanceModel

class State(TypedDict):
#   input
    description: str
    functional_requirements: list[str]

#   first stages - analysis
    roles: DefineRoles
    interactions: InteractionModel
#   second stages - design
    agent_model: AgentModel
    service_model: ServiceModel
    acquaintance_model: AcquaintanceModel

#   implementation inputs
    documentation: str
    
class DataPaths(TypedDict):
    documentation_output: str
    implementation_workspace: str