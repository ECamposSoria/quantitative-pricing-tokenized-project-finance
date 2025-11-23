"""Reusable matplotlib plots for the financial dashboard."""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .styles import get_palette


def plot_cfads_vs_debt_service(
    years: Sequence[int],
    cfads: Sequence[float],
    debt_service: Sequence[float],
) -> plt.Figure:
    """Line chart comparing CFADS and debt service over time."""
    palette = get_palette()
    fig, ax = plt.subplots()
    ax.plot(years, np.array(cfads) / 1e6, label="CFADS (MM)", color=palette.primary)
    ax.plot(
        years,
        np.array(debt_service) / 1e6,
        label="Servicio de deuda (MM)",
        color=palette.secondary,
        linestyle="--",
    )
    ax.set_title("CFADS vs. Servicio de Deuda")
    ax.set_xlabel("Año")
    ax.set_ylabel("USD millones")
    ax.axhline(0.0, color=palette.neutral, linewidth=0.8)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_dscr_series(
    years: Sequence[int],
    dscr: Sequence[float],
    min_threshold: float,
) -> plt.Figure:
    """Bar chart of DSCR values highlighting covenant breaches."""
    palette = get_palette()
    dscr_arr = np.array(dscr, dtype=float)
    colors = np.where(
        dscr_arr >= min_threshold,
        palette.accent_positive,
        palette.accent_negative,
    )

    fig, ax = plt.subplots()
    ax.bar(years, dscr_arr, color=colors)
    ax.axhline(min_threshold, color=palette.neutral, linestyle="--", label="Covenant")
    ax.set_title("DSCR por año")
    ax.set_xlabel("Año")
    ax.set_ylabel("DSCR")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_ratio_snapshot(
    labels: Iterable[str],
    values: Iterable[float],
    thresholds: Iterable[float],
) -> plt.Figure:
    """Horizontal bar plot summarising LLCR/PLCR vs. thresholds."""
    palette = get_palette()
    labels_list = list(labels)
    values_arr = np.array(list(values), dtype=float)
    threshold_arr = np.array(list(thresholds), dtype=float)
    colors = np.where(
        values_arr >= threshold_arr,
        palette.accent_positive,
        palette.accent_negative,
    )

    y_pos = np.arange(len(labels_list))
    fig, ax = plt.subplots()
    ax.barh(y_pos, values_arr, color=colors)
    ax.scatter(threshold_arr, y_pos, marker="D", color=palette.secondary, label="Covenant")
    ax.set_yticks(y_pos, labels_list)
    ax.set_xlabel("Ratio")
    ax.set_title("Resumen de LLCR / PLCR")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_capital_structure(tranche_labels: Sequence[str], notionals: Sequence[float]) -> plt.Figure:
    """Pie chart of the capital structure by tranche notional."""
    palette = get_palette()
    notionals_arr = np.array(notionals, dtype=float)
    total = notionals_arr.sum()
    if total <= 0:
        notionals_arr = np.ones_like(notionals_arr)
        total = notionals_arr.sum()
    fig, ax = plt.subplots()
    ax.pie(
        notionals_arr,
        labels=tranche_labels,
        autopct=lambda pct: f"{pct:.1f}%",
        colors=[palette.primary, palette.secondary, palette.accent_positive, palette.neutral],
    )
    ax.set_title("Estructura de Capital (Notional)")
    fig.tight_layout()
    return fig


def plot_waterfall_cascade(
    years: Sequence[int],
    interest: Sequence[float],
    principal: Sequence[float],
    dividends: Sequence[float],
) -> plt.Figure:
    """Stacked bars showing how CFADS flows through the waterfall."""

    palette = get_palette()
    fig, ax = plt.subplots()
    ax.bar(years, interest, label="Intereses", color=palette.secondary, alpha=0.8)
    ax.bar(
        years,
        principal,
        bottom=np.array(interest),
        label="Principal",
        color=palette.primary,
        alpha=0.8,
    )
    ax.plot(years, dividends, label="Dividendos", color=palette.accent_positive, linewidth=2)
    ax.set_title("Waterfall: Intereses / Principal / Dividendos")
    ax.set_xlabel("Año")
    ax.set_ylabel("USD millones")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_reserve_levels(
    years: Sequence[int],
    dsra_balance: Sequence[float],
    dsra_target: Sequence[float],
    mra_balance: Sequence[float],
    mra_target: Sequence[float],
) -> plt.Figure:
    """Line chart tracking DSRA/MRA balances versus targets."""

    palette = get_palette()
    fig, ax = plt.subplots()
    ax.plot(years, dsra_balance, label="DSRA", color=palette.primary, linewidth=2)
    ax.plot(years, dsra_target, label="DSRA Target", color=palette.primary, linestyle="--")
    ax.plot(years, mra_balance, label="MRA", color=palette.secondary, linewidth=2)
    ax.plot(years, mra_target, label="MRA Target", color=palette.secondary, linestyle="--")
    ax.set_title("Reservas DSRA / MRA")
    ax.set_xlabel("Año")
    ax.set_ylabel("USD millones")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_covenant_heatmap(
    years: Sequence[int],
    dscr_values: Sequence[float],
    thresholds: Sequence[float],
) -> plt.Figure:
    """Heatmap-like visualization showing DSCR vs. thresholds."""

    palette = get_palette()
    colors = []
    for value, threshold in zip(dscr_values, thresholds):
        if value >= threshold:
            colors.append(palette.accent_positive)
        elif value >= 1.0:
            colors.append(palette.secondary)
        else:
            colors.append(palette.accent_negative)
    fig, ax = plt.subplots()
    ax.bar(years, dscr_values, color=colors)
    ax.set_title("DSCR Heatmap")
    ax.set_xlabel("Año")
    ax.set_ylabel("DSCR")
    ax.axhline(1.45, color=palette.neutral, linestyle="--", label="Target 1.45x")
    ax.axhline(1.25, color=palette.neutral, linestyle=":", label="Warning 1.25x")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_structure_radar(metrics: Iterable[tuple[str, float]], baseline: float) -> plt.Figure:
    """Radar chart comparing concentration metrics."""

    labels, values = zip(*metrics)
    values = list(values)
    angles = np.linspace(0, 2 * np.pi, len(values), endpoint=False)
    values += values[:1]
    angles = np.concatenate([angles, angles[:1]])

    fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    ax.plot(angles, values, label="Tokenized", linewidth=2)
    ax.fill(angles, values, alpha=0.2)
    ax.plot(angles, [baseline] * len(angles), linestyle="--", label="Traditional")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_title("Comparación de estructura")
    ax.legend(loc="upper right")
    return fig


def plot_fan_chart(
    years: Sequence[int],
    percentiles: Mapping[int, Sequence[float]],
    *,
    threshold: float | None = None,
    title: str = "Fan chart",
) -> plt.Figure:
    """Plot percentile bands for simulated ratios (e.g., DSCR)."""

    palette = get_palette()
    order = sorted(percentiles.keys())
    p5 = percentiles.get(5) or percentiles.get(10)
    p25 = percentiles.get(25)
    p50 = percentiles.get(50)
    p75 = percentiles.get(75)
    p95 = percentiles.get(95) or percentiles.get(90)

    fig, ax = plt.subplots()
    if p95 is not None and p5 is not None:
        ax.fill_between(years, p5, p95, color=palette.primary, alpha=0.1, label="P5–P95")
    if p75 is not None and p25 is not None:
        ax.fill_between(years, p25, p75, color=palette.primary, alpha=0.2, label="P25–P75")
    if p50 is not None:
        ax.plot(years, p50, color=palette.primary, linewidth=2, label="P50")
    if threshold is not None:
        ax.axhline(threshold, color=palette.neutral, linestyle="--", label="Threshold")
    ax.set_title(title)
    ax.set_xlabel("Año")
    ax.set_ylabel("Valor")
    ax.legend()
    fig.tight_layout()
    return fig


__all__ = [
    "plot_cfads_vs_debt_service",
    "plot_dscr_series",
    "plot_ratio_snapshot",
    "plot_capital_structure",
    "plot_waterfall_cascade",
    "plot_reserve_levels",
    "plot_covenant_heatmap",
    "plot_structure_radar",
    "plot_fan_chart",
]
