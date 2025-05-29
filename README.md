# Agent-Based Model for Simulating COVID-19 Spread

## 1. Overview

This project implements an agent-based model (ABM) to simulate the spread of a COVID-19-like infectious disease through a heterogeneous population structured into households. Developed using the Mesa Python library, the model allows for the exploration of various epidemiological scenarios by adjusting parameters related to disease characteristics, public health interventions (masking, vaccination), immunity dynamics (natural and vaccine-induced waning), population behaviors, lockdown mechanisms, and external infection pressures (migration).

The simulation visualizes individual agents on a 2D grid, their interactions, and the resulting spread of the disease. It provides real-time charts of key epidemiological metrics and logs detailed data for further analysis.

## 2. Features

* **Agent-Based Simulation:** Models individual agents with distinct attributes and behaviors.
* **Household Structure:** Agents are grouped into households (2-6 agents per home), influencing local transmission.
* **Workplace Dynamics:** "Essential" workers commute to shared workplaces, facilitating broader mixing.
* **Disease States:** Agents transition through Susceptible, Infected, Recovered, and Dead states.
* **Age Heterogeneity:** Agents have different ages, influencing mortality rates and work eligibility.
* **Transmission Model:** Probabilistic infection based on proximity, masking, vaccination status, asymptomatic carriers, and vaccine escape.
* **Interventions:**
    * **Masking:** Reduces transmission probability.
    * **Daily Vaccination:** Ongoing vaccination of a target percentage of the eligible population.
* **Immunity Dynamics:**
    * Temporary natural immunity after recovery.
    * Vaccine-induced immunity with a waning period.
* **Lockdown Mechanism:**
    * Triggered when a certain percentage of the population is infected.
    * Restricts movement for non-essential workers for a fixed duration (14 days).
* **Migration:** Introduces new infected individuals into the simulation at a specified rate.
* **Visualization:**
    * 2D grid display of agents, homes (blue outline), and workplaces (red outline). Agent color indicates health state, and stroke color indicates vaccination status.
    * Real-time charts of population compartments (Susceptible, Infected, Recovered, Dead, Vaccinated, Vaccine Effective, Asymptomatic, Lockdown Active).
* **Data Logging:** Detailed per-step data saved to a CSV file.

## 3. Directory Structure

The project primarily consists of the following Python files:

* `agent.py`: Defines the agent classes (`PersonAgent`, `WorkplaceMarkerAgent`, `HomeMarkerAgent`).
* `model.py`: Defines the main `InfectionModel` class, orchestrating the simulation.
* `server.py`: Sets up the Mesa `ModularServer` for web-based visualization and user interaction.
* `run.py`

## 4. Requirements

* Python 3.7+
* Mesa (Agent-Based Modeling library): `pip install mesa`
* (Other standard Python libraries like `csv`, `random` are typically included with Python)

## 5. Setup and Installation

1.  **Clone the Repository (if applicable) or Download Files:**
    Ensure you have the `agent.py`, `model.py`, and `server.py` files in the same project directory.

2.  **Install Python:**
    If you don't have Python installed, download it from [python.org](https://www.python.org/).

3.  **Install Mesa:**
    Open your terminal or command prompt and run:
    ```bash
    pip install mesa
    ```

## 6. Running the Simulation

1.  **Navigate to the Project Directory:**
    Open your terminal or command prompt and use the `cd` command to go to the directory where you saved the project files.
    ```bash
    cd path/to/your/project_directory
    ```

2.  **Run the Mesa Server:**
    Execute the following command:
    ```bash
    python3 run.py
    ```

3.  **Access the Visualization:**
    Open your web browser and go to the address displayed in the terminal, which is usually:
    `http://127.0.0.1:8521/` or `http://localhost:8521/`

    You should see the simulation interface with the grid, charts, and parameter sliders.

4.  **Interacting with the Simulation:**
    * Adjust the parameters on the left-hand side as desired.
    * Click the "Reset" button to apply new parameter settings and restart the simulation.
    * Click the "Start" button to run the simulation. You can "Pause" and "Step" through it as well.

## 7. Model Parameters (User Interface)

The web interface provides sliders and inputs to control various aspects of the simulation. These are passed to the `InfectionModel` upon reset.

**General Simulation Settings:**
* `Max Sim Days`: The maximum number of days (steps) the simulation will run.

**Disease Design (Single Disease Type):**
* `Disease: Infection Rate`: The fundamental base probability of transmission per contact for an unvaccinated, unmasked, symptomatic individual infecting a similar susceptible individual (before any other modifiers like vaccine escape are applied).
* `Disease: Severity Multiplier (Fatality)`: A factor that multiplies the base age-specific mortality rates. (e.g., 1.0 = base rates, 1.5 = 50% higher mortality).
* `Disease: Vax Escape (Susceptibility)`: A factor (0.0 to 1.0) representing how much the disease evades vaccine protection against *getting infected*. (0.0 = no escape, 1.0 = complete escape).
* `Disease: Vax Escape (Transmission)`: A factor (0.0 to 1.0) representing how much the disease evades vaccine protection against *transmitting to others* if a vaccinated person becomes infected.

**Interventions & Behavior:**
* `Initial Masking Rate`: The proportion of the population that starts the simulation wearing masks.
* `Daily Vax Target (% of total pop)`: The target percentage of the *current total agent population* to be newly vaccinated each day from the eligible (susceptible, unvaccinated) pool.

**Immunity:**
* `Natural Immunity Duration (days)`: How long immunity gained from recovering from an infection lasts before an agent becomes susceptible again.
* `Vaccine Immunity Duration (days to wane)`: How long primary vaccine protection is considered fully effective before it "wanes" to a less effective state.

**Lockdown:**
* `Lockdown Threshold (% Infected)`: The percentage of the current `PersonAgent` population that, if infected, will trigger a 14-day lockdown.

**External Factors:**
* `Migration Event Prob/Day`: The probability (0.0 to 1.0) that a migration event occurs on any given day, introducing new infected individuals.
* `Num. Infected Migrants per Event`: The number of infected individuals that arrive if a migration event occurs.
* `Agent Density`: The proportion of grid cells that will be initially populated with households, effectively controlling the total number of agents.

**Fixed (Internal) Parameters:**
Several other parameters are set to default values within `model.py` and are not exposed as sliders in this simplified interface. These include:
* Age distribution and specific age-based mortality rates.
* Recovery duration (14 days).
* Proportion of infections that are asymptomatic (`asymptomatic_rate`).
* Reduction in infectiousness for asymptomatic carriers (`asymptomatic_infectiousness_modifier`).
* Effectiveness of masks (`mask_effect_one`, `mask_effect_both`).
* Base vaccine effectiveness against transmission, susceptibility, and mortality (for both non-waned and waned states).
* Proportion of the working-age population (<65) considered "essential" workers (`essential_worker_rate`).
* Number of workplaces (derived from grid size).
* Lockdown duration (fixed at 14 days).

To change these fixed parameters, you would need to modify their default values directly in the `InfectionModel`'s `__init__` method in `model.py`.

## 8. Output

**8.1. Visualizations**

* **Grid Display:**
    * **Home Cells:** Outlined in blue (Layer 0).
    * **Workplace Cells:** Outlined in red (Layer 1).
    * **Person Agents:** Displayed as circles (Layer 2).
        * **Color:** Indicates health state:
            * Blue: Susceptible
            * Red: Infected
            * Green: Recovered
            * Black: Dead (remain on grid)
        * **Text:** Shows the agent's age.
        * **Stroke (Outline) Color:** Indicates vaccination status:
            * Default (Light Grey): Unvaccinated.
            * Yellow: Vaccinated (protection considered effective).
            * Orange: Vaccinated (protection has waned).
* **Charts:**
    * Dynamically plots the number of agents in each key state over time: Susceptible, Infected, Recovered, Dead, Vaccinated (Any), Vaccine Effective, Asymptomatic.
    * Also plots "LockdownActive" (1 if active, 0 if not).

**8.2. CSV Log File**

* A CSV file (e.g., `simulation_log_households.csv`, name might vary based on latest version) is created in the project directory.
* It logs the counts of each population compartment and the lockdown status for every simulation step (day).
* Columns: `Day`, `Susceptible`, `Infected`, `Recovered`, `Dead`, `Vaccinated (Any)`, `Vaccine Effective`, `Asymptomatic`, `LockdownActive`.

## 9. Core Model Mechanics (Summary)

* **Agents (`PersonAgent`):** Individuals with age, health state, vaccination status, masking behavior, and mobility patterns (home, work).
* **Environment:** A 2D grid where agents live in multi-agent households and some commute to workplaces.
* **Disease Progression:** Agents transition from Susceptible to Infected upon exposure. Infected agents recover (gaining temporary immunity) or die after a fixed period.
* **Transmission:** Occurs probabilistically between infected and susceptible agents in close proximity (Moore neighborhood), influenced by masking, vaccination (including waning and escape factors), and whether the infector is asymptomatic.
* **Interventions:**
    * **Masking:** Reduces transmission probability if one or both interacting agents are masked.
    * **Vaccination:** A target percentage of eligible agents are vaccinated daily. Vaccination reduces susceptibility, onward transmission if infected, and mortality. Its effectiveness wanes over time.
* **Immunity:**
    * **Natural:** Recovered individuals are immune for a set duration.
    * **Vaccine-Induced:** Provides protection that wanes after a set duration.
* **Lockdown:** If active, restricts movement of non-essential workers (and essential workers under 15) to their homes.
* **Migration:** Periodically introduces new infected individuals from outside the simulation.

## 10. Assumptions and Simplifications

* **Household Structure:** Fixed size range (2-6); static composition.
* **Mixing:** Primarily local (Moore neighborhood), with structured mixing in shared home and workplace cells.
* **Disease:** Fixed recovery period; no explicit incubation; binary asymptomatic status.
* **Immunity:** Waning is a binary switch; single disease type (no viral mutation within the simulation).
* **Interventions:** Mask adherence is fixed after initialization; vaccination is for primary doses.
* **Movement:** Simplified home-work commute.
* **Markers:** Home and workplace markers are purely visual.

## 11. Future Development / Contributing

This model serves as a foundation. Potential areas for future development include:
* More complex contact networks (e.g., schools, social gatherings).
* Dynamic agent behaviors (e.g., changing masking habits based on perceived risk).
* Modeling of different vaccine types or booster doses.
* Reintroducing viral mutation and competing variants.
* Calibration against real-world epidemiological data.

Contributions and suggestions are welcome
