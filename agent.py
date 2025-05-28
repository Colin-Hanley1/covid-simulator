from mesa import Agent

class PersonAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.age = self.random.choices([5,15,25,35,45,55,65,75,85], [.117,.131,.136,.135,.124,.128,.118,.073,.039])[0]
        self.state = "Susceptible"
        self.days_infected = 0
        self.recovery_days = 14

        self.masked = False
        self.asymptomatic = False
        self.vaccinated = False
        self.vaccine_waned = False
        self.days_since_vaccination = 0
        self.days_since_recovery = 0

        self.home_pos = None
        self.work_pos = None
        self.mobility_type = self.assign_mobility_type()
        self.current_location_status = "at_home"

    def assign_mobility_type(self):
        # Assigns mobility type based on age and the model's essential worker rate.
        if self.age < 65:
            return "essential" if self.random.random() < self.model.essential_worker_rate else "isolated"
        else:
            return "isolated" # Older agents are more likely to be isolated

    def assign_work_location(self):
        # Assigns a workplace if the agent is essential and workplaces exist.
        if self.mobility_type == "essential" and self.model.workplaces:
            self.work_pos = self.random.choice(self.model.workplaces)
        else:
            self.work_pos = None

    def get_mortality_rate(self):
        # Calculates age-specific mortality rate, modified by disease severity and vaccination.
        base_rate = (
            0.00003 if self.age < 19 else
            0.00014 if self.age < 29 else
            0.00039 if self.age < 39 else
            0.00096 if self.age < 49 else
            0.00219 if self.age < 59 else
            0.00470 if self.age < 69 else
            0.01060 if self.age < 79 else
            .03253 # For 79+
        )
        base_rate *= self.model.severity_multiplier
        if self.vaccinated:
            base_rate *= self.model.vaccine_mortality_reduction_waned if self.vaccine_waned else self.model.vaccine_mortality_reduction
        return base_rate

    def calculate_effective_transmission_prob(self, susceptible_neighbor):
        # Calculates the probability of transmitting the disease to a susceptible neighbor.
        # Considers base infection rate, masking, infector's status (asymptomatic, vaccinated),
        # and susceptible's vaccination status, including vaccine escape.
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
        # Moves the agent one step towards a target position.
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

    def step(self):
        # Main step logic for the agent.
        if self.state == "Dead":
             return # Dead agents do nothing

        # Waning immunity logic
        if self.state == "Recovered":
            self.days_since_recovery += 1
            if self.days_since_recovery > self.model.natural_immunity_duration:
                self.state = "Susceptible"; self.days_since_recovery = 0
        if self.vaccinated and not self.vaccine_waned:
            self.days_since_vaccination += 1
            if self.days_since_vaccination > self.model.vaccine_immunity_duration:
                self.vaccine_waned = True

        # Infection progression and outcome
        if self.state == "Infected":
            self.days_infected += 1
            if self.days_infected >= self.recovery_days:
                if self.random.random() < self.get_mortality_rate():
                    self.state = "Dead"
                    self.model.cumulative_deaths += 1
                else:
                    self.state = "Recovered"; self.days_infected = 0; self.days_since_recovery = 0
        
        if self.state == "Dead": # Check again if agent just died
            return

        # --- Movement Logic with Lockdown Consideration ---
        can_move_freely = True # Assume free movement initially
        if self.model.lockdown_active:
            if not (self.mobility_type == "essential" and self.age > 14):
                can_move_freely = False # Restricted by lockdown

        if can_move_freely:
            # Normal movement for essential workers (if not restricted by lockdown)
            if self.mobility_type == "essential" and self.work_pos and self.home_pos and self.age > 14:
                target_pos = None
                if self.current_location_status == "going_to_work" and self.pos != self.work_pos: target_pos = self.work_pos
                elif self.current_location_status == "going_to_home" and self.pos != self.home_pos: target_pos = self.home_pos
                elif self.random.random() < 0.75 : # Chance to initiate move
                    if self.current_location_status == "at_home" and self.pos != self.work_pos:
                        target_pos = self.work_pos; self.current_location_status = "going_to_work"
                    elif self.current_location_status == "at_work" and self.pos != self.home_pos:
                        target_pos = self.home_pos; self.current_location_status = "going_to_home"
                if target_pos: self.move_towards(target_pos)
                else: # Ensure status is correct if not moving
                    if self.pos == self.home_pos: self.current_location_status = "at_home"
                    elif self.pos == self.work_pos: self.current_location_status = "at_work"
            # Normal movement for isolated (which is to stay home or return home if displaced)
            elif self.mobility_type == "isolated" and self.home_pos:
                if self.pos != self.home_pos: self.move_towards(self.home_pos)
                self.current_location_status = "at_home"
        else: # Movement restricted by lockdown (agent is not essential or too young)
            if self.home_pos and self.pos != self.home_pos:
                self.move_towards(self.home_pos) # Return home
            self.current_location_status = "at_home"


        # --- Infection Spreading Logic --- (Not reached if Dead)
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
    """A non-acting agent to visually mark workplace cells."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.agent_type = "workplace_marker"

    def step(self):
        pass # This agent does nothing each step, it's purely visual

class HomeMarkerAgent(Agent):
    """A non-acting agent to visually mark home cells."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.agent_type = "home_marker"

    def step(self):
        pass # This agent does nothing each step, it's purely visual


