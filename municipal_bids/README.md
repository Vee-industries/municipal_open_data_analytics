# Non-competitive contract awards, New York City

Predicts which New York City contracts were awarded without competition, and tests whether adding each vendor's past award history improves the prediction.

## Data

- 1,602 contracts from New York City public contract records (`data/raw/contract_amount_modifications.csv`). 963 (60.1%) were awarded without competition.
- Vendor names in the data are businesses.
- Training uses the earlier 70% of contracts by date (1,121) and testing uses the later 30% (481), so the model never sees later contracts. Vendor history features count only awards made before each contract.

## Results

| Model | AUC without vendor history | AUC with vendor history | Gain (500 bootstrap resamples, 95% interval) |
|---|---|---|---|
| Gradient boosting | 0.795 | 0.858 | +0.062 (0.036 to 0.090) |
| Logistic regression | 0.817 | 0.851 | +0.034 (0.016 to 0.053) |

The gain was positive in all 500 resamples for both models.

At a 5% false-positive rate the picture is mixed. Gradient boosting catches more non-competitive awards with vendor history (23% against 10%), while logistic regression catches fewer (16% against 29%). At 10% and 20% false-positive rates, vendor history helps both models.

## Run

```
pip install pandas scikit-learn matplotlib
python scripts/01_audit_award_method.py
python scripts/02_build_competition_dataset.py
python scripts/03_model_competition.py
python scripts/04_competition_roc_fpr.py
python scripts/05_risk_leaderboard.py
python scripts/06_feature_importance.py
python scripts/07_bootstrap_auc_delta.py
```

Run from this folder. Outputs are written to `outputs/`.
