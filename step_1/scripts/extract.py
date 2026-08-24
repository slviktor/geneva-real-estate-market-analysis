"""Backward-compatible shim. Prefer: python scripts/extract.py --sources step_1/sources.json """
from __future__ import annotations
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
script = ROOT / "scripts" / "extract.py"
sys.argv = [str(script), "--sources", str(ROOT / "step_1" / "sources.json"), *sys.argv[1:]]
runpy.run_path(str(script), run_name="__main__")
