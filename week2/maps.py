"""
MetroSafe Flight Analysis - Interactive Maps (Folium)

Map 1 - Drone Coverage by Dock:
  Each dock is plotted with a circle representing the effective response radius.
  Radius basis (Skydio X10 specs — skydio.com):
    - Max horizontal speed: 45 mph / 20 m/s (without obstacle avoidance).
    - Max speed with standard obstacle avoidance: 35.8 mph / 16 m/s.
      → Used for DFR response: safe for urban navigation while maximizing coverage.
    - Startup time: under 40 seconds (spec). Deducted from the response window.
    - DFR (Drone as First Responder) target: arrive on scene within 4 minutes of dispatch.
    - Available travel time: 4 min − 40 s startup = 200 seconds.
    - Effective radius = 16 m/s × 200 s = 3,200 m = 3.2 km ≈ 2.0 miles.
  All dock markers are the same small fixed size for precise location pinpointing.

Map 2 - Incident Heatmap:
  A weighted heatmap using each dock's coordinates, weighted by the number of
  flights (incidents responded to) from that dock. Since the dataset records
  takeoff location rather than individual incident scene coordinates, this
  represents the spatial distribution of incident responses by dispatch origin.
"""
from pathlib import Path

import folium
from folium.plugins import HeatMap

from analysis import load_and_prepare_data

# Effective response radius derived from Skydio X10 specs (see module docstring):
#   16 m/s (max speed w/ standard OA) × 200 s (4 min − 40 s startup) = 3,200 m = 2.0 miles
EFFECTIVE_RADIUS_M = 3200

# Fixed small marker radius in pixels for precise dock pinpointing
DOCK_MARKER_RADIUS = 6

OUTPUT_DIR = Path(__file__).resolve().parent


def _get_dock_summary(df):
    """Return DataFrame with one row per dock: lat, lon, address, flight count."""
    summary = (
        df.groupby("Takeoff Address")
        .agg(
            lat=("Takeoff Latitude", "first"),
            lon=("Takeoff Longitude", "first"),
            flights=("Flight ID", "count"),
        )
        .reset_index()
        .sort_values("flights", ascending=False)
    )
    return summary


def _short_address(addr):
    """Return the street number and street name portion of an address."""
    parts = str(addr).split(",")
    return parts[0].strip() if parts else str(addr)


def map_dock_coverage(df, output_path=None, title="MetroSafe Drone Coverage by Dock"):
    """
    Map 1: Dock locations with effective response radius circles.

    All dock markers are the same small fixed size for precise location pinpointing.
    The shaded circle represents the reachable area within ~4 minutes at operational speed.
    """
    docks = _get_dock_summary(df)
    center_lat = docks["lat"].mean()
    center_lon = docks["lon"].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    if output_path is None:
        output_path = OUTPUT_DIR / "map_dock_coverage.html"

    for _, row in docks.iterrows():
        short_name = _short_address(row["Takeoff Address"])
        popup_text = (
            f"<b>{short_name}</b><br>"
            f"Total flights: {int(row['flights'])}<br>"
            f"Coverage radius: {EFFECTIVE_RADIUS_M / 1000:.1f} km (2.0 mi)"
        )

        # Coverage circle (transparent fill)
        folium.Circle(
            location=[row["lat"], row["lon"]],
            radius=EFFECTIVE_RADIUS_M,
            color="#1a6fba",
            fill=True,
            fill_color="#4da6ff",
            fill_opacity=0.10,
            weight=2,
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=f"{short_name}: {int(row['flights'])} flights",
        ).add_to(m)

        # Dock marker — fixed small size for precise location pinpointing
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=DOCK_MARKER_RADIUS,
            color="#003d80",
            fill=True,
            fill_color="#1a6fba",
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(popup_text, max_width=220),
            tooltip=f"{short_name}: {int(row['flights'])} flights",
        ).add_to(m)

        # Label
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:9px;font-weight:bold;color:#003d80;'
                     f'white-space:nowrap;margin-left:14px;margin-top:-8px;">'
                     f'{short_name}</div>',
                icon_size=(200, 20),
                icon_anchor=(0, 0),
            ),
        ).add_to(m)

    title_html = (
        '<div style="position:fixed;top:12px;left:55px;z-index:1000;'
        'background:white;padding:8px 12px;border-radius:6px;'
        'border:1px solid #ccc;font-size:13px;font-weight:bold;">'
        + title
        + "<br><span style='font-size:10px;font-weight:normal;color:#555;'>"
        f"Effective radius: {EFFECTIVE_RADIUS_M / 1000:.1f} km / 2.0 mi &nbsp;|&nbsp; 35.8 mph (16 m/s) with obstacle avoidance &nbsp;|&nbsp; 4 min − 40 s startup = 200 s travel"
        "</span></div>"
    )
    m.get_root().html.add_child(folium.Element(title_html))

    legend_html = (
        '<div style="position:fixed;bottom:30px;left:55px;z-index:1000;'
        'background:white;padding:8px 12px;border-radius:6px;'
        'border:1px solid #ccc;font-size:11px;">'
        "<b>Legend</b><br>"
        '<span style="color:#1a6fba;">&#9679;</span> Dock location<br>'
        '<span style="color:#4da6ff;">&#9711;</span> 3.2 km (2.0 mi) response radius'
        "</div>"
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save(str(output_path))
    return str(output_path)


def map_incident_heatmap(df, output_path=None, title="MetroSafe Incident Response Heatmap"):
    """
    Map 2: Weighted heatmap of incidents by dock origin.

    Uses each dock's coordinates weighted by number of flights (incidents responded to).
    Since the dataset records takeoff (dock) coordinates rather than individual
    incident scene coordinates, this represents dispatch-origin density.
    """
    docks = _get_dock_summary(df)
    center_lat = docks["lat"].mean()
    center_lon = docks["lon"].mean()

    if output_path is None:
        output_path = OUTPUT_DIR / "map_incident_heatmap.html"

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

    # Build heatmap data: [lat, lon, weight]
    heat_data = [
        [row["lat"], row["lon"], row["flights"]]
        for _, row in docks.iterrows()
    ]

    HeatMap(
        heat_data,
        radius=35,
        blur=25,
        max_zoom=13,
        gradient={0.2: "#ffffcc", 0.4: "#fed976", 0.6: "#fd8d3c", 0.8: "#e31a1c", 1.0: "#800026"},
    ).add_to(m)

    # Overlay small dock markers for reference
    for _, row in docks.iterrows():
        short_name = _short_address(row["Takeoff Address"])
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=5,
            color="#333",
            fill=True,
            fill_color="#333",
            fill_opacity=0.7,
            tooltip=f"{short_name}: {int(row['flights'])} flights",
        ).add_to(m)

    title_html = (
        '<div style="position:fixed;top:12px;left:55px;z-index:1000;'
        'background:white;padding:8px 12px;border-radius:6px;'
        'border:1px solid #ccc;font-size:13px;font-weight:bold;">'
        + title
        + "<br><span style='font-size:10px;font-weight:normal;color:#555;'>"
        "Weighted by number of flights dispatched per dock"
        "</span></div>"
    )
    m.get_root().html.add_child(folium.Element(title_html))

    m.save(str(output_path))
    return str(output_path)


if __name__ == "__main__":
    # --- All flights ---
    df_all = load_and_prepare_data()

    p = map_dock_coverage(
        df_all,
        output_path=OUTPUT_DIR / "map_dock_coverage.html",
        title="MetroSafe Drone Coverage by Dock",
    )
    print(f"[OK] {p}")

    p = map_incident_heatmap(
        df_all,
        output_path=OUTPUT_DIR / "map_incident_heatmap.html",
        title="MetroSafe Incident Response Heatmap",
    )
    print(f"[OK] {p}")
