# Geneva Real Estate — Open-data market analysis

Official OCSTAT transaction statistics on the Geneva (canton) residential market.
Star schema → validated CSVs → 25 charts → LinkedIn PDF brief.

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
data/                     shared star schema — all steps
  fact_price.csv
  fact_volume.csv
  ref/                    dim_*.csv + map_geo_alias.csv
  SCHEMA.md               field definitions and metric constraints
  validate_report.md      0 FAIL · 2 WARN · 16 PASS

raw/                      downloaded source files (git-ignored; created by extract.py)

step_1/                   Step 1 — descriptive statistics snapshot
  scripts/
    extract.py            download OCSTAT xlsx + SITG GeoJSON → raw/
    transform.py          parse Excel → data/ star schema (+ optional geneva.duckdb)
    validate.py           schema and integrity checks → data/validate_report.md
    validate.sql          SQL equivalents of key checks
    viz.py                generate 25 charts → step_1/exports/figures/*.png
    make_pptx.py          full PowerPoint brief (7 slides)
    make_pptx_v2.py       short LinkedIn PowerPoint (3 slides)
    sources.json          declarative list of OCSTAT source URLs
  exports/
    figures/              25 charts, 300 dpi PNG
    brief_copy.json       all chart titles, labels, notes (edit here, not in viz.py)
  report/
    Geneva_Market_Brief_LinkedIn (main).pdf     ← main deliverable
    Geneva_Market_Brief_LinkedIn (main).pptx
    Geneva_Market_Brief_(full).pptx

requirements.txt
.gitignore
```

---

## Quickstart

```bash
pip install -r requirements.txt

# 1. Download source files into raw/
python step_1/scripts/extract.py

# 2. Parse into data/*.csv (+ optional data/geneva.duckdb)
python step_1/scripts/transform.py

# 3. Validate — expect 0 FAIL
python step_1/scripts/validate.py

# 4. Generate charts (25 PNGs)
python step_1/scripts/viz.py

# 5. Build presentation
python step_1/scripts/make_pptx_v2.py   # short LinkedIn brief (3 slides)
python step_1/scripts/make_pptx.py      # full brief (7 slides)
```

Chart titles and captions live in `step_1/exports/brief_copy.json` — edit there, then rerun `viz.py`.

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

## Data licence

Source: **OCSTAT** (Office cantonal de la statistique, Canton of Geneva) · **SITG** (Système d'Information du Territoire à Genève).

Under the [Loi sur la statistique publique cantonale (LStat, B 4 40)](https://silgeneve.ch/legis/data/rsg_b4_40.htm), Art. 21 al. 6:

> *"L'utilisation ou la reproduction des résultats statistiques publiés ou diffusés sous diverses formes est libre, pour autant que leur origine et leur source soient indiquées."*

Translation: **Use and reproduction of published statistical results is free, provided the origin and source are indicated.**

SITG geographic data (CAD_COMMUNE) is released under **Level A — Open Data** (see [SITG conditions](https://sitg.ge.ch/ressources/conditions-utilisation-donnees)): freely usable, including commercially, with mandatory source attribution.

**Attribution used throughout this project:**
`Source: OCSTAT, Canton of Geneva / SITG CAD_COMMUNE`

The CSV files in `data/` are derived aggregates of publicly available OCSTAT tables.
Raw source Excel files are not committed (git-ignored) — run `extract.py` to download them directly from OCSTAT.
