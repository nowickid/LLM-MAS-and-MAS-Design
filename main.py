from state import State
from gaia.analysis.analysis import process_analize
from gaia.design.design import process_design
import logging
from strategies.gaia_strategy import run_with_gaia
from langchain_core.runnables import RunnableConfig
   
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S'
)
if __name__ == "__main__":
    state = State(
        
        description=("""
            Schroniska dla zwierząt mierzą się z wyzwaniem zapewnienia stałej, adekwatnej opieki
            dużej liczby podopiecznych mając jednocześnie mocno ograniczone zasoby ludzkie jak i
            finansowe. Ośrodki te realizują cykliczne, powtarzalne czynności, które bezpośrednio
            wpływają na dobrostan zwierząt. Do wspomnianych czynności zaliczamy na przykład:● karmienie zwierząt● sprzątanie pomieszczeń● szczepienie zwierząt● wyprowadzanie zwierząt● przyjęcia zwierząt● adopcje zwierzątWyzwanie polega na jednoczesnym zapewnieniu wysokiej jakości opieki codziennej oraz
            płynnym prowadzeniu przyjęć/adopcji, przy ograniczonej liczbie lub umiejętności opiekunów,
            lub wolontariuszy, niestabilnej dostępności i wielu zależnościach.
        """
            
        ),
            functional_requirements = [
        "Prowadzenie cyfrowej ewidencji zwierząt i śledzenie ich stanów zdrowia",
        "Zarządzanie kontami, rolami oraz kompetencjami pracowników",
        "Zgłaszanie i aktualizowanie slotów dostępności przez personel",
        "Automatyczne generowanie cyklicznych zadań opieki (karmienie, spacery, szczepienia)",
        "Automatyczny przydział zadań na podstawie kompetencji, preferencji i obciążenia",
        "Monitorowanie pełnego cyklu życia zadania i potwierdzanie wykonania",
        "Automatyczne planowanie kalendarza szczepień i generowanie zadań medycznych",
        "Generowanie zadań sprzątania na podstawie bieżącego stanu pomieszczeń",
        "Rejestracja nowych zwierząt wraz z badaniem wstępnym i harmonogramem opieki",
        "Dynamiczna priorytetyzacja i rozróżnianie zadań krytycznych od rutynowych",
        "Zapewnienie mechanizmu sprawiedliwej i równomiernej rotacji zadań",
        "Natychmiastowa rekonfiguracja planu w przypadku nagłych zdarzeń i nieobecności",
        "Kompleksowe wsparcie procesu adopcyjnego od wniosku do finalizacji"
    ]

    )
    
    config = RunnableConfig(
     
    {
        "configurable": 
        {
            "workspace_dir": "./implementation_workspace",
            "docs_dir": "./docs",
            "documentation_pdf": "./test.pdf"
        }
    }
    )
    result = run_with_gaia(state, config=config)
    

