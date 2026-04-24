from src.docks_and_incidents import get_docks, get_incidents
from visualizations.map import create_map
import webbrowser
from pathlib import Path

def create_docks_and_incidents():
    try:
        current_docks = get_docks('./data/8_docks.xlsx')
        incidents = get_incidents('./data/100_fire_incidents.xlsx')
        return current_docks, incidents
    except Exception as e:
        print(f"Error creating docks and incidents: {e}")
        return None, None

def visualize_map(current_docks, incidents):
    create_map(current_docks, incidents)
    map_file = Path(__file__).parent / "./output/map.html"
    if map_file.exists():
        webbrowser.open(map_file.resolve().as_uri())
    else:
        print("Create docks and incidents first to visualize the map")

def menu():
    while True:
        print("\nMenu")
        print("--------------------------------")
        print("1. Create docks and incidents from data")
        print("2. Visualize a map of the docks and incidents")
        print("3. Exit")
        print("--------------------------------")
        choice = input("\nEnter your choice: ")

        if choice == "1":
            current_docks, incidents = create_docks_and_incidents()
        elif choice == "2":
            if current_docks is None or incidents is None:
                print("Create docks and incidents first to visualize the map")
                continue
            visualize_map(current_docks, incidents)
        elif choice == "3":
            break
        else:
            print("Invalid choice") 
            continue
        
if __name__ == "__main__":
    menu()
