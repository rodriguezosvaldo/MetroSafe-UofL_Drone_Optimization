import folium

def create_map(docks, incidents):
    try:
        map = folium.Map(
            location=[38.2527, -85.7585],
            zoom_start=12,
            tiles="CartoDB Positron"
        )
        for dock in docks:
            folium.Circle(
                location=[dock.latitude, dock.longitude],
                radius=dock.effective_radius*1609.344, # convert miles to meters
                color="#1f77b4",
                weight=1,
                fill=True,
                fill_color="#1f77b4",
                fill_opacity=0.10,
            ).add_to(map)

            folium.Marker(
                location=[dock.latitude, dock.longitude],
                popup=folium.Popup(
                    html=f"""
                    <div style="padding-x:2px; white-space: nowrap;">
                        <b>{dock.name}</b><br>
                        Effective Radius: {dock.effective_radius:.2f} miles
                    </div>
                    """,
                    max_width=200
                ),
                icon=folium.Icon(color="blue", icon="home", prefix="fa")
            ).add_to(map)
        for incident in incidents:
            folium.CircleMarker(
                location=[incident.latitude, incident.longitude],
                radius=4,
                color="#d62728",
                weight=1,
                fill=True,
                fill_color="#d62728",
                fill_opacity=0.9,
                popup=folium.Popup(
                    html=f"""
                    <div style="padding-x:2px; white-space: nowrap;">
                        {incident.incident_id}
                    </div>
                    """,
                    max_width=100
                ),
            ).add_to(map)
        map.save('./output/map.html')
    except Exception as e:
        print(f"Error creating map: {e}")