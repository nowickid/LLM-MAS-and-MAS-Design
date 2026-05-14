from state import State
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage, BaseMessage
from gaia.analysis.analysis_structures import AnalizeState, AnalysisFeedback, DefineRoles, IdentifiedRoles, InteractionModel, OptimizationFeedback, Prototypes
from gaia.analysis.analysis_prompts import  DEFAULT_ROLE_DEFS_PROMPT, DEFAULT_PROTOTYPES_PROMPT, DEFAULT_CRITIC_PROTOTYPES, DEFAULT_CRITIC_ROLE_DEFS_PROMPT
from models import creator_llm, critic_llm, optimization_llm
from typing import Literal
from config import settings
from utils import save_graph_visualization
from tokens_stats import tokens_counter
import logging
from langchain_core.runnables import RunnableConfig
logger = logging.getLogger(__name__)

ANALYSIS_LAYER_NAME = "GAIA_ANALYSIS"

def handle_max_iterations(state: AnalizeState, id) -> dict:
    logger.warning("Osiągnięto maksymalną liczbę iteracji %s.", id)
    return {
        "messages": [RemoveMessage(id=m.id) for m in state["messages"]],
        f"feedbacks_{id}": [AnalysisFeedback(is_complete=True, message="Maksymalna liczba iteracji osiągnięta.")]
    }
    
    
def call_optimize_prompt(state: AnalizeState, phase: Literal["prototypes", "role_defs"]) -> None:
    system = SystemMessage(content="""
# ROLE
Jesteś Meta-Architektem Promptów. Twoim celem nie jest tylko "naprawienie błędu", ale stworzenie robustnego (odpornego) systemu instrukcji, który przewiduje błędy, zanim wystąpią.

# INPUT ANALYSIS (Triangulacja)
Analizując dostarczone dane, wykonaj:
1. IDENTYFIKACJA ROOT CAUSE: Czy błąd wynika z braku wiedzy, braku ograniczeń, czy niejasnej struktury?
2. IMPACT ASSESSMENT: Czy poprawka pod ten błąd nie zepsuje innych aspektów promptu (np. tonu, formatu)?
3. GENERALIZACJA: Przekształć feedback krytyka w uniwersalną zasadę logiczną. NIE MOŻESZ ZWRACAĆ SYSTEM PROMPTU ściśle związanego z tym konkretnym błędem. Musisz stworzyć regułę, która zapobiega nie tylko temu błędowi, ale całej klasie podobnych błędów w przyszłości.

# OPTIMIZATION RULES
- Zamiast dodawać kolejne "Nie rób X", stwórz pozytywną definicję oczekiwanego zachowania.
- Stosuj "Variables isolation" - oddziel instrukcje od przykładów.
- Używaj struktury hierarchicznej (Nagłówki Markdown + Tagi XML).

# OUTPUT REQUIREMENT
Zwróć zoptymalizowany prompt oraz krótkie wyjaśnienie: "Dlaczego ta zmiana zapobiegnie tego typu błędom?".
    """)
    
    message = HumanMessage(content=f"""
    Oto obecny prompt do wygenerowania artefaktu:\n{state[f"prompt_{phase}"]}\n
    
    Wygenerowany artefakt:\n{state['messages'][-2].content} \n
    
    Feedback krytyka:\n{state['messages'][-1].content} \n
    """)
    response: OptimizationFeedback= optimization_llm.with_structured_output(OptimizationFeedback).invoke([system] +[message])
    print(f"Zoptymalizowany prompt dla {ANALYSIS_LAYER_NAME}-{phase}:\n\n {response.model_dump_json(indent=2)}\n\n")
    return {
        f"prompt_{phase}": response.new_system_prompt
    }
    
def prepare_feedback_message(parsed: AnalysisFeedback) -> HumanMessage:
    feedback_text = "Znaleziono następujące problemy:\n"
    for issue in [i for i in parsed.issues if i.need_to_fix]:
        feedback_text += f"- {issue.description}\n  Wskazówka: {issue.fix}\n"
        
    return HumanMessage(content=f"[FEEDBACK KRYTYKA]:\n{feedback_text}")
 
def only_last_messages(messages: BaseMessage, n=2) -> list[BaseMessage]:
    if len(messages) <= n:
        return messages
    
    return messages[-n:]

def call_define_prototypes(state: AnalizeState) -> dict:
    system = SystemMessage(content=state["prompt_prototypes"])
    structured_llm = creator_llm.with_structured_output(Prototypes, include_raw=True)

    response = structured_llm.invoke(
        [system] + [state["requirements"]] + only_last_messages(state["messages"])
    )
    tokens_counter.add(ANALYSIS_LAYER_NAME, "DefinePrototypes", response)
    
    raw = response["raw"]
    parsed: Prototypes = response["parsed"]

    logger.info("%s\t Prototypy:\n%s", ANALYSIS_LAYER_NAME, parsed.model_dump_json(indent=2))
    return {
        "messages": [raw],
        "identified_roles": parsed.roles,
        "interaction_model": parsed.interactions,
    }
    
def call_critic_prototypes(state: AnalizeState) -> dict:
    feedbacks = state.get("feedbacks_prototypes", [])
    if len(feedbacks) >= settings.analysis_prototypes_max_iterations:
        return handle_max_iterations(state, "prototypes")
        
    system = SystemMessage(content=DEFAULT_CRITIC_PROTOTYPES)
    structured_llm = critic_llm.with_structured_output(AnalysisFeedback, include_raw=True)
    response = structured_llm.invoke(
        [system] +
        [HumanMessage(content=(
            f"""{state["requirements"].content} 
            DO OCENY:
            Oto zidentyfikowane role:\n{state['identified_roles'].model_dump_json()} \n
            Oto model interakcji:\n{state['interaction_model'].model_dump_json()} \n
            """
        ))]
    )
    tokens_counter.add(ANALYSIS_LAYER_NAME, "CriticPrototypes", response)

    parsed: AnalysisFeedback = response["parsed"]
    
    logger.info("%s\tKrytyk prototypów:\n%s", ANALYSIS_LAYER_NAME, parsed.model_dump_json(indent=2))

    msg = (
        prepare_feedback_message(parsed)
        if not parsed.is_complete
        else [RemoveMessage(id=m.id) for m in state["messages"]]
    )
    return {
        "messages": msg,
        "feedbacks_prototypes": [parsed],
    }
    
def route_after_prototypes(state: AnalizeState) -> Literal["DefinePrototypes", "DefineRoles"]:
    feedbacks = state["feedbacks_prototypes"]
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return "DefineRoles"
    return "DefinePrototypes"

def route_after_prototypes_with_optimize(state: AnalizeState) -> Literal["OptimizePrototypes", "DefineRoles"]:
    feedbacks = state["feedbacks_prototypes"]
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return "DefineRoles"
    
    return "OptimizePrototypes"

# Model ról (pełny) 
def call_define_roles(state: AnalizeState) -> dict:
    system = SystemMessage(content=state["prompt_role_defs"])
 
    structured_llm = creator_llm.with_structured_output(DefineRoles, include_raw=True)
    response = structured_llm.invoke(
        [system] +
        [HumanMessage(content=f"{state["requirements"].content}\n\n Oto zidentyfikowane role:\n{state['identified_roles'].model_dump_json()} \n Oto model interakcji:\n{state['interaction_model'].model_dump_json()}")] +
        only_last_messages(state["messages"])
    )
    tokens_counter.add(ANALYSIS_LAYER_NAME, "DefineRoles", response)

    raw = response["raw"]
    parsed = response["parsed"]
    logger.info("%s \t Model ról:\n%s",ANALYSIS_LAYER_NAME, parsed.model_dump_json(indent=2))
 
    return {
        "messages": [raw],
        "last_roles": parsed,
    }
 
 
def call_critic_roles(state: AnalizeState) -> dict:
    feedbacks = state.get("feedbacks_roles", [])
    if len(feedbacks) >= settings.analysis_roles_max_iterations:
        return handle_max_iterations(state, "roles")
    
    system = SystemMessage(content=DEFAULT_CRITIC_ROLE_DEFS_PROMPT)
 
    structured_llm = critic_llm.with_structured_output(AnalysisFeedback, include_raw=True)
    response = structured_llm.invoke(
        [system] +
        [HumanMessage(content=f"{state["requirements"].content}\nOto zidentyfikowane role:\n{state['identified_roles'].model_dump_json()} \n Oto model interakcji:\n{state['interaction_model'].model_dump_json()} \n Oto model ról do oceny:\n{state['last_roles'].model_dump_json()}")] 
    )
    tokens_counter.add(ANALYSIS_LAYER_NAME, "CriticRoles", response)
    
    parsed: AnalysisFeedback = response["parsed"]
    
    logger.info("Krytyk modelu ról:\n%s", parsed.model_dump_json(indent=2))
    
    msg = (
        prepare_feedback_message(parsed) 
        if not parsed.is_complete 
        else [RemoveMessage(id=m.id) for m in state["messages"]]
    )
    return {
        "messages": msg,
        "feedbacks_roles": [parsed],
    }
 
 
def route_after_roles(state: AnalizeState) -> Literal["DefineRoles", "__end__"]:
    feedbacks = state["feedbacks_roles"]
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return END
    return "DefineRoles"
 
def route_after_roles_with_optimize(state: AnalizeState) -> Literal["OptimizeRoleDefs", "__end__"]:
    feedbacks = state["feedbacks_roles"]
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return END
    return "OptimizeRoleDefs"
 
 
def prepare_analize_state(state: State) -> AnalizeState:
    func_reqs = state.get("functional_requirements", [])
    description = state.get("description", "")
 
    func_block = "\n".join(f"  - {r}" for r in func_reqs) or "  (brak)"
    print(f"Funkcjonalne wymagania:\n{func_block}")
 
    desc = (
        f"Opis systemu:\n{description if description else '  (brak)'}\n"
        f"Wymagania funkcjonalne:\n{func_block if func_block else '  (brak)'}\n"
    )
    logger.debug("Opis dla Analityka:\n%s", desc)
 
    return {
        "identified_roles": None,
        "interaction_model": None,
        "last_roles": None,
        "requirements": HumanMessage(content=desc),
        "prompt_role_defs": DEFAULT_ROLE_DEFS_PROMPT,
        "prompt_prototypes": DEFAULT_PROTOTYPES_PROMPT,
        "messages": [],
        "feedbacks_prototypes": [],
        "feedbacks_roles": [],
    }
 
 
def process_analize(state: State, config: RunnableConfig = None) -> tuple[DefineRoles, InteractionModel]:    
    initial_state = prepare_analize_state(state)

    g = StateGraph(AnalizeState)
    
    g.add_node("DefinePrototypes", call_define_prototypes)
    g.add_node("CriticPrototypes", call_critic_prototypes)
    
    g.add_node("DefineRoles",        call_define_roles)
    g.add_node("CriticRoles",        call_critic_roles)
    
    g.add_edge(START,            "DefinePrototypes")
    g.add_edge("DefinePrototypes", "CriticPrototypes")
    g.add_edge("DefineRoles",    "CriticRoles")
    
    if settings.use_prompt_optimization:
        g.add_node("OptimizePrototypes",        lambda s: call_optimize_prompt(s, "prototypes"))
        g.add_node("OptimizeRoleDefs",     lambda s: call_optimize_prompt(s, "role_defs"))

        g.add_conditional_edges("CriticPrototypes", route_after_prototypes_with_optimize)
        g.add_conditional_edges("CriticRoles",        route_after_roles_with_optimize)

        g.add_edge("OptimizePrototypes",        "DefinePrototypes")
        g.add_edge("OptimizeRoleDefs",     "DefineRoles")

    else:
        g.add_conditional_edges("CriticPrototypes", route_after_prototypes)
        g.add_conditional_edges("CriticRoles", route_after_roles)
 
    graph = g.compile()
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), "analysis_flow.png")
    
    final_state: AnalizeState = graph.invoke(initial_state)
    if settings.use_prompt_optimization:
        logger.debug("\n\n\n PROMPTY: prototypy %s \n\n  role %s", final_state["prompt_prototypes"], final_state["prompt_role_defs"])
    print("Tokens used in ANALYSIS layer:\n", tokens_counter.summary())
    return {
        "roles": final_state.get("last_roles"),
        "interactions": final_state.get("interaction_model")
    }

