from state import State
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, BaseMessage
from gaia.design.design_structures import DesignState, DesignFeedback, AgentModel, ServiceModel, AcquaintanceModel, OptimizationFeedback
from gaia.design.design_prompts import DEFAULT_CRITIC_AGENTS_PROMPT, DEFAULT_AGENTS_PROMPT, DEFAULT_SERVICE_PROMPT, DEFAULT_CRITIC_SERVICE_PROMPT, DEFAULT_ACQUAINTANCES_PROMPT, DEFAULT_CRITIC_ACQUAINTANCES_PROMPT
from tokens_stats import tokens_counter
from models import creator_llm, critic_llm, optimization_llm
from typing import Literal
import logging
from config import settings
from utils import save_graph_visualization

logger = logging.getLogger(__name__)

DESIGN_LAYER_NAME = "GAIA_DESIGN"

def handle_max_iterations(state: DesignState, id) -> dict:
    logger.warning("Osiągnięto maksymalną liczbę iteracji %s.", id)
    return {
        "messages": [RemoveMessage(id=m.id) for m in state["messages"]],
        f"feedbacks_{id}": [DesignFeedback(is_complete=True, message="Maksymalna liczba iteracji osiągnięta.")]
    }
    
def call_optimize_prompt(state: DesignState, phase: Literal["agents", "services", "acquaintances"]) -> None:
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
    print(f"Zoptymalizowany prompt dla {DESIGN_LAYER_NAME}-{phase}:\n\n {response.model_dump_json(indent=2)}\n\n")
    return {
        f"prompt_{phase}": response.new_system_prompt
    }
 
def only_last_messages(messages: BaseMessage, n=2) -> list[BaseMessage]:
    if len(messages) <= n:
        return messages
    
    return messages[-n:]

def prepare_feedback_message(parsed: DesignFeedback) -> HumanMessage:
    feedback_text = "Znaleziono następujące problemy:\n"
    for issue in [i for i in parsed.issues if i.need_to_fix]:
        feedback_text += f"- {issue.description}\n  Wskazówka: {issue.fix}\n"
        
    return HumanMessage(content=f"[FEEDBACK KRYTYKA]:\n{feedback_text}")

# Model agentów
def call_agent_model(state: DesignState) -> dict:
    system = SystemMessage(content=state["prompt_agents"])

    structured_llm = creator_llm.with_structured_output(AgentModel, include_raw=True)
    response = structured_llm.invoke([system, HumanMessage(content=state["analysis_context"])] +
                                     only_last_messages(state["messages"]))
    tokens_counter.add(DESIGN_LAYER_NAME, "DefineAgents", response)
    
    raw = response["raw"]
    parsed: AgentModel = response["parsed"]
    
    logger.info("%s \t Model agentów:\n%s", DESIGN_LAYER_NAME, parsed.model_dump_json(indent=2))

    return {
        "messages": [raw],
        "agent_model": parsed,
    }


def call_critic_agents(state: DesignState) -> dict:
    feedbacks = state.get("feedbacks_agents", [])
    if len(feedbacks) >= settings.design_agents_max_iterations:
        return handle_max_iterations(state, "agents")
    
    system = SystemMessage(content=DEFAULT_CRITIC_AGENTS_PROMPT) 

    structured_llm = critic_llm.with_structured_output(DesignFeedback, include_raw=True)
    response = structured_llm.invoke(
        [system, HumanMessage(content=f"{state['analysis_context']}\n\n\n\n Model agentów do oceny: {state['agent_model'].model_dump_json()}")] 
    )
    tokens_counter.add(DESIGN_LAYER_NAME, "CriticAgents", response)
    parsed: DesignFeedback = response["parsed"]
    logger.info("%s \t Krytyk agentów:\n%s",DESIGN_LAYER_NAME,  parsed.model_dump_json(indent=2))

    msg = (
        prepare_feedback_message(parsed) 
        if not parsed.is_complete 
        else [RemoveMessage(id=m.id) for m in state["messages"]]
    )
    return {
        "messages": msg,
        "feedbacks_agents": [parsed],
    }

def route_after_agents(state: DesignState) -> Literal["DefineAgents", "DefineService"]:
    feedbacks = state.get("feedbacks_agents", [])
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return "DefineService"
    
    return "DefineAgents"
    
    
def route_after_agents_with_optimization(state: DesignState) -> Literal["OptymalizeAgents", "DefineService"]:
    feedbacks = state.get("feedbacks_agents", [])
    last = feedbacks[-1] if feedbacks else None
    if last and not last.is_complete:
        return "DefineService"
    
    return "OptymalizeAgents"
    

#  Model usług
def call_service_model(state: DesignState) -> dict:
    system = SystemMessage(content=state["prompt_services"])

    structured_llm = creator_llm.with_structured_output(ServiceModel, include_raw=True)
    response = structured_llm.invoke(
        [system,HumanMessage(content=f"{state["analysis_context"]}\n Model agentów: {state["agent_model"].model_dump_json()}")] +
        only_last_messages(state["messages"])
    )
    tokens_counter.add(DESIGN_LAYER_NAME, "DefineService", response)
    parsed: ServiceModel = response["parsed"]
    raw = response["raw"]
    logger.info("%s \t Model usług:\n%s",DESIGN_LAYER_NAME, parsed.model_dump_json(indent=2))

    return {
        "messages": raw,
        "service_model": parsed,
    }


def call_critic_services(state: DesignState) -> dict:
    feedbacks = state.get("feedbacks_services", [])
    if len(feedbacks) >= settings.design_services_max_iterations:
        return handle_max_iterations(state, "services")
    
    system = SystemMessage(content=DEFAULT_CRITIC_SERVICE_PROMPT)
    structured_llm = critic_llm.with_structured_output(DesignFeedback, include_raw=True)
    
    response = structured_llm.invoke(
        [system, HumanMessage(content=f"{state['analysis_context']}\n Model agentów: {state['agent_model'].model_dump_json()}\n\n\n\n Model usług do oceny: {state['service_model'].model_dump_json()}")]
    )
    tokens_counter.add(DESIGN_LAYER_NAME, "CriticService", response)
    
    parsed: DesignFeedback = response["parsed"]
    logger.info("Krytyk usług:\n%s", parsed.model_dump_json(indent=2))

    msg = (
        prepare_feedback_message(parsed)
        if not parsed.is_complete 
        else [RemoveMessage(id=m.id) for m in state["messages"]]
    )
    return {
        "messages": msg,
        "feedbacks_services": [parsed],
    }


def route_after_services(state: DesignState) -> Literal["DefineService", "DefineAcquaintance"]:
    feedbacks = state.get("feedbacks_services", [])
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return "DefineAcquaintance"
    return "DefineService"

def route_after_services_with_optimization(state: DesignState) -> Literal["OptymalizeServices", "DefineAcquaintance"]:
    feedbacks = state.get("feedbacks_services", [])
    last = feedbacks[-1] if feedbacks else None
    if last and last.is_complete:
        return "DefineAcquaintance"
    return "OptymalizeServices"


# ---------------------------------------------------------------------------
# KROK 3 - Model znajomości
# ---------------------------------------------------------------------------

def call_acquaintance_model(state: DesignState) -> dict:
    system = SystemMessage(content=state["prompt_acquaintances"])

    structured_llm = creator_llm.with_structured_output(AcquaintanceModel, include_raw=True)
    response = structured_llm.invoke(
        [system, HumanMessage(content=f"{state['analysis_context']}\n Model agentów: {state['agent_model'].model_dump_json()}\n Model usług: {state['service_model'].model_dump_json()}")] +
        only_last_messages(state["messages"])
    )
    tokens_counter.add(DESIGN_LAYER_NAME, "DefineAcquaintance", response)    

    parsed: AcquaintanceModel = response["parsed"]
    raw = response["raw"]
    
    logger.info("Model znajomości:\n%s", parsed.model_dump_json(indent=2))

    return {
        "messages": raw,
        "acquaintance_model": parsed,
    }


def call_critic_acquaintance(state: DesignState) -> dict:
    feedbacks = state.get("feedbacks_acquaintance", [])
    if len(feedbacks) >= settings.design_acquaintances_max_iterations:
        return handle_max_iterations(state, "acquaintance")
    
    system = SystemMessage(content=DEFAULT_CRITIC_ACQUAINTANCES_PROMPT)
    structured_llm = critic_llm.with_structured_output(DesignFeedback, include_raw=True)
    response = structured_llm.invoke(
        [system,HumanMessage(content=f"{state['analysis_context']}\n Model agentów: {state['agent_model'].model_dump_json()}\n Model usług: {state['service_model'].model_dump_json()}\n\n\n\n Model znajomości do oceny: {state['acquaintance_model'].model_dump_json()}")]
    )
    tokens_counter.add(DESIGN_LAYER_NAME, "CriticAcquaintance", response)
    
    parsed: DesignFeedback = response["parsed"]
    logger.info("Krytyk znajomości:\n%s", parsed.model_dump_json(indent=2))
    
    msg = (
        prepare_feedback_message(parsed)
        if not parsed.is_complete 
        else [RemoveMessage(id=m.id) for m in state["messages"]]
    )
    
    return {
        "messages": msg,
        "feedbacks_acquaintance": [parsed]
    }

def route_after_acquaintance(state: DesignState) -> Literal["DefineAcquaintance", END]:
    feedbacks = state.get("feedbacks_acquaintance", [])
    last = feedbacks[-1] if feedbacks else None
    if last and not last.is_complete:
        return "DefineAcquaintance"
    return END

def route_after_acquaintance_with_optimization(state: DesignState) -> Literal["OptymalizeAcquaintance", END]:
    feedbacks = state.get("feedbacks_acquaintance", [])
    last = feedbacks[-1] if feedbacks else None
    if last and not last.is_complete:
        return END
    return "OptymalizeAcquaintance"

# ---------------------------------------------------------------------------
# PRZYGOTOWANIE STANU I URUCHOMIENIE
# ---------------------------------------------------------------------------

def prepare_design_state(state: State) -> DesignState:
    logger.info("Przygotowuję stan dla projektowania...")

    description = state.get("description")
    func_reqs = state.get("functional_requirements", [])
    func_block = "\n".join(f"- {req}" for req in func_reqs)
    roles = state.get("roles")
    interactions = state.get("interactions")

    content = (
        f"Opis systemu:\n{description if description else '  (brak)'}\n"
        f"Wymagania funkcjonalne:\n{func_block if func_block else '  (brak)'}\n"
        f"Role GAIA z fazy analizy:\n{roles.model_dump_json()}\n\n"
        f"Model interakcji z fazy analizy:\n{interactions.model_dump_json()}"
    )

    return {
        "messages": [HumanMessage(content=content)],
        "feedbacks_agents": [],
        "feedbacks_services": [],
        "feedbacks_acquaintance": [],
        
        "analysis_context": content,
        "identified_roles": roles,
        "interaction_model": interactions,
        
        "agent_model": None,
        "service_model": None,
        "acquaintance_model": None,
        
        "prompt_agents": DEFAULT_AGENTS_PROMPT,
        "prompt_services": DEFAULT_SERVICE_PROMPT,
        "prompt_acquaintances": DEFAULT_ACQUAINTANCES_PROMPT,
    }


def process_design(state: State) -> dict:
    initial_state = prepare_design_state(state)

    g = StateGraph(DesignState)

    g.add_node("DefineAgents",         call_agent_model)
    g.add_node("CriticAgents",       call_critic_agents)
    g.add_node("DefineService",       call_service_model)
    g.add_node("CriticService",     call_critic_services)
    g.add_node("DefineAcquaintance",  call_acquaintance_model)
    g.add_node("CriticAcquaintance", call_critic_acquaintance)

    g.add_edge(START,                "DefineAgents")
    g.add_edge("DefineAgents",         "CriticAgents")
    g.add_edge("DefineService",       "CriticService")
    g.add_edge("DefineAcquaintance",  "CriticAcquaintance")

    if settings.use_prompt_optimization:
        g.add_node("OptymalizeAgents", lambda state: call_optimize_prompt(state, "agents"))
        g.add_node("OptymalizeServices", lambda state: call_optimize_prompt(state, "services"))
        g.add_node("OptymalizeAcquaintance", lambda state: call_optimize_prompt(state, "acquaintances"))
        
        g.add_edge("OptymalizeAgents", "DefineAgents")
        g.add_edge("OptymalizeServices", "DefineService")
        g.add_edge("OptymalizeAcquaintance", "DefineAcquaintance")
        g.add_conditional_edges("CriticAgents",       route_after_agents_with_optimization)
        g.add_conditional_edges("CriticService",     route_after_services_with_optimization)
        g.add_conditional_edges("CriticAcquaintance", route_after_acquaintance_with_optimization)
    else:
        g.add_conditional_edges("CriticAgents",       route_after_agents)
        g.add_conditional_edges("CriticService",     route_after_services)
        g.add_conditional_edges("CriticAcquaintance", route_after_acquaintance)

    graph = g.compile()
    
    if settings.generate_graphs:
        save_graph_visualization(graph.get_graph(), "design_flow.png")
    
    final_state: DesignState = graph.invoke(initial_state)    
    return {
        "agent_model":        final_state.get("agent_model"),
        "service_model":      final_state.get("service_model"),
        "acquaintance_model": final_state.get("acquaintance_model"),
    }