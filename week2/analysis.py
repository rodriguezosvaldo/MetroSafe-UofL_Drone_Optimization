import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
from io import StringIO
from fpdf import FPDF
warnings.filterwarnings('ignore')

# Capture output
output_buffer = StringIO()
original_stdout = sys.stdout
sys.stdout = output_buffer

# Load the data
df = pd.read_csv('./Dataflights.csv')

# Parse datetime columns
df['Local Takeoff Time'] = pd.to_datetime(df['Local Takeoff Time'], errors='coerce')
df['Takeoff'] = pd.to_datetime(df['Takeoff'], errors='coerce')
df['Land'] = pd.to_datetime(df['Land'], errors='coerce')

# Extract day of week and hour
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
df['Day'] = pd.Categorical(df['Local Takeoff Time'].dt.day_name(), categories=day_order, ordered=True)
df['Hour'] = df['Local Takeoff Time'].dt.hour
df['Date'] = df['Local Takeoff Time'].dt.date

print("=" * 80)
print("METROSAFE FLIGHT ANALYSIS - SUMMARY STATISTICS")
print("=" * 80)
print()

# ==============================================================================
# TABLE 1: NUMBER OF INCIDENTS BY DAY, HOUR, AND INCIDENT CATEGORY
# ==============================================================================
print("1. NUMBER OF INCIDENTS BY DAY, HOUR, AND INCIDENT CATEGORY")
print("-" * 80)

# By Day
print("\nA. INCIDENTS BY DAY OF WEEK")
incidents_by_day = df['Day'].value_counts().sort_values(ascending=False)
incidents_by_day = incidents_by_day.reindex([d for d in day_order if d in incidents_by_day.index])
for day, count in incidents_by_day.items():
    print(f"  {day:12s}: {count:3d} incidents")
print(f"  {'Total':12s}: {incidents_by_day.sum():3d} incidents")

# By Hour
print("\nB. INCIDENTS BY HOUR OF DAY")
incidents_by_hour = df['Hour'].value_counts().sort_index()
total_by_hour = 0
for hour in range(24):
    if hour in incidents_by_hour.index:
        count = incidents_by_hour[hour]
        print(f"  {hour:02d}:00-{hour:02d}:59: {count:3d} incidents")
        total_by_hour += count
print(f"  {'Total':10s}: {total_by_hour:3d} incidents")

# By Incident Category
print("\nC. INCIDENTS BY CATEGORY")
df['Type of incident'] = df['Type of incident'].fillna('Blank/Not Specified')
df['Type of incident'] = df['Type of incident'].apply(lambda x: 'Blank/Not Specified' if str(x).strip() == '' else x)

incidents_by_category = df['Type of incident'].value_counts()
for category, count in incidents_by_category.items():
    print(f"  {category:50s}: {count:3d} incidents")
print(f"  {'Total':50s}: {incidents_by_category.sum():3d} incidents")

# By Day and Hour (detailed cross-tabulation)
print("\nD. INCIDENT FREQUENCY BY DAY AND HOUR (Selected Hours)")
day_hour_crosstab = pd.crosstab(
    df['Day'],
    df['Hour']
)
# Add row totals
day_hour_crosstab['TOTAL'] = day_hour_crosstab.sum(axis=1)
print(day_hour_crosstab.to_string())
print(f"\nTOTAL: {day_hour_crosstab['TOTAL'].sum():d} incidents")

print()

# ==============================================================================
# TABLE 2: NUMBER OF FLIGHTS BY DOCK LOCATION (TAKEOFF ADDRESS)
# ==============================================================================
print("2. NUMBER OF FLIGHTS BY DOCK LOCATION")
print("-" * 80)

flights_by_location = df['Takeoff Address'].value_counts()
print()
for location, count in flights_by_location.items():
    print(f"  {location:60s}: {count:3d} flights")
print(f"  {'Total':60s}: {len(df):3d} flights")

# Alternative: by coordinates if needed
print("\nFLIGHTS BY TAKEOFF LOCATION (COORDINATES)")
location_coords = df.groupby(['Takeoff Address']).agg({
    'Takeoff Latitude': 'first',
    'Takeoff Longitude': 'first',
    'Flight ID': 'count'
}).rename(columns={'Flight ID': 'Count'}).sort_values('Count', ascending=False)

total_location_coords = 0
for idx, row in location_coords.iterrows():
    print(f"  {idx[:50]:50s}: {int(row['Count']):3d} flights (Lat: {row['Takeoff Latitude']:.4f}, Lon: {row['Takeoff Longitude']:.4f})")
    total_location_coords += int(row['Count'])
print(f"  {'Total':50s}: {total_location_coords:3d} flights")

print()

# ==============================================================================
# TABLE 3: RESPONSE TIME SUMMARY STATISTICS
# ==============================================================================
# print("3. RESPONSE TIME SUMMARY STATISTICS")
# print("-" * 80)

# # Calculate response time (time from dispatch to arrival)
# # Using 'Takeoff' as dispatch time and approximating arrival as Takeoff + Duration
# df['Duration_minutes'] = df['Duration (seconds)'] / 60
# df['Response_duration'] = df['Duration_minutes']

# # Create incidents copy after Duration_minutes is created
# incidents_df = df.copy()

# print("\nA. OVERALL RESPONSE TIME STATISTICS")
# print(f"  Total flights analyzed: {len(df)}")
# print(f"  Average response duration: {df['Duration_minutes'].mean():.2f} minutes ({df['Duration_minutes'].mean() * 60:.0f} seconds)")
# print(f"  Median response duration: {df['Duration_minutes'].median():.2f} minutes")
# print(f"  Standard deviation: {df['Duration_minutes'].std():.2f} minutes")
# print(f"  Minimum duration: {df['Duration_minutes'].min():.2f} minutes ({df['Duration (seconds)'].min():.0f} seconds)")
# print(f"  Maximum duration: {df['Duration_minutes'].max():.2f} minutes ({df['Duration (seconds)'].max():.0f} seconds)")
# print(f"  25th percentile: {df['Duration_minutes'].quantile(0.25):.2f} minutes")
# print(f"  75th percentile: {df['Duration_minutes'].quantile(0.75):.2f} minutes")

# # By incident type
# print("\nB. RESPONSE TIME BY INCIDENT TYPE")
# response_by_type = incidents_df.groupby('Type of incident')['Duration_minutes'].agg([
#     ('Count', 'count'),
#     ('Mean', 'mean'),
#     ('Median', 'median'),
#     ('Min', 'min'),
#     ('Max', 'max'),
#     ('Std Dev', 'std')
# ]).round(2).sort_values('Mean', ascending=False)

# total_count_by_type = 0
# for idx, row in response_by_type.iterrows():
#     print(f"\n  {idx}:")
#     print(f"    Count: {int(row['Count'])}, Mean: {row['Mean']:.2f} min, Median: {row['Median']:.2f} min")
#     print(f"    Range: {row['Min']:.2f} - {row['Max']:.2f} min, Std Dev: {row['Std Dev']:.2f} min")
#     total_count_by_type += int(row['Count'])
# print(f"\n  TOTAL: {total_count_by_type} incidents")

# # By location
# print("\nC. RESPONSE TIME BY DOCK LOCATION")
# response_by_location = df.groupby('Takeoff Address')['Duration_minutes'].agg([
#     ('Count', 'count'),
#     ('Mean', 'mean'),
#     ('Median', 'median'),
#     ('Min', 'min'),
#     ('Max', 'max')
# ]).round(2).sort_values('Mean', ascending=False)

# total_count_by_location = 0
# for location, row in response_by_location.iterrows():
#     print(f"  {location[:50]:50s}: Count: {int(row['Count']):2d}, Mean: {row['Mean']:6.2f} min, Median: {row['Median']:6.2f} min")
#     total_count_by_location += int(row['Count'])
# print(f"  {'Total':50s}: Count: {total_count_by_location:2d}")

# print()

# ==============================================================================
# TABLE 4: DISTANCE-TO-NEAREST-DOCK SUMMARY STATISTICS
# ==============================================================================
# print("4. DISTANCE-TO-NEAREST-DOCK SUMMARY STATISTICS")
# print("-" * 80)

# from math import radians, cos, sin, asin, sqrt

# def haversine(lon1, lat1, lon2, lat2):
#     """
#     Calculate the great circle distance between two points 
#     on the earth (specified in decimal degrees)
#     Returns distance in miles
#     """
#     # convert decimal degrees to radians 
#     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
#     # haversine formula 
#     dlon = lon2 - lon1 
#     dlat = lat2 - lat1 
#     a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#     c = 2 * asin(sqrt(a)) 
#     r = 3959  # Radius of earth in miles
#     return c * r

# # Get unique dock locations
# dock_locations = df[['Takeoff Address', 'Takeoff Latitude', 'Takeoff Longitude']].drop_duplicates(subset=['Takeoff Address'])
# docks = dock_locations.set_index('Takeoff Address')[['Takeoff Latitude', 'Takeoff Longitude']].to_dict('index')

# # For each flight, calculate distance to nearest dock
# df['Nearest_dock_distance'] = np.nan

# for idx, row in df.iterrows():
#     if pd.notna(row['Takeoff Latitude']) and pd.notna(row['Takeoff Longitude']):
#         min_distance = float('inf')
#         nearest_dock = None
        
#         for dock_name, coords in docks.items():
#             distance = haversine(
#                 row['Takeoff Longitude'], row['Takeoff Latitude'],
#                 coords['Takeoff Longitude'], coords['Takeoff Latitude']
#             )
#             if distance < min_distance:
#                 min_distance = distance
#                 nearest_dock = dock_name
        
#         df.loc[idx, 'Nearest_dock_distance'] = min_distance

# # Update incidents_df with the new column
# incidents_df = df.copy()

# # Summary statistics
# print("\nA. OVERALL DISTANCE-TO-NEAREST-DOCK STATISTICS")
# print(f"  Total flights analyzed: {len(df)}")
# print(f"  Average distance: {df['Nearest_dock_distance'].mean():.4f} miles")
# print(f"  Median distance: {df['Nearest_dock_distance'].median():.4f} miles")
# print(f"  Standard deviation: {df['Nearest_dock_distance'].std():.4f} miles")
# print(f"  Minimum distance: {df['Nearest_dock_distance'].min():.4f} miles")
# print(f"  Maximum distance: {df['Nearest_dock_distance'].max():.4f} miles")
# print(f"  25th percentile: {df['Nearest_dock_distance'].quantile(0.25):.4f} miles")
# print(f"  75th percentile: {df['Nearest_dock_distance'].quantile(0.75):.4f} miles")

# # By location
# print("\nB. DISTANCE-TO-NEAREST-DOCK BY DOCK LOCATION")
# distance_by_location = df.groupby('Takeoff Address')['Nearest_dock_distance'].agg([
#     ('Count', 'count'),
#     ('Mean', 'mean'),
#     ('Median', 'median'),
#     ('Min', 'min'),
#     ('Max', 'max')
# ]).round(4).sort_values('Mean', ascending=False)

# total_distance_location = 0
# for location, row in distance_by_location.iterrows():
#     print(f"\n  {location}:")
#     print(f"    Flights: {int(row['Count']):2d}, Mean: {row['Mean']:.4f} mi, Median: {row['Median']:.4f} mi")
#     print(f"    Range: {row['Min']:.4f} - {row['Max']:.4f} mi")
#     total_distance_location += int(row['Count'])
# print(f"\n  TOTAL: {total_distance_location} flights")

# # By incident type
# print("\nC. DISTANCE-TO-NEAREST-DOCK BY INCIDENT TYPE")
# distance_by_incident = incidents_df.groupby('Type of incident')['Nearest_dock_distance'].agg([
#     ('Count', 'count'),
#     ('Mean', 'mean'),
#     ('Median', 'median'),
#     ('Min', 'min'),
#     ('Max', 'max')
# ]).round(4).sort_values('Mean', ascending=False)

# total_distance_incident = 0
# for incident_type, row in distance_by_incident.iterrows():
#     if pd.notna(incident_type):
#         print(f"\n  {incident_type}:")
#         print(f"    Flights: {int(row['Count']):2d}, Mean: {row['Mean']:.4f} mi, Median: {row['Median']:.4f} mi")
#         print(f"    Range: {row['Min']:.4f} - {row['Max']:.4f} mi")
#         total_distance_incident += int(row['Count'])
# print(f"\n  TOTAL: {total_distance_incident} flights")

# print()
# print("=" * 80)
# print("END OF ANALYSIS")
# print("=" * 80)

# ================================================================================
# EXPORT TO PDF
# ================================================================================

# Restore stdout and get the output
sys.stdout = original_stdout
output_text = output_buffer.getvalue()

# Print to console
print(output_text)

# Create PDF
class PDFWithPageBreaks(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=10)
        
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "MetroSafe Flight Analysis - Summary Statistics", 0, 1, "C")
        self.ln(5)

pdf = PDFWithPageBreaks()
pdf.add_page()
pdf.set_font("Courier", "", 9)

# Split output into lines for better formatting
lines = output_text.split('\n')
for line in lines:
    # Handle long lines
    if len(line) > 100:
        # Split long lines
        while len(line) > 100:
            pdf.cell(0, 4, line[:100], 0, 1)
            line = line[100:]
        if line:
            pdf.cell(0, 4, line, 0, 1)
    else:
        pdf.cell(0, 4, line, 0, 1)

# Save PDF
pdf_filename = 'MetroSafe_Analysis_Report.pdf'
pdf.output(pdf_filename)
print(f"\n[OK] PDF report saved as: {pdf_filename}")
