"""Shared deterministic configuration for WP-02/WP-03 models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

# --- Reserve policy constants -------------------------------------------------
# DSRA baseline and RCAPEX diet are locked by the implementation guide and
# should never be sourced from mutable config files or spreadsheets.
INITIAL_DSRA_FUNDING_MUSD = 18.0
MRA_TARGET_PCT_NEXT_RCAPEX = 0.50

# Hard-coded RCAPEX diet (years 6–15) expressed in millions of USD.
RCAPEX_DIET_MUSD: Dict[int, float] = {
    6: 1.2,
    7: 1.5,
    8: 1.65,
    9: 1.7,
    10: 1.55,
    11: 3.4,
    12: 2.25,
    13: 2.0,
    14: 1.5,
    15: 1.25,
}


@dataclass(frozen=True)
class DSCRThresholds:
    """Phase-specific DSCR targets shared across calculators and dashboards."""

    grace: float = 1.00
    ramp: float = 1.15
    steady: float = 1.25


@dataclass(frozen=True)
class CovenantLimits:
    """Covenant floors sourced from locked requirements."""

    min_dscr: float = 1.20
    min_llcr: float = 1.20
    min_ltv: float = 0.65  # placeholder until formal LTV calc is wired
    dscr_default_trigger: float = 1.00
    dscr_grace_threshold: float = 1.00


# Minimum LLCR targets by seniority tier (used for reporting only).
LLCR_TARGET_BY_PRIORITY: Dict[int, float] = {
    1: 1.35,  # senior
    2: 1.20,  # mezzanine
    3: 1.05,  # subordinated
}


@dataclass(frozen=True)
class ReservePolicy:
    """Reserve sizing policy (deterministic, non-configurable)."""

    dsra_initial_musd: float = INITIAL_DSRA_FUNDING_MUSD
    dsra_months_cover: int = 6
    mra_target_pct_next_rcapex: float = MRA_TARGET_PCT_NEXT_RCAPEX


DEFAULT_DSCR_THRESHOLDS = DSCRThresholds()
DEFAULT_COVENANT_LIMITS = CovenantLimits()
DEFAULT_RESERVE_POLICY = ReservePolicy()


__all__ = [
    "DEFAULT_COVENANT_LIMITS",
    "DEFAULT_DSCR_THRESHOLDS",
    "DEFAULT_RESERVE_POLICY",
    "DSCRThresholds",
    "CovenantLimits",
    "ReservePolicy",
    "RCAPEX_DIET_MUSD",
    "INITIAL_DSRA_FUNDING_MUSD",
    "MRA_TARGET_PCT_NEXT_RCAPEX",
    "LLCR_TARGET_BY_PRIORITY",
]
