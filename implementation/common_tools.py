from pathlib import Path
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool
def list_files(path:str = "", config: RunnableConfig = None):
    """Returns a list of all files in the specified directory and its subdirectories,
    excluding files in ignored directories like node_modules, __pycache__ ..."""
    logger.info(f"      Listing files in path: '{path}'")
    configurable = config.get("metadata", {})
    workspace_root = Path(configurable.get("workspace_dir", ".")).resolve()
    root_dir = Path(workspace_root).resolve()
    target_dir = (root_dir / path).resolve()

    if not target_dir.is_relative_to(root_dir):
        return f"Error: Unauthorized access to path '{path}'."

    if not target_dir.exists():
        return f"Error: The specified path '{path}' does not exist."
    IGNORED_FOLDERS = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".idea", ".vscode"}

    files = []
    for f in target_dir.rglob("*"):
        if f.is_file():
            rel_path = f.relative_to(root_dir)
            path_parts = set(rel_path.parts)
            
            if not path_parts.intersection(IGNORED_FOLDERS):
                files.append(str(rel_path))
    
    return "\n".join(files) if files else "No files found."


@tool
def write_to_file(filename: str, content: str, config: RunnableConfig = None):
    """Writes the given content to a file with the specified filename in the workspace directory."""
    logger.info(f"      Writing to file: '{filename}'")
    configurable = config.get("metadata", {})
    workspace_root = Path(configurable.get("workspace_dir", ".")).resolve()
    root_dir = Path(workspace_root).resolve()
    target_file = (root_dir / filename).resolve()

    if not target_file.is_relative_to(root_dir):
        return f"Error: Unauthorized access to path '{filename}'."

    target_file.parent.mkdir(parents=True, exist_ok=True)

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Successfully wrote to file '{filename}'."

@tool
def read_file(filename: str, config: RunnableConfig = None):
    """Reads and returns the content of the specified file from the workspace directory."""
    logger.info(f"      Reading file: '{filename}'")
    configurable = config.get("metadata", {})
    workspace_root = Path(configurable.get("workspace_dir", ".")).resolve()
    root_dir = Path(workspace_root).resolve()
    target_file = (root_dir / filename).resolve()

    if not target_file.is_relative_to(root_dir):
        return f"Error: Unauthorized access to path '{filename}'."

    if not target_file.exists():
        return f"Error: The specified file '{filename}' does not exist."

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    return content
