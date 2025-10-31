"""Lightweight styling helpers for the dashboard plots."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardPalette:
    """Color palette used across dashboard figures."""

    primary: str = "#1f77b4"
    secondary: str = "#ff7f0e"
    accent_positive: str = "#2ca02c"
    accent_negative: str = "#d62728"
    neutral: str = "#7f7f7f"


def get_palette() -> DashboardPalette:
    """Return the default dashboard color palette."""
    return DashboardPalette()


__all__ = ["DashboardPalette", "get_palette"]
