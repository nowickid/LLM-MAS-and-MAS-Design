from pathlib import Path
from langchain_core.runnables.graph_mermaid import draw_mermaid_png
from langchain_core.runnables.graph import CurveStyle, NodeStyles
GRAPHS_DIR = "graphs"

def save_graph_visualization(graph, filename):
    try:
        mermaid = get_pretty_mermaid(graph)
        mermaid_syntax_horizontal = mermaid.replace("graph TD", "graph LR")
        png = draw_mermaid_png(mermaid_syntax_horizontal)
        filepath = Path(GRAPHS_DIR) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(png)
    except Exception as e:
        print(f"An unexpected exception occurred: {e}")
        print(f"Exception occurred while saving graph visualization. {filename} not saved.")
        
        
        
def get_pretty_mermaid(graph):

    styles = NodeStyles(
        first="fill:#2ecc71", # Zielony dla START
        last="fill:#e74c3c",  # Czerwony dla END
        default="fill:#f4f4f4,line-height:1.2" # Reszta (np. szary)
    )
    return graph.draw_mermaid(
        curve_style=CurveStyle.LINEAR, 
        
        node_colors=styles,        
        frontmatter_config={
            "config": {
                "flowchart": {
                    "rankSpacing": 50,    
                    "nodeSpacing": 40,   
                    "defaultRenderer": "dagre"
                }
            }
        }
    )