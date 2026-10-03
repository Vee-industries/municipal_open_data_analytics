import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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


def pick_threshold_at_fpr(y_true, scores, target_fpr):
    """
    Pick the threshold that maximizes TPR while keeping FPR <= target_fpr.
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    # Candidate thresholds are all unique scores plus sentinels.
    thresholds = np.unique(scores)

    best = None

    for thr in thresholds:
        pred = (scores >= thr).astype(int)

        fp = int(np.sum((pred == 1) & (y_true == 0)))
        tp = int(np.sum((pred == 1) & (y_true == 1)))
        n_neg = int(np.sum(y_true == 0))
        n_pos = int(np.sum(y_true == 1))

        fpr = fp / n_neg if n_neg > 0 else 0.0
        tpr = tp / n_pos if n_pos > 0 else 0.0

        if fpr <= target_fpr:
            if best is None or tpr > best["tpr"]:
                best = {
                    "threshold": float(thr),
                    "tpr": tpr,
                    "fpr": fpr,
                }

    if best is None:
        best = {
            "threshold": float(np.max(scores)),
            "tpr": 0.0,
            "fpr": 0.0,
        }

    return best


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

    plot_scores = {}
    threshold_results = []

    for model_name, factory in factories.items():
        print(f"\n=== {model_name} ===")

        # Myopic
        model_myopic = clone(factory)
        model_myopic.fit(X_train_myopic, y_train)
        myopic_scores = (
            model_myopic.predict_proba(X_test_myopic)[:, 1]
            if hasattr(model_myopic, "predict_proba")
            else 1.0 / (1.0 + np.exp(-model_myopic.decision_function(X_test_myopic)))
        )

        # Stateful
        model_stateful = clone(factory)
        model_stateful.fit(X_train_stateful, y_train)
        stateful_scores = (
            model_stateful.predict_proba(X_test_stateful)[:, 1]
            if hasattr(model_stateful, "predict_proba")
            else 1.0 / (1.0 + np.exp(-model_stateful.decision_function(X_test_stateful)))
        )

        plot_scores[model_name] = {
            "y_true": y_test.values,
            "myopic_scores": myopic_scores,
            "stateful_scores": stateful_scores,
        }

        # ROC curves
        fpr_myopic, tpr_myopic, _ = roc_curve(y_test, myopic_scores)
        fpr_stateful, tpr_stateful, _ = roc_curve(y_test, stateful_scores)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr_myopic, tpr_myopic, label=f"Myopic AUC={roc_auc_score(y_test, myopic_scores):.3f}")
        plt.plot(fpr_stateful, tpr_stateful, label=f"Stateful AUC={roc_auc_score(y_test, stateful_scores):.3f}")
        plt.plot([0, 1], [0, 1], linestyle="--", color="grey", alpha=0.4)
        plt.xlabel("False positive rate")
        plt.ylabel("True positive rate")
        plt.title(f"ROC: {model_name}")
        plt.legend()
        plt.grid(alpha=0.2)
        plt.tight_layout()
        safe_name = model_name.replace("/", "_")
        plt.savefig(OUTPUTS_DIR / f"roc_{safe_name}.png", dpi=150)
        plt.close()

        for target_fpr in [0.05, 0.10, 0.20]:
            row = {"model": model_name, "target_fpr": target_fpr}

            for label, scores in [("myopic", myopic_scores), ("stateful", stateful_scores)]:
                best = pick_threshold_at_fpr(y_test, scores, target_fpr)

                row[f"{label}_threshold"] = best["threshold"]
                row[f"{label}_tpr"] = best["tpr"]
                row[f"{label}_fpr"] = best["fpr"]

            threshold_results.append(row)

            print(
                f"Target FPR={target_fpr:.2f}: "
                f"Myopic TPR={row['myopic_tpr']:.3f} at FPR={row['myopic_fpr']:.4f} | "
                f"Stateful TPR={row['stateful_tpr']:.3f} at FPR={row['stateful_fpr']:.4f}"
            )

    results_df = pd.DataFrame(threshold_results)
    results_df.to_csv(OUTPUTS_DIR / "competition_matched_fpr.csv", index=False)

    print("\n=== MATCHED-FPR RESULTS ===")
    print(results_df.to_string(index=False))

    with open(OUTPUTS_DIR / "04_competition_roc_fpr_summary.json", "w") as f:
        json.dump({
            "threshold_results": results_df.to_dict(orient="records"),
            "roc_figures_saved": True,
        }, f, indent=2)

    print("\nSaved outputs/competition_matched_fpr.csv")
    print("Saved outputs/04_competition_roc_fpr_summary.json")


if __name__ == "__main__":
    main()