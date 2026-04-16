from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class WorkerState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    system_message: str
    context: str
    task: str
    iteration: int

class ReportStructure(BaseModel):
    report: str = Field(...,
                        description=(
            "A comprehensive summary of actions taken during this iteration. "
            "You MUST explicitly state which files were created, modified, or deleted. "
            "Crucially, you must identify any 'technical debt' or unfinished tasks: "
            "if a file (e.g., Modal.jsx) was created but not yet implemented or imported, "
            "state this clearly so future iterations know it needs work. "
        ))
