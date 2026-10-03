import csv
from pathlib import Path

import pandas as pd


RAW_FILE = Path("data/raw/contract_amount_modifications.csv")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_auto(path):
    """Read CSV with auto-detected delimiter and encoding."""
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(100000)

    if not sample.strip():
        raise ValueError(f"{path} is empty")

    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    delimiter = dialect.delimiter

    return pd.read_csv(path, delimiter=delimiter, engine="python")


def main():
    print("Reading contract_amount_modifications.csv ...")
    df = read_csv_auto(RAW_FILE)

    prime = df[df["Vendor Record Type"] == "Prime Vendor"].copy()

    print(f"\nPrime-only rows: {len(prime)}")
    print(f"Unique Prime Contract IDs: {prime['Prime Contract ID'].nunique()}")
    print(f"Duplicate rows after prime filter: {prime.duplicated(subset=['Prime Contract ID']).sum()}")

    print("\n=== PRIME CONTRACT AWARD METHOD VALUE COUNTS ===")
    counts = prime["Prime Contract Award Method"].value_counts(dropna=False)
    print(counts.to_string())

    print("\n=== EXAMPLES BY AWARD METHOD ===")
    for method, grp in prime.groupby("Prime Contract Award Method"):
        print(f"\n--- {method} ---")
        sample = grp.head(3)
        print(sample[[
            "Prime Contract ID",
            "Prime Vendor",
            "Prime Contracting Agency",
            "Prime Contract Original Amount",
            "Prime Contract Registration Date",
        ]].to_string(index=False))

    counts.to_csv(OUTPUTS_DIR / "01_award_method_counts.csv", header=["count"])
    print("\nSaved outputs/01_award_method_counts.csv")


if __name__ == "__main__":
    main()