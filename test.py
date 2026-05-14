from state import State
from gaia.analysis.analysis import process_analize
from gaia.design.design import process_design
import logging
from strategies.gaia_strategy import run_with_gaia
from langchain_core.runnables import RunnableConfig
import json
   
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S'
)

INPUTS_DIR = "inputs/requirements.json"
if __name__ == "__main__":
    
    with open(INPUTS_DIR, "r") as f:
        inputs = json.load(f)
        
    
    for input in inputs:
        print(input)
        print("=====================================")