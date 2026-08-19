"""
Step 1 extract: download chosen raw files into raw/.

  python scripts/extract.py

Does not parse Excel. SITG GeoJSON is saved as a raw API snapshot.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

STEP_ROOT = Path(__file__).resolve().parents[1]   # step_1/
ROOT = STEP_ROOT.parent                             # repo root (data/, raw/ live here)
RAW = ROOT / "raw"
DATA = ROOT / "data"
SOURCES = Path(__file__).resolve().parent / "sources.json"


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
        "Geneva-RE-Step1/1.0 (research; local)",
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
        headers={"User-Agent": "Geneva-RE-Step1/1.0 (research; local)"},
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


def main() -> int:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    RAW.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)

    results = []
    for src in sources:
        dest = RAW / f"{today}_{src['id']}.{ext_for(src['kind'])}"
        rec = {
            "id": src["id"],
            "publisher": src["publisher"],
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
            rec["ok"] = rec["bytes"] > 1000
            if not rec["ok"]:
                rec["error"] = f"file too small ({rec['bytes']} bytes)"
        except Exception as e:  # noqa: BLE001
            rec["error"] = repr(e)
        results.append(rec)
        status = "OK" if rec["ok"] else "FAIL"
        print(f"  [{status}] {src['id']} -> {rec['path']}")
        if rec["error"]:
            print(f"         {rec['error']}")

    inventory = {"access_date": today, "downloads": results}
    inv_path = DATA / "raw_inventory.json"
    inv_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_n = sum(1 for r in results if r["ok"])
    print(f"\nExtract: {ok_n}/{len(results)} OK -> {inv_path.relative_to(ROOT)}")
    return 0 if ok_n == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
