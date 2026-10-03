import pandas as pd
from pathlib import Path


PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

TITLES_FILE = PROCESSED_DIR / "engineering_titles_cleaned.csv"


def classify_title(title: str) -> str:
    """
    Classify a title-derived structural layer.

    This is title-based inference, not verified reporting lines.
    """
    t = str(title).upper()

    # Senior decision-makers
    if any(k in t for k in [
        "DIRECTOR",
        "CHIEF ENGINEER",
        "CITY ENGINEER",
        "GENERAL MANAGER",
        "DEPUTY CITY MANAGER",
    ]):
        return "Governance"

    # Middle management / coordination / supervision
    if any(k in t for k in [
        "SUPERINTENDENT",
        "SUPERVISOR",
        "FOREMAN",
        "PROJECT MANAGER",
        "COORDINATOR",
        "PLANNER",
        "ANALYST",
        "BRANCH HEAD",
        "SENIOR BRANCH HEAD",
    ]):
        return "Coordination"

    # Front-line / execution / hands-on delivery
    if any(k in t for k in [
        "OPERATIONS WORKER",
        "TRADES",
        "JOURNEYMAN",
        "TRUCK DRIVER",
        "EQUIPMENT OPERATOR",
        "ENGINEERING ASSISTANT",
        "TECHNICIAN",
        "CIVIL ENGINEER",
        "SURVEYOR",
        "SEWER SEPARATION EXPEDITER",
        "ENGINEERING DESIGN ASSISTANT",
        "MAINTENANCE COORDINATOR STREETS",
    ]):
        return "Execution"

    return "Unclassified"


def main():
    print("Loading cleaned Engineering titles...")
    df = pd.read_csv(TITLES_FILE)

    print("Assigning title-derived structural layers...")
    df["layer"] = df["normalized_title"].apply(classify_title)

    # Estimated total remuneration per normalized title
    df["estimated_total_remuneration"] = df["count"] * df["median_remuneration"]

    layer_summary = (
        df.groupby("layer")
        .agg(
            unique_titles=("normalized_title", "nunique"),
            total_employees=("count", "sum"),
            median_remuneration=("median_remuneration", "median"),
            estimated_total_remuneration=("estimated_total_remuneration", "sum"),
        )
        .sort_values("total_employees", ascending=False)
    )

    print("\n=== LAYER COUNTS ===")
    print(df["layer"].value_counts().to_string())

    print("\n=== LAYER SUMMARY ===")
    print(layer_summary.to_string())

    print("\n=== UNCLASSIFIED TITLES ===")
    unclassified = df[df["layer"] == "Unclassified"].sort_values("count", ascending=False)
    print(f"Unclassified unique titles: {len(unclassified)}")
    print(unclassified.head(60).to_string())

    df.to_csv(OUTPUTS_DIR / "engineering_hierarchy.csv", index=False)
    layer_summary.to_csv(OUTPUTS_DIR / "engineering_layer_summary.csv")

    print("\nSaved outputs/engineering_hierarchy.csv")
    print("Saved outputs/engineering_layer_summary.csv")


if __name__ == "__main__":
    main()