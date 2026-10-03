import csv
import re
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

REM_PATH = RAW_DIR / "remuneration.csv"


def read_csv_auto(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(10000)

    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    delimiter = dialect.delimiter

    print(f"Detected delimiter: {repr(delimiter)}")

    return pd.read_csv(path, delimiter=delimiter, engine="python")


def normalize_title(title: str) -> str:
    """
    Normalize title casing, spacing, punctuation, and common
    Roman numeral / capitalization variants.
    """
    if not isinstance(title, str):
        return "UNKNOWN"

    t = title.upper().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^A-Z0-9 /]", "", t)  # remove punctuation except spaces/slashes
    t = t.replace(" & ", " AND ")

    # Fix common letter-number confusion: IL -> II, IV -> IV, etc.
    t = t.replace(" IL", " II").replace(" IIL", " III").replace(" IIII", " IV")

    return t


def main():
    print("Reading raw remuneration data...")
    rem = read_csv_auto(REM_PATH)

    print("Filtering Engineering Services...")
    eng = rem[rem["Department"].str.contains("Engineering", case=False, na=False)].copy()

    print("Normalizing titles...")
    eng["normalized_title"] = eng["Title"].apply(normalize_title)

    summary = (
        eng.groupby("normalized_title")
        .agg(
            count=("normalized_title", "count"),
            median_remuneration=("Remuneration", "median"),
            original_examples=("Title", lambda s: "; ".join(sorted(set(s))[:3])),
        )
        .sort_values("count", ascending=False)
    )

    print(f"\nUnique normalized titles: {len(summary)}")
    print("\nTop 60 cleaned titles:")
    print(summary.head(60).to_string())

    summary.to_csv(PROCESSED_DIR / "engineering_titles_cleaned.csv")
    print("\nSaved data/processed/engineering_titles_cleaned.csv")


if __name__ == "__main__":
    main()