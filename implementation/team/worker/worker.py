from ..team_state import TeamState
from .worker_graph import process_worker_graph
from .worker_state import WorkerState
from langchain_core.runnables import RunnableConfig

def worker_node(state: TeamState, config: RunnableConfig = None):
    worker_state: WorkerState = {
        "messages": [],
        "task": state["worker_task"],
        "context": state["worker_context"],
        "system_message": state["worker_system_message"],
    }
    report = process_worker_graph(worker_state, config=config)
    return {
        "messages": f"Worker completed the task and generated a report:\n{report}"
    }
    