# Raw data inventory

Shared download folder for all project steps. **File contents are git-ignored**; this README is committed.

```text
raw/
  ocstat/     OCSTAT Excel tables
  bis/        BIS residential property prices (via FRED CSV)
  bfs/        BFS/OFS IMPI Excel
  sitg/       Commune boundaries (GeoJSON)
  other/      ad-hoc probes (optional; not required)
```

Naming: `{YYYY-MM-DD}_{id}.{ext}` (see `scripts/extract.py`).

```bash
python scripts/extract.py --sources step_1/sources.json
python scripts/extract.py --sources step_1/long_run/sources_long_run.json
```

Dating / year-end alignment for price indices: [`step_1/long_run/TIME_ALIGNMENT.md`](../step_1/long_run/TIME_ALIGNMENT.md).

---

## Licence by publisher

| Publisher | Licence / reuse | Public `raw/` OK? |
|-----------|-----------------|-------------------|
| **OCSTAT** (Canton of Genève) | Free use/reproduction of published statistics with **source attribution** ([OCSTAT mission / LStat](https://statistique.ge.ch/mission/welcome.asp)) | ✅ |
| **BIS** (via FRED) | Free use of BIS RPP statistics with **citation** ([BIS terms](https://www.bis.org/terms_conditions.htm); FRED series notes) | ✅ |
| **BFS/OFS** | Open government data; **attribution** ([opendata.swiss](https://opendata.swiss/en/terms-of-use); [BFS IMPI](https://www.bfs.admin.ch/bfs/en/home/statistics/prices/property-price.html)) | ✅ |
| **SITG** | Public geodata via SITG services; attribute **SITG / Canton of Genève** | ✅ |
| **Wüest Partner** | Public index + export for analysis; **no explicit open-data redistribution licence** | ❌ `local/` + fact CSV git-ignored; charts OK with citation |
| **IAZI / CIFI** | © / confidential docs — **text + link only**, no public time series from us | ❌ |

**Suggested citations**

- OCSTAT: *Office cantonal de la statistique (OCSTAT), Canton of Geneva*
- BIS: *National sources; BIS Residential Property Price database, https://www.bis.org/statistics/pp.htm*
- BFS: *Federal Statistical Office (FSO) — Swiss Residential Property Price Index (IMPI)*
- Wüest (charts only): *Source: Wüest Partner. Data used for analysis/visualisation; underlying dataset is not redistributed.*

---

## Catalogue pages (browse all related tables)

| Theme | Catalogue |
|-------|-----------|
| Transactions & property prices (GE) | [OCSTAT 05.05 — tableaux](https://statistique.ge.ch/domaines/05/05_05/tableaux.asp) |
| Consumer prices (GE) | [OCSTAT 05.02 — tableaux](https://statistique.ge.ch/domaines/05/05_02/tableaux.asp) |
| Population & demographic balance | [OCSTAT 01.01 — tableaux](https://statistique.ge.ch/domaines/01/01_01/tableaux.asp) |
| Migration | [OCSTAT 01.02 — tableaux](https://statistique.ge.ch/domaines/01/01_02/tableaux.asp) |
| Births, deaths, longevity | [OCSTAT 01.03 — tableaux](https://statistique.ge.ch/domaines/01/01_03/tableaux.asp) |
| Households & families | [OCSTAT 01.05 — tableaux](https://statistique.ge.ch/domaines/01/01_05/tableaux.asp) |
| Swiss RPP (BIS portal) | [BIS Residential Property Prices](https://www.bis.org/statistics/dataportal/pp.htm) |
| Swiss IMPI (BFS) | [BFS — Property prices / IMPI](https://www.bfs.admin.ch/bfs/en/home/statistics/prices/property-price.html) |
| Commune boundaries | [SITG CAD_COMMUNE](https://ge.ch/sitg/) |

---

## `raw/ocstat/` — market & prices (Step 1 / long_run)

| Id | Content | Geo | Start | End* | Freq | Unit | File URL | Used in |
|----|---------|-----|------:|-----:|------|------|----------|---------|
| **T_05_05_1_1_01** | Transaction volumes / values by type | Canton | ~2007 | latest Q | **Q** | n, CHF | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_1_01.xlsx) | Step 1 |
| **T_05_05_1_1_02** | Price distribution PPE/houses (tickets, quartiles) | Canton | ~2007 | latest Q | **Q** | CHF/object | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_1_02.xlsx) | Step 1, long_run |
| **T_05_05_1_2_01** | Annual transaction activity | Canton / communes | ~1990s | latest A | **A** | n, CHF | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_2_01.xlsx) | Step 1 |
| **T_05_05_1_4_01** | PPE CHF/m² P25 / median / P75 by condition & market | Canton | **1990** | latest A | **A** | CHF/m² | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_4_01.xlsx) | long_run |
| **T_05_05_1_4_03** | PPE CHF/m² by commune | Communes | **1990** | latest A | **A** | CHF/m² | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_4_03.xlsx) | Step 1, long_run |
| **T_05_05_1_4_04** | PPE CHF/m² by Ville de Genève sector | City sectors | **1990** | latest A | **A** | CHF/m² | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_4_04.xlsx) | long_run |
| **T_05_05_1_3_01** | Houses CHF/object distribution | Canton | **1990** | latest A | **A** | CHF/object | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_3_01.xlsx) | long_run |
| **T_05_05_1_3_03** | Houses CHF/object by commune | Communes | **1990** | latest A | **A** | CHF/object | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_05/T_05_05_1_3_03.xlsx) | Step 1, long_run |
| **T_05_02_04** | Indice genevois des prix à la consommation (CPI) | Canton | long | latest | **M/A** | index | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/05/05_02/T_05_02_04.xlsx) | long_run (real prices) |

\*“latest” = as of last successful extract (see dated filenames in this folder).

**Dating note:** OCSTAT annual PPE year *T* = median of transactions **during calendar year T**.

---

## `raw/ocstat/` — demography & households (Step 2A)

| Id | Content | Geo | Start | End* | Freq | Unit | File URL | Used in |
|----|---------|-----|------:|-----:|------|------|----------|---------|
| **T_01_01_9_01** | Mouvement démographique (births, deaths, migration) | Canton | ~2014 | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_01/T_01_01_9_01.xlsx) | 2A |
| **T_01_01_13_01** | Bilan démographique | Communes | **2014** | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_01/T_01_01_13_01.xlsx) | 2A |
| **T_01_01_8_02** | Population by sex and age | Canton | long | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_01/T_01_01_8_02.xlsx) | 2A |
| **T_01_01_1_03A** | Population by quinquennial age | Canton | **~1960** | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_01/T_01_01_1_03A.xlsx) | 2A |
| **T_01_01_12_08** | Population by quinquennial age | Communes | varies | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_01/T_01_01_12_08.xlsx) | 2A |
| **T_01_02_1_06** | External migration by age | Canton | **~1989** | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_02/T_01_02_1_06.xlsx) | 2A |
| **T_01_05_1_01** | Private households by type | Canton | **2011** | latest A | **A** | households | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_05/T_01_05_1_01.xlsx) | 2A |
| **T_01_05_3_01** | Population & households by type | Canton | **2011** | latest A | **A** | mixed | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_05/T_01_05_3_01.xlsx) | 2A |
| **T_01_05_3_02** | Population & households by size | Canton | **2011** | latest A | **A** | mixed | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_05/T_01_05_3_02.xlsx) | 2A |
| **T_01_03_4_06** | Fertility rates / TFR | Canton | **~1971** | latest A | **A** | rates | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_03/T_01_03_4_06.xlsx) | 2A context |
| **T_01_03_6_01** | Life expectancy | Canton | **~1985** | latest A | **A** | years | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_03/T_01_03_6_01.xlsx) | 2A context |
| **T_01_03_5_03** | Deaths by age and sex | Canton | **~1969** | latest A | **A** | persons | [xlsx](https://statistique.ge.ch/statistique/tel/domaines/01/01_03/T_01_03_5_03.xlsx) | 2A context |

---

## `raw/bis/` — Swiss residential property prices

| Id | Content | Geo | Start | End* | Freq | Unit | Links | Used in |
|----|---------|-----|------:|-----:|------|------|-------|---------|
| **BIS_CH_RPP_nominal** | Selected RPP, nominal | Switzerland | **1970 Q1** | latest Q | **Q** | index (FRED 2010=100) | [FRED series](https://fred.stlouisfed.org/series/QCHN628BIS) · [CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=QCHN628BIS) · [BIS portal](https://www.bis.org/statistics/dataportal/pp.htm) | long_run |
| **BIS_CH_RPP_real** | Selected RPP, real (CPI-deflated) | Switzerland | **1970 Q1** | latest Q | **Q** | index | [FRED series](https://fred.stlouisfed.org/series/QCHR628BIS) · [CSV](https://fred.stlouisfed.org/graph/fredgraph.csv?id=QCHR628BIS) | long_run |

**Dating in pipeline:** year *T* = **Q4** (year-end), not Q1–Q4 mean. See `TIME_ALIGNMENT.md`.  
**Note:** BIS CH series historically draws on Wüest Partner nationally — related to, not fully independent of, Wüest CH.

---

## `raw/bfs/` — Swiss Residential Property Price Index (IMPI)

| Id | Content | Geo | Start | End* | Freq | Unit | Links | Used in |
|----|---------|-----|------:|-----:|------|------|-------|---------|
| **BFS_IMPI_indexwerte** | IMPI total + sub-indices (houses / condominiums / municipality types) | Switzerland | **~2017 Q1** | latest Q | **Q** | index (Q4 2019=100) | [BFS property prices](https://www.bfs.admin.ch/bfs/en/home/statistics/prices/property-price.html) · [current DAM asset](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36551633/master) | long_run (`bfs_impi_condo` = EGW) |

**Dating in pipeline:** year *T* = **Q4**. DAM asset id **rotates** each quarter — update `step_1/long_run/sources_long_run.json` when BFS publishes a newer “Indexwerte” table.

---

## `raw/sitg/` — geography

| Id | Content | Geo | Start | End | Freq | Links | Used in |
|----|---------|-----|------:|----:|------|-------|---------|
| **sitg_cad_commune** | Commune polygons | Canton GE | snapshot | snapshot | static | [FeatureServer query (GeoJSON)](https://vector.sitg.ge.ch/arcgis/rest/services/Hosted/CAD_COMMUNE/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson) | Step 1 maps |
| **lake_leman.geojson** | Lake outline (local helper) | Lake Geneva | — | — | static | (project file) | Step 1 maps |

---

## Not in `raw/` (cite / local only)

| Id | Publisher | Content | History | Freq | Public raw? | Links | Where |
|----|-----------|---------|--------:|------|-------------|-------|-------|
| **WUEST_PPE_LakeGeneva** | Wüest Partner | Hedonic TPI, owner-occupied apartments | **1985–** | A; Q ~2000– | ❌ | [Interactive indices](https://www.wuestpartner.com/ch-fr/blog/indices-interactifs-des-prix-de-limmobilier-suisse/) · [Export form](https://www.wuest.io/online_services_classic/transaktionspreisindex/index_e.phtml) | `step_1/long_run/local/` via `fetch_wuest_local.py` |
| **WUEST_PPE_Switzerland** | Wüest Partner | Same, Switzerland | **1985–** | A; Q | ❌ | same | same |
| **WUEST_Houses_*** | Wüest Partner | Houses TPI | **1985–** | A; Q | ❌ | same | cite / optional later |
| **IAZI_SWX_Condo** | IAZI / CIFI | SWX IAZI Condominium Price Index | **1981–** (Q from 1996) | A→Q | ❌ | [Methodology PDF](https://www.iazicifi.ch/wp-content/uploads/2024/10/Information_Indices_D.pdf) | prose + link only |

Policy: [`step_1/long_run/README.md`](../step_1/long_run/README.md).

---

## Source JSON → extract

| Manifest | Bucket focus |
|----------|----------------|
| [`step_1/sources.json`](../step_1/sources.json) | Market OCSTAT + SITG |
| [`step_1/long_run/sources_long_run.json`](../step_1/long_run/sources_long_run.json) | Long-run prices: OCSTAT + BIS + BFS; Wüest/IAZI cite-only |

Inventories after extract: `data/raw_inventory_*.json` (git-ignored with other generated inventories when present).
