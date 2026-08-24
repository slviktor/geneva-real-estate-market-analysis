"""
Step 1 · long_run charts — OCSTAT vs Swiss benchmarks (Wüest / BIS / BFS).

  python step_1/long_run/scripts/viz_long_run.py

Requires: python step_1/long_run/scripts/transform_long_run.py
Wording: step_1/long_run/exports/brief_copy_long_run.json
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
STEP = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
FIGURES = STEP / "long_run" / "exports" / "figures"
COPY_PATH = STEP / "long_run" / "exports" / "brief_copy_long_run.json"
VAL_PATH = DATA / "fact_long_run_validation.json"

PAPER = "#FFFFFF"
INK = "#1F2937"
MUTED = "#6B7280"
LINE = "#D1D5DB"
CANTON = "#2563EB"
CITY = "#0F766E"
LAKE = "#D97706"
CH = "#64748B"
BIS = "#475569"
BIS_REAL = "#94A3B8"
BFS = "#9F1239"
CPI = "#9CA3AF"
CONST_GE = "#7C3AED"
CONST_CH = "#A78BFA"
NEW = "#0F766E"
EXISTING = "#2563EB"
DPI = 300
SOURCE_SHORT = (
    "Sources: OCSTAT (transactions, CPI, construction); Wüest Partner (hedonic, not redistributed); "
    "BIS/FRED; BFS IMPI & construction · Author's calc."
)


def load_copy() -> dict:
    return json.loads(COPY_PATH.read_text(encoding="utf-8"))["charts"]


def style_ax(ax, ylabel: str | None = None) -> None:
    ax.set_facecolor(PAPER)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=MUTED, labelsize=11)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=12)
    ax.grid(axis="y", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)


def fig_title(fig: plt.Figure, text: str) -> None:
    fig.text(0.01, 0.97, text, fontsize=16, color=INK,
             fontweight="bold", va="top", ha="left")


def _footnote_ncols(fig: plt.Figure, width_frac: float, fontsize: float = 8.5) -> int:
    """Chars that render to ~width_frac of the figure at given fontsize."""
    # Mixed probe ≈ body text width better than pure 'x'
    probe = ("n m " * 20)[:80]
    t = fig.text(0, 0, probe, fontsize=fontsize)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bb = t.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
    t.remove()
    if bb.width <= 0:
        return 100
    # Small uplift so wrap lines reach end-callout band, not only axes
    return max(60, int(width_frac * (len(probe) / bb.width) * 1.08))


def caption(fig: plt.Figure, note: str) -> None:
    """Footnote width ≈ title / plot+callout band (metric-based wrap)."""
    ax = fig.axes[0] if fig.axes else None
    if ax is not None:
        pos = ax.get_position()
        # Same horizontal band as title (0.01) → end callouts past axes
        target_right = min(0.99, max(pos.x1 + 0.28, 0.96))
    else:
        target_right = 0.96
    width_frac = max(0.75, target_right - 0.01)
    ncols = _footnote_ncols(fig, width_frac, fontsize=8.5)
    text = f"{note}  |  {SOURCE_SHORT}"
    wrapped = "\n".join(textwrap.wrap(text, width=ncols))
    n_lines = wrapped.count("\n") + 1
    bottom = 0.032 + 0.026 * n_lines
    for a in fig.axes:
        p = a.get_position()
        if p.y0 < bottom:
            new_h = max(0.35, p.y1 - bottom)
            a.set_position([p.x0, bottom, p.width, new_h])
    fig.text(
        0.01,
        0.012,
        wrapped,
        fontsize=8.5,
        color=MUTED,
        va="bottom",
        ha="left",
        linespacing=1.3,
    )


def dump(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"  {path.relative_to(ROOT)}")


def series(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    return df[df.series_id == sid].sort_values("year")


def has(df: pd.DataFrame, sid: str) -> bool:
    return sid in set(df.series_id)


def drawdown_path(years: pd.Series, values: pd.Series) -> pd.DataFrame:
    """% below running peak (0 = at/above peak)."""
    s = pd.DataFrame({"year": years.astype(int), "value": values.astype(float)}).dropna()
    s = s.sort_values("year").drop_duplicates("year")
    peak = s["value"].cummax()
    s["drawdown_pct"] = (s["value"] / peak - 1.0) * 100.0
    s["peak"] = peak
    return s


def drawdown_episodes(
    years: pd.Series,
    values: pd.Series,
    *,
    min_depth_pct: float = -3.0,
    label: str,
) -> list[dict]:
    """
    Completed or open peak→trough→recovery episodes.
    Duration = years from peak to recovery (or to last year if still underwater).
    Depth = max decline from that peak (%).
    """
    path = drawdown_path(years, values)
    if path.empty:
        return []
    episodes: list[dict] = []
    i = 0
    n = len(path)
    years_a = path["year"].to_numpy()
    vals = path["value"].to_numpy()
    dds = path["drawdown_pct"].to_numpy()

    while i < n:
        if dds[i] >= -1e-9:
            i += 1
            continue
        # peak is previous observation (last at high-water mark)
        peak_i = i - 1 if i > 0 else 0
        peak_year = int(years_a[peak_i])
        peak_val = float(vals[peak_i])
        j = i
        trough_i = i
        while j < n and dds[j] < -1e-9:
            if vals[j] < vals[trough_i]:
                trough_i = j
            j += 1
        trough_year = int(years_a[trough_i])
        depth = float(dds[trough_i])
        recovered = j < n
        end_i = j if recovered else n - 1
        end_year = int(years_a[end_i])
        duration_yrs = int(end_year - peak_year)
        time_to_trough = int(trough_year - peak_year)
        if depth <= min_depth_pct and duration_yrs >= 1:
            episodes.append(
                {
                    "series": label,
                    "peak_year": peak_year,
                    "trough_year": trough_year,
                    "end_year": end_year,
                    "recovered": recovered,
                    "depth_pct": round(depth, 2),
                    "duration_yrs": duration_yrs,
                    "years_to_trough": time_to_trough,
                    "peak_value": round(peak_val, 2),
                    "trough_value": round(float(vals[trough_i]), 2),
                    "label": f"{peak_year}–{end_year}",
                }
            )
        i = j if recovered else n
    return episodes


def fig_drawdowns(df: pd.DataFrame, c: dict) -> tuple[plt.Figure, pd.DataFrame]:
    """
    Top: underwater drawdown from peak (%).
    Bottom: depth × duration scatter for major episodes.
    """
    specs = [
        ("ocstat_city_ppe", "Geneva city (OCSTAT)", CITY, "-", 2.4),
        ("ocstat_canton_ppe", "Geneva canton (OCSTAT)", CANTON, "-", 2.4),
    ]
    if has(df, "wuest_ppe_lake_geneva"):
        specs.append(("wuest_ppe_lake_geneva", "Lake Geneva (Wüest)", LAKE, "-", 2.2))
    if has(df, "bis_ch_rpp_nominal"):
        specs.append(("bis_ch_rpp_nominal", "Switzerland (BIS)", BIS, "--", 1.6))

    fig, (ax0, ax1) = plt.subplots(
        2,
        1,
        figsize=(10.5, 8.0),
        gridspec_kw={"height_ratios": [1.2, 1.0], "hspace": 0.30},
    )

    all_eps: list[dict] = []
    for sid, label, color, ls, lw in specs:
        s = series(df, sid).dropna(subset=["index_1990"])
        s = s[s.year >= 1990]
        if s.empty:
            continue
        path = drawdown_path(s["year"], s["index_1990"])
        ax0.fill_between(
            path["year"],
            path["drawdown_pct"],
            0,
            color=color,
            alpha=0.10,
            linewidth=0,
        )
        ax0.plot(
            path["year"],
            path["drawdown_pct"],
            color=color,
            linestyle=ls,
            linewidth=lw,
            label=label,
        )
        all_eps.extend(
            drawdown_episodes(
                s["year"],
                s["index_1990"],
                min_depth_pct=-3.0,
                label=label,
            )
        )

    ax0.axhline(0, color=LINE, linewidth=1.0)
    style_ax(ax0, c["ylabel_top"])
    fig_title(fig, c["title"])
    ax0.legend(frameon=False, fontsize=10, loc="lower right")
    ax0.xaxis.set_major_locator(mticker.MultipleLocator(4))
    ax0.set_xlim(1989.5, None)

    markers = {
        "Geneva city (OCSTAT)": ("D", CITY, 85),
        "Geneva canton (OCSTAT)": ("o", CANTON, 90),
        "Lake Geneva (Wüest)": ("s", LAKE, 80),
        "Switzerland (BIS)": ("^", BIS, 55),
    }

    annotatable: list[tuple[float, float, str, str, str]] = []
    for ep in all_eps:
        m, color, size = markers.get(ep["series"], ("o", MUTED, 50))
        depth = abs(ep["depth_pct"])
        dur = ep["duration_yrs"]
        ax1.scatter(
            dur,
            depth,
            marker=m,
            s=size,
            color=color,
            edgecolors="white",
            linewidths=0.6,
            zorder=3,
            label=ep["series"],
        )
        if abs(ep["depth_pct"]) < 5 and ep["duration_yrs"] < 3:
            continue
        tag = ep["label"] + ("*" if not ep["recovered"] else "")
        depth_tag = f"{tag}  \u2013{abs(ep['depth_pct']):.0f}%"
        annotatable.append((dur, depth, depth_tag, color, ep["series"]))

    placed: list[tuple[float, float]] = []
    for dur, depth, depth_tag, color, ser in annotatable:
        ox, oy = 8, 4
        for px, py in placed:
            if abs(dur - px) < 3 and abs(depth - py) < 4:
                oy = -16
                break
        ax1.annotate(
            depth_tag,
            (dur, depth),
            textcoords="offset points",
            xytext=(ox, oy),
            fontsize=9,
            color=color,
            fontweight="bold",
        )
        placed.append((dur, depth))

    handles, labels = ax1.get_legend_handles_labels()
    seen: set[str] = set()
    uniq_h, uniq_l = [], []
    for h, lab in zip(handles, labels):
        if lab not in seen:
            seen.add(lab)
            uniq_h.append(h)
            uniq_l.append(lab)
    if uniq_h:
        ax1.legend(uniq_h, uniq_l, frameon=False, fontsize=10, loc="upper left")

    style_ax(ax1, c["ylabel_bottom"])
    ax1.set_xlabel(c["xlabel_bottom"], color=MUTED, fontsize=11)
    ax1.set_title(c["subtitle_bottom"], loc="left", color=INK, fontsize=14, fontweight="bold", pad=8)
    ax1.set_xlim(left=0)
    ax1.set_ylim(bottom=0)

    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.13)
    caption(fig, c["note"])
    return fig, pd.DataFrame(all_eps)


def _cagr(v0: float, v1: float, years: int) -> float:
    if v0 <= 0 or years <= 0:
        return 0.0
    return ((v1 / v0) ** (1.0 / years) - 1.0) * 100.0


def _end_tag_nom_real(row: pd.Series, base_year: int = 1990) -> str:
    """Index level + nominal and real CAGR (real uses index_real_1990)."""
    last_y = int(row["year"])
    last_v = float(row["index_1990"])
    n_years = last_y - base_year
    nom = _cagr(100.0, last_v, n_years)
    real_v = row.get("index_real_1990")
    if real_v is not None and pd.notna(real_v):
        real = _cagr(100.0, float(real_v), n_years)
        return f"{last_v:.0f}  (+{nom:.1f}% nom / +{real:.1f}% real)"
    return f"{last_v:.0f}  (+{nom:.1f}%/yr)"


def _plot_cpi_reference(ax, df: pd.DataFrame) -> pd.Series | None:
    """Plot Geneva CPI; return last row for end callout (or None)."""
    if not has(df, "ocstat_cpi_geneva"):
        return None
    s = series(df, "ocstat_cpi_geneva").dropna(subset=["index_1990"])
    s = s[s.year >= 1990]
    if s.empty:
        return None
    ax.plot(
        s.year,
        s.index_1990,
        color=CPI,
        linestyle="--",
        linewidth=1.8,
        label="Geneva CPI (OCSTAT)",
        zorder=1,
    )
    return s.iloc[-1]


def fig_normalized(df: pd.DataFrame, c: dict) -> plt.Figure:
    """Core long-run story: OCSTAT + Wüest + Geneva CPI reference."""
    fig, ax = plt.subplots(figsize=(10.5, 6.2))

    specs = [
        ("ocstat_city_ppe", "Geneva city (OCSTAT)", CITY, "-", 2.6),
        ("ocstat_canton_ppe", "Geneva canton (OCSTAT)", CANTON, "-", 2.6),
    ]
    if has(df, "wuest_ppe_lake_geneva"):
        specs.append(("wuest_ppe_lake_geneva", "Lake Geneva region (Wüest)", LAKE, "-", 2.4))
    if has(df, "wuest_ppe_switzerland"):
        specs.append(("wuest_ppe_switzerland", "Switzerland (Wüest)", CH, "-", 2.2))

    cpi_last = _plot_cpi_reference(ax, df)
    end_labels: list[tuple[float, float, str, str]] = []

    for sid, label, color, ls, lw in specs:
        s = series(df, sid).dropna(subset=["index_1990"])
        s = s[s.year >= 1990]
        if s.empty:
            continue
        ax.plot(s.year, s.index_1990, color=color, linestyle=ls,
                linewidth=lw, label=label)
        end_labels.append(
            (s.iloc[-1]["year"], s.iloc[-1]["index_1990"], _end_tag_nom_real(s.iloc[-1]), color)
        )
    if cpi_last is not None:
        end_labels.append(
            (
                float(cpi_last["year"]),
                float(cpi_last["index_1990"]),
                _end_tag_nom_real(cpi_last),
                CPI,
            )
        )

    end_labels.sort(key=lambda x: x[1], reverse=True)
    prev_val = None
    for yr, val, tag, color in end_labels:
        dy = 0
        if prev_val is not None and abs(val - prev_val) < 12:
            dy = -16
        ax.annotate(
            tag,
            xy=(yr, val),
            xytext=(8, dy),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
            color=color,
            va="center",
        )
        prev_val = val

    ax.axhline(100, color=LINE, linewidth=1.0, linestyle=":")
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_xlim(1989.5, None)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(4))
    fig.subplots_adjust(left=0.09, right=0.72, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def fig_houses(df: pd.DataFrame, c: dict) -> plt.Figure:
    """Long-run houses: OCSTAT canton + Wüest + Geneva CPI reference."""
    fig, ax = plt.subplots(figsize=(10.5, 6.2))

    specs = [
        ("ocstat_canton_houses", "Geneva canton houses (OCSTAT)", CANTON, "-", 2.6),
    ]
    if has(df, "wuest_houses_lake_geneva"):
        specs.append(("wuest_houses_lake_geneva", "Lake Geneva houses (Wüest)", LAKE, "-", 2.4))
    if has(df, "wuest_houses_switzerland"):
        specs.append(("wuest_houses_switzerland", "Switzerland houses (Wüest)", CH, "-", 2.2))

    cpi_last = _plot_cpi_reference(ax, df)
    end_labels: list[tuple[float, float, str, str]] = []
    plotted = False
    for sid, label, color, ls, lw in specs:
        s = series(df, sid).dropna(subset=["index_1990"])
        s = s[s.year >= 1990]
        if s.empty:
            continue
        plotted = True
        ax.plot(s.year, s.index_1990, color=color, linestyle=ls, linewidth=lw, label=label)
        end_labels.append(
            (s.iloc[-1]["year"], s.iloc[-1]["index_1990"], _end_tag_nom_real(s.iloc[-1]), color)
        )
    if cpi_last is not None:
        end_labels.append(
            (
                float(cpi_last["year"]),
                float(cpi_last["index_1990"]),
                _end_tag_nom_real(cpi_last),
                CPI,
            )
        )

    if not plotted:
        raise RuntimeError("no house series available — run transform (+ optional Wüest fetch)")

    end_labels.sort(key=lambda x: x[1], reverse=True)
    prev_val = None
    for yr, val, tag, color in end_labels:
        dy = 0
        if prev_val is not None and abs(val - prev_val) < 10:
            dy = -18
        ax.annotate(
            tag,
            xy=(yr, val),
            xytext=(8, dy),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
            color=color,
            va="center",
        )
        prev_val = val

    ax.axhline(100, color=LINE, linewidth=1.0, linestyle=":")
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_xlim(1989.5, None)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(4))
    fig.subplots_adjust(left=0.09, right=0.72, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def fig_prices_vs_costs(df: pd.DataFrame, c: dict) -> plt.Figure:
    """Geneva CPI vs Swiss CPI vs Geneva housing construction cost (no transaction prices)."""
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    specs = [
        ("ocstat_cpi_geneva", "Geneva CPI", CPI, "-", 2.4),
        ("ocstat_cpi_switzerland", "Switzerland CPI", CH, "--", 2.2),
        ("ocstat_construction_housing_ge", "Geneva housing construction cost", CONST_GE, "-", 2.5),
    ]

    end_labels: list[tuple[float, float, str, str]] = []
    for sid, label, color, ls, lw in specs:
        if not has(df, sid):
            continue
        s = series(df, sid).dropna(subset=["index_1990"])
        s = s[s.year >= 1990]
        if s.empty:
            continue
        ax.plot(s.year, s.index_1990, color=color, linestyle=ls, linewidth=lw, label=label)
        last = s.iloc[-1]
        last_y, last_v = int(last["year"]), float(last["index_1990"])
        y0 = int(s.iloc[0]["year"])
        g = _cagr(100.0, last_v, last_y - y0)
        end_labels.append((last_y, last_v, f"{last_v:.0f}  (+{g:.1f}%/yr)", color))

    end_labels.sort(key=lambda x: x[1], reverse=True)
    prev_val = None
    for yr, val, tag, color in end_labels:
        dy = 0
        if prev_val is not None and abs(val - prev_val) < 8:
            dy = -16
        ax.annotate(
            tag,
            xy=(yr, val),
            xytext=(8, dy),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
            color=color,
            va="center",
        )
        prev_val = val

    ax.axhline(100, color=LINE, linewidth=1.0, linestyle=":")
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.set_xlim(1989.5, None)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(4))
    fig.subplots_adjust(left=0.09, right=0.78, top=0.88, bottom=0.16)
    caption(fig, c["note"])
    return fig


def fig_yoy(df: pd.DataFrame, c: dict) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    specs = [
        ("ocstat_canton_ppe", "Geneva canton (OCSTAT)", CANTON, "-", 2.4, "o"),
    ]
    if has(df, "wuest_ppe_lake_geneva"):
        specs.append(("wuest_ppe_lake_geneva", "Lake Geneva (Wüest)", LAKE, "-", 2.1, "s"))
    if has(df, "bis_ch_rpp_nominal"):
        specs.append(("bis_ch_rpp_nominal", "Switzerland (BIS)", BIS, "--", 1.8, None))
    # Short series (~2017+): use dash-dot + markers so it is visible vs BIS
    if has(df, "bfs_impi_condo"):
        specs.append(("bfs_impi_condo", "Switzerland condo (BFS IMPI, from 2017)", BFS, "-.", 2.3, "D"))

    for sid, label, color, ls, lw, marker in specs:
        s = series(df, sid).dropna(subset=["yoy_pct"])
        s = s[s.year >= 1991]
        if s.empty:
            continue
        ax.plot(
            s.year,
            s.yoy_pct,
            color=color,
            linestyle=ls,
            linewidth=lw,
            marker=marker,
            markersize=5.0 if marker else 0,
            label=label,
            zorder=4 if sid == "bfs_impi_condo" else 2,
        )
    ax.axhline(0, color=LINE, linewidth=1.0)
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="best")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def fig_relative(df: pd.DataFrame, c: dict) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    plotted = False
    if has(df, "wuest_ppe_lake_geneva") and has(df, "wuest_ppe_switzerland"):
        lake = series(df, "wuest_ppe_lake_geneva").set_index("year")["index_1990"]
        swiss = series(df, "wuest_ppe_switzerland").set_index("year")["index_1990"]
        rel = (lake / swiss * 100).dropna()
        rel = rel[rel.index >= 1990]
        ax.plot(rel.index, rel.values, color=LAKE, linewidth=2.5, label="Lake Geneva / Switzerland (Wüest)")
        plotted = True
    if has(df, "ocstat_canton_ppe") and has(df, "bis_ch_rpp_nominal"):
        ge = series(df, "ocstat_canton_ppe").set_index("year")["index_1990"]
        swiss = series(df, "bis_ch_rpp_nominal").set_index("year")["index_1990"]
        rel_b = (ge / swiss * 100).dropna()
        rel_b = rel_b[rel_b.index >= 1990]
        ax.plot(
            rel_b.index,
            rel_b.values,
            color=BIS,
            linewidth=1.8,
            linestyle="--",
            label="Geneva canton (OCSTAT) / Switzerland (BIS)",
        )
        plotted = True
    if not plotted:
        raise RuntimeError("no relative series available")

    ax.axhline(100, color=LINE, linewidth=1.0, linestyle=":", label="Parity since 1990")
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="best")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def fig_open_official(df: pd.DataFrame, c: dict) -> plt.Figure:
    """Recent window: open official CH (BIS + BFS IMPI) vs OCSTAT / Wüest, 2017=100."""
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    specs = [
        ("ocstat_canton_ppe", "Geneva canton (OCSTAT)", CANTON, "-", 2.4),
        ("bis_ch_rpp_nominal", "Switzerland RPP nominal (BIS)", BIS, "--", 2.0),
        ("bis_ch_rpp_real", "Switzerland RPP real (BIS)", BIS_REAL, "--", 1.7),
        ("bfs_impi_condo", "Switzerland condo IMPI (BFS)", BFS, "-", 2.2),
    ]
    if has(df, "wuest_ppe_switzerland"):
        specs.append(("wuest_ppe_switzerland", "Switzerland PPE (Wüest)", CH, ":", 2.0))

    for sid, label, color, ls, lw in specs:
        if not has(df, sid):
            continue
        s = series(df, sid).dropna(subset=["index_2017"])
        s = s[s.year >= 2017]
        if s.empty:
            continue
        ax.plot(s.year, s.index_2017, color=color, linestyle=ls, linewidth=lw, label=label)
    ax.axhline(100, color=LINE, linewidth=1.0, linestyle=":")
    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def fig_implied_size(df: pd.DataFrame, c: dict) -> plt.Figure:
    """Implied typical PPE size: median object price / median CHF/m² (new vs existing)."""
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    specs = [
        ("ocstat_ppe_implied_m2_new", "New apartments (neufs)", NEW, "-", 2.5),
        ("ocstat_ppe_implied_m2_existing", "Existing apartments (non-neufs)", EXISTING, "-", 2.5),
    ]
    end_labels: list[tuple[float, float, str, str]] = []
    plotted = False
    for sid, label, color, ls, lw in specs:
        if not has(df, sid):
            continue
        s = series(df, sid).dropna(subset=["value"]).sort_values("year")
        if s.empty:
            continue
        plotted = True
        ax.plot(s.year, s.value, color=color, linestyle=ls, linewidth=lw, label=label)
        last = s.iloc[-1]
        first = s.iloc[0]
        n = int(last["year"] - first["year"])
        if n > 0 and float(first["value"]) > 0:
            cagr = (float(last["value"]) / float(first["value"])) ** (1 / n) - 1
            tag = f"{last['value']:.0f} m²  ({cagr*100:+.1f}%/yr)"
        else:
            tag = f"{last['value']:.0f} m²"
        end_labels.append((float(last["year"]), float(last["value"]), tag, color))

    if not plotted:
        raise RuntimeError("no implied-size series — re-run transform_long_run.py")

    end_labels.sort(key=lambda x: x[1], reverse=True)
    prev_val = None
    for yr, val, tag, color in end_labels:
        dy = 0
        if prev_val is not None and abs(val - prev_val) < 8:
            dy = -16
        ax.annotate(
            tag,
            xy=(yr, val),
            xytext=(8, dy),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
            color=color,
            va="center",
        )
        prev_val = val

    style_ax(ax, c["ylabel"])
    fig_title(fig, c["title"])
    ax.legend(frameon=False, fontsize=10, loc="upper right")
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))
    fig.subplots_adjust(left=0.09, right=0.78, top=0.88, bottom=0.18)
    caption(fig, c["note"])
    return fig


def write_validation_box() -> None:
    if not VAL_PATH.exists():
        return
    val = json.loads(VAL_PATH.read_text(encoding="utf-8"))
    lines = [
        "# Long-run validation box (draft)",
        "",
        "Official Geneva prices ↔ professional / national index ↔ Swiss cycle",
        "",
        "Series available: " + ", ".join(val.get("series_available") or []),
        "",
    ]
    for p in val.get("pairs", []):
        a, b = p["pair"]
        corr_i = p.get("corr_index_1990")
        corr_y = p.get("corr_yoy")
        direc = p.get("direction_agreement_yoy")
        lines.append(f"## {a} vs {b}")
        lines.append(f"- Corr (index 1990=100): {corr_i:.3f}" if corr_i is not None else "- Corr index: n/a")
        lines.append(f"- Corr (YoY): {corr_y:.3f}" if corr_y is not None else "- Corr YoY: n/a")
        if direc is not None:
            mark = "✓" if direc >= 0.7 else ("~" if direc >= 0.55 else "✗")
            lines.append(f"- Direction agreement (YoY): {direc:.0%} {mark}")
        if p.get("cagr_a") is not None and p.get("cagr_b") is not None:
            lines.append(f"- CAGR: {p['cagr_a']:.2%} vs {p['cagr_b']:.2%}")
        lines.append("")
    for n in val.get("notes", []):
        lines.append(f"- {n}")
    out = STEP / "long_run" / "exports" / "validation_box.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {out.relative_to(ROOT)}")


def main() -> int:
    plt.rcParams.update(
        {
            "figure.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "axes.unicode_minus": False,
            "font.size": 10,
        }
    )
    copy = load_copy()
    df = pd.read_csv(DATA / "fact_long_run_ppe.csv")
    dump(fig_normalized(df, copy["lr_01_normalized_trend"]), "lr_01_normalized_trend")
    dump(fig_houses(df, copy["lr_06_houses_trend"]), "lr_06_houses_trend")
    dump(fig_prices_vs_costs(df, copy["lr_07_prices_vs_costs"]), "lr_07_prices_vs_costs")
    dump(fig_implied_size(df, copy["lr_08_implied_size"]), "lr_08_implied_size")
    dump(fig_yoy(df, copy["lr_02_yoy_growth"]), "lr_02_yoy_growth")
    dump(fig_relative(df, copy["lr_03_relative_performance"]), "lr_03_relative_performance")
    dump(fig_open_official(df, copy["lr_04_open_official"]), "lr_04_open_official")
    fig05, eps = fig_drawdowns(df, copy["lr_05_drawdowns"])
    dump(fig05, "lr_05_drawdowns")
    eps_path = STEP / "long_run" / "exports" / "drawdown_episodes.csv"
    eps.to_csv(eps_path, index=False)
    print(f"  {eps_path.relative_to(ROOT)}")
    write_validation_box()
    print(f"Figures -> {FIGURES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
