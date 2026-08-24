"""
Step 1 · long_run — build comparable PPE price series for validation charts.

  python step_1/long_run/scripts/transform_long_run.py

Outputs (data/):
  fact_long_run_ppe.csv          annual levels + index_1990 + yoy  [git-ignored — may include Wüest]
  fact_long_run_validation.json  correlations / CAGR / direction agreement  [git-ignored]

Optional local (git-ignored) Wüest exports:
  step_1/long_run/local/wuest_ppe_lake_geneva.csv
  step_1/long_run/local/wuest_ppe_switzerland.csv
  step_1/long_run/local/wuest_houses_lake_geneva.csv
  step_1/long_run/local/wuest_houses_switzerland.csv
  columns: year,index   (or year,value)
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STEP = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = ROOT / "raw"
LOCAL = STEP / "long_run" / "local"
MISSING = {"", "-", "///", "( )", "nan", "None", "…", "..."}


def latest(pattern: str) -> Path:
    files = sorted(p for p in RAW.rglob(pattern) if not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"no files matching {pattern} under {RAW}")
    return files[-1]


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("\xa0", " ").strip()


def to_num(v) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("\xa0", "").replace("'", "").replace(" ", "")
    if s in MISSING or s.startswith("("):
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_year_cell(v) -> int | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        y = int(v)
        return y if 1900 <= y <= 2100 else None
    m = re.match(r"^(\d{4})", str(v).strip())
    return int(m.group(1)) if m else None


def parse_ocstat_canton_4_01(path: Path) -> pd.DataFrame:
    """Canton PPE median CHF/m². Prefer existing+libre (2006+); else all-market ensemble."""
    df = pd.read_excel(path, sheet_name="prix par m2", header=None)
    rows = []
    for i in range(16, len(df)):
        year = parse_year_cell(df.iloc[i, 0])
        if year is None:
            lab = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
            if lab.startswith("(") or lab.lower().startswith("source"):
                break
            continue
        existing = to_num(df.iloc[i, 8]) if df.shape[1] > 8 else None
        ensemble = to_num(df.iloc[i, 23]) if df.shape[1] > 23 else None
        if existing is not None:
            value, segment = existing, "existing_libre"
        elif ensemble is not None:
            value, segment = ensemble, "all_markets_ensemble"
        else:
            continue
        rows.append(
            {
                "series_id": "ocstat_canton_ppe",
                "source": "T_05_05_1_4_01",
                "publisher": "OCSTAT",
                "geography": "Geneva canton",
                "object": "PPE",
                "measure": "median_chf_m2",
                "segment": segment,
                "year": year,
                "value": value,
                "unit": "CHF_per_m2",
            }
        )
    return pd.DataFrame(rows)


def parse_ocstat_ppe_implied_size(path: Path) -> pd.DataFrame:
    """Implied typical size (m²) = median object price (kCHF)×1000 / median CHF/m².

    Same OCSTAT table (T 05.05.1.4.01), sheets `prix` and `prix par m2`.
    Segments: appartements neufs (col 3) and non neufs (col 8) — available from ~2006.
    """
    prix = pd.read_excel(path, sheet_name="prix", header=None)
    m2 = pd.read_excel(path, sheet_name="prix par m2", header=None)
    segments = [
        ("ocstat_ppe_implied_m2_new", "appartements_neufs", 3),
        ("ocstat_ppe_implied_m2_existing", "appartements_non_neufs", 8),
    ]
    rows = []
    n = min(len(prix), len(m2))
    for i in range(16, n):
        year = parse_year_cell(prix.iloc[i, 0])
        if year is None:
            lab = str(prix.iloc[i, 0]).strip() if pd.notna(prix.iloc[i, 0]) else ""
            if lab.startswith("(") or lab.lower().startswith("source"):
                break
            continue
        for sid, segment, col in segments:
            p_kchf = to_num(prix.iloc[i, col]) if prix.shape[1] > col else None
            p_m2 = to_num(m2.iloc[i, col]) if m2.shape[1] > col else None
            if p_kchf is None or p_m2 is None or p_m2 == 0:
                continue
            rows.append(
                {
                    "series_id": sid,
                    "source": "T_05_05_1_4_01",
                    "publisher": "OCSTAT",
                    "geography": "Geneva canton",
                    "object": "PPE_implied_size",
                    "measure": "implied_m2_median_proxy",
                    "segment": segment,
                    "year": year,
                    "value": float(p_kchf) * 1000.0 / float(p_m2),
                    "unit": "m2",
                }
            )
    return pd.DataFrame(rows)


def parse_ocstat_canton_houses_3_01(path: Path) -> pd.DataFrame:
    """Canton houses median CHF/object (thousands). Prefer non-neuves; else ensemble.

    Layout (sheet `prix`): neuves cols 1–4, non-neuves 6–9, ensemble 11–14.
    Early years (to ~2003) publish ensemble only.
    """
    df = pd.read_excel(path, sheet_name="prix", header=None)
    rows = []
    for i in range(13, len(df)):
        year = parse_year_cell(df.iloc[i, 0])
        if year is None:
            lab = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
            if lab.startswith("(") or lab.lower().startswith("source"):
                break
            continue
        existing = to_num(df.iloc[i, 8]) if df.shape[1] > 8 else None  # non-neuves median
        ensemble = to_num(df.iloc[i, 13]) if df.shape[1] > 13 else None
        if existing is not None:
            value, segment = existing, "existing_non_new"
        elif ensemble is not None:
            value, segment = ensemble, "all_markets_ensemble"
        else:
            continue
        rows.append(
            {
                "series_id": "ocstat_canton_houses",
                "source": "T_05_05_1_3_01",
                "publisher": "OCSTAT",
                "geography": "Geneva canton",
                "object": "Houses",
                "measure": "median_chf_object_thousands",
                "segment": segment,
                "year": year,
                "value": value,
                "unit": "kCHF_per_object",
            }
        )
    return pd.DataFrame(rows)


def parse_ocstat_commune_geo(path: Path, geo_key: str, series_id: str, geography: str) -> pd.DataFrame:
    """Commune/canton row from T_05_05_1_4_03 (year sheets). Early sheets: n,p25,med,p75 only."""
    rows = []
    for sheet in pd.ExcelFile(path).sheet_names:
        if not str(sheet).isdigit():
            continue
        year = int(sheet)
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        for _, row in df.iloc[16:].iterrows():
            if pd.isna(row.iloc[0]):
                continue
            lab = str(row.iloc[0]).strip()
            if lab.startswith("(") or lab.lower().startswith("source"):
                break
            key = norm_name(lab)
            if geo_key == "geneve" and not key.startswith("geneve"):
                continue
            if geo_key == "canton" and key != "canton":
                continue
            if len(row) <= 5:
                value, segment = to_num(row.iloc[3]), "ensemble_early_layout"
            else:
                existing = to_num(row.iloc[8])
                ensemble = to_num(row.iloc[23]) if len(row) > 23 else None
                if existing is not None:
                    value, segment = existing, "existing_libre"
                elif ensemble is not None:
                    value, segment = ensemble, "all_markets_ensemble"
                else:
                    continue
            if value is None:
                continue
            rows.append(
                {
                    "series_id": series_id,
                    "source": "T_05_05_1_4_03",
                    "publisher": "OCSTAT",
                    "geography": geography,
                    "object": "PPE",
                    "measure": "median_chf_m2",
                    "segment": segment,
                    "year": year,
                    "value": value,
                    "unit": "CHF_per_m2",
                }
            )
            break
    return pd.DataFrame(rows)


def parse_bis_annual(path: Path, series_id: str, real: bool) -> pd.DataFrame:
    """BIS RPP via FRED. Use **Q4 (year-end)** as the annual point, not Q1–Q4 mean.

    FRED dates quarters as the first day of the quarter (Q1=Jan 1, Q4=Oct 1).
    """
    raw = pd.read_csv(path)
    raw.columns = [c.strip().lower() for c in raw.columns]
    date_col = "observation_date" if "observation_date" in raw.columns else raw.columns[0]
    val_col = [c for c in raw.columns if c != date_col][0]
    d = raw.copy()
    d["date"] = pd.to_datetime(d[date_col])
    d["year"] = d["date"].dt.year
    d["quarter"] = d["date"].dt.quarter
    d["value"] = pd.to_numeric(d[val_col], errors="coerce")
    ann = d[d["quarter"] == 4][["year", "value"]].dropna().copy()
    # If latest year has no Q4 yet, keep last available quarter for that year only
    latest_year = int(d["year"].max())
    if latest_year not in set(ann["year"]):
        tail = d[d["year"] == latest_year].sort_values("quarter").iloc[-1]
        ann = pd.concat(
            [ann, pd.DataFrame([{"year": latest_year, "value": float(tail["value"])}])],
            ignore_index=True,
        )
    ann["series_id"] = series_id
    ann["source"] = "BIS_via_FRED"
    ann["publisher"] = "BIS"
    ann["geography"] = "Switzerland"
    ann["object"] = "residential_all"
    ann["measure"] = "rpp_real_index" if real else "rpp_nominal_index"
    ann["segment"] = "year_end_Q4"
    ann["unit"] = "index_native"
    return ann[
        [
            "series_id",
            "source",
            "publisher",
            "geography",
            "object",
            "measure",
            "segment",
            "year",
            "value",
            "unit",
        ]
    ]


def _bfs_impi_annual(qdf: pd.DataFrame, value_col: str) -> pd.DataFrame:
    ann = qdf[qdf["quarter"] == 4][["year", value_col]].rename(columns={value_col: "value"}).copy()
    latest_year = int(qdf["year"].max())
    if latest_year not in set(ann["year"]):
        tail = qdf[qdf["year"] == latest_year].sort_values("quarter").iloc[-1]
        ann = pd.concat(
            [ann, pd.DataFrame([{"year": latest_year, "value": float(tail[value_col])}])],
            ignore_index=True,
        )
    return ann


def parse_bfs_impi(path: Path) -> pd.DataFrame:
    """BFS IMPI — EGW (condo) + EFH (houses) totals, **Q4 year-end** (~2017–)."""
    df = pd.read_excel(path, sheet_name="T2", header=None)
    rows = []
    for i in range(11, len(df)):
        lab = df.iloc[i, 0]
        if lab is None or (isinstance(lab, float) and pd.isna(lab)):
            continue
        s = str(lab).strip()
        m = re.match(r"^Q([1-4])\s+(\d{4})$", s, re.I)
        if not m:
            if s.lower().startswith("source") or s.startswith("("):
                break
            continue
        q, year = int(m.group(1)), int(m.group(2))
        efh = to_num(df.iloc[i, 7])
        egw = to_num(df.iloc[i, 13])
        if egw is None and efh is None:
            continue
        rows.append({"year": year, "quarter": q, "egw": egw, "efh": efh})
    if not rows:
        raise ValueError(f"no IMPI quarterly rows in {path.name}")
    qdf = pd.DataFrame(rows)
    frames = []
    for value_col, sid, obj, measure in [
        ("egw", "bfs_impi_condo", "PPE", "impi_egw_index"),
        ("efh", "bfs_impi_houses", "Houses", "impi_efh_index"),
    ]:
        if qdf[value_col].notna().sum() == 0:
            continue
        ann = _bfs_impi_annual(qdf.dropna(subset=[value_col]), value_col)
        ann["series_id"] = sid
        ann["source"] = "BFS_IMPI"
        ann["publisher"] = "BFS/OFS"
        ann["geography"] = "Switzerland"
        ann["object"] = obj
        ann["measure"] = measure
        ann["segment"] = "year_end_Q4_base_2019q4"
        ann["unit"] = "index_native"
        frames.append(
            ann[
                [
                    "series_id",
                    "source",
                    "publisher",
                    "geography",
                    "object",
                    "measure",
                    "segment",
                    "year",
                    "value",
                    "unit",
                ]
            ]
        )
    return pd.concat(frames, ignore_index=True)


def load_wuest_csv(
    path: Path, series_id: str, geography: str, *, object_: str = "PPE"
) -> pd.DataFrame | None:
    if not path.exists():
        return None
    d = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in d.columns}
    year_c = cols.get("year")
    val_c = cols.get("index") or cols.get("value") or cols.get("idx")
    if year_c is None or val_c is None:
        raise ValueError(f"{path.name}: need columns year + index|value")
    out = pd.DataFrame(
        {
            "series_id": series_id,
            "source": "Wuest_Partner_local_export",
            "publisher": "Wüest Partner",
            "geography": geography,
            "object": object_,
            "measure": "hedonic_transaction_index",
            "segment": "published_annual",
            "year": pd.to_numeric(d[year_c], errors="coerce").astype("Int64"),
            "value": pd.to_numeric(d[val_c], errors="coerce"),
            "unit": "index_native",
        }
    )
    return out.dropna(subset=["year", "value"]).astype({"year": int})


def parse_ocstat_cpi_02(path: Path) -> pd.DataFrame:
    """Annual Swiss + Geneva CPI (Sep 1966=100). Prefer annual mean; fallback Dec."""
    df = pd.read_excel(path, sheet_name=0, header=None)
    rows = []
    for i in range(15, len(df)):
        year = parse_year_cell(df.iloc[i, 0])
        if year is None:
            lab = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
            if lab.startswith("(") or lab.lower().startswith("source"):
                break
            continue
        for sid, geo, mean_c, dec_c in [
            ("ocstat_cpi_switzerland", "Switzerland", 2, 1),
            ("ocstat_cpi_geneva", "Geneva canton", 7, 6),
        ]:
            mean = to_num(df.iloc[i, mean_c]) if df.shape[1] > mean_c else None
            dec = to_num(df.iloc[i, dec_c]) if df.shape[1] > dec_c else None
            if mean is not None:
                value, segment = mean, "annual_mean"
            elif dec is not None:
                value, segment = dec, "december"
            else:
                continue
            rows.append(
                {
                    "series_id": sid,
                    "source": "T_05_02_02",
                    "publisher": "OCSTAT",
                    "geography": geo,
                    "object": "CPI",
                    "measure": "cpi_index",
                    "segment": segment,
                    "year": year,
                    "value": value,
                    "unit": "index_sep1966_100",
                }
            )
    return pd.DataFrame(rows)


def parse_ocstat_construction_3_01(path: Path) -> pd.DataFrame:
    """Geneva housing construction price index (1 Apr 1988=100). Prefer October = year-end."""
    df = pd.read_excel(path, sheet_name=0, header=None)
    by_year: dict[int, dict] = {}
    for i in range(13, len(df)):
        lab = df.iloc[i, 0]
        if lab is None or (isinstance(lab, float) and pd.isna(lab)):
            continue
        s = str(lab).strip()
        if s.startswith("(") or s.lower().startswith("source"):
            break
        m = re.match(r"^(Avril|Octobre)\s+(\d{4})", s, re.I)
        if not m:
            continue
        month, year = m.group(1).lower(), int(m.group(2))
        val = to_num(df.iloc[i, 1])
        if val is None:
            continue
        slot = by_year.setdefault(year, {})
        slot["october" if month.startswith("oct") else "april"] = val
    rows = []
    for year, slot in sorted(by_year.items()):
        if "october" in slot:
            value, segment = slot["october"], "october_year_end"
        else:
            value, segment = slot["april"], "april_only"
        rows.append(
            {
                "series_id": "ocstat_construction_housing_ge",
                "source": "T_05_03_1_01",
                "publisher": "OCSTAT",
                "geography": "Geneva canton",
                "object": "Construction",
                "measure": "construction_housing_index",
                "segment": segment,
                "year": year,
                "value": value,
                "unit": "index_apr1988_100",
            }
        )
    return pd.DataFrame(rows)


def parse_bfs_construction_mfh(path: Path) -> pd.DataFrame:
    """BFS Swiss construction — Neubau Mehrfamilienhaus, Schweiz, Oct year-end (base Oct 1998=100)."""
    df = pd.read_excel(path, sheet_name="1998", header=None)
    months = [str(df.iloc[4, c]).strip().lower() if pd.notna(df.iloc[4, c]) else "" for c in range(df.shape[1])]
    years = [parse_year_cell(df.iloc[5, c]) for c in range(df.shape[1])]

    target_i = None
    in_swiss = False
    for i in range(6, len(df)):
        code = str(df.iloc[i, 0]).strip() if pd.notna(df.iloc[i, 0]) else ""
        label = str(df.iloc[i, 1]).strip() if pd.notna(df.iloc[i, 1]) else ""
        if code == "<REG_01>" or label == "Schweiz":
            in_swiss = True
            continue
        if code.startswith("<REG_") and in_swiss and code != "<REG_01>":
            break
        if in_swiss and code == "<OBJ_05>":
            target_i = i
            break
        if in_swiss and (
            "Mehrfamilienhaus" in label
            and "Holz" not in label
            and "Renovation" not in label
            and "Neubau" in label
        ):
            target_i = i
            break
    if target_i is None:
        raise ValueError(f"Neubau Mehrfamilienhaus (Schweiz) not found in {path.name}")

    by_year: dict[int, float] = {}
    for c in range(3, df.shape[1]):
        y = years[c]
        if y is None:
            continue
        val = to_num(df.iloc[target_i, c])
        if val is None:
            continue
        if "oktober" in months[c] or "october" in months[c]:
            by_year[y] = val
        elif y not in by_year and ("avril" in months[c] or "april" in months[c]):
            by_year[y] = val

    return pd.DataFrame(
        [
            {
                "series_id": "bfs_construction_mfh_ch",
                "source": "BFS_CONSTRUCTION_MULTIBASE",
                "publisher": "BFS/OFS",
                "geography": "Switzerland",
                "object": "Construction",
                "measure": "construction_mfh_new_index",
                "segment": "october_year_end_base_1998",
                "year": y,
                "value": v,
                "unit": "index_oct1998_100",
            }
            for y, v in sorted(by_year.items())
        ]
    )


def add_index_and_yoy(df: pd.DataFrame, base_year: int = 1990) -> pd.DataFrame:
    parts = []
    for sid, g in df.groupby("series_id", sort=False):
        g = g.sort_values("year").copy()
        base = g.loc[g["year"] == base_year, "value"]
        if base.empty or float(base.iloc[0]) == 0:
            g2 = g[g["year"] >= base_year]
            if g2.empty:
                g["index_1990"] = pd.NA
            else:
                g["index_1990"] = g["value"] / float(g2.iloc[0]["value"]) * 100.0
        else:
            g["index_1990"] = g["value"] / float(base.iloc[0]) * 100.0
        # Secondary rebase for short official series (IMPI from ~2017)
        b2017 = g.loc[g["year"] == 2017, "value"]
        if not b2017.empty and float(b2017.iloc[0]) != 0:
            g["index_2017"] = g["value"] / float(b2017.iloc[0]) * 100.0
        else:
            g["index_2017"] = pd.NA
        g["yoy_pct"] = g["value"].pct_change() * 100.0
        parts.append(g)
    out = pd.concat(parts, ignore_index=True)

    # Real index vs Geneva CPI (1990=100): housing prices only
    cpi = out.loc[out["series_id"] == "ocstat_cpi_geneva", ["year", "index_1990"]].dropna()
    cpi_map = cpi.set_index("year")["index_1990"].to_dict()
    real_vals = []
    for _, row in out.iterrows():
        if row["object"] in ("PPE", "Houses", "residential_all") and pd.notna(row["index_1990"]):
            c = cpi_map.get(int(row["year"]))
            if c is not None and float(c) != 0:
                real_vals.append(float(row["index_1990"]) / float(c) * 100.0)
                continue
        real_vals.append(pd.NA)
    out["index_real_1990"] = real_vals
    return out


def turning_points(yoy: pd.Series) -> list[int]:
    """Years where YoY sign flips (uses index labels = years)."""
    s = yoy.dropna()
    if len(s) < 3:
        return []
    signs = s.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    years = []
    prev = None
    for year, sig in signs.items():
        if sig == 0:
            continue
        if prev is not None and sig != prev:
            years.append(int(year))
        prev = sig
    return years


def validate(long_df: pd.DataFrame) -> dict:
    idx = long_df.pivot_table(index="year", columns="series_id", values="index_1990", aggfunc="first")
    yoy = long_df.pivot_table(index="year", columns="series_id", values="yoy_pct", aggfunc="first")

    def pair(a: str, b: str) -> dict | None:
        if a not in idx.columns or b not in idx.columns:
            return None
        m = idx[[a, b]].dropna()
        my = yoy[[a, b]].dropna()
        if len(m) < 5:
            return None
        # direction agreement on overlapping YoY
        dir_agree = None
        if len(my) >= 5:
            same = ((my[a] > 0) & (my[b] > 0)) | ((my[a] < 0) & (my[b] < 0)) | ((my[a] == 0) & (my[b] == 0))
            dir_agree = float(same.mean())
        # lag correlations on YoY
        lags = {}
        if len(my) >= 6:
            for lag in (-1, 0, 1):
                if lag == 0:
                    lags["0"] = float(my[a].corr(my[b]))
                elif lag > 0:
                    lags[str(lag)] = float(my[a].corr(my[b].shift(lag)))
                else:
                    lags[str(lag)] = float(my[a].shift(-lag).corr(my[b]))
        # CAGR on index
        def cagr(series: pd.Series) -> float | None:
            s = series.dropna()
            if len(s) < 2 or s.iloc[0] <= 0 or s.iloc[-1] <= 0:
                return None
            n = int(s.index[-1] - s.index[0])
            if n <= 0:
                return None
            return float((s.iloc[-1] / s.iloc[0]) ** (1 / n) - 1)

        return {
            "pair": [a, b],
            "n_years_index": int(len(m)),
            "year_start": int(m.index.min()),
            "year_end": int(m.index.max()),
            "corr_index_1990": float(m[a].corr(m[b])),
            "corr_yoy": float(my[a].corr(my[b])) if len(my) >= 5 else None,
            "corr_yoy_lags": lags or None,
            "direction_agreement_yoy": dir_agree,
            "cagr_a": cagr(m[a]),
            "cagr_b": cagr(m[b]),
            "turning_points_a": turning_points(my[a]) if a in my else [],
            "turning_points_b": turning_points(my[b]) if b in my else [],
        }

    pairs = []
    for a, b in [
        ("ocstat_canton_ppe", "ocstat_city_ppe"),
        ("ocstat_canton_ppe", "wuest_ppe_lake_geneva"),
        ("ocstat_canton_ppe", "bis_ch_rpp_nominal"),
        ("ocstat_canton_ppe", "bfs_impi_condo"),
        ("wuest_ppe_lake_geneva", "wuest_ppe_switzerland"),
        ("ocstat_canton_ppe", "wuest_ppe_switzerland"),
        ("wuest_ppe_switzerland", "bis_ch_rpp_nominal"),
        ("bfs_impi_condo", "bis_ch_rpp_nominal"),
        ("bfs_impi_condo", "wuest_ppe_switzerland"),
        ("ocstat_canton_houses", "wuest_houses_lake_geneva"),
        ("ocstat_canton_houses", "wuest_houses_switzerland"),
        ("wuest_houses_lake_geneva", "wuest_houses_switzerland"),
        ("ocstat_canton_houses", "bfs_impi_houses"),
        ("bfs_impi_houses", "wuest_houses_switzerland"),
        ("ocstat_cpi_geneva", "ocstat_cpi_switzerland"),
        ("ocstat_canton_ppe", "ocstat_construction_housing_ge"),
        ("ocstat_construction_housing_ge", "bfs_construction_mfh_ch"),
    ]:
        r = pair(a, b)
        if r:
            pairs.append(r)

    available = sorted(long_df["series_id"].unique().tolist())
    return {
        "base_year": 1990,
        "series_available": available,
        "wuest_loaded": [s for s in available if s.startswith("wuest_")],
        "pairs": pairs,
        "notes": [
            "OCSTAT canton/city PPE: existing+libre from 2006; earlier years use ensemble layout (documented in segment).",
            "OCSTAT houses: CHF/object (thousands); prefer non-neuves from ~2004, else ensemble — not CHF/m².",
            "OCSTAT = observed transaction median; Wüest = quality-adjusted hedonic index — levels need not match.",
            "BIS CH historically related to Wüest nationally — use as open control, not fully independent of Wüest CH.",
            "Dating: OCSTAT year T = calendar-year transaction median; Wüest = published annual (1985=100); BIS/BFS IMPI = year-end Q4.",
            "BFS IMPI condo (EGW) / houses (EFH) start ~2017; compare via index_2017 / recent-window charts.",
            "Deflator: OCSTAT Geneva CPI annual mean (T_05_02_02); index_real_1990 = index_1990 / CPI_1990 * 100.",
            "Construction: OCSTAT housing construction (T_05_03_1_01, Oct preferred); BFS CH Neubau Mehrfamilienhaus from 1998.",
            "Implied PPE size (m²): median kCHF×1000 / median CHF/m² from T_05_05_1_4_01 (neufs vs non-neufs, ~2006+).",
        ],
    }


def main() -> int:
    path_4_01 = latest("*_T_05_05_1_4_01.xlsx")
    frames = [
        parse_ocstat_canton_4_01(path_4_01),
        parse_ocstat_ppe_implied_size(path_4_01),
        parse_ocstat_commune_geo(
            latest("*_T_05_05_1_4_03.xlsx"), "geneve", "ocstat_city_ppe", "Geneva city"
        ),
        parse_ocstat_canton_houses_3_01(latest("*_T_05_05_1_3_01.xlsx")),
        parse_ocstat_cpi_02(latest("*_T_05_02_02.xlsx")),
        parse_ocstat_construction_3_01(latest("*_T_05_03_1_01.xlsx")),
        parse_bfs_construction_mfh(latest("*_BFS_CONSTRUCTION_MULTIBASE.xlsx")),
        parse_bis_annual(latest("*_BIS_CH_RPP_nominal.csv"), "bis_ch_rpp_nominal", real=False),
        parse_bis_annual(latest("*_BIS_CH_RPP_real.csv"), "bis_ch_rpp_real", real=True),
        parse_bfs_impi(latest("*_BFS_IMPI_indexwerte.xlsx")),
    ]
    for fname, sid, geo, obj in [
        ("wuest_ppe_lake_geneva.csv", "wuest_ppe_lake_geneva", "Lake Geneva", "PPE"),
        ("wuest_ppe_switzerland.csv", "wuest_ppe_switzerland", "Switzerland", "PPE"),
        ("wuest_houses_lake_geneva.csv", "wuest_houses_lake_geneva", "Lake Geneva", "Houses"),
        ("wuest_houses_switzerland.csv", "wuest_houses_switzerland", "Switzerland", "Houses"),
    ]:
        w = load_wuest_csv(LOCAL / fname, sid, geo, object_=obj)
        if w is not None:
            frames.append(w)
            print(f"  loaded local Wuest: {fname} ({len(w)} years)")
        else:
            print(f"  missing local Wuest (optional): {LOCAL / fname}")

    long_df = add_index_and_yoy(pd.concat(frames, ignore_index=True))
    DATA.mkdir(parents=True, exist_ok=True)
    out_csv = DATA / "fact_long_run_ppe.csv"
    long_df.to_csv(out_csv, index=False)
    print(f"  {out_csv.relative_to(ROOT)}  ({len(long_df)} rows, {long_df.series_id.nunique()} series)")

    val = validate(long_df)
    out_json = DATA / "fact_long_run_validation.json"
    out_json.write_text(json.dumps(val, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {out_json.relative_to(ROOT)}")
    for p in val["pairs"]:
        print(
            f"    {p['pair'][0]} vs {p['pair'][1]}: "
            f"corr_idx={p['corr_index_1990']:.3f}, corr_yoy={p['corr_yoy']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
