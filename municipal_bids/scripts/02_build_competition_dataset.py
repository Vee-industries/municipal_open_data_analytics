import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "contract_amount_modifications.csv"
OUT_FILE = PROCESSED_DIR / "contract_competition_base.csv"

NON_COMPETITIVE_METHODS = {
    "SOLE SOURCE",
    "NEGOTIATED ACQUISITION AND DOE NEGOTIATED SERVICES",
    "NEG ACQUISITSION  EXTN AND DOE NEGOTIATED SERVICES EXTN",
    "LESSEE NEGOTIATION",
    "DETERMINED BY GOV'T MANDATE",
    "INTERGOVERNMENTAL PROCUREMENT",
    "INTERGOVERNMENTAL PROCUREMENT RENEWAL",
    "GOVERNMENT TO GOVERNMENT",
    "BORO NEEDS/DISCRETIONARY FUND",
    "EMERGENCY",
    "FORCE ACCOUNT NEGOTIATION",
    "PUBLIC UTILITY",
    "CABLE SERVICE NEGOTIATION",
    "RENEWAL OF CONTRACT",
    "DEMONSTRATION PROJECT",
    "INNOVATIVE PROCUREMENT",
    "SUBSCRIPTION ETC PER PPB",
    "REAL ESTATE SALES AND PURCHASES",
}

COMPETITIVE_METHODS = {
    "COMPETITIVE SEALED BIDDING",
    "REQUEST FOR  PROPOSAL (RFP)",
    "RFP FROM A PQVL",
    "PQVL COMPETITVE BID LIST",
}


def read_csv_auto(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        sample = f.read(100000)
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    return pd.read_csv(path, delimiter=dialect.delimiter, engine="python")


def main():
    print("Reading raw contract modifications ...")
    df = read_csv_auto(RAW_FILE)

    print("Filtering prime vendor rows ...")
    prime = df[df["Vendor Record Type"] == "Prime Vendor"].copy()

    print(f"Prime-only rows: {len(prime)}")
    print(f"Unique Prime Contract IDs: {prime['Prime Contract ID'].nunique()}")

    # Parse registration date
    prime["registration_dt"] = pd.to_datetime(
        prime["Prime Contract Registration Date"], errors="coerce"
    )

    # Drop rows missing date
    prime = prime.dropna(subset=["registration_dt"]).copy()
    print(f"Rows after date parse: {len(prime)}")

    # Define competition label
    method = prime["Prime Contract Award Method"].str.strip().str.upper()
    prime["method_clean"] = method

    prime["is_non_competitive"] = (
        method.isin([m.upper() for m in NON_COMPETITIVE_METHODS])
    ).astype(int)

    # Keep only clean competitive/non-competitive rows
    method_is_competitive = method.isin([m.upper() for m in COMPETITIVE_METHODS])
    method_is_noncomp = prime["is_non_competitive"] == 1
    prime = prime[method_is_competitive | method_is_noncomp].copy()

    print(f"Rows after competitive/non-competitive filter: {len(prime)}")
    print(f"Non-competitive positive rate: {prime['is_non_competitive'].mean():.3f}")

    # Features
    orig = pd.to_numeric(prime["Prime Contract Original Amount"], errors="coerce")
    prime["log_original_amount"] = np.log1p(orig.clip(lower=0))

    prime["vendor_mwbe_flag"] = (
        prime["Prime Vendor M/WBE Category"].str.strip().str.upper() != "NON-M/WBE"
    ).astype(int)

    prime["woman_owned_flag"] = (
        prime["Prime Woman Owned Business"].str.strip().str.upper() == "YES"
    ).astype(int)

    prime["emerging_business_flag"] = (
        prime["Prime Emerging Business"].str.strip().str.upper() == "YES"
    ).astype(int)

    # Sort for temporal history
    prime = prime.sort_values(
        ["Prime Vendor", "registration_dt", "Prime Contract ID"],
        kind="mergesort",
    ).reset_index(drop=True)

    print("Building vendor-agency temporal history features ...")

    history_rows = []
    for vendor, grp in prime.groupby("Prime Vendor", sort=False):
        grp = grp.reset_index(drop=True)

        for i in range(len(grp)):
            current_dt = grp.loc[i, "registration_dt"]
            prior_mask = grp["registration_dt"] < current_dt
            prior = grp.loc[prior_mask]

            n_prior = len(prior)

            if n_prior > 0:
                prior_same_agency = prior[
                    prior["Prime Contracting Agency"] == grp.loc[i, "Prime Contracting Agency"]
                ]

                prior_noncompetitive_rate = float(prior["is_non_competitive"].mean())
                prior_same_agency_noncomp_rate = float(
                    prior_same_agency["is_non_competitive"].mean()
                ) if len(prior_same_agency) > 0 else 0.0

                if n_prior >= 2:
                    agency_shares = prior["Prime Contracting Agency"].value_counts(normalize=True)
                    prior_max_agency_share = float(agency_shares.max())
                else:
                    prior_max_agency_share = 1.0

                prior_unique_agencies = int(prior["Prime Contracting Agency"].nunique())

                prior_log_total_original = float(
                    np.log1p(
                        pd.to_numeric(
                            prior["Prime Contract Original Amount"], errors="coerce"
                        ).clip(lower=0).sum()
                    )
                )
            else:
                prior_noncompetitive_rate = 0.0
                prior_same_agency_noncomp_rate = 0.0
                prior_max_agency_share = 0.0
                prior_unique_agencies = 0
                prior_log_total_original = 0.0

            history_rows.append({
                "prior_count": n_prior,
                "prior_same_agency_count": int(len(prior_same_agency)) if n_prior > 0 else 0,
                "prior_noncompetitive_rate": prior_noncompetitive_rate,
                "prior_same_agency_noncomp_rate": prior_same_agency_noncomp_rate,
                "prior_max_agency_share": prior_max_agency_share,
                "prior_unique_agencies": prior_unique_agencies,
                "prior_log_total_original": prior_log_total_original,
            })

    history_df = pd.DataFrame(history_rows)
    prime = pd.concat([prime, history_df], axis=1)

    # Drop duplicate columns just in case
    prime = prime.loc[:, ~prime.columns.duplicated()].copy()

    keep_cols = [
        "Prime Contract ID",
        "Prime Vendor",
        "Prime Contracting Agency",
        "Prime Contract Industry",
        "Prime Contract Award Method",
        "Prime Contract Original Amount",
        "Prime Contract Registration Date",
        "registration_dt",
        "is_non_competitive",
        "log_original_amount",
        "vendor_mwbe_flag",
        "woman_owned_flag",
        "emerging_business_flag",
        "prior_count",
        "prior_same_agency_count",
        "prior_noncompetitive_rate",
        "prior_same_agency_noncomp_rate",
        "prior_max_agency_share",
        "prior_unique_agencies",
        "prior_log_total_original",
    ]
    prime = prime[[c for c in keep_cols if c in prime.columns]]

    prime.to_csv(OUT_FILE, index=False)
    print(f"Saved {OUT_FILE} with {len(prime)} rows")

    summary = {
        "rows": len(prime),
        "noncompetitive_rate": float(prime["is_non_competitive"].mean()),
        "competitive_count": int((prime["is_non_competitive"] == 0).sum()),
        "noncompetitive_count": int((prime["is_non_competitive"] == 1).sum()),
        "prior_count_zero_rate": float((prime["prior_count"] == 0).mean()),
        "prior_count_median": float(prime["prior_count"].median()),
        "excluded_ambiguous_rows": int(
            len(prime) - prime["is_non_competitive"].sum() - (prime["is_non_competitive"] == 0).sum()
        ),
    }
    with open(OUTPUTS_DIR / "02_competition_dataset_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Saved outputs/02_competition_dataset_summary.json")


if __name__ == "__main__":
    main()