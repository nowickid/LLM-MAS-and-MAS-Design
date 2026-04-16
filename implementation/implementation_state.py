from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

class ImplementationState(TypedDict):
    documentation: str
    messages: Annotated[list[BaseMessage], add_messages]
    sprint_goal: str
    project_context: str
    next_step: str



class UpdateChangeLogStructure(BaseModel):
    changes: str = Field(..., description="A detailed changelog of all changes made during the sprint execution in markdown format.")
    isProjectComplete: bool = Field(..., description="A boolean indicating whether the project is considered complete after the last sprint execution.")

class DelegateTaskStructure(BaseModel):
    sprint_goal: str = Field(..., description="The specific objective of this sprint/stage. It defines WHAT needs to be built in this phase.")
    project_context: str = Field(..., description="CRITICAL: Since the team has no memory, paste ALL necessary code snippets, architectural rules, interface definitions, or previous file contents required to execute this task without hallucinations.")
