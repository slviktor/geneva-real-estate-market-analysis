# Data schema

Source of truth: `data/*.csv`. `geneva.duckdb` is a derived copy built by `transform.py` (git-ignored).

```
fact_volume ── type_id ──► dim_type
            └── geo_id ──► dim_geo     always canton 0000

fact_price  ── type_id ──► dim_type
            ├── geo_id ──► dim_geo
            ├── market ──► dim_market
            └── condition ► dim_condition

map_geo_alias  label → geo_id
```

Missing values (`///`, `( )`, `-`) are kept as empty cells — never filled with 0 or interpolated.

---

## Three distinct price metrics

These cannot be derived from one another and must not appear on the same axis.

| Metric | What it measures | Where | Fields |
|--------|-----------------|-------|--------|
| **Transaction count** | Number of objects sold | `fact_volume.n`; `fact_price.n` (transactions in the quartile cell) | `n` |
| **CHF per object** | Full price of a house or apartment | `fact_volume` (mean = `value_chf / n`); `fact_price` where `unit = CHF_per_object` | `value_chf`; `p25` / `median` / `p75` |
| **CHF per m²** | Price per living-space m² (separate OCSTAT calculation, not ticket / area) | `fact_price` where `unit = CHF_per_m2` | `p25` / `median` / `p75` |

Key constraints:
- `mean(value_chf / n)` ≠ `median`. Do not label the average ticket as a median.
- `median(price) / median(m²)` ≠ median CHF/m².
- OCSTAT publishes **CHF/m² for apartments (PPE) only** (annual). For houses the CHF/m² column in the mémento is blank (`…`). No quarterly CHF/m² exists for any property type.

---

## `fact_volume` — transaction counts and turnover (no quartiles)

Canton level. Contains transaction count `n` and total transaction value.

| source | freq | from | semantics |
|--------|------|------|-----------|
| `T_05_05_1_1_01` | `Q` | 2007 | count + total CHF |
| `T_05_05_1_2_01` | `Y` | 1998 | count + total CHF |

Grain: `source + freq + year + quarter + type_id`.

| Field | Meaning |
|-------|---------|
| `source` | OCSTAT table identifier |
| `freq` | `Q` (quarterly) / `Y` (annual) |
| `year`, `quarter` | Quarter 1–4; annual rows have empty quarter |
| `type_id` | → `dim_type` |
| `is_provisional` | 1 = marked `p` (preliminary) in source Excel |
| `n` | **Count:** number of objects sold |
| `value_kchf` | Total, thousands of CHF (as published) |
| `value_chf` | Total × 1 000, in CHF |
| `geo_id` | Always `0000` (canton) |

`value_chf / n` = average ticket per object — not a median, not CHF/m².  
`house` = `house_existing` + `house_new` (same for `ppe`). New and existing are parts, not the ensemble.

---

## `fact_price` — quartile distributions: either per object or per m²

One table, two statistics, separated by the `unit` field.

| source | freq | geo | `unit` | quartile type | new / existing |
|--------|------|-----|--------|---------------|----------------|
| `T_05_05_1_1_02` | Q from 2007 | canton | `CHF_per_object` | object price | existing only |
| `T_05_05_1_3_03` | Y from 1990 | commune | `CHF_per_object` | house object price | ensemble (`all`) |
| `T_05_05_1_4_03` | Y from 1990 | commune | `CHF_per_m2` | apartment m² price | new / existing × libre / ZD |

Grain: `source + freq + year + quarter + geo_label + type_id + condition + market`.

| Field | Meaning |
|-------|---------|
| `source`, `freq`, `year`, `quarter` | Same as in `fact_volume` |
| `geo_label` | Name as published by OCSTAT |
| `geo_id` | BFS code; empty for `Autres communes…` |
| `type_id` | Quarterly: `house_existing` / `ppe_existing`. Annual: `house` / `ppe` |
| `condition` | `new` / `existing` / `all` |
| `market` | `libre` / `zd` / `all` |
| `is_provisional` | Same as in `fact_volume` |
| `n` | Transactions in this cell (denominator of the quartile) |
| `unit` | `CHF_per_object` or `CHF_per_m2` — the unit being split into quartiles |
| `p25`, `median`, `p75` | Q1 / median / Q3, **in `unit` units** |

Chart filter rule: filter on `unit` first, then segment. Never plot per-object and per-m² on the same axis. Do not average four quarterly medians into an annual figure. Quartiles are often missing when `n < 10`.

---

## `dim_type`

| `type_id` | `segment_v1` | ensemble | condition | OCSTAT label |
|-----------|--------------|----------|-----------|--------------|
| `house_existing` | house | 0 | existing | Maison individuelle non neuve |
| `house_new` | house | 0 | new | Maison individuelle neuve |
| `house` | house | 1 | all | Maison individuelle — Ensemble |
| `ppe_existing` | ppe | 0 | existing | Appartement en PPE non neuf |
| `ppe_new` | ppe | 0 | new | Appartement en PPE neuf |
| `ppe` | ppe | 1 | all | Appartement en PPE — Ensemble |
| `land`, `multi_unit`, `mixed`, `commercial`, `other` | — | 0 | — | non-residential (out of scope) |

---

## `dim_geo`

| Field | Meaning |
|-------|---------|
| `geo_id` | BFS code, 4 digits; canton = `0000`; sectors e.g. `6621-V.G.` |
| `grain` | `canton` / `commune` / `secteur` |
| `bfs_id` | Numeric BFS code |
| `parent_bfs_id` | For city sectors = `6621` |
| `no_cantonal` | Cantonal commune number |
| `name_ocstat`, `name_sitg` | Name in OCSTAT table / on the SITG map |
| `abreviation` | SITG code |
| `name_norm` | Normalised name for string matching |
| `has_polygon` | 1 = polygon available in GeoJSON; City of Geneva `6621` = 0 (dissolve its sectors) |

OCSTAT "Genève" → `geo_id = 6621`. City map = dissolve sectors by `parent_bfs_id`.

---

## `dim_market` / `dim_condition`

| `market` | |
|----------|-|
| `libre` | free market — main series for PPE CHF/m² |
| `zd` | zones de développement (price-controlled) |
| `all` | mix — do not use for new vs existing comparison |

| `condition` | |
|-------------|-|
| `new` | neuf |
| `existing` | non neuf |
| `all` | ensemble |

---

## `map_geo_alias`

| Field | Meaning |
|-------|---------|
| `label` | Name as it appears in the source |
| `label_norm` | Normalised form |
| `geo_id` | → `dim_geo` |
| `source` | `ocstat` / `sitg` / `alias` |

No fuzzy matching; unresolved labels are written to `data/unmatched_geo.csv` during `transform.py` (not committed).
