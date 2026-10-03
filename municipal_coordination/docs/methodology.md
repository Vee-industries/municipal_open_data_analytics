# Methodology: Municipal Coordination Compression Audit

## 1. Objective

The study measures two things:

1. Title-derived structural composition of the City of Vancouver Engineering Services department.
2. Expected information retention through hierarchical routing versus a flattened automated channel.

The study does not attempt to prove that any specific manager is unnecessary.

## 2. Data Source

Primary file:

- `Employee remuneration and expenses earning over $75,000`
- City of Vancouver Open Data Portal
- Year 2025
- Department filter: contains "Engineering"

The dataset is a salary disclosure file. It only includes employees above a pay threshold, so the true department headcount is larger.

## 3. Title Normalization

Raw titles had inconsistent casing, punctuation, and Roman numeral formatting.

Normalization steps:

1. Convert to uppercase.
2. Strip extra whitespace.
3. Remove punctuation except spaces and slashes.
4. Replace `" & "` with `" AND "`.
5. Fix common letter-number errors like `IL` to `II`.

After normalization, 719 raw titles reduced to 200 normalized titles.

## 4. Structural Layer Classification

We assigned each normalized title to one of three layers using keyword rules.

Layer definitions:

- Execution: direct service delivery, trades, operations, technical work.
- Coordination: supervisors, managers, analysts, planners, coordinators, foremen, project managers.
- Governance: directors, general managers, chief engineer, deputy city engineer.

If no keyword matched, the title was left as Unclassified.

This classification is title-derived inference. It is not based on verified reporting lines.

## 5. De-duplication

The 2025 Engineering Services data contained 1,749 rows but only 1,705 distinct employee names.

We de-duplicated by keeping the highest remuneration row per employee per year.

## 6. Layer Summary

| Layer | Employees | Percent |
|---|---:|---:|
| Execution | 1,110 | 65.1% |
| Coordination | 493 | 28.9% |
| Governance | 49 | 2.9% |
| Unclassified | 53 | 3.1% |
| Total | 1,705 | 100% |

## 7. Relay-vs-Transform Simulation

### 7.1 Tickets

We generated 500 synthetic infrastructure tickets.

Each ticket contained five facts:

- work order ID
- location
- problem code
- priority
- resource count

### 7.2 Legacy pipeline

Four routing layers were assumed:

1. Frontline Supervisor / Foreman
2. Superintendent
3. Senior Branch Head
4. Director / General Manager

At each layer:

- with probability s, the layer synthesizes and preserves all incoming facts;
- otherwise, it relays and each fact drops with probability d.

### 7.3 Flattened pipeline

A single automated summarizer with fact drop rate d_f.

We used d_f = 0.05 as a realistic imperfect summarizer assumption.

## 8. Closed-Form Model

Expected per-layer retention:

q = s + (1-s)(1-d) = 1 - (1-s)d

After L layers:

R_legacy = [1 - (1-s)d]^L

Flattened retention:

R_flat = 1 - d_f

## 9. Simulation Validation

At s=0.20, d=0.20, L=4:

- Analytic legacy retention: 0.498
- Simulated legacy retention: 0.510
- Gap: 0.012

Standard error under independent-fact assumption: 0.010, gap = 1.25 SE.

Standard error under correlated-layer assumption: 0.022, gap = 0.56 SE.

Both below 2 SE, so the simulation is consistent with finite-sample noise.

## 10. Phase Diagram

We generated a phase diagram over:

- number of legacy layers L
- per-layer relay loss d

with s fixed at 0.20 and d_f fixed at 0.05.

The boundary is:

[1 - (1-s)d]^L = 1 - d_f

The diagram is saved as:

`outputs/phase_diagram_retention.png`

## 11. Reproducibility

All scripts are numbered and runnable in sequence.

The full title classification audit is available in:

`outputs/title_classification_audit_2025.csv`

The analytic and simulated comparison is available in:

`outputs/analytic_sim_comparison.csv`

## 12. Limitations

1. Title-derived hierarchy is a proxy, not verified reporting lines.
2. Keyword classification can misclassify hybrid roles.
3. 53 employees remained unclassified.
4. The simulation uses synthetic tickets and assumed relay probabilities.
5. Decision quality was not evaluated.
6. The flattened pipeline loss rate is an assumption.

This methodology supports a preliminary measurement and model, not a policy recommendation.