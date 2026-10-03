import json
import random
import numpy as np
import pandas as pd
from pathlib import Path


OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

LAYERS = [
    "Frontline Supervisor / Foreman",
    "Superintendent",
    "Senior Branch Head",
    "Director / General Manager",
]

NUM_TICKETS = 500
RANDOM_SEED = 42


def generate_ticket(seed):
    rng = random.Random(seed)
    facts = {
        "work_order_id": f"WO-{rng.randint(10000, 99999)}",
        "location": rng.choice(["Kingsway", "Main St", "Cambie St", "Broadway", "Hastings St"]),
        "problem_code": rng.choice(["POTH", "LEAK", "LIGHT", "SIGN", "DRAIN"]),
        "priority": rng.choice(["P1", "P2", "P3"]),
        "resource_count": str(rng.randint(1, 6)),
    }
    return facts


def run_legacy_pipeline(facts, p_transform, drop_rate, rng):
    retained = dict(facts)
    for _ in LAYERS:
        if rng.random() < p_transform:
            continue
        else:
            retained = {
                k: v for k, v in retained.items()
                if rng.random() >= drop_rate
            }
    return retained


def run_flattened_pipeline(facts, flat_drop_rate, rng):
    """
    Flattened automated pipeline with realistic summarization loss.
    Assumes LLM summarizer drops a small fraction of facts, especially
    numeric details.
    """
    retained = dict(facts)
    retained = {
        k: v for k, v in retained.items()
        if rng.random() >= flat_drop_rate
    }
    return retained


def fact_retention(original, retained):
    if not original:
        return 0.0
    return len(set(original.keys()) & set(retained.keys())) / len(original.keys())


def main():
    rng = random.Random(RANDOM_SEED)

    print("Running corrected relay-vs-transform simulation...")
    print(f"Legacy layers: {LAYERS}")
    print(f"Tickets: {NUM_TICKETS}\n")

    rows = []

    for flat_drop_rate in [0.00, 0.05, 0.10]:
        for p_transform in [0.00, 0.10, 0.20, 0.30, 0.50]:
            for drop_rate in [0.10, 0.20, 0.30]:
                legacy_retentions = []
                flat_retentions = []

                for i in range(NUM_TICKETS):
                    ticket_rng = random.Random(RANDOM_SEED + i)
                    facts = generate_ticket(RANDOM_SEED + i)

                    legacy_out = run_legacy_pipeline(
                        facts,
                        p_transform=p_transform,
                        drop_rate=drop_rate,
                        rng=ticket_rng,
                    )
                    flat_out = run_flattened_pipeline(
                        facts,
                        flat_drop_rate=flat_drop_rate,
                        rng=ticket_rng,
                    )

                    legacy_retentions.append(fact_retention(facts, legacy_out))
                    flat_retentions.append(fact_retention(facts, flat_out))

                row = {
                    "flat_drop_rate": flat_drop_rate,
                    "p_transform": p_transform,
                    "drop_rate": drop_rate,
                    "legacy_mean_retention": float(np.mean(legacy_retentions)),
                    "flat_mean_retention": float(np.mean(flat_retentions)),
                    "retention_delta": float(np.mean(flat_retentions) - np.mean(legacy_retentions)),
                }
                rows.append(row)

                print(
                    f"flat_drop={flat_drop_rate:.2f}  p_transform={p_transform:.2f}  "
                    f"legacy_drop={drop_rate:.2f}  legacy_ret={row['legacy_mean_retention']:.3f}  "
                    f"flat_ret={row['flat_mean_retention']:.3f}  delta={row['retention_delta']:.3f}"
                )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUTS_DIR / "relay_vs_transform_sim_corrected.csv", index=False)
    print(f"\nSaved outputs/relay_vs_transform_sim_corrected.csv")

    # Representative setting with imperfect flat pipeline
    rep = df[(df["flat_drop_rate"] == 0.05) &
             (df["p_transform"] == 0.20) &
             (df["drop_rate"] == 0.20)].iloc[0]

    print("\n=== CORRECTED SUMMARY ===")
    print(f"At flat_drop_rate=0.05, p_transform=0.20, legacy_drop_rate=0.20:")
    print(f"Legacy retention:  {rep['legacy_mean_retention']:.3f}")
    print(f"Flattened retention: {rep['flat_mean_retention']:.3f}")
    print(f"Delta: {rep['retention_delta']:.3f}")

    print("\nNote: The flattened pipeline is now imperfect, with realistic")
    print("summarization loss. It still retains more information than the")
    print("legacy pipeline under these assumptions.")


if __name__ == "__main__":
    main()