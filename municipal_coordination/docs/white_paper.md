# Municipal Coordination Compression Audit - White Paper

## Abstract

This paper examines the information-routing role of middle management in a municipal government using open data from the City of Vancouver. We classify disclosed employees into execution, coordination, and governance layers based on job titles. We then derive a closed-form model for information retention through hierarchical routing and compare it to a flattened automated summarizer.

The classification shows coordination roles represent approximately 29 percent of disclosed employees and 31 percent of disclosed remuneration in Engineering Services for 2025.

The retention model predicts that with four legacy routing layers, 20 percent synthesis probability, and 20 percent per-layer relay loss, frontline information retention falls to approximately 0.498. An imperfect automated channel with 5 percent summarization loss retains 0.950. These results are illustrative and based on explicit assumptions, not empirical measurement of real routing fidelity.

## 1. Introduction

Municipal organizations often route operational information through multiple management layers before it reaches decision makers. Whether each layer transforms or merely relays information is an open question.

This paper separates two claims:

- Descriptive: how many employees occupy coordination-type titles?
- Modeling: under explicit relay assumptions, how much frontline information survives layered routing?

We do not claim that any specific role is unnecessary or that automation produces better decisions.

## 2. Data

Data source: City of Vancouver Open Data Portal.

File: Employee remuneration and expenses earning over $75,000.

Year: 2025.

Department: Engineering Services.

The remuneration file includes only employees over a salary threshold. It is not a complete headcount. As a result, layer proportions are lower-bound-sensitive and may be biased if lower-paid execution roles are underrepresented.

## 3. Title Classification

We normalized 719 raw titles to 200 normalized titles and assigned each to one of three layers using keyword rules.

Layers:

- Execution: direct service delivery, trades, operations, technical work.
- Coordination: supervisors, managers, analysts, planners, coordinators, project managers, foremen.
- Governance: directors, general managers, chief engineer, deputy city engineer.

This is title-derived inference, not verified reporting lines. Some roles may be hybrid and some may be misclassified.

### 3.1 Results

| Layer | Employees | Percent | Estimated Remuneration | Percent |
|---|---:|---:|---:|---:|
| Execution | 1,110 | 65.1 | $107.8M | 60.9 |
| Coordination | 493 | 28.9 | $55.6M | 31.4 |
| Governance | 49 | 2.9 | $8.7M | 4.9 |
| Unclassified | 53 | 3.1 | $4.9M | 2.8 |
| Total | 1,705 | 100 | $177.0M | 100 |

## 4. Closed-Form Retention Model

Let a fact pass through one organizational layer.

With probability s, the layer synthesizes and preserves the fact.

With probability 1-s, the layer relays and the fact survives with probability 1-d.

Expected retention per layer:

q = s + (1-s)(1-d) = 1 - (1-s)d

After L layers:

R_legacy = [1 - (1-s)d]^L

A flattened automated channel with summarization loss d_f retains:

R_flat = 1 - d_f

## 5. Simulation

We simulated 500 synthetic infrastructure tickets, each containing five facts: work order ID, location, problem code, priority, resource count.

Legacy pipeline: four layers, each with synthesis probability s and relay drop probability d.

Flattened pipeline: automated summarizer with fact loss d_f.

We varied s, d, and d_f over a grid.

At representative setting s=0.20, d=0.20, L=4:

- Simulated legacy retention: 0.510
- Analytic legacy retention: 0.498

Gap: 0.012.

Standard error checks:

- Independent-fact SE: 0.010, gap = 1.25 SE.
- Correlated-layer SE: 0.022, gap = 0.56 SE.

Both below 2 SE, consistent with finite-sample variation.

## 6. Phase Diagram

We mapped the boundary where:

[1 - (1-s)d]^L = 1 - d_f

with s fixed at 0.20 and d_f at 0.05.

For four layers, hierarchical routing is worse than flattened routing across nearly all relay loss rates above approximately 0.02. The legacy pipeline only matches or exceeds the flattened channel when per-layer relay loss is near zero. The exact boundary is shown in phase_diagram_retention.png.

## 7. Interpretation

The result is not that Vancouver managers cause measured information loss. It is that a simple model of layered relay predicts strong retention penalties under mild per-layer loss.

The contribution is the model and the phase structure, not a direct empirical audit of real human behavior.

## 8. Limitations

1. Titles are a proxy for hierarchy.
2. Title classification is keyword-based.
3. Some titles remain unclassified.
4. Simulation uses synthetic tickets.
5. Relay probabilities are assumptions.
6. Flattened loss rate is assumed.
7. Decision quality was not evaluated.

## 9. Future Work

- Validate against a real org chart.
- Use real service request data.
- Measure LLM summarization loss empirically.
- Run a pilot comparing human and automated summarization fact retention.

This paper is a measurement and modeling exercise, not a policy recommendation.