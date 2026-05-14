





 # System Description: 
Schroniska dla zwierząt mierzą się z wyzwaniem zapewnienia stałej, adekwatnej opieki
dużej liczby podopiecznych mając jednocześnie mocno ograniczone zasoby ludzkie jak i
finansowe. Ośrodki te realizują cykliczne, powtarzalne czynności, które bezpośrednio
wpływają na dobrostan zwierząt. Do wspomnianych czynności zaliczamy na przykład:● karmienie zwierząt● sprzątanie pomieszczeń● szczepienie zwierząt● wyprowadzanie zwierząt● przyjęcia zwierząt● adopcje zwierzątWyzwanie polega na jednoczesnym zapewnieniu wysokiej jakości opieki codziennej oraz
płynnym prowadzeniu przyjęć/adopcji, przy ograniczonej liczbie lub umiejętności opiekunów,
lub wolontariuszy, niestabilnej dostępności i wielu zależnościach.

## Functional Requirements:

* Rejestr zwierząt - system zapewnia prowadzenie cyfrowej ewidencji zwierząt z możliwością dodawania, edycji oraz śledzenia stanów zdrowia, statusów (np. "nakarmiony", "na spacerze") i historii zdarzeń.
   * Rejestr pracowników i ról - system zapewnia możliwość zarządzania kontami i rolami pracowników (opiekun, sprzątacz, weterynarz) wraz z przypisaniem kompetencji, limitów i preferencji.
   * Dostępność personelu - system umożliwia zgłaszanie i aktualizowanie slotów dostępności przez pracowników.
   * Generowanie zadań opieki - system automatycznie generuje zadania takie jak karmienie, spacery, szczepienie czy sprzątanie (cyklicznie lub na żądanie).
  * Automatyczny przydział zadań - system zapewnia automatyczne dopasowanie zadań do dostępnych pracowników na podstawie ich kompetencji, preferencji i aktualnego obciążenia.
   * Monitorowanie cyklu życia zadania - system umożliwia śledzenie pełnego cyklu życia zadania oraz potwierdzanie wykonania przez pracowników.
   * Kalendarz szczepień - system automatycznie planuje i monitoruje okna szczepień oraz generuje odpowiednie zadania dla personelu.
   * Sprzątanie pomieszczeń - system automatycznie generuje zadania sprzątania dziennego i na żądanie na podstawie stanu pomieszczeń.
   * Przyjęcia zwierząt - system zapewnia proces rejestracji nowych zwierząt, przeprowadzenie badań wstępnych oraz włączenie ich do harmonogramu opieki.
   * Priorytetyzacja zadań - system automatycznie rozróżnia zadania krytyczne od rutynowych i dynamicznie aktualizuje priorytety w zależności od sytuacji.
   * Sprawiedliwa rotacja opieki - system zapewnia mechanizm równomiernego rozdziału zadań między zwierzęta i opiekunów, dbając o sprawiedliwą rotację.
   * Obsługa nagłych zdarzeń - system zapewnia natychmiastową rekonfigurację planu w przypadku nagłych zdarzeń, takich jak przyjęcie nowego zwierzęcia lub nieobecność wolontariusza.
   * Wsparcie procesu adopcyjnego - system prowadzi proces adopcji, od złożenia wniosku po finalizację adopcji.


Genereted by gemini-3.1-flash-lite-preview

# GAIA ANALYSIS

## Roles:

```json
    "roles": [
    {
        "name": "Podopieczni",
        "description": "Zarządza danymi o stanie zdrowia, historii medycznej oraz statusie bytowym zwierząt w schronisku.",
        "activities": [
            "AktualizacjaStatusuZdrowotnego",
            "RejestracjaZwierzęcia",
            "WeryfikacjaTerminówSzczepień"
        ],
        "protocols": [
            "RejestracjaZdarzeńMedycznych"
        ],
        "permissions": {
            "read": [
                "HistoriaMedyczna",
                "StatusBytowy"
            ],
            "write": [
                "StatusBytowy",
                "HistoriaMedyczna"
            ],
            "consume": [],
            "produce": [
                "ZdarzenieMedyczne"
            ]
        },
        "responsibilities": {
            "liveness": "(AktualizacjaStatusuZdrowotnego | RejestracjaZwierzęcia | WeryfikacjaTerminówSzczepień)^ω",
            "safety": [
                "Każde zwierzę musi mieć przypisany unikalny identyfikator",
                "Status zdrowotny musi być zawsze spójny z historią medyczną"
            ]
        }
    },
    {
        "name": "Personel",
        "description": "Zarządza dostępnością, kompetencjami oraz realizacją zadań przez pracowników schroniska (Opiekun, Weterynarz).",
        "activities": [
            "AktualizacjaDostępności",
            "PotwierdzenieWykonaniaZadania",
            "PrzeglądPrzypisanychZadań"
        ],
        "protocols": [
            "PrzydziałZadańOpiekuńczych"
        ],
        "permissions": {
            "read": [
                "DostępnośćPracownika",
                "Kompetencje"
            ],
            "write": [
                "DostępnośćPracownika",
                "StatusZadania"
            ],
            "consume": [],
            "produce": [
                "PotwierdzenieWykonania"
            ]
        },
        "responsibilities": {
            "liveness": "(AktualizacjaDostępności || PotwierdzenieWykonaniaZadania || PrzeglądPrzypisanychZadań)^ω",
            "safety": [
                "Pracownik nie może otrzymać zadania bez wymaganych kompetencji",
                "Suma obciążenia pracownika nie może przekraczać limitu godzin"
            ]
        }
    },
    {
        "name": "Zadania",
        "description": "Koordynuje cykl życia zadań opiekuńczych, priorytetyzację oraz przydział do personelu.",
        "activities": [
            "GenerowanieZadań",
            "PriorytetyzacjaZadań",
            "PrzydzielanieZadańDoPersonelu",
            "MonitorowanieTerminów"
        ],
        "protocols": [
            "PrzydziałZadańOpiekuńczych",
            "MonitorowanieStanówPomieszczeń",
            "RejestracjaZdarzeńMedycznych"
        ],
        "permissions": {
            "read": [
                "ListaZadań",
                "Priorytety"
            ],
            "write": [
                "StatusZadania",
                "PriorytetZadania"
            ],
            "consume": [
                "ZadanieZakończone"
            ],
            "produce": [
                "NoweZadanie"
            ]
        },
        "responsibilities": {
            "liveness": "(GenerowanieZadań | PriorytetyzacjaZadań | PrzydzielanieZadańDoPersonelu | MonitorowanieTerminów)^ω",
            "safety": [
                "Zadania krytyczne muszą mieć wyższy priorytet niż rutynowe",
                "Każde zadanie musi mieć przypisanego wykonawcę lub status oczekujący"
            ]
        }
    },
    {
        "name": "Pomieszczenia",
        "description": "Monitoruje stan czystości pomieszczeń i zarządza lokalizacją zwierząt.",
        "activities": [
            "RaportowanieStanu",
            "AktualizacjaLokalizacjiZwierząt"
        ],
        "protocols": [
            "MonitorowanieStanówPomieszczeń"
        ],
        "permissions": {
            "read": [
                "StanCzystości",
                "LokalizacjaZwierząt"
            ],
            "write": [
                "StanCzystości"
            ],
            "consume": [],
            "produce": [
                "AlertCzystości"
            ]
        },
        "responsibilities": {
            "liveness": "(RaportowanieStanu | AktualizacjaLokalizacjiZwierząt)^ω",
            "safety": [
                "Pomieszczenie nie może być przeludnione",
                "Stan czystości musi być aktualizowany po każdym sprzątaniu"
            ]
        }
    }
]

```
# Interactions:
```json
   {
    "interactions": [
        {
            "goal": "PrzydziałZadańOpiekuńczych",
            "initiator": "Zadania",
            "responder": "Personel",
            "inputs": [
                "TaskPriority",
                "RequiredSkill"
            ],
            "outputs": [
                "EmployeeID",
                "ShiftAvailability"
            ],
            "processing_description": "Zadania przetwarza wymagania kompetencyjne -> wysyła do Personelu; Personel przetwarza dostępność -> wysyła identyfikator pracownika."
        },
        {
            "goal": "MonitorowanieStanówPomieszczeń",
            "initiator": "Pomieszczenia",
            "responder": "Zadania",
            "inputs": [
                "RoomID",
                "SanitationStatus"
            ],
            "outputs": [
                "TaskID",
                "UrgencyLevel"
            ],
            "processing_description": "Pomieszczenia przetwarza stan czystości -> wysyła do Zadania; Zadania przetwarza priorytet -> wysyła identyfikator zadania."
        },
        {
            "goal": "RejestracjaZdarzeńMedycznych",
            "initiator": "Podopieczni",
            "responder": "Zadania",
            "inputs": [
                "AnimalID",
                "VaccinationDate"
            ],
            "outputs": [
                "TaskID",
                "TaskDeadline"
            ],
            "processing_description": "Podopieczni przetwarza termin szczepienia -> wysyła do Zadania; Zadania przetwarza harmonogram -> wysyła identyfikator zadania."
        }
    ]
}
```
# GAIA DESIGN 

## Agents:
```json
{
    "agent_types": [
        {
            "name": "AnimalRegistryAgent",
            "aggregated_roles": [
                "Podopieczni"
            ],
            "cardinality": "1"
        },
        {
            "name": "StaffManagementAgent",
            "aggregated_roles": [
                "Personel"
            ],
            "cardinality": "1..+"
        },
        {
            "name": "TaskCoordinatorAgent",
            "aggregated_roles": [
                "Zadania"
            ],
            "cardinality": "1..+"
        },
        {
            "name": "FacilityManagementAgent",
            "aggregated_roles": [
                "Pomieszczenia"
            ],
            "cardinality": "1"
        }
    ]
}
```
# Services:
```json
    {
    "services": [
        {
            "name": "UpdateHealthStatus",
            "provided_by": "AnimalRegistryAgent",
            "derived_from": "AktualizacjaStatusuZdrowotnego",
            "inputs": [
                "AnimalID",
                "HealthData"
            ],
            "outputs": [
                "StatusUpdateConfirmation"
            ],
            "pre_condition": "AnimalExists(AnimalID)",
            "post_condition": "HealthStatusConsistentWithHistory(AnimalID)"
        },
        {
            "name": "RegisterAnimal",
            "provided_by": "AnimalRegistryAgent",
            "derived_from": "RejestracjaZwierzęcia",
            "inputs": [
                "AnimalDetails"
            ],
            "outputs": [
                "AnimalID"
            ],
            "pre_condition": "true",
            "post_condition": "AnimalHasUniqueID(AnimalID)"
        },
        {
            "name": "VerifyVaccinationSchedule",
            "provided_by": "AnimalRegistryAgent",
            "derived_from": "WeryfikacjaTerminówSzczepień",
            "inputs": [
                "AnimalID"
            ],
            "outputs": [
                "VaccinationDate"
            ],
            "pre_condition": "true",
            "post_condition": "VaccinationDateVerified(AnimalID) AND HealthStatusConsistentWithHistory(AnimalID)"
        },
        {
            "name": "InitiateMedicalEvent",
            "provided_by": "AnimalRegistryAgent",
            "derived_from": "RejestracjaZdarzeńMedycznych",
            "inputs": [
                "AnimalID",
                "VaccinationDate"
            ],
            "outputs": [
                "TaskID",
                "TaskDeadline"
            ],
            "pre_condition": "AnimalExists(AnimalID)",
            "post_condition": "MedicalEventTaskCreated(TaskID)"
        },
        {
            "name": "ProcessMedicalEvent",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "RejestracjaZdarzeńMedycznych",
            "inputs": [
                "TaskID",
                "TaskDeadline"
            ],
            "outputs": [
                "TaskStatus"
            ],
            "pre_condition": "TaskID != NULL",
            "post_condition": "TaskRegisteredInSystem(TaskID)"
        },
        {
            "name": "UpdateAvailability",
            "provided_by": "StaffManagementAgent",
            "derived_from": "AktualizacjaDostępności",
            "inputs": [
                "EmployeeID",
                "NewAvailability"
            ],
            "outputs": [
                "UpdateStatus"
            ],
            "pre_condition": "true",
            "post_condition": "AvailabilityUpdated(EmployeeID)"
        },
        {
            "name": "ConfirmTaskCompletion",
            "provided_by": "StaffManagementAgent",
            "derived_from": "PotwierdzenieWykonaniaZadania",
            "inputs": [
                "TaskID",
                "EmployeeID"
            ],
            "outputs": [
                "ConfirmationStatus"
            ],
            "pre_condition": "TaskAssignedTo(TaskID, EmployeeID)",
            "post_condition": "TaskStatus(TaskID) == 'Completed'"
        },
        {
            "name": "ReviewAssignedTasks",
            "provided_by": "StaffManagementAgent",
            "derived_from": "PrzeglądPrzypisanychZadań",
            "inputs": [
                "EmployeeID"
            ],
            "outputs": [
                "TaskList"
            ],
            "pre_condition": "true",
            "post_condition": "true"
        },
        {
            "name": "AssignCareTask",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "PrzydziałZadańOpiekuńczych",
            "inputs": [
                "TaskPriority",
                "RequiredSkill",
                "TaskID"
            ],
            "outputs": [
                "EmployeeID",
                "ShiftAvailability"
            ],
            "pre_condition": "TaskExists(TaskID) AND EmployeeAvailable(EmployeeID)",
            "post_condition": "TaskAssignedTo(TaskID, EmployeeID)"
        },
        {
            "name": "ReceiveSanitationAlert",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "MonitorowanieStanówPomieszczeń",
            "inputs": [
                "RoomID",
                "UrgencyLevel"
            ],
            "outputs": [
                "TaskID"
            ],
            "pre_condition": "RoomID != NULL",
            "post_condition": "TaskCreatedForRoom(RoomID)"
        },
        {
            "name": "GenerateTasks",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "GenerowanieZadań",
            "inputs": [
                "TriggerEvent"
            ],
            "outputs": [
                "NewTaskID"
            ],
            "pre_condition": "true",
            "post_condition": "TaskCreated(NewTaskID)"
        },
        {
            "name": "PrioritizeTasks",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "PriorytetyzacjaZadań",
            "inputs": [
                "TaskList"
            ],
            "outputs": [
                "PrioritizedList"
            ],
            "pre_condition": "true",
            "post_condition": "CriticalTasksHaveHigherPriority()"
        },
        {
            "name": "MonitorDeadlines",
            "provided_by": "TaskCoordinatorAgent",
            "derived_from": "MonitorowanieTerminów",
            "inputs": [
                "TaskID"
            ],
            "outputs": [
                "DeadlineStatus"
            ],
            "pre_condition": "TaskExists(TaskID)",
            "post_condition": "true"
        },
        {
            "name": "ReportSanitationStatus",
            "provided_by": "FacilityManagementAgent",
            "derived_from": "MonitorowanieStanówPomieszczeń",
            "inputs": [
                "RoomID",
                "SanitationStatus"
            ],
            "outputs": [
                "TaskID",
                "UrgencyLevel"
            ],
            "pre_condition": "true",
            "post_condition": "SanitationStatusUpdated(RoomID)"
        },
        {
            "name": "UpdateAnimalLocation",
            "provided_by": "FacilityManagementAgent",
            "derived_from": "AktualizacjaLokalizacjiZwierząt",
            "inputs": [
                "AnimalID",
                "RoomID"
            ],
            "outputs": [
                "UpdateConfirmation"
            ],
            "pre_condition": "RoomNotOvercrowded(RoomID)",
            "post_condition": "AnimalLocationUpdated(AnimalID, RoomID)"
        }
    ]
}
```
# Acquaintances:
```json
    {
    "acquaintances": [
        {
            "sender": "TaskCoordinatorAgent",
            "receiver": "StaffManagementAgent",
            "protocols": [
                "PrzydziałZadańOpiekuńczych"
            ]
        },
        {
            "sender": "FacilityManagementAgent",
            "receiver": "TaskCoordinatorAgent",
            "protocols": [
                "MonitorowanieStanówPomieszczeń"
            ]
        },
        {
            "sender": "AnimalRegistryAgenVt",
            "receiver": "TaskCoordinatorAgent",
            "protocols": [
                "RejestracjaZdarzeńMedycznych"
            ]
        }
    ]
}
```
    