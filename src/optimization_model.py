import gurobipy as gp
from src.docks_and_incidents import coverage, distance
from visualizations.map_incidents_and_docks import create_map
from pathlib import Path
import webbrowser

_MAX_DOCK_COVERAGE_CAPACITY = 1000
_MIP_GAP = 0.01 # 1% gap between the best solution found and the optimal solution
_TIME_LIMIT_SECONDS = 300 # 300 seconds = 5 minutes time limit for the solver

def _configure_solver(model):
    model.Params.MIPGap = _MIP_GAP 
    model.Params.TimeLimit = _TIME_LIMIT_SECONDS

def _precompute_coverage(docks, incidents):
    incident_to_docks = {i: [] for i in incidents} # List of docks that cover the incident
    dock_to_incidents = {d: [] for d in docks} # List of incidents that are covered by the dock
    dock_distance_sum = {d: 0.0 for d in docks} # Sum of the distances between the dock and the incidents it covers

    for d in docks:
        for i in incidents:
            if coverage(d, i):
                incident_to_docks[i].append(d)
                dock_to_incidents[d].append(i)
                dock_distance_sum[d] += distance(d, i)
    return incident_to_docks, dock_to_incidents, dock_distance_sum

def _coverage_weight(dock_distance_sum, dock_locations_quantity):
    max_tiebreak = max(dock_distance_sum.values(), default=0) * dock_locations_quantity
    return max_tiebreak + 1

def _build_base_model(docks, incidents, dock_locations_quantity, incident_to_docks, dock_to_incidents):
    model = gp.Model("maximize_incidents_covered")
    _configure_solver(model)

    x = model.addVars(docks, vtype=gp.GRB.BINARY, name="x")
    y = model.addVars(incidents, vtype=gp.GRB.BINARY, name="y")

    for i in incidents:
        covering_docks = incident_to_docks[i]
        if covering_docks:
            model.addConstr(gp.quicksum(x[d] for d in covering_docks) >= y[i]) # Each incident must be covered by at least one dock
        else:
            model.addConstr(y[i] == 0) # If an incident is not covered by any dock, it must be set to 0

    for d in docks:
        coverable_incidents = dock_to_incidents[d]
        if coverable_incidents:
            model.addConstr(gp.quicksum(y[i] for i in coverable_incidents) <= _MAX_DOCK_COVERAGE_CAPACITY) # The number of incidents covered by a dock must be less than or equal to the maximum number of incidents a dock can cover

    model.addConstr(gp.quicksum(x[d] for d in docks) <= dock_locations_quantity) # The number of docks must be less than or equal to the number of dock locations available
    model.addConstr(gp.quicksum(y[i] for i in incidents) <= dock_locations_quantity * _MAX_DOCK_COVERAGE_CAPACITY) # Redundant constraint to ensure the number of incidents covered is less than or equal to the number of dock locations available multiplied by the maximum number of incidents a dock can cover
    return model, x, y

def maximize_incidents_covered(docks, incidents, dock_locations_quantity):
    incident_to_docks, dock_to_incidents, dock_distance_sum = _precompute_coverage(docks, incidents)
    model, x, y = _build_base_model(docks, incidents, dock_locations_quantity, incident_to_docks, dock_to_incidents)

    coverage_weight = _coverage_weight(dock_distance_sum, dock_locations_quantity)
    # Objective function: Maximize the number of incidents covered
    model.setObjective(
        coverage_weight * gp.quicksum(y[i] for i in incidents) - gp.quicksum(dock_distance_sum[d] * x[d] for d in docks), # Maximize the number of incidents covered minus the total travel distance to covered incidents
        gp.GRB.MAXIMIZE,
    )
    model.optimize()

    if model.Status not in (gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SUBOPTIMAL):
        print(f"Coverage optimization ended with status {model.Status}")
        return


    selected_docks = [d for d in docks if x[d].X > 0.5]
    covered_incidents = [i for i in incidents if y[i].X > 0.5]
    print(f"Incidents covered: {len(covered_incidents)}")
    print(f"Selected docks: {len(selected_docks)}")
    create_map(selected_docks, covered_incidents, "optimized_map", all_incidents=incidents)
    map_file = Path(__file__).resolve().parent.parent / "output/optimized_map.html"
    if map_file.exists():
        webbrowser.open(map_file.resolve().as_uri())


