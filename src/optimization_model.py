import gurobipy as gp
from src.docks_and_incidents import coverage
from visualizations.map import create_map
from pathlib import Path
import webbrowser

# Maximize the number of incidents covered by the docks
def maximize_incidents_covered(docks, incidents, dock_locations_quantity):
    model = gp.Model("maximize_incidents_covered")

    # Add variables
    x = model.addVars(docks, vtype=gp.GRB.BINARY, name="x")
    y = model.addVars(incidents, vtype=gp.GRB.BINARY, name="y")

    # Add constraints
    for i in incidents:
        model.addConstr(gp.quicksum(x[d] for d in docks if coverage(d, i)) >= y[i]) # At least one dock must cover the incident

    model.addConstr(gp.quicksum(x[d] for d in docks) <= dock_locations_quantity) # The number of docks must be less than or equal to the number of dock locations available
    
    # Add objective function
    model.setObjective(gp.quicksum(y[i] for i in incidents), gp.GRB.MAXIMIZE) # Maximize the number of incidents covered

    # Optimize the model
    model.optimize()

    # New map with the optimized docks and incidents
    selected_docks = [d for d in docks if x[d].X == 1]
    covered_incidents = [i for i in incidents if y[i].X == 1]
    create_map(selected_docks, covered_incidents, "optimized_map")
    map_file = Path(__file__).resolve().parent.parent / "output/optimized_map.html"
    if map_file.exists():
        webbrowser.open(map_file.resolve().as_uri())