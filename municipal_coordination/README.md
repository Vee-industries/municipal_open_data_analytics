# Municipal Coordination Compression Audit

A measurement and modeling study of title-derived structural composition and information retention in the City of Vancouver's Engineering Services department.

This project does not recommend eliminating specific roles. It measures what can be inferred from open data and models information loss under explicit assumptions.

## Data

- Source: City of Vancouver Open Data Portal
- Files:
  - Employee remuneration and expenses earning over $75,000
  - Workforce pay rates and sex
- Year used: 2025
- Department: Engineering Services

The remuneration file includes only employees earning over $75,000. It is not a full department headcount.

## Project Structure

```text
municipal_coordination/
├── data/
│   ├── raw/
│   │   ├── remuneration.csv
│   │   └── pay_rates.csv
│   └── processed/
│       ├── engineering_titles_raw.csv
│       ├── engineering_titles_cleaned.csv
│       └── engineering_2025_deduped.csv
├── scripts/
│   ├── 01_inspect_data.py
│   ├── 02_department_summary.py
│   ├── 03_clean_titles.py
│   ├── 04_map_hierarchy.py
│   ├── 05_spot_check.py
│   ├── 06_refine_classification.py
│   ├── 07_spot_check_refined.py
│   ├── 08_relay_vs_transform_sim.py
│   ├── 09_generate_pitch.py
│   ├── 10_verify_department_scope.py
│   ├── 11_rebuild_layer_summary_2025.py
│   ├── 12_update_relay_vs_transform_sim.py
│   ├── 13_generate_final_pitch.py
│   └── 14_analytic_model_and_audit.py
├── docs/
│   └── methodology.md
├── outputs/
│   ├── engineering_hierarchy_2025.csv
│   ├── engineering_layer_summary_2025.csv
│   ├── relay_vs_transform_sim_corrected.csv
│   ├── analytic_sim_comparison.csv
│   ├── title_classification_audit_2025.csv
│   ├── phase_diagram_retention.png
│   ├── final_pitch.md
│   └── white_paper.md
└── README.md
```

## How to Run

1. Place the raw CSV files in `data/raw/`.
2. Run scripts in order from `01` to `14`:

```bash
python scripts/01_inspect_data.py
python scripts/02_department_summary.py
python scripts/03_clean_titles.py
python scripts/04_map_hierarchy.py
python scripts/05_spot_check.py
python scripts/06_refine_classification.py
python scripts/07_spot_check_refined.py
python scripts/08_relay_vs_transform_sim.py
python scripts/09_generate_pitch.py
python scripts/10_verify_department_scope.py
python scripts/11_rebuild_layer_summary_2025.py
python scripts/12_update_relay_vs_transform_sim.py
python scripts/13_generate_final_pitch.py
python scripts/14_analytic_model_and_audit.py
```

The later scripts depend on outputs from the earlier ones.

## Key Results

### Title-Derived Layer Composition

| Layer | Employees | % Employees |
|---|---:|---:|
| Execution | 1,110 | 65.1% |
| Coordination | 493 | 28.9% |
| Governance | 49 | 2.9% |
| Unclassified | 53 | 3.1% |
| **Total disclosed** | **1,705** | |

### Closed-Form Retention Model

Per-layer retention:

```text
q = 1 - (1 - s)d
```

After L layers:

```text
R_legacy = [1 - (1 - s)d]^L
```

Flattened automated channel:

```text
R_flat = 1 - d_f
```

Representative setting:

- s = 0.20
- d = 0.20
- L = 4
- d_f = 0.05

Result:

- Legacy retention: 0.498 analytic, 0.510 simulated
- Flattened retention: 0.950
- Simulation gap within 2 SE of analytic value

## Testing

This project does not currently have an automated unit test suite like `run_all_tests.py`.

Verification is performed by running the scripts in order and checking that:

- Raw data delimiters are auto-detected.
- Title normalization reduces raw title count.
- Layer summary employee counts sum correctly.
- Analytic retention matches simulation within 2 SE.
- Output CSVs and phase diagram are generated without errors.

The main integrity check is the comparison between analytic and simulated retention in `scripts/14_analytic_model_and_audit.py`.

## Handoff Notes

If someone else takes over this project, the next steps are:

- Validate title classification against a real City of Vancouver org chart.
- Obtain real infrastructure ticket data and measure fact retention empirically.
- Replace the assumed 5% flattened summarization loss with a measured LLM loss.
- Add sensitivity analysis for the four routing layers assumption.
- Test alternative classifiers for title assignment.

The current work is an illustrative model, not a direct audit of real management behavior. That limitation should remain explicit in any future publication.

## AI Use Disclosure

AI tools were used for code generation, debugging, mathematical checking, and documentation drafting.

The project direction, research question, quality control, and decision-making were human-led. In particular:

- Identifying the management-layer measurement target.
- Catching the multi-year headcount error.
- Requiring closed-form validation of the simulation.
- Choosing the Vancouver open data source.
- Enforcing matched false-positive and honesty requirements.

AI assisted with implementation and formatting. It did not select the research direction or replace judgment.

## Limitations

1. Titles are a proxy for hierarchy, not verified reporting lines.
2. Title classification is keyword-based and may contain errors.
3. Some employees remained unclassified.
4. The simulation uses synthetic tickets and assumed relay probabilities.
5. Decision quality was not evaluated.
6. The flattened pipeline loss rate is an assumption.

## Outputs

The full analysis is in:

```text
outputs/final_pitch.md
```

The reproducible title classification audit is in:

```text
outputs/title_classification_audit_2025.csv
```

The retention phase diagram is in:

```text
outputs/phase_diagram_retention.png
```

The formal white paper is in:

```text
outputs/white_paper.md
```

This is a preliminary measurement and model, not a policy recommendation.