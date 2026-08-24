# Time alignment (dating conventions)

When series share the same cycles but look **shifted**, check whether year `T` means the same thing.

## What each source means by “year T”

| Series | What year `T` is | In our pipeline |
|--------|------------------|-----------------|
| **OCSTAT** PPE median CHF/m² | Median of **transactions during calendar year T** (flow over the year). Excel: *Chiffres annuels*. | As published |
| **Wüest** published annual | Official **yearly** hedonic transaction price index (base 1985=100). Calendar-year series from 1985; pairs with OCSTAT annual medians. Incomplete years (no Q4 yet) are dropped. | **Used for all complete years** |
| **Wüest** quarterly | Q1…Q4 from 2000 (same product, higher frequency) | Parsed in fetch for reference only — **not** used on long-run charts |
| **BIS** RPP (FRED) | Quarterly; FRED stamps **start of quarter** (Q1=`YYYY-01-01`, Q4=`YYYY-10-01`) | **Q4 only** (year-end). If Q4 missing for latest year → last available quarter |
| **BFS IMPI** condo (EGW) | Quarterly (base Q4 2019=100) | **Q4 only** (year-end); same fallback |

## Wüest: why published annual (not Q4)

OCSTAT year T is a **calendar-year transaction median**. Wüest’s **published annual** index is the natural yearly counterpart (same product as on the Wüest export / website).

An earlier experiment used **Q4 rescaled onto annual at 2000** to tighten YoY turning-point alignment with OCSTAT. That improved lag diagnostics but:

- no longer matched the annual numbers users see on Wüest;
- required an opaque scale factor.

**Current rule:** Wüest → **published annual only**; rebase to 1990=100 in transform/viz. Residual OCSTAT↔Wüest gaps are methodology (raw median CHF/m² vs hedonic constant-quality index), not only dating.

## Rule we apply now

| Family | Dating |
|--------|--------|
| **OCSTAT** | calendar-year median / annual mean CPI as published |
| **Wüest** | published annual (1985=100) |
| **BIS / BFS IMPI** | year-end **Q4** labelled as year T |

## Re-run after dating change

```bash
python step_1/long_run/scripts/fetch_wuest_local.py
# offline: python step_1/long_run/scripts/fetch_wuest_local.py --from-local
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
```
