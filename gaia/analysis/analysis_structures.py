from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from operator import add
from pydantic import BaseModel, Field
from typing import List

# Zidentyfikowane role (prototypy)
class RolePrototype(BaseModel):
    """Wstępny prototyp roli - tylko nazwa i krótki opis."""
    name: str = Field(description="Nazwa roli (PascalCase)")
    description: str = Field(description="Krótki opis celu istnienia roli w systemie")
 
 
class IdentifiedRoles(BaseModel):
    """Zidentyfikowane prototypy ról."""
    roles: List[RolePrototype]
 
 
# Model interakcji (między rolami)
class RoleInteraction(BaseModel):
    """Pojedyncza interakcja między dwiema rolami."""
    goal: str = Field(description="Cel interakcji (PascalCase)")
    initiator: str = Field(description="Nazwa roli inicjującej")
    responder: str = Field(description="Nazwa roli odpowiadającej")
    inputs: List[str] = Field(description="Dane wnoszone przez inicjatora")
    outputs: List[str] = Field(description="Dane zwracane przez respondera")
    processing_description: str = Field(description="Opis przetwarzania") 
 
 
class InteractionModel(BaseModel):
    """Model interakcji między rolami."""
    interactions: List[RoleInteraction]
 
class Prototypes(BaseModel):
    """Zidentyfikowane prototypy ról i interakcji."""
    roles: IdentifiedRoles
    interactions: InteractionModel
# prototypy
# class Prototypes(BaseModel):
#     """Zidentyfikowane prototypy ról i interakcji."""
#     roles: IdentifiedRoles
#     interactions: InteractionModel
    
# Model ról (pełny)
class Permissions(BaseModel):
    """Uprawnienia do zasobów informacyjnych dla danej roli."""
    read: List[str] = Field(default_factory=list,
        description="Lista zasobów do odczytu")
    write: List[str] = Field(default_factory=list,
        description="Lista zasobów do zapisu/modyfikacji")
    consume: List[str] = Field(default_factory=list,
        description="Lista zasobów do skonsumowania (usunięcia)")
    produce: List[str] = Field(default_factory=list,
        description="Lista zasobów wytwarzanych przez rolę")
 
 
class Responsibilities(BaseModel):
    """Odpowiedzialności roli (Liveness i Safety)."""
    liveness: str = Field(
        description="Wyrażenie regularne cyklu życia roli,")
    safety: List[str] = Field(default_factory=list,
        description="Lista niezmienników, np. ['saldo > 0']")
 
 
class GaiaRole(BaseModel):
    """Kompletna definicja roli - permissions, responsibilities, protocols."""
    name: str = Field(description="Nazwa roli (PascalCase) - musi odpowiadać prototypowi")
    description: str = Field(description="Opis roli spójny z prototypem")
    activities: List[str] = Field(description="Działania które agent może wykonać bez interakcji z inną rolą")
    protocols: List[str] = Field(description="Interakcji z innymi rolami")
    permissions: Permissions
    responsibilities: Responsibilities
 
 
class DefineRoles(BaseModel):
    """Pełny model ról GAIA."""
    roles: List[GaiaRole]
 


# Wspólne
class AnalysisFeedback(BaseModel):
    is_complete: bool = Field(
        description="Czy artefakt jest kompletny i spełnia wymagania metodyki GAIA?")
    message: str = Field(
        default="",
        description="ZOSTAW PUSTĘ JEŚLI IS_COMPLETE = TRUE. Jeśli is_complete = false, podaj konkretne wskazówki co jest nie tak i co należy poprawić.")
    

class OptimalizationFeedback(BaseModel):
    new_system_prompt: str = Field(
        description="Zoptymalizowany prompt do wygenerowania lepszego artefaktu.")
    explenations: str = Field(
        description="Wyjaśnienie, dlaczego ten prompt jest lepszy i jakie zmiany wprowadza.")
    
class AnalizeState(TypedDict):
    messages:  Annotated[list[BaseMessage], add_messages]
    feedbacks_prototypes: Annotated[list[AnalysisFeedback], add]
    feedbacks_roles: Annotated[list[AnalysisFeedback], add]
    
    identified_roles:  Optional[IdentifiedRoles]
    interaction_model: Optional[InteractionModel]
    last_roles:        Optional[DefineRoles]
    
    requirements: BaseMessage

    prompt_role_defs: str
    prompt_prototypes: str