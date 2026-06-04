# Cleaning the data collected from Louisville Metro Open Data Portal (https://data.louisvilleky.gov/)

import argparse
import re
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from src.geocode_addresses import STATE, geocode_addresses



RAW_LMPD_XLSX = PROJECT_ROOT / "data" / "RAW_crime_data_2025.xlsx"
RAW_JCPS_CSV = PROJECT_ROOT / "data" / "RAW_Jefferson_County_KY_Schools.csv"

LMPD_OUTPUT_XLSX = PROJECT_ROOT / "output" / "clean_and_geocoded_LMPD_data_2025.xlsx"
JCPS_OUTPUT_XLSX = PROJECT_ROOT / "output" / "clean_and_geocoded_JCPS_schools.xlsx"

_BLOCK_RE = re.compile(r"\bBLOCK\b", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")

def clean_street(value: object) -> str | None:
    """Return street text with the literal word ``BLOCK`` removed (LMPD block addresses).
    ``"2200 BLOCK BROWNSBORO RD"`` -> ``"2200 BROWNSBORO RD"``.
    Returns ``None`` for missing/empty values.
    """
    if not isinstance(value, str):
        return None
    cleaned = _BLOCK_RE.sub("", value)
    cleaned = _WS_RE.sub(" ", cleaned).strip(" ,;:.")
    return cleaned or None

def normalize_text(value: object) -> str | None:
    """Strip and return non-empty text; ``None`` for missing values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None

def normalize_zip_code(value: object) -> str | None:
    """Return a 5-digit ZIP string, or ``None`` if not usable."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        digits = str(int(value))
    else:
        digits = "".join(ch for ch in str(value).strip() if ch.isdigit())
    if len(digits) < 5:
        return None
    return digits[:5]

def build_full_address(
    street: object, city: object, zip_code: object, state: str = STATE
) -> str | None:
    """Compose ``"<street>, <city>, <zip>, <state>"``; ``None`` if anything missing."""
    parts = [street, city, zip_code, state]
    if not all(isinstance(p, str) and p.strip() for p in parts):
        return None
    return ", ".join(str(p).strip() for p in parts)

def add_geocode_columns(
    dataframe: pd.DataFrame,
    *,
    street: pd.Series,
    city: pd.Series,
    zip_code: pd.Series,
    state: pd.Series | str = STATE,
) -> pd.DataFrame:
    """Add ``clean_street``, ``city``, ``zip_code``, and ``clean_address`` for geocoding."""
    out = dataframe.copy()
    out["clean_street"] = street.map(clean_street)
    out["city"] = city.map(normalize_text)
    out["zip_code"] = zip_code.map(normalize_zip_code)
    if isinstance(state, pd.Series):
        state_values = state.map(normalize_text)
    else:
        state_values = pd.Series(state, index=out.index)

    out["clean_address"] = [
        build_full_address(s, c, z, st or STATE)
        for s, c, z, st in zip(
            out["clean_street"], out["city"], out["zip_code"], state_values
        )
    ]
    return out

def run_geocoding(
    cleaned_df: pd.DataFrame,
    output_xlsx: str | Path,
    *,
    label: str = "records",
) -> pd.DataFrame:
    """Geocode a cleaned dataframe and write the final Excel output."""
    output_path = Path(output_xlsx)
    print(f"\n--- Geocoding ({label}) ---")
    result = geocode_addresses(cleaned_df, output_path)
    print(f"Final output: {output_path} ({len(result):,} {label})\n")
    return result

def LMPD_data_cleaning(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean LMPD 2025 incidents and add geocoding columns (no geocoding step)."""
    delete_columns = [
        "date_reported",
        "badge_id",
        "offense_classification",
        "offense_code_name",
        "nibrs_group_name",
        "was_offense_completed",
        "lmpd_division",
        "lmpd_beat",
        "location_category",
        "block_address",
        "ObjectId",
    ]

    print("\n--- Data cleaning (LMPD 2025) ---")
    print(f"Incidents loaded: {len(dataframe):,}")

    n = len(dataframe)
    dataframe = dataframe.drop_duplicates(subset=["incident_number"])
    print(
        f"Duplicates removed (incident_number): {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["incident_number"].notna()]
    print(
        f"Rows without incident_number removed: {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["block_address"].notna()]
    print(
        f"Rows without block_address removed: {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    dataframe = add_geocode_columns(
        dataframe,
        street=dataframe["block_address"],
        city=dataframe["city"],
        zip_code=dataframe["zip_code"],
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["clean_address"].notna()]
    print(
        f"Rows without usable clean_address removed: "
        f"{n - len(dataframe):,} -> {len(dataframe):,} remaining"
    )

    dataframe = dataframe.drop(columns=delete_columns, errors="ignore")
    print(f"Columns removed: {delete_columns}")

    nibrs_priority = {
        "09A": "High",
        "09B": "High",
        "09C": "High",
        "100": "High",
        "11A": "High",
        "120": "High",
        "13A": "High",
        "13B": "Medium",
        "200": "High",
        "220": "Medium",
        "23A": "Low",
        "23B": "Low",
        "23C": "Low",
        "23D": "Medium",
        "23F": "Medium",
        "23G": "Medium",
        "23H": "Medium",
        "240": "Medium",
        "280": "Low",
        "290": "Medium",
        "30C": "Medium",
        "35A": "Medium",
        "35B": "Low",
        "49A": "Medium",
        "49B": "Medium",
        "49C": "Medium",
        "520": "High",
        "521": "High",
        "522": "High",
        "526": "High",
        "620": "Low",
        "64A": "Medium",
        "64B": "Medium",
        "720": "Medium",
        "90B": "Low",
        "90C": "Medium",
        "90D": "Low",
        "90J": "Low",
    }

    #==============================================================================
    # Uncomment this block and comment the block below to keep all incidents with priority labels (High/Medium/Low):
    # dataframe["priority"] = dataframe["nibrs_code"].map(nibrs_priority)
    # print(f"Priority assigned: {len(dataframe):,} incidents")
    #==============================================================================
    
    #==============================================================================
    # This block keeps only the incidents with High priority
    n = len(dataframe)
    dataframe = dataframe[dataframe["nibrs_code"].map(nibrs_priority) == "High"]
    dataframe["priority"] = dataframe["nibrs_code"].map(nibrs_priority)
    print(
        f"Non-High priority incidents removed: {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )
    #==============================================================================
    
    print(f"Cleaning done: {len(dataframe):,} incidents ready for geocoding")
    return dataframe

def JCPS_data_cleaning(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean JCPS school locations and add geocoding columns (no geocoding step)."""
    delete_columns = [
        "X",
        "Y",
        "LEVEL_",
        "LOC",
        "ADDRESS",
        "CITY",
        "ZIP",
        "PHONE",
        "SCH_AB",
        "SCH_WEB",
    ]

    print("\n--- Data cleaning (JCPS schools) ---")
    print(f"Schools loaded: {len(dataframe):,}")

    n = len(dataframe)
    dataframe = dataframe.drop_duplicates(subset=["OBJECTID"])
    print(
        f"Duplicates removed (OBJECTID): {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["LOC_TYPE"] == "JCPS"]
    print(
        f"Rows without JCPS type schools removed: {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["ADDRESS"].notna()]
    print(
        f"Rows without ADDRESS removed: {n - len(dataframe):,} "
        f"-> {len(dataframe):,} remaining"
    )

    dataframe = add_geocode_columns(
        dataframe,
        street=dataframe["ADDRESS"],
        city=dataframe["CITY"],
        zip_code=dataframe["ZIP"],
        state=dataframe["ST"],
    )

    n = len(dataframe)
    dataframe = dataframe[dataframe["clean_address"].notna()]
    print(
        f"Rows without usable clean_address removed: "
        f"{n - len(dataframe):,} -> {len(dataframe):,} remaining"
    )

    dataframe = dataframe.drop(columns=delete_columns, errors="ignore")
    print(f"Columns removed: {delete_columns}")
    print(f"Cleaning done: {len(dataframe):,} schools ready for geocoding")
    return dataframe

def prepare_lmpd_pipeline() -> pd.DataFrame:
    """Load raw LMPD data, clean, geocode, and return the final dataframe."""
    print(f"Reading raw data: {RAW_LMPD_XLSX}")
    df = pd.read_excel(RAW_LMPD_XLSX)
    cleaned = LMPD_data_cleaning(df)
    geocoded = run_geocoding(cleaned, LMPD_OUTPUT_XLSX, label="incidents")
    return geocoded

def prepare_jcps_pipeline() -> pd.DataFrame:
    """Load raw JCPS schools CSV, clean, geocode, and return the final dataframe."""
    print(f"Reading raw data: {RAW_JCPS_CSV}")
    df = pd.read_csv(RAW_JCPS_CSV)
    cleaned = JCPS_data_cleaning(df)
    geocoded = run_geocoding(cleaned, JCPS_OUTPUT_XLSX, label="schools")
    return geocoded

_DATASET_CHOICES = {
    "1": "lmpd",
    "2": "jcps",
    "3": "both",
    "lmpd": "lmpd",
    "jcps": "jcps",
    "both": "both",
}

def prompt_dataset_choice() -> str:
    """Ask the user which dataset pipeline to run."""
    print("Select the dataset to process")
    print("1- lmpd")
    print("2- jcps")
    print("3- both")
    while True:
        choice = input("Enter choice (1-3): ").strip().lower()
        dataset = _DATASET_CHOICES.get(choice)
        if dataset:
            return dataset
        print("Invalid choice. Please enter 1, 2, or 3.")

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and geocode LMPD or JCPS datasets.")
    parser.add_argument(
        "--dataset",
        choices=("lmpd", "jcps", "both"),
        help="Which dataset pipeline to run (skips interactive menu).",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv:
        args = parse_args(argv)
        if args.dataset is None:
            print("Error: --dataset is required when passing command-line arguments.")
            return 1
        dataset = args.dataset
    else:
        dataset = prompt_dataset_choice()

    if dataset in ("lmpd", "both"):
        prepare_lmpd_pipeline()
    if dataset in ("jcps", "both"):
        prepare_jcps_pipeline()
    return 0

if __name__ == "__main__":
    sys.exit(main())


