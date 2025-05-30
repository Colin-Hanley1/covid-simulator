from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider, NumberInput, Choice

try:
    # Assuming model.py is in the same directory or a submodule
    from .model import InfectionModel
except ImportError:
    from model import InfectionModel

def agent_portrayal(agent):
    """
    Defines how each agent will be drawn on the grid.
    Handles PersonAgents, HomeMarkerAgents, and WorkplaceMarkerAgents differently.
    """
    if agent is None:
        return

    agent_type = getattr(agent, 'agent_type', None) # Get agent_type if it exists

    # --- Portrayal for HomeMarkerAgent ---
    if agent_type == "home_marker":
        return {
            "Shape": "rect",
            "w": 1,  # Fill the cell width
            "h": 1,  # Fill the cell height
            "Filled": "true", # Mesa canvas often expects string "true"
            "Color": "rgba(0, 0, 255, 0.05)",  # Very faint, mostly transparent blue fill
            "stroke_color": "#0000FF",         # Bright blue outline
            "Layer": 0,                        # Draw home markers on layer 0 (bottom)
        }
    # --- Portrayal for WorkplaceMarkerAgent ---
    elif agent_type == "workplace_marker":
        return {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Filled": "true",
            "Color": "rgba(255, 0, 0, 0.05)",  # Very faint, mostly transparent red fill
            "stroke_color": "#FF0000",         # Bright red outline
            "Layer": 1,                        # Draw workplace markers on layer 1 (above homes)
        }

    # --- Portrayal for PersonAgent (default if not a marker) ---
    # This assumes if agent_type is None or not a known marker type, it's a PersonAgent.
    portrayal = {
        "Shape": "circle",
        "r": 0.8,
        "Filled": "true",
        "Layer": 2,       # Draw PersonAgents on layer 2 (on top of markers)
        "Color": "gray",  # Default color
        "stroke_color": "#BDBDBD", # Default subtle stroke for all PersonAgents
        "text": str(getattr(agent, 'age', '')), # Display agent's age
        "text_color": "lightgray" # Default text color
    }

    # Set color based on infection state for PersonAgents
    agent_state = getattr(agent, 'state', 'Dead') # Default to Dead if state is somehow missing
    portrayal["Color"] = {
        "Susceptible": "blue",
        "Infected": "red",
        "Recovered": "green",
        "Dead": "black"
    }.get(agent_state, "gray") # Use gray if state is unknown (should not happen)

    # Set text color based on infection state for better visibility
    portrayal["text_color"] = "white" if agent_state != "Dead" else "lightgray"
    
    # Visual cue for vaccination status using stroke color
    if getattr(agent, 'vaccinated', False):
        portrayal["text_color"] = "#FFFF00"  # Bright yellow stroke for vaccinated agents
        if getattr(agent, 'vaccine_waned', False):
            portrayal["text_color"] = "#FFA500" # Orange stroke for waned vaccine
    
    # Optional: Add a visual cue for masking if desired
    # if getattr(agent, 'masked', False):
    #     portrayal["r"] = 0.6 # Example: make masked agents slightly smaller
    #     # Or add another small shape, e.g., a dot of a specific color
        
    return portrayal


# Define grid and canvas dimensions
NEW_GRID_WIDTH = 50
NEW_GRID_HEIGHT = 50
CANVAS_PIXEL_WIDTH = 750  # Adjust as needed for your screen space
CANVAS_PIXEL_HEIGHT = 750 # Adjust as needed for your screen space

grid = CanvasGrid(agent_portrayal, NEW_GRID_WIDTH, NEW_GRID_HEIGHT, CANVAS_PIXEL_WIDTH, CANVAS_PIXEL_HEIGHT)

# Define the chart for visualizing model-level data
chart = ChartModule([
    {"Label": "Susceptible", "Color": "blue"},
    {"Label": "Infected", "Color": "red"},
    {"Label": "Recovered", "Color": "green"},
    {"Label": "Dead", "Color": "black"}, # Shows current number of agents in "Dead" state
    {"Label": "Vaccinated (Any)", "Color": "orange"}, # Total ever vaccinated
    {"Label": "Vaccine Effective", "Color": "darkorange"}, # Vaccinated and not waned
    {"Label": "Asymptomatic", "Color": "purple"}
], data_collector_name='datacollector') # Ensure this matches the DataCollector instance name in model.py

# Define the model parameters that will be adjustable via the server UI
model_params = {
    # Grid and Population Density
    "width": NEW_GRID_WIDTH, # Fixed width for this server instance
    "height": NEW_GRID_HEIGHT, # Fixed height for this server instance
    "density": Slider("Agent Density", 0.8, 0.1, 0.9, 0.05), # Controls total initial agent count

    # Simulation Control
    "max_days": Slider("Max Sim Days", 10, 365, 730, 5),
    
    # Core Disease Characteristics (Single Disease Type)
    "infection_rate": Slider("Infectivity", 0.05, 0.01, 0.95, 0.01),
    "severity_multiplier": Slider("Virulence Multiplier", 1.0, 0.5, 10.0, 0.1),
    "vaccine_escape_sus_factor": Slider("Disease: Vax Escape (Susceptibility)", 0.0, 0.0, 1.0, 0.05),
    "vaccine_escape_trans_factor": Slider("Disease: Vax Escape (Transmission)", 0.0, 0.0, 1.0, 0.05),
    
    # Interventions & Behavior (Dynamic Masking - these control base propensities)
    "avg_mask_propensity_normal": Slider("Avg. Mask Propensity (Normal)", 0.3, 0.0, 1.0, 0.05),
    "avg_mask_propensity_lockdown": Slider("Avg. Mask Propensity (Lockdown)", 0.8, 0.0, 1.0, 0.05),
    "masking_risk_threshold": Slider("Masking Risk Threshold (Local Risk > X)", 0.1, 0.0, 1.0, 0.05),
    "risk_perception_radius": NumberInput("Risk Perception Radius (cells)", value=1), # Ensure NumberInput args are compatible

    # Vaccination Behavior
    "daily_vaccination_target_percentage": Slider("Daily Vaccination (% of total pop)", 0.01, 0.0, 0.05, 0.001),
    "avg_vaccine_willingness": Slider("Avg. Vaccine Willingness", 0.7, 0.0, 1.0, 0.05),
    
    # Immunity Dynamics
    "natural_immunity_duration": Slider("Natural Immunity Duration (days)", 180, 60, 360, 10),
    "vaccine_immunity_duration": Slider("Vaccine Immunity Duration (days)", 150, 60, 300, 10),
    
    # Lockdown Mechanism
    "lockdown_infection_threshold_percentage": Slider("Lockdown Threshold (% Infected)", 0.10, 0.01, 0.5, 0.01),
    "avg_lockdown_compliance": Slider("Avg. Lockdown Compliance", 0.9, 0.0, 1.0, 0.05),

    # Voluntary Behavior Changes
    "avg_prop_voluntary_isolation": Slider("Avg. Prop. Voluntary Isolation (Essential, High Risk)", 0.25, 0.0, 1.0, 0.05),
    "voluntary_isolation_risk_threshold": Slider("Voluntary Isolation Risk Threshold (Local Risk > X)", 0.5, 0.1, 1.0, 0.05),
    
    # External Factors
    "migration_event_probability": Slider("Migration Event Prob/Day", 0.05, 0.0, 0.5, 0.01),
    "num_migrants_per_event": NumberInput("Num. Infected Migrants per Event", value=1), # Ensure NumberInput args are compatible
}

# Create and run the server
server = ModularServer(
    InfectionModel,
    [grid, chart],
    "COVID-19 Simulation with Dynamic Behaviors", # Updated server title
    model_params
)