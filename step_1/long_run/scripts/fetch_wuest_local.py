"""Download Wüest transaction price index XLS into long_run/local/ (git-ignored).

Fetches:
  - Owner-occupied apartments (nutzung=2)
  - Single-family houses (nutzung=3)
  Market region: Lake Geneva + Switzerland (mrcode=7)

Dating: use **published annual** series (1985=100) for all years.
This pairs naturally with OCSTAT calendar-year transaction medians.
Quarterly points are parsed only for reference / optional later use — not written to CSVs.
"""
from __future__ import annotations

from pathlib import Path

import urllib.parse
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
LOCAL = ROOT / "step_1" / "long_run" / "local"
POST_URL = "https://www.wuest.io/online_services_classic/transaktionspreisindex/php/preisindex.php"
META = {
    "source": "Wüest Partner",
    "url": "https://www.wuest.io/online_services_classic/transaktionspreisindex/index_e.phtml",
    "note": "Local analysis only; do not commit/redistribute raw XLS in public GitHub.",
}

# Wüest form: nutzung 2 = apartments (PPE), 3 = single-family houses
JOBS = [
    {
        "nutzung": "2",
        "label": "Owner-occupied apartments (PPE)",
        "raw": "wuest_transaction_ppe_lake_geneva_raw.xls",
        "lg_csv": "wuest_ppe_lake_geneva.csv",
        "ch_csv": "wuest_ppe_switzerland.csv",
    },
    {
        "nutzung": "3",
        "label": "Single-family houses",
        "raw": "wuest_transaction_houses_lake_geneva_raw.xls",
        "lg_csv": "wuest_houses_lake_geneva.csv",
        "ch_csv": "wuest_houses_switzerland.csv",
    },
]


def download_xls(nutzung: str, dest: Path) -> Path:
    data = urllib.parse.urlencode(
        {
            "nutzung": nutzung,
            "mrcode": "7",
            "ausgabeformat": "XLS",
            "sprachco": "2",
            "conf_tac": "1",
            "submit": "Submit query",
        }
    ).encode()
    req = urllib.request.Request(
        POST_URL,
        data=data,
        headers={"User-Agent": "Geneva-RE/1.0 (research; local non-commercial)"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read()
        ctype = resp.headers.get("Content-Type", "")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(body)
    print(f"  wrote {dest.relative_to(ROOT)} ({len(body)} bytes, {ctype})")
    if len(body) < 500 or b"<html" in body[:200].lower():
        raise RuntimeError(f"unexpected response for nutzung={nutzung}: {body[:300]!r}")
    return dest


def _read_sheet(xls: Path) -> pd.DataFrame:
    try:
        return pd.read_excel(xls, sheet_name=0, header=None)
    except Exception:
        return pd.read_excel(xls, sheet_name=0, header=None, engine="xlrd")


def parse_wuest_tables(xls: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (quarterly, annual) long frames with columns year[,q], lg, ch."""
    xl = _read_sheet(xls)
    qrows, arows = [], []
    for i in range(len(xl)):
        lab = xl.iloc[i, 1]
        if pd.isna(lab):
            continue
        s = str(lab).strip()
        if "/" in s and s[0].isdigit():
            try:
                y, q = s.split("/", 1)
                qrows.append(
                    {
                        "year": int(y),
                        "q": int(q),
                        "lg": float(xl.iloc[i, 4]),
                        "ch": float(xl.iloc[i, 14]),
                    }
                )
            except (ValueError, TypeError):
                continue
        elif s.isdigit() and 1980 <= int(s) <= 2100:
            try:
                arows.append(
                    {
                        "year": int(s),
                        "lg": float(xl.iloc[i, 4]),
                        "ch": float(xl.iloc[i, 14]),
                    }
                )
            except (ValueError, TypeError):
                continue
    return pd.DataFrame(qrows), pd.DataFrame(arows)


def published_annual(
    annual: pd.DataFrame, quarterly: pd.DataFrame, col: str
) -> pd.DataFrame:
    """Published yearly hedonic index (base 1985=100) — as on Wüest export.

    Drops incomplete calendar years: if quarterly rows exist for year Y but
    max quarter < 4, exclude Y (YTD / provisional annual point).
    """
    ann = annual.set_index("year")[col].astype(float).sort_index()
    if not quarterly.empty and col in quarterly.columns:
        for y in list(ann.index):
            yq = quarterly.loc[quarterly["year"] == y, "q"]
            if len(yq) and int(yq.max()) < 4:
                ann = ann.drop(index=y)
    out = ann.rename("index").reset_index()
    out["dating"] = "published_annual"
    return out


def write_series(df: pd.DataFrame, path: Path, geography: str, series_label: str) -> None:
    out = df[["year", "index"]].copy()
    out.to_csv(path, index=False)
    meta = path.with_suffix(".meta.txt")
    dating = ",".join(sorted(df["dating"].unique()))
    meta.write_text(
        "\n".join(
            [
                f"geography: {geography}",
                f"source: {META['source']}",
                f"url: {META['url']}",
                f"series: Hedonic transaction price index — {series_label}",
                f"dating: {dating}",
                "rule: published annual series only (1985=100), as on Wüest export / website",
                "reason: pair with OCSTAT calendar-year transaction medians; figures match Wüest annual table",
                "filter: drop year Y if quarterly exists for Y but max quarter < 4 (incomplete calendar year)",
                "retrieval: local download via wuest.io form POST",
                META["note"],
            ]
        ),
        encoding="utf-8",
    )
    print(f"  {path.name}: {len(out)} years ({out.year.min()}-{out.year.max()}) dating={dating}")


def main() -> int:
    import sys

    from_local = "--from-local" in sys.argv
    LOCAL.mkdir(parents=True, exist_ok=True)
    for job in JOBS:
        print(f"== {job['label']} (nutzung={job['nutzung']})")
        xls = LOCAL / job["raw"]
        if from_local:
            if not xls.exists():
                raise FileNotFoundError(f"missing local XLS: {xls}")
            print(f"  using existing {xls.relative_to(ROOT)}")
        else:
            try:
                xls = download_xls(job["nutzung"], xls)
            except OSError as exc:
                if not xls.exists():
                    raise
                print(f"  download failed ({exc}); re-parsing existing {xls.name}")
        quarterly, annual = parse_wuest_tables(xls)
        print(f"  parsed quarterly={len(quarterly)} annual={len(annual)}")
        write_series(
            published_annual(annual, quarterly, "lg"),
            LOCAL / job["lg_csv"],
            "Lake Geneva",
            job["label"],
        )
        write_series(
            published_annual(annual, quarterly, "ch"),
            LOCAL / job["ch_csv"],
            "Switzerland",
            job["label"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
