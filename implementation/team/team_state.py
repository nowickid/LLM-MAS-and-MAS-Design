from typing import Annotated, TypedDict
from langchain_core.messages import  BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

class TeamState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    sprint_goal: str
    project_context: str
    worker_task: str
    worker_context: str
    worker_system_message: str
    report: str
    next_step: str


class TaskStucture(BaseModel):
    task: str = Field(..., description="The task assigned to the worker.")
    context: str = Field(..., description="The context in which the task should be performed.")
    system_message: str = Field(..., description="The system message guiding the worker's behavior.")

class ReportStructure(BaseModel):
    report: str = Field(..., description="A comprehensive markdown-formatted summary of the executed task. Must include: [STATUS], [ACTIONS TAKEN], and [FINAL RESULT/DATA]. ")
