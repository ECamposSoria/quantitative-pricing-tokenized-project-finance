"""
Visualization helpers focused on AMM analytics.
"""

from __future__ import annotations

from typing import Iterable

import matplotlib.pyplot as plt


def plot_price_series(prices: Iterable[float], title: str = "AMM Price Path") -> plt.Figure:
    """Generate a simple line chart for AMM price evolution."""
    fig, ax = plt.subplots()
    ax.plot(list(prices))
    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel("Price (token1 per token0)")
    return fig
