from src.optimization_model import maximize_incidents_covered

# MetroSafe current dock locations
METROSAFE_DOCK_LOCATIONS = [
    "1510 South 6th Street",
    "1525 Winter Avenue",
    "2620 Frankfort Avenue",
    "2900 Hikes Lane",
    "3228 River Park Drive",
    "3511 Fincastle Road",
    "4535 Manslick Road",
    "601 West Chestnut Street",
]

def charts_tables():
    return
    
def no_fixed_locations(docks, incidents, k_min, k_max):
    k_range = {
        "k_min": k_min,
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
    fixed_locations = [d for d in docks if d.name in METROSAFE_DOCK_LOCATIONS]
    initial_incidents_coverage = sum(len(d.incidents_covered(incidents)[0]) for d in fixed_locations) # Number of incidents covered by the fixed locations
    docks_remaining = [d for d in docks if d.name not in METROSAFE_DOCK_LOCATIONS] # Optimize the remaining docks
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

def menu(docks, incidents):
    while True:
        print("\n                    Menu")
        print("---------------------------------------------------")
        print("1. Test optimizations with no fixed locations")
        print("2. Test optimizations starting from the 8 current MetroSafe dock locations")
        print("0. Exit")
        print("---------------------------------------------------")
        choice = input("\nEnter your choice: ")

        if choice == "1":
            k_min = int(input("Enter the number of docks to optimize in the first iteration: "))
            k_max = int(input("Enter the maximum number of docks to optimize: "))
            if k_min > k_max:
                print("The minimum number of docks to optimize must be less than the maximum number of docks to optimize")
                continue
            if k_min < 0:
                print("The minimum number of docks to optimize must be greater than 0")
                continue
            if k_max < 0:
                print("The maximum number of docks to optimize must be greater than 0")
                continue
            no_fixed_locations(docks, incidents, k_min, k_max)
        elif choice == "2":
            k_max = int(input("Enter the maximum number of docks to optimize: "))
            if k_max < 8:
                print("The maximum number of docks to optimize must be greater than 8")
                continue
            fixed_locations(docks, incidents, k_max)
        elif choice == "0":
            break
        else:
            print("Invalid choice")

def test_multiple_optimizations(docks, incidents):
    menu(docks, incidents)
