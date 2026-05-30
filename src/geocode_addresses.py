r"""Geocoding pipeline for the LMPD 2025 incidents dataset.

Steps:
    1. Read the source Excel file.
    2. Clean ``block_address`` (remove the literal word ``BLOCK``) and build a
       full ``clean_address`` column with the format
       ``"<street>, <city>, <zip>, KY"``.
    3. Deduplicate to avoid geocoding the same address many times.
    4. Split unique addresses into Census Geocoder batch CSV files
       (max 10,000 rows per batch).
    5. POST each batch to the Census Geocoder ``addressbatch`` endpoint and
       store the raw CSV responses (resumable: existing responses are reused).
    6. Parse the responses, then merge ``latitude`` / ``longitude`` back into
       the original dataset on ``clean_address``.
    7. Drop incidents without both ``latitude`` and ``longitude``.
    8. Delete intermediate CSVs and Census batch/response files. Only the
       output Excel (with ``latitude`` and ``longitude``) remains on disk.

"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
BATCHES_DIR = DATA_DIR / "census_batches"
RESPONSES_DIR = DATA_DIR / "census_responses"

DEFAULT_INPUT_XLSX = DATA_DIR / "RAW_crime_data_2025.xlsx"
DEFAULT_OUTPUT_XLSX = OUTPUT_DIR / "LMPD_incidents_2025_geocoded.xlsx"
UNIQUE_ADDRESSES_CSV = DATA_DIR / "unique_addresses.csv"
GEOCODED_UNIQUE_CSV = DATA_DIR / "unique_addresses_geocoded.csv"

STATE = "KY"
MAX_BATCH_SIZE = 10_000

# Census Geocoder batch endpoint. ``locations`` is enough for lat/lon; switch to
# ``geographies`` if census tracts/blocks are ever needed.
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BENCHMARK = "Public_AR_Current"
# A single batch of 10k addresses can take several minutes server-side.
REQUEST_TIMEOUT_S = 60 * 30

# Census batch response is CSV without headers.
CENSUS_RESPONSE_COLS = [
    "uid",
    "input_address",
    "match_indicator",
    "match_type",
    "matched_address",
    "coordinates",
    "tigerline_id",
    "side",
]

_BLOCK_RE = re.compile(r"\bBLOCK\b", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _ensure_dirs() -> None:
    for d in (DATA_DIR, OUTPUT_DIR, BATCHES_DIR, RESPONSES_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _cleanup_geocoding_artifacts() -> None:
    """Remove intermediate files created during geocoding; keep only the output Excel."""
    print("[6/6] Removing intermediate geocoding files")
    for path in (UNIQUE_ADDRESSES_CSV, GEOCODED_UNIQUE_CSV):
        if path.is_file():
            path.unlink()
            print(f"      removed {path.relative_to(PROJECT_ROOT)}")

    for directory in (BATCHES_DIR, RESPONSES_DIR):
        if not directory.is_dir():
            continue
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_path.unlink()
                print(f"      removed {file_path.relative_to(PROJECT_ROOT)}")
        try:
            directory.rmdir()
        except OSError:
            pass


def clean_street(value: object) -> str | None:
    """Return ``block_address`` with the literal word ``BLOCK`` removed.

    ``"2200 BLOCK BROWNSBORO RD"`` -> ``"2200 BROWNSBORO RD"``.
    Returns ``None`` for missing/empty values.
    """
    if not isinstance(value, str):
        return None
    cleaned = _BLOCK_RE.sub("", value)
    cleaned = _WS_RE.sub(" ", cleaned).strip(" ,;:.")
    return cleaned or None


def build_full_address(
    street: object, city: object, zip_code: object, state: str = STATE
) -> str | None:
    """Compose ``"<street>, <city>, <zip>, <state>"``; ``None`` if anything missing."""
    parts = [street, city, zip_code, state]
    if not all(isinstance(p, str) and p.strip() for p in parts):
        return None
    return ", ".join(str(p).strip() for p in parts)


def step_clean_and_dedup(input_xlsx: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the Excel, add ``clean_address``, and return ``(full_df, unique_df)``."""
    print(f"[1/6] Reading {input_xlsx}")
    df = pd.read_excel(input_xlsx)
    print(f"      rows loaded: {len(df):,}")

    df["clean_street"] = df["block_address"].map(clean_street)
    df["clean_address"] = [
        build_full_address(s, c, z)
        for s, c, z in zip(df["clean_street"], df["city"], df["zip_code"])
    ]
    usable = df["clean_address"].notna()
    n_usable = int(usable.sum())
    print(f"      rows with usable clean_address: {n_usable:,}")
    print(f"      rows missing street/city/zip for geocoding: {len(df) - n_usable:,}")

    unique = (
        df.loc[usable, ["clean_address", "clean_street", "city", "zip_code"]]
        .drop_duplicates(subset=["clean_address"])
        .reset_index(drop=True)
    )
    unique.insert(0, "uid", range(1, len(unique) + 1))
    print(
        f"      unique addresses to geocode: {len(unique):,} "
        f"(from {n_usable:,} rows; {n_usable - len(unique):,} duplicate addresses skipped)"
    )
    return df, unique


def step_make_batches(unique: pd.DataFrame) -> list[Path]:
    """Write Census Geocoder batch CSVs (uid, street, city, state, zip)."""
    print("[2/6] Writing Census Geocoder batch CSVs")
    for old in BATCHES_DIR.glob("batch_*.csv"):
        old.unlink()

    total = len(unique)
    n_batches = (total + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE
    paths: list[Path] = []
    for i in range(n_batches):
        start = i * MAX_BATCH_SIZE
        end = min(start + MAX_BATCH_SIZE, total)
        chunk = unique.iloc[start:end].copy()
        chunk["state"] = STATE
        out_cols = ["uid", "clean_street", "city", "state", "zip_code"]
        path = BATCHES_DIR / f"batch_{i + 1:02d}.csv"
        chunk[out_cols].to_csv(path, index=False, header=False)
        paths.append(path)
        print(
            f"      {path.relative_to(PROJECT_ROOT)} -> {len(chunk):,} rows"
        )
    return paths


def _post_one_batch(batch_path: Path) -> bytes:
    with batch_path.open("rb") as fh:
        files = {"addressFile": (batch_path.name, fh, "text/csv")}
        data = {"benchmark": BENCHMARK}
        resp = requests.post(
            CENSUS_URL, files=files, data=data, timeout=REQUEST_TIMEOUT_S
        )
    resp.raise_for_status()
    return resp.content


def step_submit_batches(batch_paths: list[Path]) -> list[Path]:
    """Submit each batch to the Census Geocoder, saving the CSV response.

    Already-existing response files are reused, so the step is resumable.
    """
    print("[3/6] Submitting batches to Census Geocoder")
    response_paths: list[Path] = []
    for batch_path in batch_paths:
        suffix = batch_path.stem.split("_")[-1]
        out_path = RESPONSES_DIR / f"response_{suffix}.csv"
        if out_path.exists() and out_path.stat().st_size > 0:
            print(
                f"      {out_path.relative_to(PROJECT_ROOT)} already exists; "
                f"skipping ({out_path.stat().st_size:,} bytes)"
            )
            response_paths.append(out_path)
            continue
        print(
            f"      POST {batch_path.name} -> {CENSUS_URL} (this can take a "
            f"few minutes per batch)"
        )
        t0 = time.time()
        content = _post_one_batch(batch_path)
        out_path.write_bytes(content)
        dt = time.time() - t0
        print(
            f"      saved {out_path.relative_to(PROJECT_ROOT)} "
            f"({len(content):,} bytes in {dt:.1f}s)"
        )
        response_paths.append(out_path)
    return response_paths


def step_parse_responses(response_paths: list[Path]) -> pd.DataFrame:
    """Combine response CSVs and extract numeric latitude/longitude."""
    print("[4/6] Parsing Census Geocoder responses")
    frames = []
    for path in response_paths:
        # ``quotechar='"'`` handles the Census-quoted ``input_address``; engine=python
        # is more forgiving with the irregular row widths the service emits.
        df = pd.read_csv(
            path,
            header=None,
            names=CENSUS_RESPONSE_COLS,
            dtype=str,
            quotechar='"',
            engine="python",
            on_bad_lines="warn",
        )
        print(f"      {path.relative_to(PROJECT_ROOT)}: {len(df):,} rows")
        frames.append(df)
    resp = pd.concat(frames, ignore_index=True)

    coords = resp["coordinates"].fillna("")
    split = coords.str.split(",", n=1, expand=True)
    if split.shape[1] == 2:
        resp["longitude"] = pd.to_numeric(split[0], errors="coerce")
        resp["latitude"] = pd.to_numeric(split[1], errors="coerce")
    else:
        resp["longitude"] = pd.NA
        resp["latitude"] = pd.NA

    resp["uid"] = pd.to_numeric(resp["uid"], errors="coerce").astype("Int64")
    matched = (resp["match_indicator"].fillna("").str.lower() == "match").sum()
    print(
        f"      matched: {matched:,} / {len(resp):,} "
        f"({matched / max(len(resp), 1):.1%})"
    )
    return resp


def drop_incidents_without_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with valid ``latitude`` and ``longitude`` for downstream analysis."""
    if "latitude" not in df.columns or "longitude" not in df.columns:
        raise ValueError("DataFrame must contain 'latitude' and 'longitude' columns")

    before = len(df)
    filtered = df.loc[df["latitude"].notna() & df["longitude"].notna()].copy()
    filtered.reset_index(drop=True, inplace=True)
    removed = before - len(filtered)
    print(
        f"      incidents without coordinates removed: {removed:,} "
        f"-> {len(filtered):,} remaining"
    )
    return filtered


def step_merge_back(
    df: pd.DataFrame, unique: pd.DataFrame, resp: pd.DataFrame, output_xlsx: Path
) -> pd.DataFrame:
    """Merge lat/lon back to the original dataframe and write the final Excel."""
    print("[5/6] Merging lat/lon back to the original dataset")
    coords = resp[["uid", "latitude", "longitude", "match_indicator", "matched_address"]]
    unique_geo = unique.merge(coords, on="uid", how="left")

    lookup = (
        unique_geo[["clean_address", "latitude", "longitude"]]
        .drop_duplicates(subset=["clean_address"])
        .set_index("clean_address")
    )
    merged = df.merge(lookup, how="left", left_on="clean_address", right_index=True)
    merged = merged.drop(columns=["clean_street"], errors="ignore")

    have_coords = (merged["latitude"].notna() & merged["longitude"].notna()).sum()
    print(
        f"      after merge: {len(merged):,} rows, "
        f"{have_coords:,} with coordinates, {len(merged) - have_coords:,} without"
    )
    print("      filtering rows without latitude/longitude...")
    merged = drop_incidents_without_coordinates(merged)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    merged.to_excel(output_xlsx, index=False)
    print(f"      output written: {output_xlsx} ({len(merged):,} rows)")
    return merged


def geocode_addresses(
    input_xlsx: str | Path,
    output_xlsx: str | Path = DEFAULT_OUTPUT_XLSX,
) -> pd.DataFrame:
    """Run the full geocoding pipeline for ``input_xlsx`` and return the merged df.

    Parameters
    ----------
    input_xlsx:
        Path to the LMPD incidents Excel file to geocode.
    output_xlsx:
        Path where the final geocoded Excel file will be written.
        Defaults to ``output/LMPD_incidents_2025_geocoded.xlsx``.
    """
    input_path = Path(input_xlsx)
    output_path = Path(output_xlsx)

    _ensure_dirs()

    print("\n--- Geocoding (Census batch API) ---")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")

    df, unique = step_clean_and_dedup(input_path)
    batch_paths = step_make_batches(unique)
    response_paths = step_submit_batches(batch_paths)
    resp = step_parse_responses(response_paths)
    merged = step_merge_back(df, unique, resp, output_path)
    _cleanup_geocoding_artifacts()
    print(f"Geocoding done: {len(merged):,} incidents with coordinates")
    return merged


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_XLSX,
        help="Path to the LMPD incidents Excel file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_XLSX,
        help="Path for the geocoded Excel output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    geocode_addresses(args.input, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
