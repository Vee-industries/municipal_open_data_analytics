import csv
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

REM_PATH = RAW_DIR / "remuneration.csv"


def read_csv_auto(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(10000)
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    return pd.read_csv(path, delimiter=dialect.delimiter, engine="python")


def main():
    print("Reading raw remuneration data...")
    rem = read_csv_auto(REM_PATH)

    print("\n=== YEAR COUNTS IN RAW FILE ===")
    print(rem["Year"].value_counts().sort_index().to_string())

    print("\n=== ENGINEERING DEPARTMENT ROWS BY YEAR ===")
    eng_all = rem[rem["Department"].str.contains("Engineering", case=False, na=False)]
    print(eng_all["Year"].value_counts().sort_index().to_string())

    # Focus on most recent year only
    latest_year = int(rem["Year"].max())
    print(f"\nLatest year in dataset: {latest_year}")

    eng_2025 = eng_all[eng_all["Year"] == latest_year].copy()

    print(f"\nEngineering rows in {latest_year}: {len(eng_2025)}")
    print(f"Distinct employee names in {latest_year}: {eng_2025['Name'].nunique()}")

    # If an employee appears more than once in same year/department, keep highest remuneration row
    eng_2025_dedup = (
        eng_2025
        .sort_values("Remuneration", ascending=False)
        .drop_duplicates(subset=["Name", "Department", "Year"], keep="first")
    )

    print(f"Distinct employees after de-duplication: {len(eng_2025_dedup)}")

    eng_2025_dedup.to_csv(PROCESSED_DIR / "engineering_2025_deduped.csv", index=False)
    print("\nSaved data/processed/engineering_2025_deduped.csv")


if __name__ == "__main__":
    main()