"""Reusable matplotlib plots for the financial dashboard."""

from __future__ import annotations

from typing import Iterable, Sequence

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


__all__ = [
    "plot_cfads_vs_debt_service",
    "plot_dscr_series",
    "plot_ratio_snapshot",
    "plot_capital_structure",
]
