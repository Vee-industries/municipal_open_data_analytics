import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score


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

    history_cols = [
        "prior_count",
        "prior_same_agency_count",
        "prior_noncompetitive_rate",
        "prior_same_agency_noncomp_rate",
        "prior_max_agency_share",
        "prior_unique_agencies",
        "prior_log_total_original",
    ]

    stateful_cols = myopic_num_cols + myopic_cat_cols + history_cols

    split_idx = int(len(df_encoded) * 0.70)
    train = df_encoded.iloc[:split_idx].copy()
    test = df_encoded.iloc[split_idx:].copy()

    X_train_stateful = train[stateful_cols]
    X_test_stateful = test[stateful_cols]

    y_train = train[TARGET]
    y_test = test[TARGET]

    model = HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.08, random_state=0
    )

    print("Training stateful HistGradientBoosting model ...")
    model.fit(X_train_stateful, y_train)

    auc = float(roc_auc_score(y_test, model.predict_proba(X_test_stateful)[:, 1]))
    print(f"Test AUC: {auc:.4f}")

    print("\nComputing permutation importance on test set ...")
    perm = permutation_importance(
        model,
        X_test_stateful,
        y_test,
        scoring="roc_auc",
        n_repeats=30,
        random_state=0,
        n_jobs=-1,
    )

    importance_df = pd.DataFrame({
        "feature": stateful_cols,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    })

    importance_df = importance_df.sort_values("importance_mean", ascending=False)

    print("\n=== TOP 25 FEATURES BY PERMUTATION IMPORTANCE ===")
    print(importance_df.head(25).to_string(index=False))

    importance_df.to_csv(OUTPUTS_DIR / "feature_importance.csv", index=False)

    print("\nSaved outputs/feature_importance.csv")

    summary = {
        "model": "HistGradientBoostingClassifier",
        "test_auc": auc,
        "top_25_features": importance_df.head(25).to_dict(orient="records"),
    }
    with open(OUTPUTS_DIR / "06_feature_importance_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("Saved outputs/06_feature_importance_summary.json")


if __name__ == "__main__":
    main()