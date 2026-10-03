import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

SIM_FILE = OUTPUTS_DIR / "relay_vs_transform_sim_corrected.csv"
HIERARCHY_FILE = OUTPUTS_DIR / "engineering_hierarchy_2025.csv"

L = 4  # legacy routing layers


def main():
    # ------------------------------------------------------------------
    # 1. Compare simulation to analytic retention model
    # ------------------------------------------------------------------
    print("Loading simulation results...")
    sim = pd.read_csv(SIM_FILE)

    print("\n=== ANALYTIC VS SIMULATED RETENTION ===")
    rows = []
    for _, r in sim.iterrows():
        s = r["p_transform"]
        d = r["drop_rate"]
        d_f = r["flat_drop_rate"]

        q = 1 - (1 - s) * d
        analytic_legacy = q ** L
        analytic_flat = 1 - d_f

        rows.append({
            "flat_drop_rate": d_f,
            "p_transform": s,
            "drop_rate": d,
            "sim_legacy": r["legacy_mean_retention"],
            "analytic_legacy": analytic_legacy,
            "sim_flat": r["flat_mean_retention"],
            "analytic_flat": analytic_flat,
            "legacy_gap": r["legacy_mean_retention"] - analytic_legacy,
            "flat_gap": r["flat_mean_retention"] - analytic_flat,
        })

    compare = pd.DataFrame(rows)
    print(compare.head(10).to_string(index=False))

    # Expected standard error under per-fact independence
    compare["se_legacy_indep"] = np.sqrt(
        analytic_legacy * (1 - analytic_legacy) / (500 * 5)
    )
    compare["gap_in_se_indep"] = compare["legacy_gap"] / compare["se_legacy_indep"]

    # Expected standard error under per-layer correlated decisions
    compare["se_legacy_corr"] = np.sqrt(
        analytic_legacy * (1 - analytic_legacy) / 500
    )
    compare["gap_in_se_corr"] = compare["legacy_gap"] / compare["se_legacy_corr"]

    # Representative row
    rep = compare[
        (compare["flat_drop_rate"] == 0.05) &
        (compare["p_transform"] == 0.20) &
        (compare["drop_rate"] == 0.20)
    ].iloc[0]

    print("\n=== REPRESENTATIVE SETTING ===")
    print(f"p_transform={rep['p_transform']:.2f}, drop_rate={rep['drop_rate']:.2f}, "
          f"flat_drop={rep['flat_drop_rate']:.2f}")
    print(f"Simulated legacy retention: {rep['sim_legacy']:.4f}")
    print(f"Analytic legacy retention:  {rep['analytic_legacy']:.4f}")
    print(f"Legacy gap: {rep['legacy_gap']:.4f}")
    print(f"Independent-fact SE: {rep['se_legacy_indep']:.4f} -> gap in SE: {rep['gap_in_se_indep']:.2f}")
    print(f"Correlated-layer SE: {rep['se_legacy_corr']:.4f} -> gap in SE: {rep['gap_in_se_corr']:.2f}")
    print("Interpretation: gap < 2 SE is consistent with finite-sample noise.")

    compare.to_csv(OUTPUTS_DIR / "analytic_sim_comparison.csv", index=False)
    print("\nSaved analytic_sim_comparison.csv")

    # ------------------------------------------------------------------
    # 2. Phase diagram: number of layers vs relay loss
    # ------------------------------------------------------------------
    print("\nGenerating phase diagram...")

    s_fixed = 0.20
    d_f_fixed = 0.05
    flat_ret = 1 - d_f_fixed

    L_range = np.arange(1, 9)
    d_range = np.linspace(0.0, 0.6, 120)

    legacy_grid = np.zeros((len(L_range), len(d_range)))
    for i, L_val in enumerate(L_range):
        for j, d_val in enumerate(d_range):
            q = 1 - (1 - s_fixed) * d_val
            legacy_grid[i, j] = q ** L_val

    diff_grid = flat_ret - legacy_grid  # positive -> flattening wins

    plt.figure(figsize=(10, 6))
    plt.contourf(d_range, L_range, diff_grid, levels=50, cmap="RdBu_r")
    plt.colorbar(label="Flat retention - Legacy retention")
    plt.axhline(4, color="black", linestyle="--", alpha=0.5, label="Inferred Vancouver depth = 4")
    plt.axhline(0, color="white", alpha=0.0)  # dummy

    # Contour line where difference = 0
    cs = plt.contour(d_range, L_range, diff_grid, levels=[0], colors="black")
    plt.clabel(cs, inline=True, fontsize=9, fmt="flat = legacy")

    plt.xlabel("Relay loss rate per layer (d)")
    plt.ylabel("Number of legacy routing layers (L)")
    plt.title(f"Information retention: flattened vs legacy\n(s={s_fixed:.2f}, flat loss={d_f_fixed:.2f})")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "phase_diagram_retention.png", dpi=150)
    plt.show()

    print("Saved phase_diagram_retention.png")

    # ------------------------------------------------------------------
    # 3. Title audit table
    # ------------------------------------------------------------------
    print("\nGenerating title audit table...")
    h = pd.read_csv(HIERARCHY_FILE)
    h.columns = [c.strip() for c in h.columns]

    # Ensure necessary columns exist
    if "normalized_title" not in h.columns:
        # Re-normalize from Title if needed
        import re
        def normalize_title(title):
            if not isinstance(title, str):
                return "UNKNOWN"
            t = title.upper().strip()
            t = re.sub(r"\s+", " ", t)
            t = re.sub(r"[^A-Z0-9 /]", "", t)
            t = t.replace(" & ", " AND ")
            t = t.replace(" IL", " II").replace(" IIL", " III").replace(" IIII", " IV")
            return t
        h["normalized_title"] = h["Title"].apply(normalize_title)

    audit = (
        h.groupby(["normalized_title", "layer"])
        .agg(
            employees=("Name", "nunique"),
            median_remuneration=("Remuneration", "median"),
            example_original_titles=("Title", lambda s: "; ".join(sorted(set(s))[:3])),
        )
        .reset_index()
        .sort_values(["layer", "employees"], ascending=[True, False])
    )

    audit.to_csv(OUTPUTS_DIR / "title_classification_audit_2025.csv", index=False)
    print(f"Saved title_classification_audit_2025.csv with {len(audit)} titles")

    # Print summary counts per layer
    print("\n=== TITLE AUDIT SUMMARY ===")
    print(audit.groupby("layer").agg(
        titles=("normalized_title", "nunique"),
        employees=("employees", "sum"),
    ).to_string())


if __name__ == "__main__":
    main()