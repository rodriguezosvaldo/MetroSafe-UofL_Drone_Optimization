import gurobipy as gp
from docks_and_incidents import coverage, coverage_toy_example

# test_incidents = [Incident(1, 1, 1), Incident(2, 2, 2), Incident(3, 3, 3), Incident(4, 4, 4), Incident(5, 5, 5), Incident(6, 6, 6)]
# test_docks = [Dock('A', 1, 1, 1, 1), Dock('B', 2, 2, 2, 2), Dock('C', 3, 3, 3, 3)]

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


    # Results for toy example
    print(f"Number of incidents covered: {model.ObjVal}")

    for d in docks:
        print(f"x[{d.name}] = {x[d].X}")

    for i in incidents:
        print(f"y[{i.incident_id}] = {y[i].X}")

    