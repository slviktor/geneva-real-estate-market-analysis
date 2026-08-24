"""
Download source files listed in a sources JSON into raw/.

  python scripts/extract.py --sources step_1/sources.json
  python scripts/extract.py --sources step_1/long_run/sources_long_run.json

Does not parse Excel. Writes data/raw_inventory_<sources_stem>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
DATA = ROOT / "data"
DEFAULT_SOURCES = ROOT / "step_1" / "sources.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_curl(url: str, dest: Path, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "curl",
        "-sL",
        "--fail",
        "--ssl-no-revoke",
        "--connect-timeout",
        "30",
        "-m",
        str(timeout),
        "-A",
        "Geneva-RE/1.0 (research; local)",
        "-o",
        str(dest),
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"curl {r.returncode}: {(r.stderr or r.stdout)[:500]}")


def download_requests(url: str, dest: Path, timeout: int = 120) -> None:
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Geneva-RE/1.0 (research; local)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def download(url: str, dest: Path, force_curl: bool) -> None:
    host = url.split("/")[2] if "//" in url else ""
    use_curl = force_curl or "statistique.ge.ch" in host or "ge.ch" in host
    if use_curl:
        download_curl(url, dest)
        return
    try:
        download_requests(url, dest)
    except OSError:
        download_curl(url, dest)


def ext_for(kind: str) -> str:
    return {"xlsx": "xlsx", "geojson": "geojson", "csv": "csv"}.get(kind, "bin")


def raw_bucket(src: dict) -> str:
    """Subfolder under raw/: ocstat | bis | bfs | sitg | other."""
    if src.get("raw_bucket"):
        return str(src["raw_bucket"]).strip("/\\")
    pub = (src.get("publisher") or "").lower()
    if "ocstat" in pub:
        return "ocstat"
    if "sitg" in pub:
        return "sitg"
    if "bis" in pub or "fred" in pub:
        return "bis"
    if "bfs" in pub or "ofs" in pub:
        return "bfs"
    return "other"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download raw sources into raw/")
    p.add_argument(
        "--sources",
        type=Path,
        default=DEFAULT_SOURCES,
        help=f"Path to sources JSON (default: {DEFAULT_SOURCES.relative_to(ROOT)})",
    )
    p.add_argument(
        "--inventory",
        type=Path,
        default=None,
        help="Inventory JSON path (default: data/raw_inventory_<sources_stem>.json)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    sources_path = args.sources if args.sources.is_absolute() else ROOT / args.sources
    if not sources_path.exists():
        raise SystemExit(f"sources file not found: {sources_path}")

    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    inv_path = args.inventory
    if inv_path is None:
        inv_path = DATA / f"raw_inventory_{sources_path.stem}.json"
    elif not inv_path.is_absolute():
        inv_path = ROOT / inv_path

    results = []
    for src in sources:
        if src.get("skip_download"):
            results.append(
                {
                    "id": src["id"],
                    "publisher": src.get("publisher", ""),
                    "kind": src.get("kind", "cite"),
                    "url": src.get("url", ""),
                    "path": None,
                    "ok": True,
                    "bytes": None,
                    "sha256": None,
                    "error": None,
                    "skip_download": True,
                    "note": src.get("note", "cite-only; not downloaded"),
                }
            )
            print(f"  [SKIP] {src['id']} (cite-only)")
            continue

        dest = RAW / raw_bucket(src) / f"{today}_{src['id']}.{ext_for(src['kind'])}"
        rec = {
            "id": src["id"],
            "publisher": src.get("publisher", ""),
            "kind": src["kind"],
            "url": src["url"],
            "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
            "ok": False,
            "bytes": None,
            "sha256": None,
            "error": None,
        }
        try:
            download(src["url"], dest, force_curl=src.get("force_curl", False))
            rec["bytes"] = dest.stat().st_size
            rec["sha256"] = sha256(dest)
            # FRED CSV headers are tiny; allow smaller open stats files
            min_bytes = int(src.get("min_bytes", 1000))
            rec["ok"] = rec["bytes"] > min_bytes
            if not rec["ok"]:
                rec["error"] = f"file too small ({rec['bytes']} bytes)"
        except Exception as e:  # noqa: BLE001
            rec["error"] = repr(e)
        results.append(rec)
        status = "OK" if rec["ok"] else "FAIL"
        print(f"  [{status}] {src['id']} -> {rec['path']}")
        if rec["error"]:
            print(f"         {rec['error']}")

    inventory = {
        "access_date": today,
        "sources_file": str(sources_path.relative_to(ROOT)).replace("\\", "/"),
        "downloads": results,
    }
    inv_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_n = sum(1 for r in results if r["ok"])
    print(f"\nExtract: {ok_n}/{len(results)} OK -> {inv_path.relative_to(ROOT)}")
    return 0 if ok_n == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
