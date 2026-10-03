import json
import random
import numpy as np
import pandas as pd
from pathlib import Path


OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Simulation parameters.
# These are assumptions, not measured facts about Vancouver Engineering.
LAYERS = [
    "Frontline Supervisor / Foreman",
    "Superintendent",
    "Senior Branch Head",
    "Director / General Manager",
]

NUM_TICKETS = 500
RANDOM_SEED = 42

# Legacy pipeline parameters
P_TRANSFORM_DEFAULT = 0.20   # probability a layer actually synthesizes
DROP_RATE_DEFAULT = 0.20     # probability each fact is dropped during relay

# Flattened pipeline parameters
P_FLAT_RETAIN = 1.00         # direct automated summarization retains all facts


def generate_ticket(seed):
    """Generate a synthetic infrastructure ticket with known facts."""
    rng = random.Random(seed)
    work_order_id = f"WO-{rng.randint(10000, 99999)}"
    location = rng.choice(["Kingsway", "Main St", "Cambie St", "Broadway", "Hastings St"])
    problem_code = rng.choice(["POTH", "LEAK", "LIGHT", "SIGN", "DRAIN"])
    priority = rng.choice(["P1", "P2", "P3"])
    resource_count = rng.randint(1, 6)

    facts = {
        "work_order_id": work_order_id,
        "location": location,
        "problem_code": problem_code,
        "priority": priority,
        "resource_count": str(resource_count),
    }

    return facts


def run_legacy_pipeline(facts, p_transform, drop_rate, rng):
    """Simulate multi-layer human relay/synthesis."""
    retained = dict(facts)

    for layer in LAYERS:
        if rng.random() < p_transform:
            # Layer synthesizes and preserves all incoming facts.
            continue
        else:
            # Layer relays, dropping facts with probability drop_rate.
            retained = {
                k: v for k, v in retained.items()
                if rng.random() >= drop_rate
            }

    return retained


def run_flattened_pipeline(facts):
    """Simulate direct LLM summarization with fact retention."""
    return dict(facts)


def fact_retention(original, retained):
    """Compute fraction of original facts retained."""
    if not original:
        return 0.0
    retained_keys = set(original.keys()) & set(retained.keys())
    return len(retained_keys) / len(original.keys())


def estimate_output_length(original, retained, pipeline_type):
    """
    Coarse proxy for summarization length.
    Legacy: retained facts plus noise words.
    Flattened: retained facts only.
    """
    if pipeline_type == "legacy":
        return len(retained) + random.randint(2, 8)
    else:
        return len(retained)


def main():
    rng = random.Random(RANDOM_SEED)

    print("Running relay-vs-transform simulation...")
    print(f"Legacy layers: {LAYERS}")
    print(f"Tickets: {NUM_TICKETS}\n")

    rows = []

    for p_transform in [0.00, 0.10, 0.20, 0.30, 0.50]:
        for drop_rate in [0.10, 0.20, 0.30]:
            legacy_retentions = []
            flat_retentions = []
            legacy_lengths = []
            flat_lengths = []

            for i in range(NUM_TICKETS):
                ticket_rng = random.Random(RANDOM_SEED + i)
                facts = generate_ticket(RANDOM_SEED + i)

                legacy_out = run_legacy_pipeline(
                    facts, p_transform=p_transform, drop_rate=drop_rate,
                    rng=ticket_rng,
                )
                flat_out = run_flattened_pipeline(facts)

                legacy_retentions.append(fact_retention(facts, legacy_out))
                flat_retentions.append(fact_retention(facts, flat_out))

                legacy_lengths.append(estimate_output_length(facts, legacy_out, "legacy"))
                flat_lengths.append(estimate_output_length(facts, flat_out, "flattened"))

            row = {
                "p_transform": p_transform,
                "drop_rate": drop_rate,
                "legacy_mean_retention": float(np.mean(legacy_retentions)),
                "flat_mean_retention": float(np.mean(flat_retentions)),
                "retention_delta": float(np.mean(flat_retentions) - np.mean(legacy_retentions)),
                "legacy_mean_output_length": float(np.mean(legacy_lengths)),
                "flat_mean_output_length": float(np.mean(flat_lengths)),
                "legacy_output_below_100_percent": float(
                    np.mean([r < 1.0 for r in legacy_retentions])
                ),
            }
            rows.append(row)

            print(
                f"p_transform={p_transform:.2f}  drop_rate={drop_rate:.2f}  "
                f"legacy_ret={row['legacy_mean_retention']:.3f}  "
                f"flat_ret={row['flat_mean_retention']:.3f}  "
                f"delta={row['retention_delta']:.3f}"
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUTS_DIR / "relay_vs_transform_sim_results.csv", index=False)

    print(f"\nSaved outputs/relay_vs_transform_sim_results.csv")

    # Best/worst legacy settings
    best = df.loc[df["legacy_mean_retention"].idxmax()]
    worst = df.loc[df["legacy_mean_retention"].idxmin()]

    print("\n=== SUMMARY ===")
    print(f"Best legacy retention:  {best['legacy_mean_retention']:.3f} "
          f"at p_transform={best['p_transform']:.2f}, drop_rate={best['drop_rate']:.2f}")
    print(f"Worst legacy retention: {worst['legacy_mean_retention']:.3f} "
          f"at p_transform={worst['p_transform']:.2f}, drop_rate={worst['drop_rate']:.2f}")
    print(f"Flattened retention:    {rows[0]['flat_mean_retention']:.3f} (all settings)")

    print("\nNote: This simulation is illustrative. It does not prove what real")
    print("managers do daily; it only estimates information loss under assumed")
    print("relay probabilities.")


if __name__ == "__main__":
    main()