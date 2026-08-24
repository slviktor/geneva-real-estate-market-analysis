"""
Parse raw OCSTAT / SITG into ref catalogs + facts (CSV) and geneva.duckdb.

  python scripts/transform.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

try:
    import duckdb
except ImportError:
    duckdb = None

STEP_ROOT = Path(__file__).resolve().parents[1]   # step_1/
ROOT = STEP_ROOT.parent                             # repo root (data/, raw/ live here)
RAW = ROOT / "raw"
DATA = ROOT / "data"
REF = DATA / "ref"

MISSING = {"", "-", "///", "( )", "nan", "None", "…", "..."}


def latest(pattern: str) -> Path:
    files = sorted(p for p in RAW.rglob(pattern) if not p.name.startswith("~$"))
    if not files:
        raise FileNotFoundError(f"no files matching {pattern} under {RAW}")
    return files[-1]


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s


def to_num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return pd.NA
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    t = str(v).strip().replace("\xa0", " ").replace("'", "").replace(" ", "")
    if t in MISSING:
        return pd.NA
    t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return pd.NA


_YEAR_RE = re.compile(r"^(\d{4})(?:\s*[pP])?\s*$")


def parse_year_cell(v) -> tuple[int | None, int]:
    """OCSTAT writes provisional years as '2025 p'."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None, 0
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        y = int(v)
        return (y, 0) if 1900 <= y <= 2100 else (None, 0)
    t = str(v).strip().replace("\xa0", " ")
    m = _YEAR_RE.match(t)
    if not m:
        return None, 0
    return int(m.group(1)), 0 if t[:4] == t.strip() else 1


def quarter_num(v) -> int | None:
    m = {"I": 1, "II": 2, "III": 3, "IV": 4, "1": 1, "2": 2, "3": 3, "4": 4}
    t = str(v).strip()
    return m.get(t)


# --- catalogs ---------------------------------------------------------------

TYPE_ROWS = [
    # type_id, ocstat_label, segment_v1, is_ensemble, condition
    ("land", "Terrain non bâti", None, 0, None),
    ("house_existing", "Maison individuelle non neuve", "house", 0, "existing"),
    ("house_new", "Maison individuelle neuve", "house", 0, "new"),
    ("house", "Maison individuelle — Ensemble", "house", 1, "all"),
    ("multi_unit", "Bâtiment à plusieurs logements", None, 0, None),
    ("mixed", "Bâtiment mixte (activité et habitation)", None, 0, None),
    ("commercial", "Bât. admin., commercial ou industriel", None, 0, None),
    ("ppe_existing", "Appartement en PPE non neuf", "ppe", 0, "existing"),
    ("ppe_new", "Appartement en PPE neuf", "ppe", 0, "new"),
    ("ppe", "Appartement en PPE — Ensemble", "ppe", 1, "all"),
    ("other", "Autre", None, 0, None),
]

COLS_1101 = {
    2: "land",
    3: "house_existing",
    4: "house_new",
    5: "house",
    6: "multi_unit",
    7: "mixed",
    8: "commercial",
    9: "ppe_existing",
    10: "ppe_new",
    11: "ppe",
}
COLS_1201 = {
    1: "land",
    2: "house_existing",
    3: "house_new",
    4: "house",
    5: "multi_unit",
    6: "mixed",
    7: "commercial",
    8: "ppe_existing",
    9: "ppe_new",
    10: "ppe",
    11: "other",
}


def build_dim_geo() -> pd.DataFrame:
    path = latest("*_sitg_cad_commune.geojson")
    gj = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    geneve_bfs = None
    for ft in gj["features"]:
        p = ft["properties"]
        name = str(p.get("commune") or "").strip()
        bfs = p.get("no_com_federal")
        cantonal = p.get("no_comm")
        is_secteur = name.startswith("Genève-")
        if is_secteur:
            geneve_bfs = geneve_bfs or bfs
        rows.append(
            {
                "name_sitg": name,
                "name_ocstat": None if is_secteur else name,
                "abreviation": p.get("abreviation"),
                "bfs_id": int(bfs) if bfs is not None else pd.NA,
                "no_cantonal": int(cantonal) if cantonal is not None else pd.NA,
                "grain": "secteur" if is_secteur else "commune",
                "parent_bfs_id": pd.NA,
                "has_polygon": 1,
            }
        )
    dim = pd.DataFrame(rows)
    extras = [
        {
            "name_sitg": "Canton de Genève",
            "name_ocstat": "Canton",
            "abreviation": "GE",
            "bfs_id": 0,
            "no_cantonal": pd.NA,
            "grain": "canton",
            "parent_bfs_id": pd.NA,
            "has_polygon": 0,
        }
    ]
    if geneve_bfs is not None:
        dim.loc[dim["grain"] == "secteur", "parent_bfs_id"] = int(geneve_bfs)
        # OCSTAT publishes one «Genève»; SITG only has 4 secteurs. Facts join the
        # parent commune; map later dissolves secteurs on parent_bfs_id.
        extras.append(
            {
                "name_sitg": "Genève",
                "name_ocstat": "Genève",
                "abreviation": "GE-Ville",
                "bfs_id": int(geneve_bfs),
                "no_cantonal": pd.NA,
                "grain": "commune",
                "parent_bfs_id": pd.NA,
                "has_polygon": 0,
            }
        )
    dim = pd.concat([dim, pd.DataFrame(extras)], ignore_index=True)
    dim["geo_id"] = dim.apply(
        lambda r: f"{int(r.bfs_id):04d}" if pd.notna(r.bfs_id) and r.grain != "secteur"
        else f"{int(r.bfs_id):04d}-{r.abreviation}" if r.grain == "secteur"
        else r.name_sitg,
        axis=1,
    )
    dim["name_norm"] = dim["name_ocstat"].fillna(dim["name_sitg"]).map(norm_name)
    return dim[
        [
            "geo_id",
            "grain",
            "bfs_id",
            "parent_bfs_id",
            "no_cantonal",
            "name_ocstat",
            "name_sitg",
            "abreviation",
            "name_norm",
            "has_polygon",
        ]
    ]


# OCSTAT spelling → BFS. Keys after norm_name(). Keep explicit; do not fuzzy-match.
GEO_ALIAS = {
    "le grand-saconnex": "6623",
    "carouge (ge)": "6608",
    "carouge ge": "6608",
}


def geo_keys(dim: pd.DataFrame) -> pd.DataFrame:
    """Join grain only: commune + canton. Secteurs stay for the map dissolve."""
    return dim.loc[dim["grain"].isin(("commune", "canton"))].copy()


def geo_lookup(dim: pd.DataFrame, label: str) -> str | None:
    n = norm_name(label)
    if not n or n.startswith("(") or n.startswith("source"):
        return None
    if n.startswith("autres communes"):
        return None  # residual groups: membership changes by year/table
    if n in GEO_ALIAS:
        return GEO_ALIAS[n]
    keys = geo_keys(dim)
    hit = keys.loc[keys["name_norm"] == n]
    if len(hit) == 1:
        return hit.iloc[0]["geo_id"]
    hit2 = keys.loc[keys["name_sitg"].map(norm_name) == n]
    if len(hit2) == 1:
        return hit2.iloc[0]["geo_id"]
    return None


def build_geo_alias_table(dim: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in geo_keys(dim).iterrows():
        for src, col in (("ocstat", "name_ocstat"), ("sitg", "name_sitg")):
            lab = r[col]
            if pd.isna(lab) or not str(lab).strip():
                continue
            rows.append(
                {
                    "label": str(lab).strip(),
                    "label_norm": norm_name(lab),
                    "geo_id": r["geo_id"],
                    "source": src,
                }
            )
    for lab, geo_id in GEO_ALIAS.items():
        rows.append({"label": lab, "label_norm": lab, "geo_id": geo_id, "source": "alias"})
    out = pd.DataFrame(rows).drop_duplicates(["label_norm", "geo_id", "source"])
    return out.sort_values(["geo_id", "source", "label_norm"]).reset_index(drop=True)


# --- parsers ----------------------------------------------------------------

def parse_volume_quarterly(path: Path) -> pd.DataFrame:
    frames = []
    for sheet, metric in (("Nombre", "n"), ("Valeur", "value_kchf")):
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        recs = []
        last_y, last_p = None, 0
        for _, row in df.iloc[12:].iterrows():
            y, p = parse_year_cell(row.iloc[0])
            if y is not None:
                last_y, last_p = y, p
            q = quarter_num(row.iloc[1])
            if last_y is None or q is None:
                continue
            for col, type_id in COLS_1101.items():
                recs.append(
                    {
                        "source": "T_05_05_1_1_01",
                        "freq": "Q",
                        "year": last_y,
                        "quarter": q,
                        "type_id": type_id,
                        "is_provisional": last_p,
                        metric: to_num(row.iloc[col] if col < len(row) else None),
                    }
                )
        frames.append(pd.DataFrame(recs))
    return frames[0].merge(
        frames[1],
        on=["source", "freq", "year", "quarter", "type_id", "is_provisional"],
        how="outer",
    )


def parse_volume_annual(path: Path) -> pd.DataFrame:
    frames = []
    for sheet, metric in (("Nombre", "n"), ("Valeur", "value_kchf")):
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        recs = []
        for _, row in df.iloc[12:].iterrows():
            year, prov = parse_year_cell(row.iloc[0])
            if year is None:
                continue
            for col, type_id in COLS_1201.items():
                recs.append(
                    {
                        "source": "T_05_05_1_2_01",
                        "freq": "Y",
                        "year": year,
                        "quarter": pd.NA,
                        "type_id": type_id,
                        "is_provisional": prov,
                        metric: to_num(row.iloc[col] if col < len(row) else None),
                    }
                )
        frames.append(pd.DataFrame(recs))
    return frames[0].merge(
        frames[1],
        on=["source", "freq", "year", "quarter", "type_id", "is_provisional"],
        how="outer",
    )


def parse_price_canton_q(path: Path) -> pd.DataFrame:
    recs = []
    mapping = {
        "Maisons individuelles": "house_existing",
        "Appartements PPE": "ppe_existing",
    }
    for sheet, type_id in mapping.items():
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        last_y, last_p = None, 0
        for _, row in df.iloc[10:].iterrows():
            y, p = parse_year_cell(row.iloc[0])
            if y is not None:
                last_y, last_p = y, p
            q = quarter_num(row.iloc[1])
            if last_y is None or q is None:
                continue
            recs.append(
                {
                    "source": "T_05_05_1_1_02",
                    "freq": "Q",
                    "year": last_y,
                    "quarter": q,
                    "geo_label": "Canton",
                    "type_id": type_id,
                    "condition": "existing",
                    "market": "libre" if type_id == "ppe_existing" else "all",
                    "is_provisional": last_p,
                    "n": to_num(row.iloc[2]),
                    "p25_kchf": to_num(row.iloc[3]),
                    "median_kchf": to_num(row.iloc[4]),
                    "p75_kchf": to_num(row.iloc[5]),
                    "unit": "CHF_per_object",
                }
            )
    return pd.DataFrame(recs)


def _group_cols(start: int) -> tuple[int, int, int, int]:
    return start, start + 1, start + 2, start + 3


PPE_GROUPS = [
    # n, p25, med, p75, condition, market
    (*_group_cols(1), "new", "libre"),
    (*_group_cols(6), "existing", "libre"),
    (*_group_cols(11), "all", "libre"),
    (*_group_cols(16), "all", "zd"),
    (*_group_cols(21), "all", "all"),
]


def parse_price_ppe_commune(path: Path, dim_geo: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    recs, unmatched = [], []
    for sheet in pd.ExcelFile(path).sheet_names:
        if not str(sheet).isdigit():
            continue
        year = int(sheet)
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        for _, row in df.iloc[16:].iterrows():
            label = row.iloc[0]
            if pd.isna(label):
                continue
            label = str(label).strip()
            if label.startswith("(") or label.startswith("Source") or label.lower().startswith("la quasi"):
                break
            if label.startswith("     "):
                continue
            geo_id = geo_lookup(dim_geo, label)
            if geo_id is None:
                if label and not label.startswith("Autres"):
                    unmatched.append(f"{year}|{label}")
                if not label.startswith("Autres") and label != "Canton":
                    continue
                if label.startswith("Autres"):
                    geo_id = None
                if label == "Canton":
                    geo_id = "0000"
            for n_c, p25_c, med_c, p75_c, cond, market in PPE_GROUPS:
                if p75_c >= len(row):
                    continue
                recs.append(
                    {
                        "source": "T_05_05_1_4_03",
                        "freq": "Y",
                        "year": year,
                        "quarter": pd.NA,
                        "geo_id": geo_id,
                        "geo_label": label,
                        "type_id": "ppe",
                        "condition": cond,
                        "market": market,
                        "is_provisional": 0,
                        "n": to_num(row.iloc[n_c]),
                        "p25": to_num(row.iloc[p25_c]),
                        "median": to_num(row.iloc[med_c]),
                        "p75": to_num(row.iloc[p75_c]),
                        "unit": "CHF_per_m2",
                    }
                )
    return pd.DataFrame(recs), unmatched


def parse_price_house_commune(path: Path, dim_geo: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    recs, unmatched = [], []
    for sheet in pd.ExcelFile(path).sheet_names:
        if not str(sheet).isdigit():
            continue
        year = int(sheet)
        df = pd.read_excel(path, sheet_name=sheet, header=None)
        for _, row in df.iloc[10:].iterrows():
            label = row.iloc[0]
            if pd.isna(label):
                continue
            label = str(label).strip()
            if label.startswith("(") or label.startswith("Source"):
                break
            geo_id = geo_lookup(dim_geo, label)
            if geo_id is None:
                if label.startswith("Autres"):
                    geo_id = None
                elif label == "Canton":
                    geo_id = "0000"
                else:
                    unmatched.append(f"{year}|{label}")
                    continue
            recs.append(
                {
                    "source": "T_05_05_1_3_03",
                    "freq": "Y",
                    "year": year,
                    "quarter": pd.NA,
                    "geo_id": geo_id,
                    "geo_label": label,
                    "type_id": "house",
                    "condition": "all",
                    "market": "all",
                    "is_provisional": 0,
                    "n": to_num(row.iloc[1]),
                    "p25": to_num(row.iloc[2]),
                    "median": to_num(row.iloc[3]),
                    "p75": to_num(row.iloc[4]),
                    "unit": "CHF_per_object",
                    "p25_kchf": to_num(row.iloc[2]),
                    "median_kchf": to_num(row.iloc[3]),
                    "p75_kchf": to_num(row.iloc[4]),
                }
            )
    out = pd.DataFrame(recs)
    if not out.empty:
        for c in ("p25", "median", "p75"):
            out[c] = out[c + "_kchf"] * 1000
        out = out.drop(columns=["p25_kchf", "median_kchf", "p75_kchf"])
    return out, unmatched


def main() -> int:
    REF.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    dim_type = pd.DataFrame(
        TYPE_ROWS, columns=["type_id", "ocstat_label", "segment_v1", "is_ensemble", "condition"]
    )
    dim_geo = build_dim_geo()
    dim_market = pd.DataFrame(
        [
            ("libre", "Marché libre"),
            ("zd", "Zones de développement"),
            ("all", "Ensemble (libre + ZD / all dwellings)"),
        ],
        columns=["market", "label"],
    )
    dim_condition = pd.DataFrame(
        [
            ("new", "Neuf"),
            ("existing", "Non neuf"),
            ("all", "Ensemble"),
        ],
        columns=["condition", "label"],
    )
    map_geo = build_geo_alias_table(dim_geo)

    vol_q = parse_volume_quarterly(latest("*_T_05_05_1_1_01.xlsx"))
    vol_y = parse_volume_annual(latest("*_T_05_05_1_2_01.xlsx"))
    fact_volume = pd.concat([vol_q, vol_y], ignore_index=True)
    fact_volume["value_chf"] = fact_volume["value_kchf"] * 1000
    fact_volume["geo_id"] = "0000"  # canton-only tables

    price_q = parse_price_canton_q(latest("*_T_05_05_1_1_02.xlsx"))
    price_q["geo_id"] = "0000"
    for c in ("p25", "median", "p75"):
        price_q[c] = price_q[c + "_kchf"] * 1000
    price_q = price_q.drop(columns=["p25_kchf", "median_kchf", "p75_kchf"])

    ppe, u1 = parse_price_ppe_commune(latest("*_T_05_05_1_4_03.xlsx"), dim_geo)
    house, u2 = parse_price_house_commune(latest("*_T_05_05_1_3_03.xlsx"), dim_geo)
    fact_price = pd.concat([price_q, ppe, house], ignore_index=True)

    dim_type.to_csv(REF / "dim_type.csv", index=False, encoding="utf-8")
    dim_geo.to_csv(REF / "dim_geo.csv", index=False, encoding="utf-8")
    dim_market.to_csv(REF / "dim_market.csv", index=False, encoding="utf-8")
    dim_condition.to_csv(REF / "dim_condition.csv", index=False, encoding="utf-8")
    map_geo.to_csv(REF / "map_geo_alias.csv", index=False, encoding="utf-8")
    fact_volume.to_csv(DATA / "fact_volume.csv", index=False, encoding="utf-8")
    fact_price.to_csv(DATA / "fact_price.csv", index=False, encoding="utf-8")

    unmatched = sorted(set(u1 + u2))
    pd.DataFrame({"label": unmatched}).to_csv(DATA / "unmatched_geo.csv", index=False, encoding="utf-8")

    mapped = int(fact_price["geo_id"].notna().sum())
    residual = int(fact_price["geo_label"].fillna("").str.startswith("Autres").sum())
    geneve_n = int((fact_price["geo_id"] == "6621").sum())

    db = DATA / "geneva.duckdb"
    tables = {
        "dim_type": REF / "dim_type.csv",
        "dim_geo": REF / "dim_geo.csv",
        "dim_market": REF / "dim_market.csv",
        "dim_condition": REF / "dim_condition.csv",
        "map_geo_alias": REF / "map_geo_alias.csv",
        "fact_volume": DATA / "fact_volume.csv",
        "fact_price": DATA / "fact_price.csv",
    }
    if duckdb is None:
        print("duckdb not installed — CSV only. pip install duckdb")
    else:
        if db.exists():
            db.unlink()
        con = duckdb.connect(str(db))
        for name, path in tables.items():
            con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto(?)", [str(path)])
        sql_path = Path(__file__).with_name("validate.sql")
        sql_body = "\n".join(
            ln for ln in sql_path.read_text(encoding="utf-8").splitlines() if not ln.strip().startswith("--")
        )
        for stmt in sql_body.split(";"):
            stmt = stmt.strip()
            if stmt:
                con.execute(stmt)
        sample = con.execute(
            "SELECT year, type_id, n_q, n_y, n_gap FROM v_check_q_vs_year WHERE year=2007 LIMIT 8"
        ).fetchdf()
        joinq = con.execute("SELECT * FROM v_join_geo ORDER BY source").fetchdf()
        con.close()
        print(sample.to_string(index=False))
        print(joinq.to_string(index=False))
        print(f"DuckDB -> {db}")

    log = DATA / "transform_log.md"
    log.write_text(
        "\n".join(
            [
                "# Transform log",
                "",
                f"- dim_geo: {len(dim_geo)} rows (45 communes + 4 Genève secteurs + canton + Genève parent)",
                f"- dim_type: {len(dim_type)} types",
                f"- fact_volume: {len(fact_volume)}",
                f"- fact_price: {len(fact_price)} (geo_id set: {mapped}; Autres residual: {residual}; Genève 6621: {geneve_n})",
                f"- unmatched named labels: {len(unmatched)}",
                "",
                "Star: dim_* ← facts on geo_id / type_id / market / condition.",
                "geo_id = BFS `no_com_federal` (SITG). OCSTAT `Genève` → 6621, not 4 secteurs.",
                "`Autres communes…` kept in facts with empty geo_id (composition changes by year).",
                "Money: millier de francs → CHF (`value_chf`, house medians). PPE commune = CHF/m².",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Transform log -> {log.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
