from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    generate_graphs: bool = True
    # GAIA
    generate_pdf_reports: bool = True
    use_prompt_optimization: bool = False
    analysis_prototypes_max_iterations: int = 0
    analysis_roles_max_iterations: int = 0
    design_services_max_iterations: int = 0
    design_agents_max_iterations: int = 0
    design_acquaintances_max_iterations: int = 0
    
    # IMPLEMENTATION
    docs_dir: str = "docs"
    implementation_recursion_limit: int = 50
    team_recursion_limit: int = 50
    worker_recursion_limit: int = 50
        
settings = Settings()