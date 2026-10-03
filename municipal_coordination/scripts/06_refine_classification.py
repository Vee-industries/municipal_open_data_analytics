import pandas as pd
from pathlib import Path


PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

TITLES_FILE = PROCESSED_DIR / "engineering_titles_cleaned.csv"


def classify_title(title: str) -> str:
    """
    Classify title into Execution, Coordination, or Governance.

    This is title-derived inference, not verified reporting lines.
    The classification is deliberately coarse and conservative.
    """
    t = str(title).upper()

    # Governance: senior decision-makers and department heads
    governance_keywords = [
        "DIRECTOR",
        "GENERAL MANAGER",
        "CITY ENGINEER",
        "DEPUTY CITY ENGINEER",
        "DEPUTY GM",
        "ASSOCIATE DIRECTOR",
        "CHIEF ENGINEER",
        "DIR ",
    ]
    if any(k in t for k in governance_keywords):
        return "Governance"

    # Coordination: supervisors, managers, analysts, planners,
    # project managers, foremen, coordinators, branch heads, team leads
    coordination_keywords = [
        "SUPERINTENDENT",
        "SUPERVISOR",
        "FOREMAN",
        "FORMAN",
        "MANAGER",
        "COORDINATOR",
        "ANALYST",
        "PLANNER",
        "PROJECT MANAGER",
        "BRANCH HEAD",
        "SECTION HEAD",
        "TEAM LEAD",
        "ADMINISTRATION",
        "MANAGEMENT",
    ]
    if any(k in t for k in coordination_keywords):
        return "Coordination"

    # Execution: hands-on delivery, trades, technical, inspections,
    # operations, maintenance, and direct public service work
    execution_keywords = [
        "WORKER",
        "OPERATOR",
        "TRADES",
        "JOURNEYMAN",
        "JOURNEYPERSON",
        "TRUCK DRIVER",
        "EQUIPMENT",
        "ENGINEERING ASSISTANT",
        "TECHNICIAN",
        "ENGINEER",
        "SURVEYOR",
        "INSPECTOR",
        "CLERK",
        "PIPELAYER",
        "PAINTER",
        "RAKER",
        "HELPER",
        "LEAD HAND",
        "STOREKEEPER",
        "ACCOUNTANT",
        "SEWER",
        "MACHINIST",
        "CARPENTER",
        "ELECTRICIAN",
        "PLUMBER",
        "OPERATIONS",
        "MAINTENANCE",
        "TRAINEE",
        "SPECIALIST",
        "ADVISOR",
        "ASSISTANT",
    ]
    if any(k in t for k in execution_keywords):
        return "Execution"

    return "Unclassified"


def main():
    print("Loading cleaned Engineering titles...")
    df = pd.read_csv(TITLES_FILE)

    print("Assigning refined title-derived structural layers...")
    df["layer"] = df["normalized_title"].apply(classify_title)

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

    print("\n=== REFINED LAYER COUNTS ===")
    print(df["layer"].value_counts().to_string())

    print("\n=== REFINED LAYER SUMMARY ===")
    print(layer_summary.to_string())

    print("\n=== REMAINING UNCLASSIFIED TITLES ===")
    unclassified = df[df["layer"] == "Unclassified"].sort_values("count", ascending=False)
    print(f"Unclassified unique titles: {len(unclassified)}")
    print(unclassified.head(80).to_string())

    df.to_csv(OUTPUTS_DIR / "engineering_hierarchy_refined.csv", index=False)
    layer_summary.to_csv(OUTPUTS_DIR / "engineering_layer_summary_refined.csv")

    print("\nSaved outputs/engineering_hierarchy_refined.csv")
    print("Saved outputs/engineering_layer_summary_refined.csv")


if __name__ == "__main__":
    main()