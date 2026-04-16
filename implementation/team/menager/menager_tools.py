from implementation.common_tools import list_files
from langchain.tools import tool
from implementation.team.team_state import TaskStucture, ReportStructure
import logging
logger = logging.getLogger(__name__)

@tool(args_schema=TaskStucture)
def submit_task(task, context, system_message):
    """
    Submits a task to a worker with the given context and system message.
    """
    
    logger.info("       Submitting task to worker: %s", task)
    return "Task submitted to worker"

@tool(args_schema=ReportStructure)
def submit_final_report(report):
    """
    Call this tool ONLY when the goal is FULLY achieved and you are 100% CERTAIN of the result.
    
    CRITICAL RULE:
    If you have even a shadow of a doubt, or lack empirical evidence, DO NOT use this tool yet.
    Instead, you MUST run verification tests, diagnostics, or sanity checks to prove it works.
    Only submit the report after successful verification.
    """
    logger.info("       Submitting final report to supervisor.")
    return "Final report submitted to supervisor"

tools = [submit_task, submit_final_report, list_files]