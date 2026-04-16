from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from models import menager_llm
from tokens_stats import tokens_counter
from typing import Literal
from implementation.team.team_state import TeamState
from .menager_tools import tools
from config import settings
from utils import save_graph_visualization
import logging

llm_with_tools = menager_llm.bind_tools(tools)

tool_node = ToolNode(tools)

logger = logging.getLogger(__name__)

def prepare_input(state: TeamState):
    if not state["messages"]:
        logger.info("[Menager] got new task to do: %s", state['sprint_goal'])  
        system_prompt = """
            You are a Senior Technical Manager in a Software House AI.
            You manage a single, **Polymorphic Worker** capable of adopting any technical persona you define.

            YOUR OBJECTIVE: Execute a software project stage defined by the Sprint Goal.
            YOU CAN ONLY USE THE TOOLS. REST OF THE COMMUNICATION WILL BE IGNORED.

            *** WORKER OPERATIONAL PROFILE (CRITICAL) ***
            - NATURE: The Worker is an Autonomous LLM Agent, not a human. It operates based on your prompts.
            - INTERFACE: The Worker has full access to a TERMINAL/CONSOLE and FILE SYSTEM. It executes shell commands and manages files programmatically.
            - NO GUI/MOUSE: The Worker runs in a HEADLESS environment.
              - It CANNOT use a mouse, click buttons, or interact with visual interfaces.
              - It CANNOT "open a browser" to verify UI visually.
              - All interactions must be done via CLI, APIs, or code execution.

            *** CRITICAL DELEGATION RULES ***
            - DO NOT WRITE CODE YOURSELF. Your job is to define requirements, not to implement them.
            - DO NOT dictate the exact implementation details (e.g., "Write `def func(): ...`").
            - INSTEAD, describe the **desired behavior**, **inputs/outputs**, **edge cases**, and **acceptance criteria**.
            - Trust the Worker's expertise. Give them the autonomy to write the syntax.

*           ** QUALITY ASSURANCE & DEFINITION OF DONE ***
            - CODE MUST RUN: A Sprint is ONLY completed when the code is implemented AND verified to be working. Static files are not enough.
            - PRAGMATIC TESTING You MUST instruct the Worker to write and run tests (Unit/Integration) for business logic and complex algorithms.
              - *AVOID* testing trivial boilerplate (e.g., simple getters/setters, standard config loads) to save resources.
              - *ENFORCE* testing of critical paths and edge cases.
            
            YOUR RESPONSIBILITIES:
            1. Analyze the situation: Review the current state: project context, and goal.
            2. Determine Strategy: Decide which role is needed NOW (Developer, Tester, DevOps) and what specific task they must perform.
            
            3. Configure the Worker:
            - WRITE THEIR SYSTEM PROMPT: Define their persona (e.g., "You are a Senior Python Dev").
            - DEFINE THE TASK: Describe WHAT needs to be done, not HOW. 
              * BAD: "Write this code: [code block]"
              * GOOD: "Create a class `X` that handles add/remove operations and persists data to JSON. Handle file not found errors."
            - PROVIDE CONTEXT: The Worker is stateless. You MUST paste all relevant existing code, error logs, or file structures into their context message so they can see the current state.

            4. Report: Evaluate if the goal is FULLY achieved.
             - If you are 100% certain: Submit a summary to the architect.
             - If you have any doubt (even the slightest): Do NOT submit yet. Instead, perform verification tests, run diagnostics, or execute proof-of-work actions to confirm functionality. Only report success once validity is proven.
        """
        return {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"""
                --- STARTING NEW SPRINT ---
                
                SPRINT GOAL: 
                {state['sprint_goal']}
                
                PROJECT CONTEXT: 
                {state['project_context']}
                """)
            ]
        }
    
    return {}

def update_next_step(last_message):

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "submit_task":
            return{
                "worker_task": tool_call["args"]["task"],
                "worker_context": tool_call["args"]["context"],
                "worker_system_message": tool_call["args"]["system_message"],
                "next_step": "worker"
            }
        if tool_call["name"] == "submit_final_report":
            report = tool_call["args"]["report"]
            logger.info("[Menager] Sprint completed. Report: %s", report)
            return{
                "report": tool_call["args"]["report"],
                "next_step": END
            }
        
    return{
        "next_step": "call_model"
    }


def call_model(state: TeamState):
    response = llm_with_tools.invoke(state["messages"])
    metadata = response.usage_metadata
    tokens_counter.add("IMLEMENTATION", "Menager", {"raw": response, "usage_metadata": metadata})

    next_step_update = update_next_step(response)

    return{
        "messages": response,
        **next_step_update
    }

def route(state: TeamState) ->Literal["call_model", END]:
    return "call_model" if state["next_step"] == "call_model" else  END

def prepare_graph():
    graph = StateGraph(TeamState)
    
    graph.add_node("prepare_input", prepare_input)
    graph.add_node("call_model", call_model)
    graph.add_node("tool_node", tool_node)
        
    graph.add_edge(START, "prepare_input")
    graph.add_edge("prepare_input", "call_model")
    graph.add_edge("call_model", "tool_node")
    graph.add_conditional_edges("tool_node", route)

    menager_process = graph.compile()

    if settings.generate_graphs:
        save_graph_visualization(
            menager_process.get_graph(),
            "menager_graph.png"
        )

    return menager_process

menager_process = prepare_graph()

def menager_node(state: TeamState):
    final_state = menager_process.invoke(state)
    return final_state