# Advanced Agent-Based Model for Simulating COVID-19 Spread

## 1. Overview

This project implements an agent-based model (ABM) to simulate the spread of a COVID-19-like infectious disease. It features a population structured into households, with agents exhibiting dynamic, more "humanlike" behaviors in response to the simulated pandemic. Developed using the Mesa Python library, the model allows for the exploration of various epidemiological scenarios by adjusting parameters related to disease characteristics, public health interventions (dynamic masking, ongoing daily vaccination), immunity dynamics (natural and vaccine-induced waning), agent decision-making (risk perception, compliance, willingness), lockdown mechanisms, and external infection pressures (migration).

The simulation visualizes individual agents on a 2D grid, their interactions within homes, workplaces, and the community, and the resulting spread of the disease. It provides real-time charts of key epidemiological metrics and logs detailed data for further analysis.

## 2. Features

* **Agent-Based Simulation:** Models individual agents with distinct attributes and adaptive behaviors.
* **Household Structure:** Agents are grouped into households (2-6 agents per home), significantly influencing local transmission dynamics.
* **Workplace Dynamics:** "Essential" workers commute to shared workplaces, facilitating broader mixing.
* **Disease States:** Agents transition through Susceptible, Infected, Recovered, and Dead states. Dead agents remain on the grid.
* **Age Heterogeneity:** Agents have diverse ages based on a realistic distribution, influencing mortality and work eligibility.
* **Dynamic "Humanlike" Behaviors:**
    * **Perceived Risk:** Agents assess local infection risk based on nearby infected individuals.
    * **Dynamic Mask-Wearing:** Mask usage is decided each step based on perceived risk, lockdown status, individual propensities, and simple social influence.
    * **Voluntary Mobility Reduction:** Essential workers may choose to self-isolate based on high perceived risk.
    * **Variable Lockdown Compliance:** Agents have individual propensities to comply with lockdown movement restrictions.
    * **Willingness-Based Vaccine Uptake:** Daily vaccination success depends on agents' individual willingness to vaccinate.
* **Transmission Model:** Probabilistic infection based on proximity, dynamic masking, vaccination status (including waning and escape factors), and asymptomatic carriers.
* **Interventions:**
    * **Daily Vaccination:** Ongoing vaccination of a target percentage of the eligible population, considering agent willingness.
* **Immunity Dynamics:**
    * Temporary natural immunity after recovery, subject to waning.
    * Vaccine-induced immunity with a waning period to a less effective state.
* **Lockdown Mechanism:**
    * Triggered when a specified percentage of the population becomes infected.
    * Restricts movement for non-essential workers (and essential workers under 15, unless non-compliant) for a fixed duration (14 days).
* **Migration:** Introduces new infected individuals into the simulation at a specified rate.
* **Visualization:**
    * 2D grid display: Homes (blue outline), workplaces (red outline), and `PersonAgent`s. Agent color indicates health state; text color indicates vaccination status.
    * Real-time charts: Tracks Susceptible, Infected, Recovered, Dead, Vaccinated (Any), Vaccine Effective, Asymptomatic, Lockdown Active, and Average Masked agents.
* **Data Logging:** Detailed per-step data saved to a CSV file for offline analysis.

## 3. Directory Structure

* `agent.py`: Defines `PersonAgent`, `WorkplaceMarkerAgent`, and `HomeMarkerAgent` classes.
* `model.py`: Defines the main `InfectionModel` class.
* `server.py`: Sets up the Mesa `ModularServer` for web-based visualization.
* `run.py`

## 4. Requirements

* Python 3.7+
* Mesa (Agent-Based Modeling library): `pip install mesa`

## 5. Setup and Installation

1.  **Ensure Git is installed** (if cloning).
2.  **Clone the Repository or Download Files:** Place `agent.py`, `model.py`, and `server.py` in the same project directory.
3.  **Install Python.**
4.  **Install Mesa:**
    ```bash
    pip install mesa
    ```

## 6. Running the Simulation

1.  **Navigate to Project Directory:**
    ```bash
    cd path/to/your/project_directory
    ```
2.  **Run Mesa Server:**
    ```bash
    python3 run.py
    ```
3.  **Access Visualization:** Open your web browser to `http://127.0.0.1:8521/` (or `http://localhost:8521/`).
4.  **Interact:** Adjust parameters, click "Reset" to apply, then "Start" to run.

## 7. Model Parameters (User Interface)

The following parameters can be adjusted via sliders or inputs in the web interface. These settings are passed to the `InfectionModel` when the simulation is reset.

**General Simulation Settings:**
* `Agent Density`: (Slider: 0.1 to 0.9, step 0.05) Controls the proportion of grid cells initially used to seed households, effectively determining the total number of agents. Higher density means more agents.
* `Max Sim Days`: (Slider: 50 to 365, step 10) The maximum number of days (steps) the simulation will run.

**Disease Characteristics (Single Disease Type):**
* `Disease: Infection Rate`: (Slider: 0.01 to 0.3, step 0.01) The fundamental base probability of transmission per contact between an infectious and a susceptible agent, before other modifiers (masking, vaccination, etc.) are applied.
* `Disease: Severity Multiplier (Fatality)`: (Slider: 0.5 to 3.0, step 0.1) A factor that multiplies the baseline age-specific mortality rates. >1.0 increases severity, <1.0 decreases it.
* `Disease: Vax Escape (Susceptibility)`: (Slider: 0.0 to 1.0, step 0.05) The degree (0 = no escape, 1 = full escape) to which the disease evades vaccine-induced protection against becoming infected.
* `Disease: Vax Escape (Transmission)`: (Slider: 0.0 to 1.0, step 0.05) The degree to which the disease evades a vaccine's ability to reduce onward transmission from an infected vaccinated individual.

**Behavioral Parameters:**
* **Masking Behavior:**
    * `Avg. Mask Propensity (Normal)`: (Slider: 0.0 to 1.0, step 0.05) The average base probability for an agent to wear a mask when no lockdown is active and perceived risk is below the threshold. Individual agents vary around this mean.
    * `Avg. Mask Propensity (Lockdown)`: (Slider: 0.0 to 1.0, step 0.05) The average base probability for an agent to wear a mask when a lockdown *is* active.
    * `Masking Risk Threshold (Local Risk > X)`: (Slider: 0.0 to 1.0, step 0.05) If an agent's perceived local risk (fraction of infected neighbors) exceeds this threshold, their likelihood of masking increases.
    * `Risk Perception Radius (cells)`: (NumberInput: 1 to N, step 1) The Moore neighborhood radius an agent uses to assess local infection risk.
* **Voluntary Isolation Behavior (for Essential Workers):**
    * `Avg. Prop. Voluntary Isolation (Essential, High Risk)`: (Slider: 0.0 to 1.0, step 0.05) The average base probability an essential worker will choose to stay home (act isolated) if their perceived local risk is high (above threshold) and no lockdown is active.
    * `Voluntary Isolation Risk Threshold (Local Risk > X)`: (Slider: 0.1 to 1.0, step 0.05) The perceived local risk level above which essential workers consider voluntary isolation.
* **Lockdown Compliance:**
    * `Avg. Lockdown Compliance Propensity`: (Slider: 0.0 to 1.0, step 0.05) The average probability that an agent (subject to lockdown rules) will comply with stay-at-home orders. Higher means more compliance.
* **Vaccine Willingness:**
    * `Avg. Vaccine Willingness`: (Slider: 0.0 to 1.0, step 0.05) The average base probability that an eligible (susceptible, unvaccinated) agent will accept a vaccine when offered through the daily vaccination process.

**Interventions:**
* `Daily Vax Target (% of total pop)`: (Slider: 0.0 to 0.05, step 0.001) The target percentage of the *current total agent population* to be newly vaccinated each day from the eligible pool, subject to agent willingness.

**Immunity Dynamics:**
* `Natural Immunity Duration (days)`: (Slider: 60 to 360, step 10) How long immunity from prior infection lasts before an agent becomes susceptible again.
* `Vaccine Immunity Duration (days to wane)`: (Slider: 60 to 300, step 10) How long primary vaccine protection is considered fully effective before its effectiveness reduces (status `vaccine_waned` becomes `True`).

**Lockdown Mechanism:**
* `Lockdown Threshold (% Infected)`: (Slider: 0.01 to 0.5, step 0.01) The percentage of the current `PersonAgent` population that, if infected, triggers a 14-day lockdown.

**External Factors:**
* `Migration Event Prob/Day`: (Slider: 0.0 to 0.5, step 0.01) The daily probability of a migration event occurring, introducing new infected individuals.
* `Num. Infected Migrants per Event`: (NumberInput: 1 to N) The number of new infected individuals introduced if a migration event occurs.

**Fixed (Internal) Parameters:**
(These are set in `model.py` and not directly via UI sliders in this version)
* Age distribution probabilities.
* Base age-specific mortality rates.
* Recovery duration (14 days).
* Proportion of infections that are asymptomatic (`asymptomatic_rate`).
* Reduction in infectiousness for asymptomatic carriers (`asymptomatic_infectiousness_modifier`).
* Effectiveness of masks when one or both are worn (`mask_effect_one`, `mask_effect_both`).
* Base vaccine effectiveness values (for non-waned and waned states, against susceptibility, transmission, and mortality).
* Proportion of working-age population considered "essential" (`essential_worker_rate`).
* Number of workplaces (derived from grid size).
* Lockdown duration (fixed at 14 days).

## 9. Output

**9.1. Visualizations**
* **Grid Display:** Homes (blue outline), Workplaces (red outline), Person Agents (circles colored by health state: Blue-S, Red-I, Green-R, Black-D; stroke color by vax status: Yellow-VaxEffective, Orange-VaxWaned). Agent's age is shown as text.
* **Charts:** Time-series plots for Susceptible, Infected, Recovered, Dead (current count), Vaccinated (Any), Vaccine Effective, Asymptomatic, LockdownActive (0 or 1), and AvgMasked (proportion of agents masked).

**9.2. CSV Log File**
* A CSV file (e.g., `simulation_log.csv`) is generated, logging the same metrics as the chart for each simulation day.

## 10. Core Model Mechanics (Summary)

* **Agents (`PersonAgent`):** Individuals with age, household, work status, and dynamic behavioral propensities.
* **Environment:** A 2D grid with households and workplaces influencing contact patterns.
* **Perception-Decision-Action Cycle:** Each step, agents perceive local risk, make decisions about masking and mobility (considering lockdown, compliance, voluntary isolation), then act (move, potentially transmit/contract disease, update health state).
* **Disease Progression & Transmission:** Standard SIRD-like model with local transmission modified by behaviors and immunity.
* **Interventions:** Daily vaccination campaign (uptake subject to willingness) and rule-based lockdowns.
* **Immunity:** Waning natural and vaccine-induced immunity.
* **Migration:** Stochastic introduction of external infections.

## 11. Assumptions and Simplifications

* **Behavioral Model:** While dynamic, agent decisions are based on simplified rules, thresholds, and randomized propensities. Does not implement full cognitive models (e.g., Theory of Planned Behavior). Perceived risk is primarily local. Social influence is basic.
* **Static Propensities:** Individual base propensities for behaviors are set at initialization and do not evolve (though actions change with context). No intervention fatigue modeled on these base propensities yet.
* **Household & Workplace Structure:** Fixed household size range; static compositions. Workplaces are generic.
* **Other:** Fixed recovery period; no explicit incubation; binary asymptomatic status; single disease type.

