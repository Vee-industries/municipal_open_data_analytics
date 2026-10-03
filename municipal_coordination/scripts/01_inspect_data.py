import csv
import pandas as pd
from pathlib import Path


RAW_DIR = Path("data/raw")

REM_PATH = RAW_DIR / "remuneration.csv"
PAY_PATH = RAW_DIR / "pay_rates.csv"


def read_csv_auto(path: Path) -> pd.DataFrame:
    """
    Read a CSV using auto-detected delimiter and encoding.
    Handles comma, semicolon, and tab-separated files.
    """
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(10000)

    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    delimiter = dialect.delimiter

    print(f"Detected delimiter for {path.name}: {repr(delimiter)}")

    return pd.read_csv(path, delimiter=delimiter, engine="python")


def main():
    print("Reading raw Vancouver open data...\n")

    rem = read_csv_auto(REM_PATH)
    pay = read_csv_auto(PAY_PATH)

    print("\n=== REMUNERATION ===")
    print("Rows:", len(rem))
    print("Columns:", list(rem.columns))
    print("\nFirst 3 rows:")
    print(rem.head(3))

    print("\n=== PAY RATES ===")
    print("Rows:", len(pay))
    print("Columns:", list(pay.columns))
    print("\nFirst 3 rows:")
    print(pay.head(3))


if __name__ == "__main__":
    main()