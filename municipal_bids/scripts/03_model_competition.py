import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

MODELING_FILE = PROCESSED_DIR / "contract_competition_base.csv"
TARGET = "is_non_competitive"


def load_dataset():
    df = pd.read_csv(MODELING_FILE, parse_dates=["registration_dt"])
    df = df.sort_values("registration_dt").reset_index(drop=True)
    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce").fillna(0).astype(int)
    return df


def encode_categoricals(df, max_agency=25, max_industry=15):
    out = df.copy()

    top_agencies = out["Prime Contracting Agency"].value_counts().head(max_agency).index
    agency_cat = out["Prime Contracting Agency"].where(
        out["Prime Contracting Agency"].isin(top_agencies), "OTHER_AGENCY"
    )
    agency_dummies = pd.get_dummies(agency_cat, prefix="agency", dummy_na=False)

    top_industries = out["Prime Contract Industry"].value_counts().head(max_industry).index
    industry_cat = out["Prime Contract Industry"].where(
        out["Prime Contract Industry"].isin(top_industries), "OTHER_INDUSTRY"
    )
    industry_dummies = pd.get_dummies(industry_cat, prefix="industry", dummy_na=False)

    encoded = pd.concat([out, agency_dummies, industry_dummies], axis=1)
    return encoded


def main():
    print("Loading competition modeling base ...")
    df = load_dataset()
    print(f"Rows: {len(df)}")
    print(f"Non-competitive rate: {df[TARGET].mean():.3f}")

    df_encoded = encode_categoricals(df)

    myopic_num_cols = [
        "log_original_amount",
        "vendor_mwbe_flag",
        "woman_owned_flag",
        "emerging_business_flag",
    ]

    myopic_cat_cols = [
        c for c in df_encoded.columns
        if (
            c.startswith(("agency_", "industry_"))
            and c not in {"Prime Contracting Agency", "Prime Contract Industry"}
        )
    ]

    myopic_cols = myopic_num_cols + myopic_cat_cols

    stateful_cols = myopic_cols + [
        "prior_count",
        "prior_same_agency_count",
        "prior_noncompetitive_rate",
        "prior_same_agency_noncomp_rate",
        "prior_max_agency_share",
        "prior_unique_agencies",
        "prior_log_total_original",
    ]

    split_idx = int(len(df_encoded) * 0.70)
    train = df_encoded.iloc[:split_idx].copy()
    test = df_encoded.iloc[split_idx:].copy()

    print(f"\nTrain rows: {len(train)}")
    print(f"Test rows: {len(test)}")

    X_train_myopic = train[myopic_cols]
    X_test_myopic = test[myopic_cols]

    X_train_stateful = train[stateful_cols]
    X_test_stateful = test[stateful_cols]

    y_train = train[TARGET]
    y_test = test[TARGET]

    print(f"Train positive rate: {y_train.mean():.3f}")
    print(f"Test positive rate: {y_test.mean():.3f}")

    factories = {
        "LogisticRegression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0),
        ),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.08, random_state=0
        ),
    }

    results = []

    for model_name, factory in factories.items():
        print(f"\n=== {model_name} ===")

        # Myopic
        model_myopic = clone(factory)
        model_myopic.fit(X_train_myopic, y_train)

        if hasattr(model_myopic, "predict_proba"):
            myopic_scores = model_myopic.predict_proba(X_test_myopic)[:, 1]
        else:
            d = model_myopic.decision_function(X_test_myopic)
            myopic_scores = 1.0 / (1.0 + np.exp(-d))

        # Stateful
        model_stateful = clone(factory)
        model_stateful.fit(X_train_stateful, y_train)

        if hasattr(model_stateful, "predict_proba"):
            stateful_scores = model_stateful.predict_proba(X_test_stateful)[:, 1]
        else:
            d = model_stateful.decision_function(X_test_stateful)
            stateful_scores = 1.0 / (1.0 + np.exp(-d))

        auc_myopic = (
            float(roc_auc_score(y_test, myopic_scores))
            if y_test.nunique() > 1
            else float("nan")
        )
        auc_stateful = (
            float(roc_auc_score(y_test, stateful_scores))
            if y_test.nunique() > 1
            else float("nan")
        )

        delta = auc_stateful - auc_myopic

        print(f"Myopic AUC: {auc_myopic:.4f}")
        print(f"Stateful AUC: {auc_stateful:.4f}")
        print(f"AUC delta: {delta:.4f}")

        results.append({
            "model": model_name,
            "myopic_auc": auc_myopic,
            "stateful_auc": auc_stateful,
            "auc_delta": delta,
            "test_positive_rate": float(y_test.mean()),
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUTS_DIR / "competition_results.csv", index=False)

    print("\n=== COMPETITION RISK RESULTS ===")
    print(results_df.to_string(index=False))

    with open(OUTPUTS_DIR / "03_competition_summary.json", "w") as f:
        json.dump({
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "results": results_df.to_dict(orient="records"),
        }, f, indent=2)

    print("\nSaved outputs/competition_results.csv")
    print("Saved outputs/03_competition_summary.json")


if __name__ == "__main__":
    main()