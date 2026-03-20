import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
import sys
from io import StringIO
from fpdf import FPDF
warnings.filterwarnings('ignore')

# Default data path (CSV in project root)
DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / 'Dataflights.csv'


def load_and_prepare_data(csv_path=None):
    """Load CSV and prepare columns for analysis. Returns prepared DataFrame."""
    path = Path(csv_path) if csv_path else DEFAULT_DATA_PATH
    df = pd.read_csv(path)
    df['Local Takeoff Time'] = pd.to_datetime(df['Local Takeoff Time'], errors='coerce')
    df['Takeoff'] = pd.to_datetime(df['Takeoff'], errors='coerce')
    df['Land'] = pd.to_datetime(df['Land'], errors='coerce')
    df['Day'] = pd.Categorical(df['Local Takeoff Time'].dt.day_name(), categories=DAY_ORDER, ordered=True)
    df['Hour'] = df['Local Takeoff Time'].dt.hour
    df['Date'] = df['Local Takeoff Time'].dt.date
    df['Type of incident'] = df['Type of incident'].fillna('Blank/Not Specified')
    df['Type of incident'] = df['Type of incident'].apply(lambda x: 'Blank/Not Specified' if str(x).strip() == '' else x)
    return df


def get_incidents_by_day(df):
    """Return incidents count per day of week (ordered Monday-Sunday)."""
    incidents = df['Day'].value_counts().sort_values(ascending=False)
    return incidents.reindex([d for d in DAY_ORDER if d in incidents.index])


def get_incidents_by_hour(df):
    """Return incidents count per hour of day."""
    return df['Hour'].value_counts().sort_index()


def get_incidents_by_category(df):
    """Return incidents count per category."""
    return df['Type of incident'].value_counts()


def get_day_hour_crosstab(df):
    """Return crosstab of incidents by day and hour."""
    ct = pd.crosstab(df['Day'], df['Hour'])
    ct['TOTAL'] = ct.sum(axis=1)
    return ct


def get_flights_by_location(df):
    """Return flights count per dock location."""
    return df['Takeoff Address'].value_counts()


def get_drone_utilization_by_dock(df):
    """Return crosstab: dock (rows) x drone/vehicle (columns), values = takeoff count."""
    ct = pd.crosstab(df['Takeoff Address'], df['Vehicle'])
    ct['TOTAL'] = ct.sum(axis=1)
    return ct


def run_report(output_buffer, add_chart_markers=False, df=None, title=None):
    """Generate the full text report into the given buffer. Returns prepared df.
    If add_chart_markers=True, inserts [CHART:key] lines for PDF chart embedding.
    If df is provided, use it instead of loading (allows pre-filtered data).
    If title is provided, use it for the report header."""
    if df is None:
        df = load_and_prepare_data()
    m = add_chart_markers
    report_title = title or "METROSAFE FLIGHT ANALYSIS - SUMMARY STATISTICS"

    print("=" * 80, file=output_buffer)
    print(report_title, file=output_buffer)
    print("=" * 80, file=output_buffer)
    print(file=output_buffer)

    # TABLE 1
    print("1. NUMBER OF INCIDENTS BY DAY, HOUR, AND INCIDENT CATEGORY", file=output_buffer)
    print("-" * 80, file=output_buffer)

    print("\nA. INCIDENTS BY DAY OF WEEK", file=output_buffer)
    incidents_by_day = get_incidents_by_day(df)
    for day, count in incidents_by_day.items():
        print(f"  {day:12s}: {count:3d} incidents", file=output_buffer)
    print(f"  {'Total':12s}: {incidents_by_day.sum():3d} incidents", file=output_buffer)
    if m:
        print("[CHART:incidents_by_day]", file=output_buffer)

    if m:
        print("[NEWPAGE]", file=output_buffer)
    print("\nB. INCIDENTS BY HOUR OF DAY", file=output_buffer)
    incidents_by_hour = get_incidents_by_hour(df)
    total_by_hour = 0
    for hour in range(24):
        if hour in incidents_by_hour.index:
            count = incidents_by_hour[hour]
            print(f"  {hour:02d}:00-{hour:02d}:59: {count:3d} incidents", file=output_buffer)
            total_by_hour += count
    print(f"  {'Total':10s}: {total_by_hour:3d} incidents", file=output_buffer)
    if m:
        print("[CHART:incidents_by_hour]", file=output_buffer)

    if m:
        print("[NEWPAGE]", file=output_buffer)
    print("\nC. INCIDENT FREQUENCY BY DAY AND HOUR (Selected Hours)", file=output_buffer)
    day_hour_crosstab = get_day_hour_crosstab(df)
    print(day_hour_crosstab.to_string(), file=output_buffer)
    print(f"\nTOTAL: {day_hour_crosstab['TOTAL'].sum():d} incidents", file=output_buffer)
    if m:
        print("[CHART:day_hour_heatmap]", file=output_buffer)

    if m:
        print("[NEWPAGE]", file=output_buffer)
    print("\nD. INCIDENTS BY CATEGORY", file=output_buffer)
    incidents_by_category = get_incidents_by_category(df)
    for category, count in incidents_by_category.items():
        print(f"  {category:50s}: {count:3d} incidents", file=output_buffer)
    print(f"  {'Total':50s}: {incidents_by_category.sum():3d} incidents", file=output_buffer)
    if m:
        print("[CHART:incidents_by_category]", file=output_buffer)
    print(file=output_buffer)

    if m:
        print("[NEWPAGE]", file=output_buffer)
    # TABLE 2
    print("2. NUMBER OF FLIGHTS BY DOCK LOCATION", file=output_buffer)
    print("-" * 80, file=output_buffer)
    flights_by_location = get_flights_by_location(df)
    print(file=output_buffer)
    for location, count in flights_by_location.items():
        print(f"  {location:60s}: {count:3d} flights", file=output_buffer)
    print(f"  {'Total':60s}: {len(df):3d} flights", file=output_buffer)
    if m:
        print("[CHART:flights_by_location]", file=output_buffer)
    print(file=output_buffer)

    if m:
        print("[NEWPAGE]", file=output_buffer)
    print("3. DRONE UTILIZATION BY DOCK", file=output_buffer)
    print("-" * 80, file=output_buffer)
    if m:
        print("[CHART:drone_utilization]", file=output_buffer)
    print(file=output_buffer)

    return df


def _generate_pdf(output_text, chart_paths=None, pdf_filename='MetroSafe_Analysis_Report.pdf', title=None):
    """Generate PDF report from text output. chart_paths: dict of key -> png path for embedding."""
    chart_paths = chart_paths or {}
    if title is None:
        title = "MetroSafe Flight Analysis - Summary Statistics"

    class PDFWithPageBreaks(FPDF):
        def __init__(self, header_title):
            super().__init__()
            self.set_auto_page_break(auto=True, margin=10)
            self.header_title = header_title

        def header(self):
            if self.page == 1:
                self.set_font("Helvetica", "B", 14)
                self.cell(0, 10, self.header_title, 0, 1, "C")
                self.ln(5)

    pdf = PDFWithPageBreaks(title)

    pdf.add_page()
    pdf.set_font("Courier", "", 9)

    for line in output_text.split('\n'):
        line_stripped = line.strip()
        if line_stripped == '[NEWPAGE]':
            pdf.add_page()
            continue
        if line_stripped.startswith('[CHART:') and line_stripped.endswith(']'):
            key = line_stripped[7:-1]
            if key in chart_paths:
                img_path = chart_paths[key]
                try:
                    pdf.ln(3)
                    pdf.image(img_path, w=180)  # 180mm width for A4 page
                    pdf.ln(3)
                except Exception:
                    pass
            continue

        if len(line) > 100:
            while len(line) > 100:
                pdf.cell(0, 4, line[:100], 0, 1)
                line = line[100:]
            if line:
                pdf.cell(0, 4, line, 0, 1)
        else:
            pdf.cell(0, 4, line, 0, 1)

    pdf.output(pdf_filename)
    return pdf_filename


if __name__ == '__main__':
    from visualizations import generate_all_charts, cleanup_chart_files

    output_buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_buffer

    df = run_report(output_buffer, add_chart_markers=True)

    sys.stdout = original_stdout
    output_text = output_buffer.getvalue()

    charts = generate_all_charts(df)
    chart_paths = {key: path for key, path in charts}

    pdf_path = Path(__file__).resolve().parent / 'MetroSafe_Analysis_Report.pdf'
    _generate_pdf(output_text, chart_paths, str(pdf_path))

    cleanup_chart_files([p for _, p in charts])
    print("Report successfully generated.")
