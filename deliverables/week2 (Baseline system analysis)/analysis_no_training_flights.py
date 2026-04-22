"""
MetroSafe Flight Analysis - Excluding Training/Test Flights
Generates the same report as analysis.py but excludes training, test, and similar flights.
"""
import sys
from io import StringIO
from pathlib import Path

from analysis import load_and_prepare_data, run_report, _generate_pdf
from visualizations import generate_all_charts, cleanup_chart_files

# Incident categories to exclude (training, test, etc.)
EXCLUDED_INCIDENT_CATEGORIES = [
    "Non-operational (i.e. training flight)",
    "Test",
    "Non-operational (i.e. training flight), Test Flight",
    "Training",
    "Training Flight",
    "Test flight",
    "testing",
    "Testing",
]

REPORT_TITLE = "METROSAFE FLIGHT ANALYSIS - SUMMARY STATISTICS (Excluding Training/Test Flights)"
PDF_FILENAME = "MetroSafe_Analysis_Report_no_Training_flights.pdf"


def load_and_prepare_data_no_training():
    """Load data and exclude training/test incident categories."""
    df = load_and_prepare_data()
    df = df[~df["Type of incident"].isin(EXCLUDED_INCIDENT_CATEGORIES)].copy()
    return df


if __name__ == "__main__":
    df = load_and_prepare_data_no_training()

    output_buffer = StringIO()
    original_stdout = sys.stdout
    sys.stdout = output_buffer

    run_report(output_buffer, add_chart_markers=True, df=df, title=REPORT_TITLE)

    sys.stdout = original_stdout
    output_text = output_buffer.getvalue()

    charts = generate_all_charts(df)
    chart_paths = {key: path for key, path in charts}

    pdf_path = Path(__file__).resolve().parent / PDF_FILENAME
    _generate_pdf(output_text, chart_paths, str(pdf_path), title=REPORT_TITLE)

    cleanup_chart_files([p for _, p in charts])
    print("Report successfully generated.")
