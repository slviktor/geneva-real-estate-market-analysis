# Step 1 · Long-run Price Benchmarks

Module inside **Market Analytics** (`step_1/`) — not a separate step number.

## Question

> Is Geneva’s price path just the Swiss housing cycle, or a structural premium?

## Role

| Does | Does not |
|------|----------|
| Collect long comparable series (canton / city / region / CH) | Build demand or supply models |
| Index everything (e.g. 1990 = 100) + Geneva / CH relative | Replace OCSTAT CHF/m² as the model *level* target |
| Context for portfolio + later validation (Step 2D / 4) | Block Step 2B |

## Layout

```text
step_1/long_run/
  README.md                   this file (incl. Wüest / IAZI policy)
  TIME_ALIGNMENT.md           dating conventions (OCSTAT annual vs BIS/BFS Q4)
  sources_long_run.json
  local/                      private Wüest exports only (git-ignored)
  scripts/                    fetch_wuest_local, transform, viz, pptx
  exports/figures/            lr_01 … lr_08 charts
```

```text
raw/ocstat|bis|bfs|sitg/      redistributable downloads (git-ignored)
```

## Licence policy

| Source | Chart in portfolio? | Commit raw to GitHub? |
|--------|---------------------|------------------------|
| OCSTAT, BIS, BFS IMPI | ✅ | ✅ under `raw/` |
| **Wüest Partner** | ✅ with *Source: Wüest Partner* + URL | ❌ never CSV/XLS |
| **IAZI** | ❌ no public time series from us | ❌ — text + link only |

### Wüest Partner — OK to chart, not OK to redistribute machine-readable series

Public index pages: transaction-price indices are published, updated quarterly, and the interactive tool allows **export**.

For a **non-commercial portfolio** it is reasonable to build **our own chart** from that public/exportable index, label **Source: Wüest Partner**, link the source, and **not** publish CSV/XLS (raw or processed) in GitHub.

There is **no explicit open-data licence** allowing redistribution of the underlying dataset — **not** equivalent to OCSTAT.

**Local vs public repo**

| Artifact | Local machine | Public GitHub |
|----------|---------------|---------------|
| `step_1/long_run/local/wuest_*.csv` (+ raw XLS) | ✅ after `fetch_wuest_local.py` | ❌ git-ignored |
| `data/fact_long_run_ppe.csv` (includes Wüest rows when local export present) | ✅ after `transform_long_run.py` | ❌ git-ignored |
| `data/fact_long_run_validation.json` | ✅ | ❌ git-ignored |
| Chart PNGs with Wüest lines + citation | ✅ | ✅ OK with *Source: Wüest Partner* |

Rebuild locally (file stays on disk, never committed):

```bash
python step_1/long_run/scripts/fetch_wuest_local.py
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
```

**Citation example:**

> **Lake Geneva — Transaction Price Index, owner-occupied apartments**  
> Source: Wüest Partner.  
> Data used for analysis/visualisation; underlying Wüest Partner dataset is not redistributed.

| Series (planned) | Geography | Object |
|---|---|---|
| Transaction Price Index | Lake Geneva | Owner-occupied apartments (PPE) |
| Transaction Price Index | Lake Geneva | Houses |
| Transaction Price Index | Switzerland | Owner-occupied apartments (PPE) |
| Transaction Price Index | Switzerland | Houses |

- **URL:** https://www.wuestpartner.com/ch-fr/blog/indices-interactifs-des-prix-de-limmobilier-suisse/
- **Local only:** `step_1/long_run/local/` (git-ignored)

### IAZI / CIFI — text benchmark only

Published IAZI index docs: **© IAZI AG … All rights reserved**, information **confidential**, not to be passed to third parties without consent.

We **do not** rebuild a public IAZI time series for LinkedIn/GitHub or digitise values from that material without permission.

We **may** write:

> As an external benchmark, the SWX IAZI Condominium Price Index tracks Swiss condominium transaction prices.

(+ link; arm’s-length transactions; annual from 1981, quarterly from 1996.)

- **URL:** https://www.iazicifi.ch/wp-content/uploads/2024/10/Information_Indices_D.pdf

### Open series in `raw/`

| Source | Bucket |
|---|---|
| OCSTAT | `raw/ocstat/` |
| BIS RPP (FRED) | `raw/bis/` |
| BFS IMPI | `raw/bfs/` |

Full catalogue (licence, file URLs, start/end, frequency): [`raw/README.md`](../../raw/README.md).

## Extract / transform / viz

```bash
python scripts/extract.py --sources step_1/long_run/sources_long_run.json
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
```

Outputs (**local only** — git-ignored if they contain Wüest):  
`data/fact_long_run_ppe.csv`, `data/fact_long_run_validation.json`,  
`step_1/long_run/exports/figures/lr_0*.png` (incl. `lr_05_drawdowns`, `lr_08_implied_size`),  
`exports/drawdown_episodes.csv`, `exports/validation_box.md`.

Dating conventions: [`TIME_ALIGNMENT.md`](TIME_ALIGNMENT.md).

Optional Wüest (local only — exports + fact CSV stay git-ignored):

```bash
python step_1/long_run/scripts/fetch_wuest_local.py
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
```
