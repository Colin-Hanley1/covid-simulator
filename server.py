from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import Slider, NumberInput, Choice

try:
    from .model import InfectionModel
except ImportError:
    from model import InfectionModel

def agent_portrayal(agent):
    if agent is None:
        return

    agent_type = getattr(agent, 'agent_type', None)

    # REMOVED: Portrayal for StatusDisplayAgent
    # if agent_type == "status_display":
    #     return { ... } 
    
    if agent_type == "home_marker":
        return {
            "Shape": "rect", "w": 1, "h": 1, "Filled": "true",
            "Color": "rgba(0, 0, 255, 0.05)", "stroke_color": "#0000FF", "Layer": 0,
        }
    elif agent_type == "workplace_marker":
        return {
            "Shape": "rect", "w": 1, "h": 1, "Filled": "true",
            "Color": "rgba(255, 0, 0, 0.05)", "stroke_color": "#FF0000", "Layer": 1,
        }

    # --- Portrayal for PersonAgent (default) ---
    # This assumes if agent_type is not a marker, it's a PersonAgent or similar
    portrayal = {
        "Shape": "circle", "r": 0.8, "Filled": "true", "Layer": 2, 
        "Color": "gray", "stroke_color": "#BDBDBD", 
        "text": str(getattr(agent, 'age', '')), "text_color": "lightgray"
    }
    agent_state = getattr(agent, 'state', 'Dead') # Default to Dead if state somehow missing
    portrayal["Color"] = {
        "Susceptible": "blue", "Infected": "red",
        "Recovered": "green", "Dead": "black"
    }.get(agent_state, "gray")
    portrayal["text_color"] = "white" if agent_state != "Dead" else "lightgray"
    if getattr(agent, 'vaccinated', False):
        portrayal["stroke_color"] = "#FFFF00" 
        if getattr(agent, 'vaccine_waned', False):
            portrayal["stroke_color"] = "#FFA500"
    return portrayal


NEW_GRID_WIDTH = 50
NEW_GRID_HEIGHT = 50
CANVAS_PIXEL_WIDTH = 750
CANVAS_PIXEL_HEIGHT = 750

grid = CanvasGrid(agent_portrayal, NEW_GRID_WIDTH, NEW_GRID_HEIGHT, CANVAS_PIXEL_WIDTH, CANVAS_PIXEL_HEIGHT)

chart = ChartModule([
    {"Label": "Susceptible", "Color": "blue"}, {"Label": "Infected", "Color": "red"},
    {"Label": "Recovered", "Color": "green"}, {"Label": "Dead", "Color": "black"},
    {"Label": "Vaccinated (Any)", "Color": "orange"}, {"Label": "Vaccine Effective", "Color": "darkorange"},
    {"Label": "Asymptomatic", "Color": "purple"}
], data_collector_name='datacollector')

model_params = {
    "width": NEW_GRID_WIDTH, "height": NEW_GRID_HEIGHT,
    "max_days": Slider("Max Sim Days", 365, 10, 730, 5),
    "infection_rate": Slider("Infectivity", 0.05, 0.01, 0.5, 0.01),
    "severity_multiplier": Slider("Virulence Multiplier", 1.0, 0.1, 10.0, 0.1),
    "masking_rate": Slider("Initial Masking Rate", 0.0, 0.0, 1.0, 0.05),
    "daily_vaccination_target_percentage": Slider("Daily Vaccination Rate", 0.00, 0.0, 0.1, 0.001),
    "natural_immunity_duration": Slider("Natural Immunity Duration (days)", 180, 0, 360, 10),
    "vaccine_immunity_duration": Slider("Vaccine Immunity Duration (days)", 180, 0, 360, 10),
    "lockdown_infection_threshold_percentage": Slider("Lockdown Threshold (1 = No Lockdown)", 0.10, 0.01, 1, 0.01),
    "migration_event_probability": Slider("Migration Event Prob/Day", 0.05, 0.0, 0.5, 0.01),
    "num_migrants_per_event": NumberInput("Num. Infected Migrants per Event", value=1),
    "density": Slider("Population Density", 0.8, 0.1, 0.9, 0.05)
}

server = ModularServer(
    InfectionModel,
    [grid, chart],
    "COVID-19 Simulation", # Updated title
    model_params
)