from state import State
import logging
from strategies.gaia_strategy import run_with_gaia
from strategies.non_gaia_strategy import run_without_gaia
from strategies.prepared_gaia_strategy import run_with_prepared_gaia
from langchain_core.runnables import RunnableConfig
import json
from tokens_stats import tokens_counter
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S'
)

INPUTS_DIR = "inputs/requirements.json"

def prepare_config_for_gaia(id, title):
    return RunnableConfig({
        "configurable": 
        {
            "workspace_dir": f"evaluation/{id}/gaia/implementation_workspace",
            "docs_dir": f"evaluation/{id}/gaia/docs",
            "documentation_pdf": f"evaluation/{id}/gaia/{title}test.pdf"
        }})
def prepare_config_for_non_gaia(id, title):
    return RunnableConfig({
        "configurable": 
        {
            "workspace_dir": f"evaluation/{id}/non_gaia/implementation_workspace",
            "docs_dir": f"evaluation/{id}/non_gaia/docs",
        }})

def prepare_config_for_prepared_gaia(id, title, gaia_artifacts):
    return RunnableConfig({
        "configurable": 
        {
            "workspace_dir": f"evaluation/{id}/prepared_gaia/implementation_workspace",
            "docs_dir": f"evaluation/{id}/prepared_gaia/docs",
            "documentation_pdf": f"evaluation/{id}/prepared_gaia/{title}test.pdf",
            "gaia_artifacts": gaia_artifacts
        }})
    
def create_evaluation_directories(id):
    os.makedirs(f"evaluation/{id}/gaia/implementation_workspace", exist_ok=True)
    os.makedirs(f"evaluation/{id}/gaia/docs", exist_ok=True)
    os.makedirs(f"evaluation/{id}/non_gaia/implementation_workspace", exist_ok=True)
    os.makedirs(f"evaluation/{id}/non_gaia/docs", exist_ok=True)
    os.makedirs(f"evaluation/{id}/prepared_gaia/implementation_workspace", exist_ok=True)
    os.makedirs(f"evaluation/{id}/prepared_gaia/docs", exist_ok=True)
    
def save_tokens_stats(id, strategy):
    tokens_counter.save(f"evaluation/{id}/{strategy}/tokens_stats.json")
    tokens_counter.reset()
    
    

if __name__ == "__main__":
    exclude_ids = ["2", "3"] 
    with open(INPUTS_DIR, "r") as f:
        inputs = json.load(f)
        
    
    for input in inputs:
        if input["id"] in exclude_ids:
            continue
        create_evaluation_directories(input["id"])
        state = State(
            description=input["description"],
            functional_requirements=input["requirements"]
        )
        config = prepare_config_for_gaia(input["id"], input["title"])
        result = run_with_gaia(state, config=config)
        save_tokens_stats(input["id"], "gaia")
        
        config = prepare_config_for_non_gaia(input["id"], input["title"])
        result = run_without_gaia(state, config=config)
        save_tokens_stats(input["id"], "non_gaia")
        
        config = prepare_config_for_prepared_gaia(input["id"], input["title"], input["gaia_artifacts"])
        result = run_with_prepared_gaia(state, config=config)
        save_tokens_stats(input["id"], "prepared_gaia")        

