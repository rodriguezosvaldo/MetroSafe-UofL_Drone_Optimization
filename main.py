from src.docks_and_incidents import create_docks_and_incidents
from src.optimization_model import maximize_incidents_covered
from visualizations.map_incidents_and_docks import create_map
from src.optimization_tests import optimization_test

# CONSTANTS
DOCKS_EXCEL_FILE_PATH = "output/docks_JCPS_MetroSafe.xlsx"
INCIDENTS_EXCEL_FILE_PATH = "output/clean_and_geocoded_LMPD_data_2025.xlsx"

def menu():
    while True:
        print("\n                    Menu")
        print("---------------------------------------------------")
        print("1. Create docks and incidents from data")
        print("******** Optimization Models ********")
        print("2. Maximize the number of incidents covered by the docks")
        print("3. Run the optimization model with the defined test parameters")
        print("4. Exit")
        print("---------------------------------------------------")
        choice = input("\nEnter your choice: ")

        if choice == "1":
            docks, incidents = create_docks_and_incidents(DOCKS_EXCEL_FILE_PATH, INCIDENTS_EXCEL_FILE_PATH)
            create_map(docks, incidents, "docks_and_incidents_map")
            continue
        elif choice == "2":
            try:
                if docks is None or incidents is None:
                    raise Exception("Create docks and incidents first to run the optimization model")
                dock_locations_quantity = int(input("Enter the number of dock locations available: "))
                maximize_incidents_covered(docks, incidents, dock_locations_quantity)
            except Exception as e:
                print("Be sure to create docks and incidents before running the optimization model")
                print(f"Error running the optimization model: {e}")
                continue
        elif choice == "3":
            optimization_test(docks, incidents)
            continue
        elif choice == "4":
            break
        else:
            print("Invalid choice") 
            continue
        
if __name__ == "__main__":
    menu()
