from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    generate_graphs: bool = True
    # GAIA
    generate_pdf_reports: bool = True
    use_prompt_optimization: bool = False
    analysis_prototypes_max_iterations: int =   4
    analysis_roles_max_iterations: int =        4
    design_services_max_iterations: int =       4
    design_agents_max_iterations: int =         4
    design_acquaintances_max_iterations: int =  4
    
    # IMPLEMENTATION
    implementation_recursion_limit: int = 50
    team_recursion_limit: int = 150
    worker_recursion_limit: int = 150
        
settings = Settings()