from mesa import Agent
import random # Added for normalvariate

class PersonAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.age = self.random.choices([5,15,25,35,45,55,65,75,85], [.117,.131,.136,.135,.124,.128,.118,.073,.039])[0]
        self.state = "Susceptible"
        self.days_infected = 0
        self.recovery_days = 14

        self.masked = False # Will be updated dynamically
        self.asymptomatic = False
        self.vaccinated = False
        self.vaccine_waned = False
        self.days_since_vaccination = 0
        self.days_since_recovery = 0

        self.home_pos = None
        self.work_pos = None
        self.mobility_type = self.assign_mobility_type()
        self.current_location_status = "at_home"

        # New behavioral attributes for more humanlike responses
        self.perceived_local_risk = 0.0 # Updated each step
        
        # Masking propensities (values between 0 and 1)
        self.base_propensity_to_mask_normal = max(0, min(1, self.random.normalvariate(self.model.avg_mask_propensity_normal, 0.2)))
        self.base_propensity_to_mask_lockdown = max(0, min(1, self.random.normalvariate(self.model.avg_mask_propensity_lockdown, 0.15)))

        # Voluntary isolation for essential workers
        self.prop_voluntary_isolation_if_risk_high = max(0, min(1, self.random.normalvariate(self.model.avg_prop_voluntary_isolation, 0.2)))
        
        # Lockdown compliance
        self.base_compliance_propensity = max(0, min(1, self.random.normalvariate(self.model.avg_lockdown_compliance, 0.15))) # Higher means more compliant

        # Vaccine willingness
        self.base_willingness_to_vaccinate = max(0, min(1, self.random.normalvariate(self.model.avg_vaccine_willingness, 0.25)))


    def assign_mobility_type(self):
        if self.age < 65:
            return "essential" if self.random.random() < self.model.essential_worker_rate else "isolated"
        else:
            return "isolated"

    def assign_work_location(self):
        if self.mobility_type == "essential" and self.model.workplaces:
            self.work_pos = self.random.choice(self.model.workplaces)
        else:
            self.work_pos = None

    def get_mortality_rate(self):
        base_rate = (
            0.00003 if self.age < 19 else 0.00014 if self.age < 29 else
            0.00039 if self.age < 39 else 0.00096 if self.age < 49 else
            0.00219 if self.age < 59 else 0.00470 if self.age < 69 else
            0.01060 if self.age < 79 else .03253
        )
        base_rate *= self.model.severity_multiplier
        if self.vaccinated:
            base_rate *= self.model.vaccine_mortality_reduction_waned if self.vaccine_waned else self.model.vaccine_mortality_reduction
        return base_rate

    def calculate_effective_transmission_prob(self, susceptible_neighbor):
        base_prob = self.model.infection_rate
        modifier = 1.0
        if self.masked and susceptible_neighbor.masked: modifier *= self.model.mask_effect_both
        elif self.masked or susceptible_neighbor.masked: modifier *= self.model.mask_effect_one
        if self.asymptomatic: modifier *= self.model.asymptomatic_infectiousness_modifier
        if self.vaccinated:
            vacc_trans_reduction_factor_base = self.model.vaccine_transmission_reduction_infector_waned if self.vaccine_waned else self.model.vaccine_transmission_reduction_infector
            base_protection_trans = (1.0 - vacc_trans_reduction_factor_base)
            effective_protection_trans = base_protection_trans * (1.0 - self.model.vaccine_escape_trans_factor)
            modifier *= (1.0 - effective_protection_trans)
        if susceptible_neighbor.vaccinated:
            vacc_sus_reduction_factor_base = self.model.vaccine_susceptibility_reduction_susceptible_waned if susceptible_neighbor.vaccine_waned else self.model.vaccine_susceptibility_reduction_susceptible
            base_protection_sus = (1.0 - vacc_sus_reduction_factor_base)
            effective_protection_sus = base_protection_sus * (1.0 - self.model.vaccine_escape_sus_factor)
            modifier *= (1.0 - effective_protection_sus)
        return max(0, min(base_prob * modifier, 1.0))

    def move_towards(self, target_pos):
        if self.pos == target_pos:
            if target_pos == self.home_pos: self.current_location_status = "at_home"
            if target_pos == self.work_pos: self.current_location_status = "at_work"
            return
        dx = target_pos[0] - self.pos[0]; dy = target_pos[1] - self.pos[1]
        new_x, new_y = self.pos[0], self.pos[1]
        if dx != 0: new_x += dx // abs(dx)
        if dy != 0: new_y += dy // abs(dy)
        self.model.grid.move_agent(self, (new_x, new_y))
        if self.pos == self.home_pos: self.current_location_status = "at_home"
        elif self.pos == self.work_pos: self.current_location_status = "at_work"

    def update_perceived_local_risk(self):
        """Updates agent's perceived risk based on infected neighbors."""
        if self.pos is None: # Agent might have been removed (e.g. if dead logic changed)
            self.perceived_local_risk = 0.0
            return

        infected_neighbors_count = 0
        neighbor_cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False, radius=self.model.risk_perception_radius)
        # Consider neighbors in neighborhood cells, not just direct cellmates for risk perception
        actual_neighbors_in_area = 0
        for cell_pos in neighbor_cells:
            cell_contents = self.model.grid.get_cell_list_contents([cell_pos])
            for agent in cell_contents:
                if isinstance(agent, PersonAgent) and agent != self: # Don't count self
                    actual_neighbors_in_area +=1
                    if agent.state == "Infected":
                        infected_neighbors_count += 1
        
        if actual_neighbors_in_area > 0:
            self.perceived_local_risk = infected_neighbors_count / actual_neighbors_in_area
        else:
            self.perceived_local_risk = 0.0
        # Simple global risk component (can be weighted)
        # global_infected_ratio = self.model.count_state("Infected") / sum(1 for _ in self.model.schedule.agents if isinstance(_, PersonAgent))
        # self.perceived_local_risk = (self.perceived_local_risk * 0.7) + (global_infected_ratio * 0.3)


    def decide_masking(self):
        """Agent decides whether to wear a mask."""
        prob_mask = self.base_propensity_to_mask_normal
        if self.model.lockdown_active:
            prob_mask = self.base_propensity_to_mask_lockdown
        
        # Influence of perceived risk
        if self.perceived_local_risk > self.model.masking_risk_threshold:
            prob_mask = min(1.0, prob_mask * 1.5 + (self.perceived_local_risk * 0.5)) # Risk perception boosts masking

        # Simple social influence: if majority of neighbors mask, more likely to mask
        if self.pos: # Check if agent is on grid
            masking_neighbors = 0
            total_neighbors = 0
            neighbor_agents = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            for neighbor in neighbor_agents:
                if isinstance(neighbor, PersonAgent):
                    total_neighbors += 1
                    if neighbor.masked:
                        masking_neighbors +=1
            if total_neighbors > 0 and (masking_neighbors / total_neighbors) > 0.5:
                prob_mask = min(1.0, prob_mask * 1.2) # Social norm effect

        self.masked = self.random.random() < prob_mask

    def get_current_vaccine_willingness(self):
        """Calculates current willingness to vaccinate, possibly modified by risk."""
        # For now, just base willingness. Can be expanded.
        # Example: willingness_modified_by_risk = self.base_willingness_to_vaccinate + (self.perceived_local_risk * 0.2)
        # return max(0, min(1, willingness_modified_by_risk))
        return self.base_willingness_to_vaccinate


    def step(self):
        if self.state == "Dead":
             return

        # --- 0. Perception Phase ---
        self.update_perceived_local_risk()

        # --- 1. Behavioral Decisions (e.g., Masking) ---
        self.decide_masking() # Agent decides if they wear a mask for this step

        # --- 2. Waning Immunity Logic & State Updates (Recovery/Death) ---
        if self.state == "Recovered":
            self.days_since_recovery += 1
            if self.days_since_recovery > self.model.natural_immunity_duration:
                self.state = "Susceptible"; self.days_since_recovery = 0
        if self.vaccinated and not self.vaccine_waned:
            self.days_since_vaccination += 1
            if self.days_since_vaccination > self.model.vaccine_immunity_duration:
                self.vaccine_waned = True

        if self.state == "Infected":
            self.days_infected += 1
            if self.days_infected >= self.recovery_days:
                if self.random.random() < self.get_mortality_rate():
                    self.state = "Dead"; self.model.cumulative_deaths += 1
                else:
                    self.state = "Recovered"; self.days_infected = 0; self.days_since_recovery = 0
        
        if self.state == "Dead": # Check again if agent just died
            return

        # --- 3. Movement Logic with Lockdown & Behavioral Considerations ---
        current_mobility = self.mobility_type
        obeys_lockdown = True # Assume compliance initially

        if self.model.lockdown_active:
            # Check compliance
            if self.random.random() > self.base_compliance_propensity:
                obeys_lockdown = False # Agent chooses not to comply this step

            if obeys_lockdown and not (self.mobility_type == "essential" and self.age > 14):
                current_mobility = "isolated" # Forced to isolate by lockdown compliance
            elif not obeys_lockdown: # Agent is not complying with lockdown
                pass # They will attempt their normal mobility_type movement
        
        # Voluntary isolation for essential workers if risk is very high (and not in a stricter lockdown)
        if not self.model.lockdown_active and current_mobility == "essential" and \
           self.perceived_local_risk > self.model.voluntary_isolation_risk_threshold:
            if self.random.random() < self.prop_voluntary_isolation_if_risk_high:
                current_mobility = "isolated"
        
        # Actual Movement
        if current_mobility == "essential" and self.work_pos and self.home_pos and self.age > 14:
            target_pos = None
            if self.current_location_status == "going_to_work" and self.pos != self.work_pos: target_pos = self.work_pos
            elif self.current_location_status == "going_to_home" and self.pos != self.home_pos: target_pos = self.home_pos
            elif self.random.random() < 0.75 : 
                if self.current_location_status == "at_home" and self.pos != self.work_pos:
                    target_pos = self.work_pos; self.current_location_status = "going_to_work"
                elif self.current_location_status == "at_work" and self.pos != self.home_pos:
                    target_pos = self.home_pos; self.current_location_status = "going_to_home"
            if target_pos: self.move_towards(target_pos)
            else:
                if self.pos == self.home_pos: self.current_location_status = "at_home"
                elif self.pos == self.work_pos: self.current_location_status = "at_work"
        # Covers "isolated" by initial type, by lockdown, or by voluntary choice
        elif current_mobility == "isolated" and self.home_pos:
            if self.pos != self.home_pos: self.move_towards(self.home_pos)
            self.current_location_status = "at_home"


        # --- 4. Infection Spreading Logic ---
        if self.state == "Infected":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False)
            for neighbor_agent in neighbors:
                if isinstance(neighbor_agent, PersonAgent) and neighbor_agent.state == "Susceptible":
                    transmission_prob = self.calculate_effective_transmission_prob(neighbor_agent)
                    if self.random.random() < transmission_prob:
                        neighbor_agent.state = "Infected"
                        neighbor_agent.asymptomatic = self.random.random() < self.model.asymptomatic_rate
                        neighbor_agent.days_infected = 0

class WorkplaceMarkerAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.agent_type = "workplace_marker"
    def step(self): pass

class HomeMarkerAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.agent_type = "home_marker"
    def step(self): pass

# StatusDisplayAgent REMOVED as per previous request
