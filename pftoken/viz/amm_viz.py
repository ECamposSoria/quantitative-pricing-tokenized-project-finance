"""
Visualization helpers focused on AMM analytics.
"""

from __future__ import annotations

from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np


def plot_price_series(prices: Iterable[float], title: str = "AMM Price Path") -> plt.Figure:
    """Generate a simple line chart for AMM price evolution."""
    fig, ax = plt.subplots()
    ax.plot(list(prices))
    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel("Price (token1 per token0)")
    return fig


def plot_price_vs_dcf(pool_prices: Iterable[float], dcf_prices: Iterable[float]) -> plt.Figure:
    fig, ax = plt.subplots()
    ax.plot(pool_prices, label="Pool")
    ax.plot(dcf_prices, label="DCF")
    ax.set_title("Pool vs DCF Price")
    ax.set_xlabel("Step")
    ax.set_ylabel("Price")
    ax.legend()
    return fig


def plot_il_heatmap(il_surface: np.ndarray, ratios: Iterable[float], ranges: Iterable[tuple[int, int]]) -> plt.Figure:
    fig, ax = plt.subplots()
    im = ax.imshow(il_surface, aspect="auto", origin="lower", cmap="coolwarm")
    ax.set_xticks(range(len(list(ratios))))
    ax.set_xticklabels([f"{r:.2f}" for r in ratios])
    ax.set_yticks(range(len(list(ranges))))
    ax.set_yticklabels([f"{lo},{hi}" for lo, hi in ranges])
    ax.set_xlabel("Price Ratio")
    ax.set_ylabel("Tick Range")
    ax.set_title("IL Heatmap")
    fig.colorbar(im, ax=ax, label="IL Fraction")
    return fig


def plot_stress_outcomes(stress_results: Dict[str, np.ndarray]) -> plt.Figure:
    fig, ax = plt.subplots()
    for name, path in stress_results.items():
        ax.plot(path, label=name)
    ax.set_title("Liquidity Paths Under Stress")
    ax.set_xlabel("Step")
    ax.set_ylabel("Liquidity (notional)")
    ax.legend()
    return fig


def plot_liquidity_depth(depth_curve: np.ndarray) -> plt.Figure:
    fig, ax = plt.subplots()
    ax.plot(depth_curve[:, 0], depth_curve[:, 1])
    ax.set_title("Liquidity Depth Curve")
    ax.set_xlabel("Price")
    ax.set_ylabel("Token0 Depth")
    return fig
