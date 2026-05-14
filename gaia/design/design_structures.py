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
            "Warunek końcowy. Jeśli usługa posiada 'outputs', określ ich stan końcowy "
            "(np. 'X != null'). Użyj 'true' tylko jeśli usługa nie zmienia trwale stanu."
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
class Issue(BaseModel):
    criterion: str = Field(description="Które kryterium GAIA zostało złamane (SŁOWNIE)")
    description: str = Field(description="Szczegółowy opis tego, co jest źle")
    fix: str = Field(description="Konkretna wskazówka jak to naprawić")
    need_to_fix: bool = Field(
        description="Czy ten problem musi być naprawiony, aby artefakt mógł być uznany za kompletny? (true/false)"
    )                     

class DesignFeedback(BaseModel):
    issues: List[Issue] = Field(
        default_factory=list,
        description="Jeśli is_complete = false, dodaj tutaj każdy znaleziony błąd. Zostaw pustą listę, jeśli is_complete = true."
    )
    is_complete: bool = Field(
        description="Czy artefakt jest kompletny i spełnia wymagania metodyki GAIA?"
    )

class OptimizationFeedback(BaseModel):
    specific_issue: str = Field(
        description="Krok 1: Zdefiniuj konkretny błąd w kontekście obecnego zadania (Co poszło nie tak?)."
    )
    abstract_rule: str = Field(
        description="Krok 2: GENERALIZACJA. Przetłumacz `specific_issue` na uniwersalną zasadę. NIE UŻYWAJ słów kluczowych z obecnego zadania (np. zamiast 'psy/karaluchy' użyj 'aktorzy/obiekty domenowe')."
    )
    new_system_prompt: str = Field(
        description="Krok 3: Zoptymalizowany, PEŁNY system prompt. Musi zawierać regułę wypracowaną w `abstract_rule`. Kategoryczny zakaz hardkodowania w nim rozwiązań specyficznych dla pojedynczego przypadku."
    )
    explanation: str = Field(
        description="Krok 4: Wyjaśnienie mechanizmu. Dlaczego zaktualizowany prompt zapobiegnie całej KLASIE podobnych błędów, a nie tylko temu jednemu?"
    )
   
   
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