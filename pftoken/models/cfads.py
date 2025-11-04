"""
Cash Flow Available for Debt Service (CFADS) calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .params import ProjectParameters


class CFADSScenarioInputs(BaseModel):
    """
    Scenario modifiers applied on top of the deterministic parameters.
    """

    model_config = ConfigDict(validate_assignment=True)

    arpu_multiplier: float = Field(1.0, ge=0.0)
    arpu_growth_shock: float = Field(0.0, ge=-1.0)
    device_multiplier: float = Field(1.0, ge=0.0)
    device_growth_shock: float = Field(0.0, ge=-1.0)
    additional_devices: int = 0
    opex_multiplier: float = Field(1.0, ge=0.0)
    opex_inflation_override: Optional[float] = Field(None, ge=-1.0)
    working_capital_override: Optional[float] = Field(None, ge=0.0, le=1.0)
    additional_capex: float = 0.0
    interest_override: Optional[float] = None
    depreciation_override: Optional[float] = None


@dataclass(frozen=True)
class CFADSStatement:
    year: int
    devices: float
    arpu: float
    revenue: float
    opex: float
    ebitda: float
    depreciation: float
    interest: float
    ebt: float
    taxes: float
    capex: float
    rcapex_investment: float
    delta_working_capital: float
    cfads: float


def calculate_cfads(
    params: ProjectParameters,
    year: int,
    scenario: Optional[CFADSScenarioInputs] = None,
) -> CFADSStatement:
    """
    Calculate CFADS for a given year using validated project parameters.
    """

    if year not in params.timeline_years:
        raise ValueError(f"Year {year} outside model timeline.")

    scen = scenario or CFADSScenarioInputs()

    devices = _compute_devices(params, year, scen)
    arpu = _compute_arpu(params, year, scen)
    revenue = devices * arpu

    opex = _compute_opex(params, year, revenue, scen)
    ebitda = revenue - opex

    rcapex = _rcapex_for_year(params.rcapex_schedule, year)
    capex_total = scen.additional_capex

    depreciation = (
        scen.depreciation_override
        if scen.depreciation_override is not None
        else _compute_depreciation(params, rcapex)
    )

    interest = (
        scen.interest_override
        if scen.interest_override is not None
        else _interest_for_year(params.debt_service_schedule, year)
    )

    working_capital_pct = (
        scen.working_capital_override
        if scen.working_capital_override is not None
        else params.financials.working_capital_pct
    )
    delta_wc = revenue * working_capital_pct

    ebt = ebitda - depreciation - interest
    taxable_income = max(ebt, 0.0)
    taxes = taxable_income * params.financials.tax_rate

    cfads_value = ebitda - taxes - capex_total - delta_wc

    return CFADSStatement(
        year=year,
        devices=devices,
        arpu=arpu,
        revenue=revenue,
        opex=opex,
        ebitda=ebitda,
        depreciation=depreciation,
        interest=interest,
        ebt=ebt,
        taxes=taxes,
        capex=capex_total,
        rcapex_investment=rcapex,
        delta_working_capital=delta_wc,
        cfads=cfads_value,
    )


class CFADSModel:
    """Convenience wrapper mirroring the previous placeholder API."""

    def __init__(self, params: ProjectParameters):
        self.params = params

    def run(
        self,
        year: int,
        scenario: Optional[CFADSScenarioInputs] = None,
    ) -> CFADSStatement:
        return calculate_cfads(self.params, year, scenario=scenario)


def _compute_devices(
    params: ProjectParameters, year: int, scenario: CFADSScenarioInputs
) -> float:
    growth = params.operational.iot_device_growth_rate + scenario.device_growth_shock
    effective_growth = max(growth, -0.99)
    base_devices = params.operational.initial_devices * (
        (1 + effective_growth) ** (year - 1)
    )
    devices = base_devices * scenario.device_multiplier + scenario.additional_devices
    return max(devices, 0.0)


def _compute_arpu(
    params: ProjectParameters, year: int, scenario: CFADSScenarioInputs
) -> float:
    growth = params.operational.arpu_growth_rate + scenario.arpu_growth_shock
    effective_growth = max(growth, -0.99)
    base_arpu = params.operational.base_arpu * (
        (1 + effective_growth) ** (year - 1)
    )
    return base_arpu * scenario.arpu_multiplier


def _compute_opex(
    params: ProjectParameters,
    year: int,
    revenue: float,
    scenario: CFADSScenarioInputs,
) -> float:
    base_ratio = params.financials.opex_ratio
    inflation = (
        scenario.opex_inflation_override
        if scenario.opex_inflation_override is not None
        else params.financials.opex_growth_rate
    )
    effective_inflation = max(inflation, -0.99)
    opex_base = revenue * base_ratio
    opex = opex_base * ((1 + effective_inflation) ** (year - 1))
    return opex * scenario.opex_multiplier


def _compute_depreciation(params: ProjectParameters, rcapex: float) -> float:
    useful_life = params.operational.satellite_life_years
    base = params.financials.initial_capex / useful_life
    incremental = rcapex / useful_life if useful_life else 0.0
    return base + incremental


def _interest_for_year(debt_schedule: pd.DataFrame, year: int) -> float:
    mask = debt_schedule["year"] == year
    return float(debt_schedule.loc[mask, "interest_due"].sum())


def _rcapex_for_year(rcapex_schedule: pd.DataFrame, year: int) -> float:
    mask = rcapex_schedule["year"] == year
    if mask.any():
        return float(rcapex_schedule.loc[mask, "rcapex_amount"].sum())
    return 0.0


__all__ = [
    "CFADSScenarioInputs",
    "CFADSStatement",
    "calculate_cfads",
    "CFADSModel",
]
