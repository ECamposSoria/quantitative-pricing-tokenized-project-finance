"""
Heatmap visualisations for AMM liquidity distributions.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np


def plot_liquidity_heatmap(grid: Sequence[Sequence[float]], title: str = "Liquidity Heatmap") -> plt.Figure:
    data = np.asarray(grid, dtype=float)
    fig, ax = plt.subplots()
    heatmap = ax.imshow(data, origin="lower", aspect="auto")
    fig.colorbar(heatmap, ax=ax, label="Liquidity")
    ax.set_title(title)
    ax.set_xlabel("Tick bucket")
    ax.set_ylabel("Time step")
    return fig
