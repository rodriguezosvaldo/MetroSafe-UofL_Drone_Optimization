from src.docks_and_incidents import create_docks_and_incidents
from src.optimization_model import maximize_incidents_covered


def menu():
    while True:
        print("\n                    Menu")
        print("---------------------------------------------------")
        print("1. Create docks and incidents from data")
        print("******** Optimization Models ********")
        print("2. Maximize the number of incidents covered by the docks")
        print("3. Exit")
        print("---------------------------------------------------")
        choice = input("\nEnter your choice: ")

        if choice == "1":
            current_docks, incidents = create_docks_and_incidents()
            continue
        elif choice == "2":
            try:
                if current_docks is None or incidents is None:
                    raise Exception("Create docks and incidents first to run the optimization model")
                maximize_incidents_covered(current_docks, incidents)
            except Exception as e:
                print("Be sure to create docks and incidents before running the optimization model")
                print(f"Error running the optimization model: {e}")
                continue
        elif choice == "3":
            break
        else:
            print("Invalid choice") 
            continue
        
if __name__ == "__main__":
    menu()
