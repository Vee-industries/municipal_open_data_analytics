import json
from pathlib import Path

import numpy as np
import pandas as pd


PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = PROCESSED_DIR / "contract_competition_base.csv"
OUTPUT_CSV = OUTPUTS_DIR / "vendor_agency_risk_leaderboard.csv"


def main():
    print("Loading competition modeling base ...")
    df = pd.read_csv(INPUT_FILE, parse_dates=["registration_dt"])

    # Aggregate by vendor-agency pair
    print("Aggregating vendor-agency award history ...")

    group = (
        df.groupby(["Prime Vendor", "Prime Contracting Agency"])
        .agg(
            total_awards=("Prime Contract ID", "nunique"),
            non_competitive_awards=("is_non_competitive", "sum"),
            total_original_amount=("Prime Contract Original Amount", lambda s: pd.to_numeric(s, errors="coerce").clip(lower=0).sum()),
            first_award_date=("registration_dt", "min"),
            last_award_date=("registration_dt", "max"),
            distinct_industries=("Prime Contract Industry", "nunique"),
        )
        .reset_index()
    )

    group["non_competitive_rate"] = group["non_competitive_awards"] / group["total_awards"]

    # Keep pairs with at least 2 awards to avoid one-off noise
    repeat = group[group["total_awards"] >= 2].copy()

    # A simple illustrative risk score:
    # higher when non-competitive rate is high and award count / dollars are high.
    repeat["risk_score"] = (
        repeat["non_competitive_rate"]
        * np.log1p(repeat["total_awards"])
        * np.log1p(repeat["total_original_amount"])
    )

    repeat = repeat.sort_values(
        ["risk_score", "non_competitive_rate", "total_awards"],
        ascending=False,
    ).reset_index(drop=True)

    print(f"\nVendor-agency pairs with >=2 awards: {len(repeat)}")
    print(f"Top 25 pairs by non-competitive award concentration:\n")

    top = repeat.head(25)
    for _, row in top.iterrows():
        print(
            f"{row['Prime Vendor'][:45]:<45} | {row['Prime Contracting Agency'][:40]:<40} "
            f"| awards={int(row['total_awards']):>3} "
            f"| noncomp={int(row['non_competitive_awards']):>3} "
            f"| rate={row['non_competitive_rate']:.2f} "
            f"| ${row['total_original_amount']:>15,.0f}"
        )

    repeat.to_csv(OUTPUT_CSV, index=False)

    print(f"\nSaved {OUTPUT_CSV}")

    summary = {
        "total_vendor_agency_pairs": int(len(group)),
        "repeat_pairs_with_2plus_awards": int(len(repeat)),
        "top_25_printed": True,
        "risk_score_definition": (
            "non_competitive_rate * log1p(total_awards) * log1p(total_original_amount)"
        ),
    }

    with open(OUTPUTS_DIR / "05_risk_leaderboard_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Saved outputs/05_risk_leaderboard_summary.json")


if __name__ == "__main__":
    main()