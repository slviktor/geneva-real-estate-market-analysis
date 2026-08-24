# Geneva Real Estate — Open-data market analysis

Official OCSTAT transaction statistics on the Geneva (canton) residential market,
plus long-run benchmarks (BIS, BFS IMPI; optional local Wüest charts).

**Stack:** Python · DuckDB · pandas · matplotlib · python-pptx

---

## Key findings (Step 1 — 2024 / Q2 2026)

| Metric | Value |
|--------|-------|
| Existing apartments (PPE), free market, canton 2024 | **CHF 10,853/m²** |
| Same segment, City of Geneva 2024 | **CHF 12,597/m²** (+16.1% vs canton) |
| Commune range | Vernier 7,182 → Genève 12,597 CHF/m² (1.8×) |
| House median, canton 2024 | **CHF 2.19M per dwelling** |
| 50% of apartment transactions | CHF 1.0–1.9M per object |
| 50% of house transactions | CHF 1.6–3.2M per dwelling |

**Practical takeaways:**

- "New is cheaper" at canton level is a composition effect — within each commune, new apartments cost 17–29% more.
- Two stagnation cycles in 35 years: 1990–2003 (–24%, full cycle 13 years) and 2012–2020 (–13%, full cycle 8 years). Both fully recovered; each new peak exceeded the previous one.
- Three macro shocks (2008, COVID, 2022 rate hikes) — no sustained median decline. The premium segment (P75) corrects 2–3× faster than P25.

> Apartments are priced in CHF/m² (annual OCSTAT median).
> Houses are priced in CHF per dwelling — OCSTAT does not publish living-space CHF/m² for houses.

---

## Repository layout

```
data/                     shared star schema (Step 1 facts + dims)
raw/                      downloads (git-ignored); catalogue in raw/README.md
scripts/extract.py        shared downloader

step_1/                   Market Analytics (levels, volumes, maps, brief)
  sources.json
  scripts/                transform, validate, viz, pptx
  exports/  report/
  long_run/               Long-run price benchmarks (module inside Step 1)
    README.md             Wüest / IAZI citation policy
    TIME_ALIGNMENT.md     dating conventions (annual vs Q4)
    sources_long_run.json
    local/                private Wüest exports (git-ignored)
```

**Not published yet:** `step_2/` (Effective Demand — work in progress) is local-only.

---

## Quickstart

```bash
pip install -r requirements.txt

# Download Step 1 sources
python scripts/extract.py --sources step_1/sources.json

# Step 1 pipeline
python step_1/scripts/transform.py
python step_1/scripts/validate.py
python step_1/scripts/viz.py
python step_1/scripts/make_pptx_v2.py

# Long-run benchmarks (OCSTAT + BIS + BFS; optional local Wüest)
python scripts/extract.py --sources step_1/long_run/sources_long_run.json
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
# Optional Wüest (local only — never committed):
#   python step_1/long_run/scripts/fetch_wuest_local.py
#   then re-run transform_long_run.py + viz_long_run.py
```

Chart titles: edit `step_1/exports/brief_copy.json` or `step_1/long_run/exports/brief_copy_long_run.json`, then re-run the matching viz script.

---

## Data coverage and constraints

| Series | Unit | Grain | Latest |
|--------|------|-------|--------|
| Apartment prices (existing, free market) | CHF/m² median + P25–P75 | Annual, canton + communes | **2024** |
| House prices | CHF/dwelling median + P25–P75 | Annual communes / quarterly canton | Annual **2024**, quarterly **Q2 2026** |
| Transaction mix (new vs existing) | Average ticket | Quarterly canton | **Q2 2026** |
| Existing-stock price range | CHF/object P25–median–P75 | Quarterly canton | **Q2 2026** |
| Activity | n transactions | Annual + quarterly | **Q2 2026** |

**Hard constraints:**
- CHF/m² for houses: not published by OCSTAT.
- Quarterly CHF/m² for apartments: not published by OCSTAT.
- Quartile distributions for *new* stock: annual only (CHF/m², apartments).
- Missing communes ≠ zero price; `n < 10` → quartiles suppressed by OCSTAT.
- No interpolation of missing periods.

---

## Data licence (summary)

| Source | Publish raw / processed? | Attribution |
|--------|--------------------------|-------------|
| **OCSTAT** | ✅ | Office cantonal de la statistique, Canton of Geneva |
| **SITG** | ✅ | SITG CAD_COMMUNE (Open Data Level A) |
| **BIS** RPP (via FRED) | ✅ | BIS Residential Property Price database; note “via FRED” |
| **BFS** IMPI | ✅ | Federal Statistical Office — Swiss Residential Property Price Index |
| **Wüest Partner** | ❌ machine-readable series | Charts OK with *Source: Wüest Partner*; see `step_1/long_run/README.md` |
| **IAZI** | ❌ | Text + link only |

OCSTAT ([LStat Art. 21 al. 6](https://silgeneve.ch/legis/data/rsg_b4_40.htm)): use/reproduction free with source indicated.

Raw downloads under `raw/` are git-ignored — run `extract.py`.  
Long-run fact tables that may embed Wüest (`data/fact_long_run_ppe.csv`, `data/fact_long_run_validation.json`) are also git-ignored.

Full catalogue: [`raw/README.md`](raw/README.md).
