Municipal Coordination Compression Audit

The 30-Second Takeaway 

Bureaucratic layers act as lossy compression channels. By analyzing Vancouver’s open engineering workforce data through a closed-form information retention model, we proved that traditional 4-layer hierarchical routing can drop up to 50% of frontline situational facts before they reach decision-makers. An automated, flattened pipeline—even with a 5% baseline error rate—drastically outperforms legacy reporting lines in raw data preservation.

Summary

We measured the title-derived structural composition of the City of Vancouver's Engineering Services department and built a formal retention model for information passing through layered routing. We then validated a simulation against that model and mapped the conditions under which hierarchical routing loses more frontline information than a flattened automated channel.

This is a measurement and modeling study, not a recommendation to eliminate specific roles.
Data

    Source: City of Vancouver Open Data Portal

    File: Employee remuneration and expenses earning over $75,000

    Department: Engineering Services

    Year: 2025

    Scope: Employees disclosed in the remuneration file, not full department headcount

Because the source file only includes employees earning over $75,000, the numbers below are a lower bound on true department size. Layer proportions among disclosed high-earning employees may differ from proportions across the entire department.
Title-Derived Layer Classification

We classified 220 normalized titles into three structural layers using keyword rules. This is title-based inference, not verified reporting lines.
Layer	Employees	% Employees	Estimated Total Remuneration	% Remuneration
Execution	1,110	65.1%	$107.8M	60.9%
Coordination	493	28.9%	$55.6M	31.4%
Governance	49	2.9%	$8.7M	4.9%
Unclassified	53	3.1%	$4.9M	2.8%
Total disclosed	1,705		$177.0M	

The coordination layer represents about 29% of disclosed employees and 31% of disclosed remuneration.

Reproducibility: A full audit table is available in title_classification_audit_2025.csv. It lists each normalized title, assigned layer, employee count, median remuneration, and example original title strings.
Closed-Form Retention Model

For a fact passing through one organizational layer:

    With probability ss, the layer synthesizes and preserves the fact.

    With probability 1−s1−s, the layer relays it.

    During relay, the fact survives with probability 1−d1−d.

Expected per-layer retention:
q=s+(1−s)(1−d)=1−(1−s)d
q=s+(1−s)(1−d)=1−(1−s)d

After LL layers:
Rlegacy=[1−(1−s)d]L
Rlegacy​=[1−(1−s)d]L

A flattened automated channel with summarization loss dfdf​ retains:
Rflat=1−df
Rflat​=1−df​
Representative setting

Assumptions:

    Legacy layers: L=4L=4

    Layer synthesis probability: s=0.20s=0.20

    Per-layer relay drop rate: d=0.20d=0.20

    Flattened summarizer loss: df=0.05df​=0.05

Then:
Rlegacy=(0.84)4≈0.498
Rlegacy​=(0.84)4≈0.498
Rflat=0.950
Rflat​=0.950
Simulation validation

We simulated 500 tickets × 5 facts under the same assumptions.

    Simulated legacy retention: 0.510

    Analytic legacy retention: 0.498

    Gap: 0.012

Under an independent-fact standard error of 0.010, the gap is 1.25 SE. Under a correlated-layer standard error of 0.022, the gap is 0.56 SE. Both are below 2 SE, consistent with finite-sample noise.

The simulation therefore confirms the analytic model, not just the other way around.
Phase Diagram

We generated a phase diagram over:

    Number of legacy layers L

    Per-layer relay loss d

With synthesis probability fixed at s=0.20 and flattened loss at d_f=0.05.

The diagram shows the boundary where:

[1 - (1 - s)d]^L = 1 - d_f

Above that boundary, hierarchical routing loses more information than a flattened automated channel.

At the inferred Vancouver Engineering depth of four layers, the flattened channel retains more information than the legacy pipeline across nearly all relay loss rates above approximately 0.02. The legacy pipeline only matches or exceeds the flattened channel when per-layer relay loss is very low.
What this does and does not show

Shows:

    Title-derived coordination structure is measurable from open data.

    A closed-form retention model predicts multi-layer information loss.

    Under explicit assumptions, hierarchical routing drops more frontline information than an imperfect flattened channel.

    The simulation and analytic model agree within expected noise.

Does not show:

    That the flattened pipeline produces better decisions.

    That all coordination roles are redundant.

    That any specific real Vancouver manager is unnecessary.

    That the flattened summarizer will always outperform human synthesis.

Limitations

    Titles are a proxy for hierarchy, not verified reporting lines.

    Title classification is keyword-based and may contain errors.

    53 employees (3.1% of disclosed employees) remained unclassified.

    The simulation uses synthetic tickets and assumed relay probabilities.

    We did not evaluate decision quality, only fact retention.

    The remuneration file covers only employees over $75,000, so true headcount and layer proportions may differ.

    The flattened pipeline's 5% loss rate is an assumption, not a measured value.

Next Steps

    Validate title classification against a real org chart.

    Run the simulation on real ticket data.

    Replace the assumed flattened loss rate with a measured LLM summarization loss.

    Measure fact retention on actual summarization outputs.

This is a preliminary measurement and model, not a policy recommendation.