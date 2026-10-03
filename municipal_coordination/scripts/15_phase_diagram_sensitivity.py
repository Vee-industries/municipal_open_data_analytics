import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path


OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

S = 0.20
DF_FIXED = 0.05
L_INFERRED = 4


def legacy_retention(L, d, s=S):
    q = 1 - (1 - s) * d
    return q ** L


def flat_retention(d_f):
    return 1 - d_f


def main():
    # ---------------------------------------------------------------
    # Panel 1: L vs d, d_f fixed
    # ---------------------------------------------------------------
    L_range = np.arange(1, 9)
    d_range = np.linspace(0.0, 0.6, 120)

    legacy_grid = np.zeros((len(L_range), len(d_range)))
    for i, L_val in enumerate(L_range):
        for j, d_val in enumerate(d_range):
            legacy_grid[i, j] = legacy_retention(L_val, d_val)

    flat_fixed = flat_retention(DF_FIXED)
    diff_grid = flat_fixed - legacy_grid

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Panel 1: existing phase diagram
    ax1 = axes[0]
    cf = ax1.contourf(d_range, L_range, diff_grid, levels=50, cmap="RdBu_r")
    fig.colorbar(cf, ax=ax1, label="Flat retention - Legacy retention")
    ax1.axhline(L_INFERRED, color="black", linestyle="--", alpha=0.5,
                label=f"Inferred Vancouver depth = {L_INFERRED}")
    cs = ax1.contour(d_range, L_range, diff_grid, levels=[0], colors="black")
    ax1.clabel(cs, inline=True, fontsize=9, fmt="flat = legacy")
    ax1.set_xlabel("Relay loss rate per layer (d)")
    ax1.set_ylabel("Number of legacy routing layers (L)")
    ax1.set_title(f"Panel A: d_f fixed at {DF_FIXED:.2f}, s={S:.2f}")
    ax1.grid(alpha=0.2)
    ax1.legend(loc="upper right")

    # ---------------------------------------------------------------
    # Panel 2: d_f sensitivity at L=4
    # ---------------------------------------------------------------
    ax2 = axes[1]
    d_f_range = np.linspace(0.0, 0.30, 120)

    d_values_to_show = [0.05, 0.10, 0.20, 0.30]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]

    for d_val, color in zip(d_values_to_show, colors):
        legacy_val = legacy_retention(L_INFERRED, d_val)
        diff = flat_retention(d_f_range) - legacy_val

        ax2.plot(
            d_f_range,
            diff,
            color=color,
            label=f"legacy d={d_val:.2f}",
        )

        # Mark where difference crosses zero, if within range
        zero_crossings = np.where(np.diff(np.sign(diff)))[0]
        for idx in zero_crossings:
            d_f_cross = d_f_range[idx]
            ax2.axvline(
                d_f_cross,
                color=color,
                linestyle=":",
                alpha=0.5,
            )
            ax2.text(
                d_f_cross,
                0.05,
                f"d_f={d_f_cross:.2f}",
                rotation=90,
                fontsize=8,
                color=color,
                alpha=0.8,
            )

    ax2.axhline(0.0, color="black", linewidth=1.0)
    ax2.set_xlabel("Flattened summarizer loss rate (d_f)")
    ax2.set_ylabel("Flat retention - Legacy retention")
    ax2.set_title(
        f"Panel B: d_f sensitivity at L={L_INFERRED}, s={S:.2f}"
    )
    ax2.grid(alpha=0.2)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(OUTPUTS_DIR / "phase_diagram_sensitivity.png", dpi=150)
    plt.close()

    print("Saved outputs/phase_diagram_sensitivity.png")

    # ---------------------------------------------------------------
    # Sensitivity table for representative L=4, s=0.20
    # ---------------------------------------------------------------
    rows = []
    for d_val in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        legacy_val = legacy_retention(L_INFERRED, d_val)
        for d_f_val in [0.00, 0.02, 0.05, 0.08, 0.10, 0.15, 0.20]:
            flat_val = flat_retention(d_f_val)
            rows.append({
                "L": L_INFERRED,
                "s": S,
                "d": d_val,
                "d_f": d_f_val,
                "legacy_retention": legacy_val,
                "flat_retention": flat_val,
                "flat_minus_legacy": flat_val - legacy_val,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUTS_DIR / "phase_diagram_sensitivity_table.csv", index=False)
    print("Saved outputs/phase_diagram_sensitivity_table.csv")


if __name__ == "__main__":
    main()