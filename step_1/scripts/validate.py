"""
Checks on data/*.csv (source of truth). DuckDB not required.

  python scripts/validate.py

Writes data/validate_report.md. Exit 1 if any FAIL.
Method: step_1/scripts/validate.py (writes data/validate_report.md)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

STEP_ROOT = Path(__file__).resolve().parents[1]   # step_1/
ROOT = STEP_ROOT.parent                             # repo root (data/ lives here)
DATA = ROOT / "data"
REF = DATA / "ref"
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


def _md_table(rows: list[dict]) -> str:
    if not rows:
        return "_none_"
    cols = list(rows[0].keys())
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def check(name: str, status: str, detail: str) -> dict:
    return {"check": name, "status": status, "detail": detail}


def as_geo_id(s: pd.Series) -> pd.Series:
    """CSV infers 0000 as 0 and 6621 as float. Restore BFS strings."""
    out = []
    for v in s:
        if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and v.strip() == ""):
            out.append(pd.NA)
            continue
        t = str(v).strip()
        if t.endswith(".0") and t[:-2].lstrip("-").isdigit():
            t = t[:-2]
        if t.isdigit() or (t.startswith("-") and t[1:].isdigit()):
            out.append(f"{int(t):04d}")
        else:
            out.append(t)
    return pd.Series(out, index=s.index, dtype="string")


def load() -> dict[str, pd.DataFrame | dict]:
    inv_path = DATA / "raw_inventory.json"
    inv = json.loads(inv_path.read_text(encoding="utf-8")) if inv_path.exists() else {}
    vol = pd.read_csv(DATA / "fact_volume.csv")
    price = pd.read_csv(DATA / "fact_price.csv")
    geo = pd.read_csv(REF / "dim_geo.csv")
    vol["geo_id"] = as_geo_id(vol["geo_id"])
    price["geo_id"] = as_geo_id(price["geo_id"])
    geo["geo_id"] = as_geo_id(geo["geo_id"])
    return {
        "inv": inv,
        "vol": vol,
        "price": price,
        "geo": geo,
        "typ": pd.read_csv(REF / "dim_type.csv"),
        "unmatched": pd.read_csv(DATA / "unmatched_geo.csv")
        if (DATA / "unmatched_geo.csv").exists()
        else pd.DataFrame(columns=["label"]),
    }


def run_checks(d: dict) -> list[dict]:
    vol: pd.DataFrame = d["vol"]
    price: pd.DataFrame = d["price"]
    for frame in (vol, price):
        if "is_provisional" not in frame.columns:
            frame["is_provisional"] = 0
        frame["is_provisional"] = frame["is_provisional"].fillna(0).astype(int)
    geo: pd.DataFrame = d["geo"]
    typ: pd.DataFrame = d["typ"]
    inv = d["inv"]
    unmatched: pd.DataFrame = d["unmatched"]
    out: list[dict] = []

    downloads = inv.get("downloads", [])
    if downloads:
        n_ok = sum(1 for r in downloads if r.get("ok"))
        out.append(
            check(
                "extract_inventory",
                PASS if n_ok == 6 else FAIL,
                f"{n_ok}/{len(downloads)} files OK (need 6: 5 OCSTAT + SITG)",
            )
        )
    else:
        out.append(check("extract_inventory", WARN, "raw_inventory.json not found — skipped (run extract.py first)"))

    vol_keys = ["source", "freq", "year", "quarter", "type_id"]
    price_keys = ["source", "freq", "year", "quarter", "geo_label", "type_id", "condition", "market"]
    vol_dups = int(vol.duplicated(vol_keys).sum())
    price_dups = int(price.duplicated(price_keys).sum())
    out.append(
        check(
            "unique_grain",
            PASS if vol_dups == 0 and price_dups == 0 else FAIL,
            f"fact_volume dups={vol_dups}; fact_price dups={price_dups}",
        )
    )

    chf_gap = float((vol["value_chf"] - vol["value_kchf"] * 1000).abs().max())
    out.append(check("chf_x1000", PASS if chf_gap == 0 else FAIL, f"max |value_chf - kchf*1000| = {chf_gap}"))

    orph_type = sorted(set(vol.type_id) - set(typ.type_id)) + sorted(set(price.type_id) - set(typ.type_id))
    out.append(check("type_fk", PASS if not orph_type else FAIL, f"orphan type_id={orph_type or 'none'}"))

    geo_ids = set(geo.geo_id.astype(str))
    pid = price.geo_id.dropna().astype(str)
    orph_geo = sorted(set(pid) - geo_ids)
    out.append(check("geo_fk", PASS if not orph_geo else FAIL, f"orphan geo_id={orph_geo[:8] or 'none'}"))

    n_un = 0
    if len(unmatched) and "label" in unmatched.columns:
        n_un = int((unmatched["label"].fillna("") != "").sum())
    out.append(check("geo_named_match", PASS if n_un == 0 else FAIL, f"unmatched named labels={n_un}"))

    residual = price["geo_label"].fillna("").str.startswith("Autres")
    residual_mapped = int((residual & price.geo_id.notna()).sum())
    out.append(
        check(
            "autres_not_mapped",
            PASS if residual_mapped == 0 else FAIL,
            f"Autres rows={int(residual.sum())}; wrongly mapped={residual_mapped}",
        )
    )

    gva = int((price.geo_id.astype(str) == "6621").sum())
    out.append(check("geneve_6621", PASS if gva > 0 else FAIL, f"fact_price rows with geo_id=6621: {gva}"))

    wide = vol.pivot_table(index=["source", "freq", "year", "quarter"], columns="type_id", values="n")
    ens_bad = 0
    ens_n = 0
    for ens, a, b in (("house", "house_existing", "house_new"), ("ppe", "ppe_existing", "ppe_new")):
        if not {ens, a, b}.issubset(wide.columns):
            continue
        diff = (wide[ens] - wide[a] - wide[b]).dropna()
        ens_n += len(diff)
        ens_bad += int((diff.abs() > 0.5).sum())
    out.append(
        check(
            "ensemble_identity",
            PASS if ens_bad == 0 else FAIL,
            f"house/ppe ensemble != parts in {ens_bad}/{ens_n} periods (tol 0.5)",
        )
    )

    q = (
        vol[(vol.freq == "Q") & (vol.source == "T_05_05_1_1_01") & (vol["is_provisional"] == 0)]
        .groupby(["year", "type_id"], as_index=False)
        .agg(n_q=("n", "sum"), n_quarters=("quarter", "nunique"))
    )
    y = vol[(vol.freq == "Y") & (vol.source == "T_05_05_1_2_01")][["year", "type_id", "n"]].rename(
        columns={"n": "n_y"}
    )
    g = q.merge(y, on=["year", "type_id"], how="inner")
    g = g[g.n_quarters == 4]
    g["gap"] = g.n_q - g.n_y
    n_gap = int((g.gap.abs() > 0.5).sum())
    worst = g.loc[g.gap.abs().idxmax()] if len(g) else None
    detail = f"complete non-provisional years {int(g.year.min())}-{int(g.year.max())}, mismatches={n_gap}"
    if worst is not None and n_gap:
        detail += f"; worst {int(worst.year)} {worst.type_id} {worst.n_q:.0f} vs {worst.n_y:.0f}"
    out.append(check("q_sum_eq_year", PASS if n_gap == 0 and len(g) else FAIL, detail))

    q_all = vol[vol.freq == "Q"]
    nq = q_all.groupby("year")["quarter"].nunique()
    incomplete = [int(y) for y, n in nq.items() if n < 4]
    prov_years = sorted(q_all.loc[q_all["is_provisional"] == 1, "year"].unique().tolist())
    out.append(
        check(
            "quarters_present",
            WARN if incomplete else PASS,
            f"years with <4 quarters: {incomplete or 'none'}; provisional years: {prov_years or 'none'}",
        )
    )

    def year_holes(series: pd.Series, start_expect: int | None = None) -> list[int]:
        ys = sorted(int(x) for x in series.dropna().unique())
        if not ys:
            return []
        lo, hi = ys[0], ys[-1]
        missing = [y for y in range(lo, hi + 1) if y not in ys]
        if start_expect is not None and lo > start_expect:
            missing = list(range(start_expect, lo)) + missing
        return missing

    holes_vq = year_holes(vol.loc[vol.freq == "Q", "year"], 2007)
    holes_vy = year_holes(vol.loc[vol.freq == "Y", "year"], 1998)
    holes_p3 = year_holes(price.loc[price.source == "T_05_05_1_3_03", "year"], 1990)
    holes_p4 = year_holes(price.loc[price.source == "T_05_05_1_4_03", "year"], 1990)
    holes = {"Q_volume": holes_vq, "Y_volume": holes_vy, "house_commune": holes_p3, "ppe_commune": holes_p4}
    any_h = any(holes.values())
    out.append(
        check(
            "year_continuity",
            WARN if any_h else PASS,
            "; ".join(f"{k} missing {v}" for k, v in holes.items() if v) or "no holes from series start to last year",
        )
    )

    q_before = vol[(vol.freq == "Q") & (vol.year < 2007)]
    out.append(
        check(
            "no_fake_quarters",
            PASS if q_before.empty else FAIL,
            f"quarterly rows before 2007: {len(q_before)}",
        )
    )

    q_bad = 0
    q_n = 0
    for src, df in price.groupby("source"):
        both = df[["p25", "median", "p75"]].dropna()
        q_n += len(both)
        q_bad += int(((both.p25 > both["median"]) | (both["median"] > both.p75)).sum())
    out.append(check("quartile_order", PASS if q_bad == 0 else FAIL, f"p25<=median<=p75 violations {q_bad}/{q_n}"))

    suppress = price[price.n.notna() & price["median"].isna()]
    leak = int((suppress.n >= 10).sum())
    out.append(
        check(
            "median_suppressed_small_n",
            PASS if leak == 0 else FAIL,
            f"n and no median: {len(suppress)} rows (OCSTAT hides n<10); n>=10 with no median: {leak}",
        )
    )

    house_m = price.loc[price.source == "T_05_05_1_3_03", "median"].dropna()
    ppe_m = price.loc[
        (price.source == "T_05_05_1_4_03") & (price.market == "libre") & (price.condition == "existing"),
        "median",
    ].dropna()
    house_ok = house_m.empty or (house_m.min() >= 50_000 and house_m.max() <= 80_000_000)
    ppe_ok = ppe_m.empty or (ppe_m.min() >= 500 and ppe_m.max() <= 40_000)
    out.append(
        check(
            "unit_sanity",
            PASS if house_ok and ppe_ok else FAIL,
            f"house median CHF {house_m.min():.0f}-{house_m.max():.0f}; "
            f"PPE CHF/m2 {ppe_m.min():.0f}-{ppe_m.max():.0f}",
        )
    )

    last = int(price.loc[price.source == "T_05_05_1_4_03", "year"].max())
    canton = price[
        (price.source == "T_05_05_1_4_03")
        & (price.year == last)
        & (price.geo_id.astype(str) == "0000")
        & (price.condition == "existing")
        & (price.market == "libre")
    ]
    city = price[
        (price.source == "T_05_05_1_4_03")
        & (price.year == last)
        & (price.geo_id.astype(str) == "6621")
        & (price.condition == "existing")
        & (price.market == "libre")
    ]
    c_med = float(canton["median"].iloc[0]) if len(canton) and pd.notna(canton["median"].iloc[0]) else None
    g_med = float(city["median"].iloc[0]) if len(city) and pd.notna(city["median"].iloc[0]) else None
    differ = c_med is not None and g_med is not None and abs(c_med - g_med) > 1
    out.append(
        check(
            "canton_ne_geneve",
            PASS if differ else FAIL,
            f"{last} PPE existing libre median: canton={c_med}, Geneve={g_med}",
        )
    )

    named = price[
        price.geo_id.notna()
        & (price.source.isin(["T_05_05_1_3_03", "T_05_05_1_4_03"]))
        & ~price.geo_label.fillna("").str.startswith("Autres")
        & (price.geo_label != "Canton")
    ]
    n_communes = named.geo_id.nunique()
    out.append(
        check(
            "commune_panel_sparse",
            WARN if n_communes < 40 else PASS,
            f"named communes with prices: {n_communes} (OCSTAT publishes large communes only, not 45)",
        )
    )

    return out


def write_report(checks: list[dict], d: dict) -> Path:
    vol, price = d["vol"], d["price"]
    counts = {
        FAIL: sum(1 for c in checks if c["status"] == FAIL),
        WARN: sum(1 for c in checks if c["status"] == WARN),
        PASS: sum(1 for c in checks if c["status"] == PASS),
    }
    lines = [
        "# Validate report",
        "",
        f"Date: {date.today().isoformat()}. Method: `step_1/scripts/validate.py`.",
        "",
        f"**{counts[FAIL]} FAIL · {counts[WARN]} WARN · {counts[PASS]} PASS**",
        "",
        "## Coverage",
        "",
        f"- fact_volume: {len(vol)} rows; years Q {int(vol.loc[vol.freq=='Q','year'].min())}–{int(vol.loc[vol.freq=='Q','year'].max())}; "
        f"Y {int(vol.loc[vol.freq=='Y','year'].min())}–{int(vol.loc[vol.freq=='Y','year'].max())}",
        f"- fact_price: {len(price)} rows; years {int(price.year.min())}–{int(price.year.max())}",
        "",
        _md_table(checks),
        "",
        "## Notes",
        "",
        "- Median missing with n<10 is OCSTAT, not a parse hole.",
        "- `Autres communes…` have empty geo_id on purpose.",
        "- Provisional years (`2025 p` in Excel → `is_provisional=1`) are not compared to the annual table.",
        "",
    ]
    path = DATA / "validate_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    d = load()
    checks = run_checks(d)
    path = write_report(checks, d)
    for c in checks:
        print(f"  [{c['status']}] {c['check']}: {c['detail']}")
    print(f"\nReport -> {path.relative_to(ROOT)}")
    return 1 if any(c["status"] == FAIL for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
