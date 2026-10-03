import re
import pandas as pd
from pathlib import Path


PROCESSED_DIR = Path("data/processed")
OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

ENG_2025_FILE = PROCESSED_DIR / "engineering_2025_deduped.csv"


def normalize_title(title: str) -> str:
    if not isinstance(title, str):
        return "UNKNOWN"

    t = title.upper().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^A-Z0-9 /]", "", t)
    t = t.replace(" & ", " AND ")
    t = t.replace(" IL", " II").replace(" IIL", " III").replace(" IIII", " IV")
    return t


def classify_title(title: str) -> str:
    t = str(title).upper()

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
    print("Loading deduped 2025 Engineering data...")
    df = pd.read_csv(ENG_2025_FILE)

    print("Normalizing titles...")
    df["normalized_title"] = df["Title"].apply(normalize_title)

    print("Classifying structural layers...")
    df["layer"] = df["normalized_title"].apply(classify_title)

    df["estimated_total_remuneration"] = df["Remuneration"]

    layer_summary = (
        df.groupby("layer")
        .agg(
            unique_titles=("normalized_title", "nunique"),
            total_employees=("Name", "nunique"),
            median_remuneration=("Remuneration", "median"),
            estimated_total_remuneration=("estimated_total_remuneration", "sum"),
        )
        .sort_values("total_employees", ascending=False)
    )

    print("\n=== 2025 DEDUPED LAYER COUNTS ===")
    print(df["layer"].value_counts().to_string())

    print("\n=== 2025 DEDUPED LAYER SUMMARY ===")
    print(layer_summary.to_string())

    print("\n=== UNCLASSIFIED TITLES 2025 ===")
    unclassified = df[df["layer"] == "Unclassified"].sort_values("Remuneration", ascending=False)
    print(f"Unclassified unique titles: {unclassified['normalized_title'].nunique()}")
    print(f"Unclassified employees: {unclassified['Name'].nunique()}")
    print(unclassified.groupby("normalized_title")["Name"].count().sort_values(ascending=False).head(60).to_string())

    df.to_csv(OUTPUTS_DIR / "engineering_hierarchy_2025.csv", index=False)
    layer_summary.to_csv(OUTPUTS_DIR / "engineering_layer_summary_2025.csv")

    print("\nSaved outputs/engineering_hierarchy_2025.csv")
    print("Saved outputs/engineering_layer_summary_2025.csv")


if __name__ == "__main__":
    main()