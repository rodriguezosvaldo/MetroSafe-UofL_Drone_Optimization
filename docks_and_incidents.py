import numpy as np

class Dock:
    def __init__(self, name, latitude, longitude, drone_speed, response_time):
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.drone_speed = drone_speed
        self.response_time = response_time
        self.effective_radius = self.drone_speed * self.response_time

class Incident:
    def __init__(self, incident_id, latitude, longitude):
        self.incident_id = incident_id
        self.latitude = latitude
        self.longitude = longitude


def coverage(dock, incident):
    EARTH_RADIUS = 3958.7603 # milles (Source: Wikipedia)
    delta_latitude = np.radians(incident.latitude - dock.latitude)
    delta_longitude = np.radians(incident.longitude - dock.longitude)
    
    distance_dock_incident = 2 * EARTH_RADIUS * np.arcsin(np.sqrt(np.sin(delta_latitude / 2)**2 + np.cos(np.radians(dock.latitude)) * np.cos(np.radians(incident.latitude)) * np.sin(delta_longitude / 2)**2)) # Haversine formula
    return distance_dock_incident <= dock.effective_radius

def coverage_toy_example(dock, incident):
    import random
    choice = random.choice([True, False])
    print(f"Coverage: {dock.name} - {incident.incident_id} = {choice}")
    return choice
    