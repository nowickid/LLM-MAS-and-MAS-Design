from langgraph.graph import StateGraph, START, END
from .worker_state import WorkerState
from .worker_tools import tools, kill_background_processes
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode
from models import worker_llm
from tokens_stats import tokens_counter
from typing import Literal
from config import settings
import logging
import json

llm_with_tools = worker_llm.bind_tools(tools)

tool_node = ToolNode(tools)
logger = logging.getLogger(__name__)


def prepare_input(state: WorkerState):
    logger.info("[Worker] task to do: %s,", {state['task']})
    return {
        "messages": [
            SystemMessage(content=f"""{state['system_message']}\n
                          RULES:
- If you need to create a file, call 'write_to_file' immediately.
- If you need to read, call 'read_file'.
- DO NOT describe what you will do. DO NOT output code blocks.
- JUST CALL THE TOOLS.
- If you deem the task fully completed, write a concise report on it
- DO NOT write the report as a plain text message. Pass the content to the 'send_report' tool.
                          """),
            HumanMessage(content=f"CONTEXT: {state['context']}\nTASK TO DO: {state['task']}, \n"),
        ],
        "iteration": 1
    }

def call_model(state: WorkerState):
    if state["iteration"]  == settings.worker_recursion_limit:
        logger.warning("[Worker] Reached maximum recursion limit (%d). Generating final report.", settings.worker_recursion_limit)
        state["messages"].append(HumanMessage(content="You have reached the maximum number of iterations. Please provide a concise final report on the task. DO NOT USE TOOLS ANYMORE."))
    
    response = llm_with_tools.invoke(state["messages"])
    metadata = response.usage_metadata
    tokens_counter.add("IMLEMENTATION", "Worker", {"raw": response, "usage_metadata": metadata})
    return{
        "messages": response,
        "iteration": state["iteration"] + 1
    }


def route(state: WorkerState) ->Literal["tool_node", END]:
    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return END
    
    return "tool_node"

def post_tool_route(state: WorkerState) -> Literal["call_model", END]:
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, ToolMessage):
        if last_message.name == "send_report":
            return END
            
    return "call_model"

def extract_report(result):
    final_report = "No report generated."
    
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call["name"] == "send_report":
                    args = tool_call.get("args", {})
                    final_report = args.get("report") or args.get("content") or str(args)
                    return final_report

        if isinstance(message, AIMessage) and isinstance(message.content, str):
            if '"name": "send_report"' in message.content:
                try:
                    data = json.loads(message.content)
                    
                    if data.get("name") == "send_report":
                        params = data.get("parameters", {}) or data.get("args", {})
                        final_report = params.get("report") or params.get("content")
                        return final_report
                        
                except json.JSONDecodeError:
                    # Jeśli to nie jest poprawny JSON, ale zawiera tekst raportu,
                    # można spróbować wyciąć go ręcznie, ale zazwyczaj json.loads wystarczy
                    pass

    return final_report
    
def prepare_graph():
    graph = StateGraph(WorkerState)
    
    graph.add_node("prepare_input", prepare_input)
    graph.add_node("call_model", call_model)
    graph.add_node("tool_node", tool_node)
    
    graph.add_edge(START, "prepare_input")
    graph.add_edge("prepare_input", "call_model")

    graph.add_conditional_edges("call_model", route)
    graph.add_conditional_edges("tool_node", post_tool_route)

    worker_process = graph.compile()

    if settings.generate_graphs:
        from utils import save_graph_visualization
        save_graph_visualization(worker_process.get_graph(), "worker_graph.png")
    return worker_process

worker_process = prepare_graph()
    
def process_worker_graph(state: WorkerState, config):
    woker_config = {
        **config,
        "recursion_limit": settings.worker_recursion_limit
    }
    
    result = worker_process.invoke(state,
        config=woker_config
    )
    kill_background_processes()
    final_report = extract_report(result)

    logger.info("[Worker] generated report: %s", final_report)
    return final_report