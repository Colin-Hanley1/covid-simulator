from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import csv
import random

try:
    # Remove StatusDisplayAgent from imports
    from .agent import PersonAgent, WorkplaceMarkerAgent, HomeMarkerAgent
except ImportError:
    from agent import PersonAgent, WorkplaceMarkerAgent, HomeMarkerAgent # StatusDisplayAgent removed


class InfectionModel(Model):
    def __init__(self, width=50, height=50,
                 max_days=150, infection_rate=0.05, masking_rate=0.1,
                 daily_vaccination_target_percentage=0.01,
                 natural_immunity_duration=180, vaccine_immunity_duration=150,
                 severity_multiplier=1.0, vaccine_escape_sus_factor=0.0,
                 vaccine_escape_trans_factor=0.0, migration_event_probability=0.05,
                 num_migrants_per_event=1, density=0.8, asymptomatic_rate=0.35,
                 asymptomatic_infectiousness_modifier=0.5, mask_effect_both=0.2,
                 mask_effect_one=0.5, vaccine_transmission_reduction_infector=0.4,
                 vaccine_susceptibility_reduction_susceptible=0.3,
                 vaccine_mortality_reduction=0.1,
                 vaccine_transmission_reduction_infector_waned=0.7,
                 vaccine_susceptibility_reduction_susceptible_waned=0.6,
                 vaccine_mortality_reduction_waned=0.4, essential_worker_rate=0.3,
                 lockdown_infection_threshold_percentage=0.1
                 ):

        super().__init__()
        self.width = width; self.height = height
        self.grid = MultiGrid(self.width, self.height, torus=True)
        self.schedule = RandomActivation(self)
        
        self.person_agent_next_id = 0
        self.workplace_marker_next_id = -1 
        self.home_marker_next_id = -10000 
        # self.status_display_agent_id = -20000 # REMOVED

        self.cumulative_deaths = 0 

        self.infection_rate = infection_rate
        self.masking_rate = masking_rate
        self.daily_vaccination_target_percentage = daily_vaccination_target_percentage
        self.natural_immunity_duration = natural_immunity_duration
        self.vaccine_immunity_duration = vaccine_immunity_duration
        self.severity_multiplier = severity_multiplier
        self.vaccine_escape_sus_factor = vaccine_escape_sus_factor
        self.vaccine_escape_trans_factor = vaccine_escape_trans_factor
        self.migration_event_probability = migration_event_probability
        self.num_migrants_per_event = num_migrants_per_event
        self.asymptomatic_rate = asymptomatic_rate
        self.asymptomatic_infectiousness_modifier = asymptomatic_infectiousness_modifier
        self.mask_effect_both = mask_effect_both
        self.mask_effect_one = mask_effect_one
        self.vaccine_transmission_reduction_infector = vaccine_transmission_reduction_infector
        self.vaccine_susceptibility_reduction_susceptible = vaccine_susceptibility_reduction_susceptible
        self.vaccine_mortality_reduction = vaccine_mortality_reduction
        self.vaccine_transmission_reduction_infector_waned = vaccine_transmission_reduction_infector_waned
        self.vaccine_susceptibility_reduction_susceptible_waned = vaccine_susceptibility_reduction_susceptible_waned
        self.vaccine_mortality_reduction_waned = vaccine_mortality_reduction_waned
        self.essential_worker_rate = essential_worker_rate
        self.num_workplaces = max(1, int(self.width * self.height * 0.01))

        self.lockdown_infection_threshold_percentage = lockdown_infection_threshold_percentage
        self.lockdown_active = False
        self.lockdown_duration_days = 14 
        self.lockdown_end_day = -1 

        self.max_days = max_days
        self.day = 0
        self.running = True

        self.csv_filename = "simulation_log_no_status_text.csv" 
        with open(self.csv_filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Day", "Susceptible", "Infected", "Recovered", "Dead",
                             "Vaccinated (Any)", "Vaccine Effective", "Asymptomatic", "LockdownActive"])

        self.workplaces = [] 
        attempts = 0
        actual_num_workplaces = min(self.num_workplaces, self.width * self.height)
        if actual_num_workplaces > 0:
            while len(self.workplaces) < actual_num_workplaces and attempts < self.width * self.height * 2:
                x_work, y_work = self.random.randrange(self.width), self.random.randrange(self.height)
                if (x_work, y_work) not in self.workplaces: self.workplaces.append((x_work, y_work))
                attempts += 1
        if not self.workplaces and actual_num_workplaces > 0:
            self.workplaces.append((self.random.randrange(self.width), self.random.randrange(self.height)))
        for i, wp_pos in enumerate(self.workplaces):
            marker = WorkplaceMarkerAgent(self.workplace_marker_next_id - i, self)
            self.grid.place_agent(marker, wp_pos)

        self.home_locations = [] 
        total_cells = self.width * self.height
        num_person_agents_to_create = int(total_cells * density)
        person_agents_created_count = 0
        all_possible_cells = [(x,y) for x in range(self.width) for y in range(self.height)]
        self.random.shuffle(all_possible_cells)
        home_cell_candidate_index = 0
        while person_agents_created_count < num_person_agents_to_create and home_cell_candidate_index < len(all_possible_cells):
            current_home_pos = all_possible_cells[home_cell_candidate_index]; home_cell_candidate_index += 1
            if current_home_pos not in self.home_locations: self.home_locations.append(current_home_pos)
            else: continue 
            household_size = self.random.randint(2, 6)
            if person_agents_created_count + household_size > num_person_agents_to_create:
                household_size = num_person_agents_to_create - person_agents_created_count
            if household_size <= 0: break
            for _ in range(household_size):
                if person_agents_created_count >= num_person_agents_to_create: break 
                agent = PersonAgent(self.person_agent_next_id, self); self.person_agent_next_id += 1
                agent.home_pos = current_home_pos; agent.assign_work_location() 
                if self.random.random() < 0.02:
                     agent.state = "Infected"; agent.asymptomatic = self.random.random() < self.asymptomatic_rate
                agent.masked = self.random.random() < self.masking_rate
                self.grid.place_agent(agent, current_home_pos); self.schedule.add(agent)
                person_agents_created_count += 1
        if person_agents_created_count == 0 and num_person_agents_to_create > 0:
            print(f"Warning: Could not create any PersonAgents. Check density ({density}).")
        for i, home_pos_coord in enumerate(self.home_locations):
            home_marker = HomeMarkerAgent(self.home_marker_next_id - i, self)
            self.grid.place_agent(home_marker, home_pos_coord)

        # REMOVED: StatusDisplayAgent creation and placement
        # status_agent = StatusDisplayAgent(self.status_display_agent_id, self)
        # status_agent_pos = (0, self.height -1) 
        # self.grid.place_agent(status_agent, status_agent_pos)
        # self.schedule.add(status_agent)

        self.datacollector = DataCollector(
            model_reporters={
                "Susceptible": lambda m: m.count_state("Susceptible"),
                "Infected": lambda m: m.count_state("Infected"),
                "Recovered": lambda m: m.count_state("Recovered"),
                "Dead": lambda m: m.count_state("Dead"), 
                "Vaccinated (Any)": lambda m: self.count_vaccinated(),
                "Vaccine Effective": lambda m: self.count_vaccine_effective(),
                "Asymptomatic": lambda m: self.count_asymptomatic(),
                "LockdownActive": lambda m: 1 if m.lockdown_active else 0
            }
        )
        self.datacollector.collect(self)

    def count_state(self, state_name):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent) and agent.state == state_name)
    def count_vaccinated(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent) and agent.vaccinated)
    def count_vaccine_effective(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent) and agent.vaccinated and not agent.vaccine_waned)
    def count_asymptomatic(self):
        return sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent) and agent.state == "Infected" and agent.asymptomatic)

    def perform_daily_vaccination(self):
        if self.daily_vaccination_target_percentage <= 0: return
        eligible_candidates = [
            agent for agent in self.schedule.agents
            if isinstance(agent, PersonAgent) and \
               agent.state == "Susceptible" and not agent.vaccinated
        ]
        if not eligible_candidates: return
        self.random.shuffle(eligible_candidates)
        num_person_agents = sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent))
        if num_person_agents == 0: return
        num_to_target_today = int(num_person_agents * self.daily_vaccination_target_percentage)
        actually_vaccinated_this_step = 0
        for agent in eligible_candidates:
            if actually_vaccinated_this_step >= num_to_target_today: break
            agent.vaccinated = True; agent.vaccine_waned = False; agent.days_since_vaccination = 0
            actually_vaccinated_this_step += 1

    def introduce_migrants(self):
        for _ in range(self.num_migrants_per_event):
            migrant_agent = PersonAgent(self.person_agent_next_id, self); self.person_agent_next_id += 1
            migrant_agent.state = "Infected"
            migrant_agent.asymptomatic = self.random.random() < self.asymptomatic_rate; migrant_agent.days_infected = 0
            migrant_agent.masked = False; migrant_agent.vaccinated = False
            x, y = self.random.randrange(self.grid.width), self.random.randrange(self.grid.height)
            migrant_agent.home_pos = (x,y); self.grid.place_agent(migrant_agent, (x,y))
            migrant_agent.assign_work_location(); self.schedule.add(migrant_agent)

    def write_csv_log(self):
        with open(self.csv_filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                self.day, self.count_state("Susceptible"), self.count_state("Infected"),
                self.count_state("Recovered"), self.count_state("Dead"), 
                self.count_vaccinated(), self.count_vaccine_effective(),
                self.count_asymptomatic(), 1 if self.lockdown_active else 0
            ])

    def step(self):
        num_person_agents = sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent))
        if num_person_agents > 0:
            current_infected_percentage = self.count_state("Infected") / num_person_agents
            if not self.lockdown_active and current_infected_percentage >= self.lockdown_infection_threshold_percentage:
                self.lockdown_active = True
                self.lockdown_end_day = self.day + self.lockdown_duration_days
                print(f"Day {self.day}: LOCKDOWN INITIATED. Ends on day {self.lockdown_end_day}. Infected: {current_infected_percentage*100:.2f}%")
        
        if self.lockdown_active and self.day >= self.lockdown_end_day:
            self.lockdown_active = False
            self.lockdown_end_day = -1 
            print(f"Day {self.day}: LOCKDOWN ENDED.")

        if self.random.random() < self.migration_event_probability: self.introduce_migrants()
        self.perform_daily_vaccination()
        
        self.schedule.step() # PersonAgents will step. StatusDisplayAgent was removed from schedule.

        self.datacollector.collect(self)
        self.write_csv_log()

        self.day += 1

        infected_person_agents = sum(1 for agent in self.schedule.agents if isinstance(agent, PersonAgent) and agent.state == "Infected")
        if infected_person_agents == 0 and self.day > 10: self.running = False
        if self.day >= self.max_days: self.running = False