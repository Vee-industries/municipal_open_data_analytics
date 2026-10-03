import csv
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

    print(f"Detected delimiter for {path.name}: {repr(delimiter)}")

    return pd.read_csv(path, delimiter=delimiter, engine="python")


def main():
    rem = read_csv_auto(REM_PATH)

    print("\n=== TOP DEPARTMENTS BY ROW COUNT ===")
    top_departments = (
        rem.groupby("Department")["Title"]
        .count()
        .sort_values(ascending=False)
        .head(20)
    )
    print(top_departments.to_string())

    print("\n=== ENGINEERING SERVICES: TITLE COUNTS AND MEDIAN PAY ===")
    eng = rem[rem["Department"].str.contains("Engineering", case=False, na=False)].copy()

    if eng.empty:
        print("No department containing 'Engineering' found.")
        return

    eng_summary = (
        eng.groupby("Title")
        .agg(
            count=("Title", "count"),
            median_remuneration=("Remuneration", "median"),
        )
        .sort_values("count", ascending=False)
    )

    print(f"Rows in Engineering department(s): {len(eng)}")
    print(f"Unique titles: {eng['Title'].nunique()}")
    print("\nTop 40 titles:")
    print(eng_summary.head(40).to_string())

    eng.to_csv(PROCESSED_DIR / "engineering_titles_raw.csv", index=False)
    print("\nSaved raw Engineering titles to data/processed/engineering_titles_raw.csv")


if __name__ == "__main__":
    main()