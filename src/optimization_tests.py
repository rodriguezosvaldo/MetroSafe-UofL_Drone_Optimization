from src.optimization_model import maximize_incidents_covered

def no_fixed_locations(docks, incidents, k_max):
    k_range = {
        "k_min": 8,
        "k_max": k_max,
    }
    results = []
    for k in range(k_range["k_min"], k_range["k_max"]):
        print(f"Running optimization test for k = {k}...")
        r = maximize_incidents_covered(docks, incidents, k)
        if r is None:
            continue

        # Calculate delta coverage and break if it is 0
        if results:
            r["delta_coverage"] = r["incidents_covered"] - results[-1]["incidents_covered"]
            if r["delta_coverage"] == 0:
                results.append(r)
                break
        else:
            r["delta_coverage"] = 0
        
        results.append(r)
        
    return results

def fixed_locations(docks, incidents, k_max):
    fixed_locations_names = [
        "Kenton Greenway",
        "Kentucky Derby Museum",
        "Louisville Slugger Museum",
        "Louisville Waterfront Park",
        "Louisville Zoo",
    ]
    fixed_locations = [d for d in docks if d.name in fixed_locations_names]
    initial_incidents_coverage = sum(len(d.incidents_covered(incidents)[0]) for d in fixed_locations) # Number of incidents covered by the fixed locations
    docks_remaining = [d for d in docks if d.name not in fixed_locations_names] # Optimize the remaining docks
    results = [
        {
            "k": len(fixed_locations),
            "incidents_covered": initial_incidents_coverage,
            "coverage_rate": initial_incidents_coverage / len(incidents),
            "docks_selected": len(fixed_locations),
            "delta_coverage": initial_incidents_coverage,
        }
    ]
    for k in range(k_max):
        r = maximize_incidents_covered(docks_remaining, incidents, k)
        if r is None:
            continue
        
        # Calculate delta coverage and break if it is 0
        r["delta_coverage"] = r["incidents_covered"] - results[-1]["incidents_covered"]
        if r["delta_coverage"] == 0:
            results.append(r)
            break
        
        results.append(r)
    return results

def optimization_test(docks, incidents):
    k_max = int(input("Enter the maximum number of dock locations: "))
    no_fixed_locations(docks, incidents, k_max)