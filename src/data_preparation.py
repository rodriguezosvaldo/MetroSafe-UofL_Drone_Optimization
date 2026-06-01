# Cleaning the data collected from Louisville Metro Open Data Portal (https://data.louisvilleky.gov/)
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.geocode_addresses import geocode_addresses

RAW_DATA_XLSX = PROJECT_ROOT / "data" / "RAW_crime_data_2025.xlsx"
CLEANED_INTERIM_XLSX = PROJECT_ROOT / "output" / "_cleaned_for_geocode.xlsx"
OUTPUT_XLSX = PROJECT_ROOT / "output" / "clean_and_geocoded_LMPD_data_2025.xlsx"

def data_cleaning_and_geocoding(dataframe: pd.DataFrame) -> pd.DataFrame:
    print("\n--- Data cleaning (LMPD 2025) ---")
    print(f"Incidents loaded: {len(dataframe):,}")

    n = len(dataframe)
    dataframe = dataframe.drop_duplicates(subset=["incident_number"])
    print(f"Duplicates removed (incident_number): {n - len(dataframe):,} -> {len(dataframe):,} remaining")

    n = len(dataframe)
    dataframe = dataframe[dataframe["incident_number"].notna()]
    print(f"Rows without incident_number removed: {n - len(dataframe):,} -> {len(dataframe):,} remaining")

    n = len(dataframe)
    dataframe = dataframe[dataframe["block_address"].notna()]
    print(f"Rows without block_address removed: {n - len(dataframe):,} -> {len(dataframe):,} remaining")

    NIBRS_PRIORITY = {
        '09A': 'High',
        '09B': 'High',
        '09C': 'High',
        '100': 'High',
        '11A': 'High',
        '120': 'High',
        '13A': 'High',
        '13B': 'Medium',
        '200': 'High',
        '220': 'Medium',
        '23A': 'Low',
        '23B': 'Low',
        '23C': 'Low',
        '23D': 'Medium',
        '23F': 'Medium',
        '23G': 'Medium',
        '23H': 'Medium',
        '240': 'Medium',
        '280': 'Low',
        '290': 'Medium',
        '30C': 'Medium',
        '35A': 'Medium',
        '35B': 'Low',
        '49A': 'Medium',
        '49B': 'Medium',
        '49C': 'Medium',
        '520': 'High',
        '521': 'High',
        '522': 'High',
        '526': 'High',
        '620': 'Low',
        '64A': 'Medium',
        '64B': 'Medium',
        '720': 'Medium',
        '90B': 'Low',
        '90C': 'Medium',
        '90D': 'Low',
        '90J': 'Low',
    }

    dataframe["priority"] = dataframe["nibrs_code"].map(NIBRS_PRIORITY)
    print(f"Priority assigned: {len(dataframe):,} incidents")

    # n = len(dataframe)
    # dataframe = dataframe[dataframe["nibrs_code"].map(NIBRS_PRIORITY) == "High"]
    # dataframe["priority"] = dataframe["nibrs_code"].map(NIBRS_PRIORITY)
    # print(f"Non-High priority incidents removed: {n - len(dataframe):,} -> {len(dataframe):,} remaining")
    # print(f"Cleaning done: {len(dataframe):,} incidents ready for geocoding")

    CLEANED_INTERIM_XLSX.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_excel(CLEANED_INTERIM_XLSX, index=False)
    print(f"Interim file written: {CLEANED_INTERIM_XLSX}")

    result = geocode_addresses(CLEANED_INTERIM_XLSX, OUTPUT_XLSX)
    if CLEANED_INTERIM_XLSX.is_file():
        CLEANED_INTERIM_XLSX.unlink()
        print(f"Interim file removed: {CLEANED_INTERIM_XLSX.name}")
    print(f"Final output: {OUTPUT_XLSX} ({len(result):,} incidents)\n")
    return result


if __name__ == "__main__":
    print(f"Reading raw data: {RAW_DATA_XLSX}")
    df = pd.read_excel(RAW_DATA_XLSX)
    data_cleaning_and_geocoding(df)


