from typing import TypedDict, Annotated, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from gaia.analysis.analysis_structures import DefineRoles, InteractionModel, IdentifiedRoles
from operator import add


# Model agentów
class AgentType(BaseModel):
    """
    Typ agenta = zbiór ról.
    Zazwyczaj relacja 1:1 (rola = typ agenta).
    Można złożyć kilka blisko powiązanych ról w jeden typ.
    """
    name: str = Field(description="Nazwa typu agenta (PascalCase), np. CustomerAgent")
    aggregated_roles: List[str] = Field(description="Nazwy ról GAIA które ten typ agreguje (zazwyczaj jedna)")
    cardinality: str = Field(
        description=(
            "Kwalifikator instancji wg GAIA: "
            "'n' - dokładnie n instancji, "
            "'m..n' - między m a n instancji, "
            "'*' - 0 lub więcej instancji, "
            "'+' - 1 lub więcej instancji. "
            "Przykłady: '1', '2..5', '*', '+'"
        )
    )
 
 
class AgentModel(BaseModel):
    """Wynik kroku 1: model agentów."""
    agent_types: List[AgentType]
 
 
# ---------------------------------------------------------------------------
# KROK 2 - Model usług
# ---------------------------------------------------------------------------
 
class Service(BaseModel):
    """
    Usługa jest pochodną: protokołów, aktywności,
    odpowiedzialności i pozwoleń roli/agenta.
    """
    name: str = Field(description="Nazwa usługi, np. 'vet customer'")
    provided_by: str = Field(description="Nazwa AgentType dostarczającego usługę")
    derived_from: str = Field(
        description=(
            "Z czego wynika usługa: nazwa protokołu, aktywności lokalnej, "
            "liveness lub uprawnienia (read/write/produce/consume) z analizy"
        )
    )
    inputs: List[str] = Field(description="Wejścia - pochodna protokołów, np. ['customerDetails']")
    outputs: List[str] = Field(description="Wyjścia - pochodna protokołów, np. ['creditRating']")
    pre_condition: str = Field(
        description=(
            "Warunek wstępny jako wyrażenie logiczne, np. "
            "'customer vetter available'. "
            "Użyj 'true' jeśli brak warunków."
        )
    )
    post_condition: str = Field(
        description=(
            "Warunek końcowy jako wyrażenie logiczne, np. "
            "'creditRating ≠ NULL'. "
            "Użyj 'true' jeśli brak warunków."
        )
    )
 
 
class ServiceModel(BaseModel):
    """Wynik kroku 2: model usług."""
    services: List[Service]
 
 
# ---------------------------------------------------------------------------
# KROK 3 - Model znajomości (acquaintance)
# ---------------------------------------------------------------------------
 
class Acquaintance(BaseModel):
    """
    Skierowana krawędź grafu znajomości: a → b oznacza że a wysyła
    komunikat do b (b niekoniecznie wysyła komunikat do a).
    Nie zastanawiamy się jakie komunikaty ani kiedy - tylko SAM FAKT komunikacji.
    """
    sender: str = Field(description="AgentType wysyłający komunikat")
    receiver: str = Field(description="AgentType odbierający komunikat")
    protocols: List[str] = Field(description="Protokoły komunikacyjne (pochodne z analizy) które uzasadniają tę znajomość")
 
 
class AcquaintanceModel(BaseModel):
    """
    Wynik kroku 3: model znajomości - graf skierowany.
    Cel: wykrycie potencjalnych wąskich gardeł.
    Dobra praktyka: zapewnienie luźnych powiązań między agentami.
    """
    acquaintances: List[Acquaintance] = Field(
        description="Lista skierowanych krawędzi grafu znajomości")
 
 
# ---------------------------------------------------------------------------
# FEEDBACK
# ---------------------------------------------------------------------------
 
class DesignFeedback(BaseModel):
    is_complete: bool = Field(
        description="Czy model jest kompletny i spójny z poprzednimi artefaktami?")
    message: str = Field(
        default="",
        description="WYPEŁNIJ TYLKO JEŚLI is_complete=False. Szczegółowe braki i niezgodności.")
 
 
class OptimalizationFeedback(BaseModel):
    new_system_prompt: str = Field(
        description="Zoptymalizowany prompt do wygenerowania lepszego artefaktu.")
    explenations: str = Field(
        description="Wyjaśnienie, dlaczego ten prompt jest lepszy i jakie zmiany wprowadza.")
   
   
# ---------------------------------------------------------------------------
# STAN PODGRAFU PROJEKTOWANIA
# ---------------------------------------------------------------------------
 
 
 
class DesignState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    feedbacks_agents: Annotated[list[DesignFeedback], add]
    feedbacks_services: Annotated[list[DesignFeedback], add]
    feedbacks_acquaintances: Annotated[list[DesignFeedback], add]
    
    analysis_context: str
    identified_roles:  IdentifiedRoles
    interaction_model: InteractionModel
 
    agent_model:        Optional[AgentModel]
    service_model:      Optional[ServiceModel]
    acquaintance_model: Optional[AcquaintanceModel]
    
    prompt_agents: str
    prompt_services: str
    prompt_acquaintances: str