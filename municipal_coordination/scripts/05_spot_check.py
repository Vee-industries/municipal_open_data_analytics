import pandas as pd
from pathlib import Path


OUTPUTS_DIR = Path("outputs")
HIERARCHY_FILE = OUTPUTS_DIR / "engineering_hierarchy.csv"


def main():
    print("Loading engineering hierarchy...")
    df = pd.read_csv(HIERARCHY_FILE)

    layers = ["Execution", "Coordination", "Governance", "Unclassified"]
    sample_size = 20
    random_state = 42

    for layer in layers:
        subset = df[df["layer"] == layer]
        print(f"\n{'='*80}")
        print(f"LAYER: {layer}  ({len(subset)} unique titles, {subset['count'].sum()} employees)")
        print(f"{'='*80}")

        if subset.empty:
            print("  (no titles)")
            continue

        sample = subset.sample(n=min(sample_size, len(subset)), random_state=random_state)
        sample = sample.sort_values("count", ascending=False)

        for _, row in sample.iterrows():
            print(
                f"  {row['normalized_title'][:50]:<50} "
                f"n={int(row['count']):>5}  "
                f"median=${row['median_remuneration']:>10,.0f}"
            )

    print("\nDone.")


if __name__ == "__main__":
    main()