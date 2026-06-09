import folium
from src.docks_and_incidents import coverage

def create_map(docks, incidents, map_name, all_incidents=None):
    try:
        map = folium.Map(
            location=[38.2527, -85.7585],
            zoom_start=12,
            tiles="CartoDB Positron"
        )
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
        total_incidents = len(all_incidents) if all_incidents is not None else len(incidents)
        if all_incidents is not None:
            covered_incidents = len(incidents)
        else:
            covered_incidents = sum(
                1 for incident in incidents
                if any(coverage(dock, incident) for dock in docks)
            )
        uncovered_incidents = total_incidents - covered_incidents
        covered_incidents_percentage = (covered_incidents / total_incidents * 100) if total_incidents else 0
        uncovered_incidents_percentage = (uncovered_incidents / total_incidents * 100) if total_incidents else 0

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

            folium.CircleMarker(
                location=[dock.latitude, dock.longitude],
                radius=3,
                color="#1f77b4",
                fill=True,
                fill_color="#1f77b4",
                fill_opacity=1,
                popup=folium.Popup(
                    html=f"""
                    <div style="padding-x:2px; white-space: nowrap;">
                        <b>{dock.name}</b><br>
                        Effective Radius: {dock.effective_radius:.2f} miles<br>
                        Covered Incidents: {incidents_by_dock[dock.name]}
                    </div>
                    """,
                    max_width=200
                ),
            ).add_to(map)

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
            <div><b>Total Incidents:</b> {total_incidents}</div>
            <div><b>Dock Locations:</b> {len(docks)}</div>
            <div><b>Covered Incidents:</b> {covered_incidents} ({covered_incidents_percentage:.0f}%)</div>
            <div><b>Uncovered Incidents:</b> {uncovered_incidents} ({uncovered_incidents_percentage:.0f}%)</div>
        </div>
        """
        map.get_root().html.add_child(folium.Element(legend_html))
        map.save(f'./output/{map_name}.html')
    except Exception as e:
        print(f"Error creating map: {e}")