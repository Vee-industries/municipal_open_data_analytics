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

    X_train_myopic = train[myopic_cols]
    X_test_myopic = test[myopic_cols]

    X_train_stateful = train[stateful_cols]
    X_test_stateful = test[stateful_cols]

    y_train = train[TARGET]
    y_test = test[TARGET]

    factories = {
        "LogisticRegression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, C=1.0),
        ),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.08, random_state=0
        ),
    }

    bootstrap_rows = []

    n_boot = 500
    rng = np.random.default_rng(42)

    n_test = len(test)
    test_idx = np.arange(n_test)

    for model_name, factory in factories.items():
        print(f"\n=== {model_name} ===")

        model_myopic = clone(factory)
        model_myopic.fit(X_train_myopic, y_train)
        myopic_scores = (
            model_myopic.predict_proba(X_test_myopic)[:, 1]
            if hasattr(model_myopic, "predict_proba")
            else 1.0 / (1.0 + np.exp(-model_myopic.decision_function(X_test_myopic)))
        )

        model_stateful = clone(factory)
        model_stateful.fit(X_train_stateful, y_train)
        stateful_scores = (
            model_stateful.predict_proba(X_test_stateful)[:, 1]
            if hasattr(model_stateful, "predict_proba")
            else 1.0 / (1.0 + np.exp(-model_stateful.decision_function(X_test_stateful)))
        )

        y_test_arr = y_test.to_numpy()

        deltas = []

        for _ in range(n_boot):
            idx = rng.integers(0, n_test, size=n_test)

            y_boot = y_test_arr[idx]
            myopic_boot = myopic_scores[idx]
            stateful_boot = stateful_scores[idx]

            if np.unique(y_boot).size < 2:
                continue

            auc_myopic = roc_auc_score(y_boot, myopic_boot)
            auc_stateful = roc_auc_score(y_boot, stateful_boot)

            deltas.append(auc_stateful - auc_myopic)

        deltas = np.array(deltas)

        lo = float(np.quantile(deltas, 0.025))
        med = float(np.quantile(deltas, 0.50))
        hi = float(np.quantile(deltas, 0.975))
        pct_positive = float(np.mean(deltas > 0))

        print(f"Bootstrap AUC delta: median={med:.4f}, 95% CI=[{lo:.4f}, {hi:.4f}]")
        print(f"Percent of bootstraps positive: {pct_positive:.1%}")

        bootstrap_rows.append({
            "model": model_name,
            "auc_delta_median": med,
            "auc_delta_ci_low": lo,
            "auc_delta_ci_high": hi,
            "pct_positive": pct_positive,
            "n_bootstraps": int(len(deltas)),
        })

    results_df = pd.DataFrame(bootstrap_rows)
    results_df.to_csv(OUTPUTS_DIR / "bootstrap_auc_delta.csv", index=False)

    print("\n=== BOOTSTRAP AUC DELTA RESULTS ===")
    print(results_df.to_string(index=False))

    with open(OUTPUTS_DIR / "07_bootstrap_auc_delta_summary.json", "w") as f:
        json.dump({
            "results": results_df.to_dict(orient="records"),
            "n_bootstraps": n_boot,
        }, f, indent=2)

    print("\nSaved outputs/bootstrap_auc_delta.csv")
    print("Saved outputs/07_bootstrap_auc_delta_summary.json")


if __name__ == "__main__":
    main()