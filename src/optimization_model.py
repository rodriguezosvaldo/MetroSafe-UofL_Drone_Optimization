import gurobipy as gp
from src.docks_and_incidents import coverage, distance
from visualizations.map_incidents_and_docks import create_map
from pathlib import Path
import webbrowser

# Base model, only two constraints:
# 1. Each incident must be covered by at least one dock
# 2. The number of docks must be less than or equal to the number of dock locations available
def _build_base_model(docks, incidents, dock_locations_quantity):
    model = gp.Model("maximize_incidents_covered")

    x = model.addVars(docks, vtype=gp.GRB.BINARY, name="x")
    y = model.addVars(incidents, vtype=gp.GRB.BINARY, name="y")

    for i in incidents:
        model.addConstr(gp.quicksum(x[d] for d in docks if coverage(d, i)) >= y[i])

    model.addConstr(gp.quicksum(x[d] for d in docks) <= dock_locations_quantity)

    return model, x, y

# Choose the docks that cover the most incidents while minimizing the total travel distance
def _minimize_travel_distance(model, optimal_coverage, docks, incidents, x, y):
    # Number of incidents covered must be at least the number of incidents covered in the optimal solution
    model.addConstr(gp.quicksum(y[i] for i in incidents) >= optimal_coverage) # We have to maintain the incidents covered in the optimal solution while making other optimizations

    # If two docks cover the same number of incidents, choose the one with the minimum total travel distance
    coverable_pairs = [(d, i) for d in docks for i in incidents if coverage(d, i)] # All possible pairs of docks and incidents with coverage TRUE
    z = model.addVars(coverable_pairs, vtype=gp.GRB.BINARY, name="z") # 1 if the dock covers the incident, 0 otherwise

    for d, i in coverable_pairs:
        model.addConstr(z[d, i] <= x[d]) # Assign only one dock to each incident
        model.addConstr(z[d, i] <= y[i]) # The incident must be covered if the dock is selected

    for i in incidents:
        model.addConstr(gp.quicksum(z[d, i] for d in docks if coverage(d, i)) == y[i])

    model.setObjective(
        gp.quicksum(distance(d, i) * z[d, i] for d, i in coverable_pairs),
        gp.GRB.MINIMIZE,
    )
    model.optimize()

# Maximize incidents covered
def maximize_incidents_covered(docks, incidents, dock_locations_quantity):
    model, x, y = _build_base_model(docks, incidents, dock_locations_quantity)

    #==========================================================================================================
    # Maximize the number of incidents covered
    model.setObjective(gp.quicksum(y[i] for i in incidents), gp.GRB.MAXIMIZE)
    model.optimize()
    #==========================================================================================================

    # Check if the optimization is the optimal solution
    # if model.Status != gp.GRB.OPTIMAL:
    #     print(f"Optimization ended with status {model.Status}")
    #     return

    optimal_coverage = model.ObjVal # The number of incidents covered in the optimal solution
    _minimize_travel_distance(model, optimal_coverage, docks, incidents, x, y)


    # Create the map
    selected_docks = [d for d in docks if x[d].X > 0.5]
    covered_incidents = [i for i in incidents if y[i].X > 0.5]
    create_map(selected_docks, covered_incidents, "optimized_map", all_incidents=incidents)
    map_file = Path(__file__).resolve().parent.parent / "output/optimized_map.html"
    if map_file.exists():
        webbrowser.open(map_file.resolve().as_uri())