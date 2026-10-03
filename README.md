# Municipal open-data analytics

Two solo projects built for the AI in Municipal Governance hackathon, August 2026. Kevin Vaillancourt.

- [`municipal_bids/`](municipal_bids/): predicts which New York City contracts were awarded without competition, and measures how much a vendor's past award history improves the prediction.
- [`municipal_coordination/`](municipal_coordination/): classifies City of Vancouver Engineering Services job titles into execution, coordination and governance layers, and models information loss across those layers.

## Data notes

- The Vancouver source data lists individual employees by name. Those files are not included here; the summaries by job title are. To rerun from scratch, download the remuneration data from the City of Vancouver Open Data Portal into `municipal_coordination/data/raw/`.
- The New York City contract files used by the scripts are included.

AI use is disclosed in [`municipal_coordination/docs/ai_use_disclosure.md`](municipal_coordination/docs/ai_use_disclosure.md).
