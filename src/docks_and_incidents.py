import numpy as np
import pandas as pd
import math

# CONSTANTS
# Drone speed and response time are constant values
DRONE_SPEED = 35.8 # 35.8 miles/hour = 16 meters/s data from https://www.skydio.com/x10/technical-specs
RESPONSE_TIME = 0.033 # 0.033 hours = 2 minutes target response time

class Dock:
    def __init__(self, name, latitude, longitude, drone_speed, response_time):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.drone_speed = drone_speed
        self.response_time = response_time
        self.effective_radius = self.drone_speed * self.response_time # miles

class Incident:
    def __init__(self, incident_id, latitude, longitude):
        self.incident_id = incident_id
        self.latitude = latitude
        self.longitude = longitude

# Returns True if the incident is within the effective radius of the dock, False otherwise
def coverage(dock, incident):
    # Haversine formula 
    # EARTH_RADIUS = 3958.7603 # milles (Source: Wikipedia)
    # delta_latitude = np.radians(incident.latitude - dock.latitude)
    # delta_longitude = np.radians(incident.longitude - dock.longitude)
    # distance_dock_incident = 2 * EARTH_RADIUS * np.arcsin(np.sqrt(np.sin(delta_latitude / 2)**2 + np.cos(np.radians(dock.latitude)) * np.cos(np.radians(incident.latitude)) * np.sin(delta_longitude / 2)**2)) # Haversine formula
    
    # Euclidean formula
    delta_latitude_miles = np.abs(incident.latitude - dock.latitude)*69
    mean_latitude = (incident.latitude + dock.latitude)/2
    delta_longitude_miles = np.abs(incident.longitude - dock.longitude)*math.cos(mean_latitude)*69
    distance_dock_incident = np.sqrt(delta_latitude_miles**2 + delta_longitude_miles**2)
    
    return distance_dock_incident <= dock.effective_radius

def coverage_toy_example(dock, incident):
    import random
    choice = random.choice([True, False])
    print(f"Coverage: {dock.name} - {incident.incident_id} = {choice}")
    return choice

# Create docks and incidents objects from data
def get_docks(excel_file_path):
    docks = []
    docks_data = pd.read_excel(excel_file_path)
    for index, row in docks_data.iterrows():
        dock = Dock(row['Address'], row['Latitude'], row['Longitude'], DRONE_SPEED, RESPONSE_TIME)
        docks.append(dock)
    print(f"Docks created: {len(docks)}")
    return docks

def get_incidents(excel_file_path):
    incidents = []
    incidents_data = pd.read_excel(excel_file_path)
    for index, row in incidents_data.iterrows():
        incident = Incident(row['inci_no'], row['latitude'], row['longitude'])
        incidents.append(incident)
    print(f"Incidents created: {len(incidents)}")
    return incidents
