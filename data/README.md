# Data

- `raw/` — data exactly as collected or received. **Never edit.** One subfolder per source.
  - `faa/` — place `FAA_All_Volumes_Compiled.xlsx` here.
- `interim/` — cleaned and unified records (schema: `docs/data_schema.md`).
- `processed/` — analysis-ready data with model outputs and labels.

Raw and interim data must not be pushed to a public repository (see `docs/ethics.md`).
