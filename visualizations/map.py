import folium
from src.docks_and_incidents import coverage

def create_map(docks, incidents, map_name):
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

        incidents_by_dock = {
            dock.name: sum(1 for incident in incidents if coverage(dock, incident))
            for dock in docks
        }

        dock_coverage_rows = "".join(
            f"<li>{dock_name}: {incident_count}</li>"
            for dock_name, incident_count in incidents_by_dock.items()
        )
        total_incidents_covered = sum(incidents_by_dock.values())

        legend_html = f"""
        <div style="
            position: fixed;
            bottom: 25px;
            left: 25px;
            z-index: 1000;
            background-color: white;
            border: 2px solid #666;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 13px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            max-width: 320px;
        ">
            <div><b>Docks:</b> {len(docks)}</div>
            <div><b>Incidents:</b> {len(incidents)}</div>
            <div style="margin-top: 8px;"><b>Incidents Covered</b></div>
            <ul style="margin: 4px 0 0 16px; padding: 0;">
                {dock_coverage_rows}
            </ul>
            <div style="margin-top: 6px;"><b>Total:</b> {total_incidents_covered}</div>
        </div>
        """
        map.get_root().html.add_child(folium.Element(legend_html))
        map.save(f'./output/{map_name}.html')
    except Exception as e:
        print(f"Error creating map: {e}")