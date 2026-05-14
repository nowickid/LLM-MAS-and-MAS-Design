from typing import TypedDict, Annotated, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from operator import add
from pydantic import BaseModel, Field, model_validator
from typing import List

# Zidentyfikowane role (prototypy)
class RolePrototype(BaseModel):
    """Wstępny prototyp roli - tylko nazwa i krótki opis."""
    name: str = Field(description="Nazwa roli (PascalCase, język angielski)")
    description: str = Field(description="""
        Rozbudowany opis celu istnienia roli. Z tego opisu muszą bezpośrednio wynikać akcje wewnętrzne i komunikacja z innymi rolami.
        """)
 
class IdentifiedRoles(BaseModel):
    """Zidentyfikowane prototypy ról."""
    roles: List[RolePrototype]
 
 
# protocol_name description
class RoleInteraction(BaseModel):
    goal: str = Field(description="Cel biznesowy interakcji (PascalCase, ang.)")
    protocol_name: str = Field(description="Nazwa protokołu (PascalCase, ang., np. 'RequestDataProcessing', 'NotifyStateChange').")
    description: str = Field(description="Krótki opis tej komunikacji i zjawiska, które ją wyzwala.")
    initiator: str = Field(description="Nazwa roli inicjującej")
    responder: str = Field(description="Nazwa roli odpowiadającej")
    inputs: List[str] = Field(description="Obiekty danych (Rzeczowniki, PascalCase, np. 'EntityProfile', 'TransactionRecord') wnoszone przez inicjatora. ZAKAZ używania czasowników!")
    outputs: List[str] = Field(description="Obiekty danych (Rzeczowniki, PascalCase) zwracane przez respondera. ZAKAZ używania czasowników!") 
 
class InteractionModel(BaseModel):
    """Model interakcji między rolami."""
    interactions: List[RoleInteraction]
 
class Prototypes(BaseModel):
    """Zidentyfikowane prototypy ról i interakcji."""
    roles: IdentifiedRoles
    interactions: InteractionModel

class Permissions(BaseModel):
    read: List[str] = Field(default_factory=list,
        description="Nazwy obiektów DANYCH (Rzeczowniki, np. 'Document', 'StateInfo'). ZAKAZ wpisywania nazw aktywności/protokołów!")
    write: List[str] = Field(default_factory=list,
        description="Nazwy obiektów DANYCH modyfikowanych przez rolę. ZAKAZ wpisywania procesów!")
    consume: List[str] = Field(default_factory=list,
        description="Obiekty danych trwale usuwane/konsumowane przez rolę.")
    produce: List[str] = Field(default_factory=list,
        description="Nowe obiekty danych tworzone przez rolę.")
 
class Responsibilities(BaseModel):
    liveness: str = Field(
        description="Logiczny, CHRONOLOGICZNY ciąg życia roli (np. Inicjalizacja -> Przetwarzanie -> Potwierdzenie). Używaj wyłącznie elementów z list 'activities' i 'protocols'.")
    safety: List[str] = Field(default_factory=list,
        description="Zasady niezmienniczości i stany brzegowe (np. ['EntityStatus == Active', 'QueueSize <= MaxLimit']). ZAKAZ stosowania wyłącznie trywialnych warunków 'UniqueID != Null'.")
 
class GaiaRole(BaseModel):
    """Kompletna definicja roli - permissions, responsibilities, protocols."""
    name: str = Field(description="Nazwa roli (PascalCase) - musi odpowiadać prototypowi")
    description: str = Field(description="Opis roli spójny z prototypem")
    activities: List[str] = Field(description="Wewnętrzne działania obliczeniowe/procesy roli BEZ KOMUNIKACJI (PascalCase, ang.). ZAKAZ używania nazw zdefiniowanych jako protokoły!")
    protocols: List[str] = Field(description="Ścisłe powiązanie z Modelami Interakcji. Lista musi zawierać protokoły zadeklarowane w polu 'protocol_name' (np. dodając prefiksy jak Request/Respond).")
    permissions: Permissions
    responsibilities: Responsibilities
     
class DefineRoles(BaseModel):
    """Pełny model ról GAIA."""
    roles: List[GaiaRole]
 


# Wspólne
class Issue(BaseModel):
    criterion: str = Field(description="Które kryterium GAIA zostało złamane (SŁOWNIE)")
    description: str = Field(description="Szczegółowy opis tego, co jest źle")
    fix: str = Field(description="Konkretna wskazówka jak to naprawić")
    need_to_fix: bool = Field(
        description="Czy ten problem musi być naprawiony, aby artefakt mógł być uznany za kompletny? (true/false)"
    )
class AnalysisFeedback(BaseModel):
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