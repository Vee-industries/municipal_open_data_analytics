import pandas as pd
from pathlib import Path


OUTPUTS_DIR = Path("outputs")
LAYER_SUMMARY_FILE = OUTPUTS_DIR / "engineering_layer_summary_refined.csv"
SIM_RESULTS_FILE = OUTPUTS_DIR / "relay_vs_transform_sim_results.csv"
PITCH_FILE = OUTPUTS_DIR / "final_pitch.md"


def pct(part, whole):
    return 100.0 * part / whole if whole else 0.0


def main():
    layer_df = pd.read_csv(LAYER_SUMMARY_FILE)
    sim_df = pd.read_csv(SIM_RESULTS_FILE)

    # Representative simulation setting: 20% synthesis, 20% drop per relay.
    rep = sim_df[(sim_df["p_transform"] == 0.20) & (sim_df["drop_rate"] == 0.20)].iloc[0]

    total_employees = int(layer_df["total_employees"].sum())
    total_remuneration = float(layer_df["estimated_total_remuneration"].sum())

    execution_employees = int(layer_df.loc[layer_df["layer"] == "Execution", "total_employees"].sum())
    coordination_employees = int(layer_df.loc[layer_df["layer"] == "Coordination", "total_employees"].sum())
    governance_employees = int(layer_df.loc[layer_df["layer"] == "Governance", "total_employees"].sum())
    unclassified_employees = int(layer_df.loc[layer_df["layer"] == "Unclassified", "total_employees"].sum())

    execution_pay = float(layer_df.loc[layer_df["layer"] == "Execution", "estimated_total_remuneration"].sum())
    coordination_pay = float(layer_df.loc[layer_df["layer"] == "Coordination", "estimated_total_remuneration"].sum())
    governance_pay = float(layer_df.loc[layer_df["layer"] == "Governance", "estimated_total_remuneration"].sum())
    unclassified_pay = float(layer_df.loc[layer_df["layer"] == "Unclassified", "estimated_total_remuneration"].sum())

    pitch = f"""# Municipal Coordination Compression Audit

## Summary

We measured the title-derived structural depth of the City of Vancouver's Engineering Services department and simulated how much frontline operational information survives a multi-layer management routing pipeline compared to a flattened automated routing pipeline.

This is a measurement study, not a recommendation to eliminate any specific roles.

## Data

- Source: City of Vancouver Open Data Portal
- Files:
  - Employee remuneration and expenses earning over $75,000
  - Workforce pay rates and sex
- Department: Engineering Services
- Year: 2025
- Employees in dataset: {total_employees}

## Title-Derived Layer Classification

We classified 430 normalized titles into three structural layers using keyword rules. This is title-based inference, not verified reporting lines.

| Layer | Employees | % Employees | Estimated Total Remuneration | % Remuneration |
|---|---:|---:|---:|---:|
| Execution | {execution_employees} | {pct(execution_employees, total_employees):.1f}% | ${execution_pay:,.0f} | {pct(execution_pay, total_remuneration):.1f}% |
| Coordination | {coordination_employees} | {pct(coordination_employees, total_employees):.1f}% | ${coordination_pay:,.0f} | {pct(coordination_pay, total_remuneration):.1f}% |
| Governance | {governance_employees} | {pct(governance_employees, total_employees):.1f}% | ${governance_pay:,.0f} | {pct(governance_pay, total_remuneration):.1f}% |
| Unclassified | {unclassified_employees} | {pct(unclassified_employees, total_employees):.1f}% | ${unclassified_pay:,.0f} | {pct(unclassified_pay, total_remuneration):.1f}% |

The coordination layer represents about {pct(coordination_employees, total_employees):.0f}% of employees and {pct(coordination_pay, total_remuneration):.0f}% of estimated remuneration.

## Relay-vs-Transform Simulation

We simulated 500 synthetic infrastructure tickets. Each ticket contained five known facts: work order ID, location, problem code, priority, and resource count.

The legacy pipeline passed tickets through four inferred management layers. Each layer either:

- synthesized and preserved all incoming facts, or
- relayed and probabilistically dropped facts.

The flattened pipeline assumed an automated summarizer that retained all facts.

This simulation is illustrative. It does not prove what real managers do daily. It only estimates information loss under explicit relay assumptions.

### Result at 20% synthesis probability, 20% drop rate per relay layer

| Pipeline | Mean Fact Retention |
|---|---:|
| Legacy multi-layer | {rep['legacy_mean_retention']:.3f} |
| Flattened automated | {rep['flat_mean_retention']:.3f} |
| Difference | {rep['retention_delta']:.3f} |

Across all simulated settings, legacy retention ranged from 0.239 to 0.824, depending on assumptions. Flattened retention was assumed perfect at 1.000.

## What this does and does not show

**Shows:**

- Title-derived coordination depth is measurable from open data.
- Under explicit relay-loss assumptions, multi-layer routing drops frontline information.
- A flattened automated routing pipeline could preserve more information.

**Does not show:**

- That the flattened pipeline produces better decisions.
- That all coordination roles are redundant.
- That any specific real Vancouver manager is unnecessary.

The flattened pipeline's 100% retention is an optimistic assumption. A real summarization system may also lose or distort information.

## Limitations

1. Titles are a proxy for hierarchy, not verified reporting lines.
2. Title classification is keyword-based and may contain errors.
3. {unclassified_employees} employees ({pct(unclassified_employees, total_employees):.1f}% of department) remained unclassified.
4. The simulation uses synthetic tickets and assumed relay probabilities.
5. We did not evaluate decision quality, only fact retention.

## Next Steps

- Validate title classification against a real org chart.
- Run the simulation on real ticket data.
- Replace the perfect summarizer assumption with a real LLM pipeline.
- Measure fact retention on actual summarization outputs.

---

This is a preliminary measurement, not a policy recommendation.
"""

    PITCH_FILE.write_text(pitch, encoding="utf-8")
    print(f"Saved {PITCH_FILE}")


if __name__ == "__main__":
    main()