"""
Financial coverage ratios for project finance (DSCR, LLCR, PLCR).

Implements T-004: Ratios financieros DSCR/LLCR/PLCR
Integrates with T-003 (CFADS) and T-006 (waterfall/debt service).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from .cfads import CFADSScenarioInputs, calculate_cfads
from .params import ProjectParameters


@dataclass(frozen=True)
class CoverageRatioResult:
    """Single period coverage ratio metrics."""

    year: int
    cfads: float
    debt_service: float
    debt_outstanding: float
    dscr: float
    llcr: float
    plcr: float


@dataclass
class CoverageRatioResults:
    """Complete coverage ratios for all project periods."""

    results: List[CoverageRatioResult]
    covenant_min_dscr: float
    covenant_min_llcr: float

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame for analysis."""
        return pd.DataFrame([
            {
                'year': r.year,
                'cfads': r.cfads,
                'debt_service': r.debt_service,
                'debt_outstanding': r.debt_outstanding,
                'dscr': r.dscr,
                'llcr': r.llcr,
                'plcr': r.plcr,
            }
            for r in self.results
        ])

    def get_dscr_violations(self) -> List[CoverageRatioResult]:
        """Return periods where DSCR < covenant threshold."""
        return [r for r in self.results if r.dscr < self.covenant_min_dscr]

    def get_llcr_violations(self) -> List[CoverageRatioResult]:
        """Return periods where LLCR < covenant threshold."""
        return [r for r in self.results if r.llcr < self.covenant_min_llcr]

    def summary(self) -> dict:
        """Return summary statistics."""
        df = self.to_dataframe()
        return {
            'min_dscr': df['dscr'].replace([np.inf, -np.inf], np.nan).min(),
            'avg_dscr': df['dscr'].replace([np.inf, -np.inf], np.nan).mean(),
            'min_llcr': df['llcr'].replace([np.inf, -np.inf], np.nan).min(),
            'avg_llcr': df['llcr'].replace([np.inf, -np.inf], np.nan).mean(),
            'min_plcr': df['plcr'].replace([np.inf, -np.inf], np.nan).min(),
            'avg_plcr': df['plcr'].replace([np.inf, -np.inf], np.nan).mean(),
            'dscr_violations': len(self.get_dscr_violations()),
            'llcr_violations': len(self.get_llcr_violations()),
        }


def present_value(cashflows: np.ndarray, r: float) -> float:
    """
    Valor Presente Neto con descuento desde t=1.

    El flujo en el año actual (índice 0) se descuenta por (1+r)^1,
    el flujo del próximo año (índice 1) se descuenta por (1+r)^2, etc.

    Formula: VP = Σ [CFt / (1+r)^t] para t = 1, 2, ..., N
    """
    if len(cashflows) == 0:
        return 0.0

    # Empezar desde t=1, no t=0
    T = np.arange(1, len(cashflows) + 1)
    disc = 1.0 / (1.0 + r) ** T
    return float(np.sum(cashflows * disc))


def compute_dscr(
    cfads: np.ndarray,
    debt_service: np.ndarray,
    min_threshold: float = 1.0,
    warn: bool = True,
) -> np.ndarray:
    """
    DSCR_t = CFADS_t / ServicioDeuda_t

    ServicioDeuda_t = Intereses_t + Amortización_t

    Interpretación:
    - DSCR > 1: Flujo suficiente para pagar deuda
    - DSCR < 1: Flujo insuficiente (incumplimiento técnico)

    Args:
        cfads: Cash Flow Available for Debt Service por período
        debt_service: Servicio de deuda total (intereses + principal) por período
        min_threshold: Umbral mínimo de covenant (default 1.0)
        warn: Emitir warnings cuando DSCR < threshold

    Returns:
        Array de DSCR por período (np.inf cuando debt_service = 0)
    """
    # Validar que no haya valores negativos
    if np.any(cfads < 0) and warn:
        warnings.warn(
            f"CFADS negativo detectado en {np.sum(cfads < 0)} períodos. "
            "Esto puede indicar problemas de flujo de caja.",
            UserWarning,
        )

    if np.any(debt_service < 0) and warn:
        warnings.warn(
            "Servicio de deuda negativo detectado. Verificar debt_schedule.",
            UserWarning,
        )

    # Evitar división por cero (períodos de gracia retornan np.inf)
    with np.errstate(divide="ignore", invalid="ignore"):
        dscr = np.where(debt_service > 0, cfads / debt_service, np.inf)

    # Advertir sobre incumplimientos técnicos
    if warn:
        violations = np.sum((dscr < min_threshold) & (dscr != np.inf))
        if violations > 0:
            warnings.warn(
                f"DSCR < {min_threshold} en {violations} períodos. "
                "Incumplimiento técnico de covenant.",
                UserWarning,
            )

    return dscr


def compute_llcr(
    cfads_future: np.ndarray,
    debt_outstanding: float,
    discount_rate: float,
) -> float:
    """
    LLCR = VP(CFADS desde t hasta maturity deuda) / DeudaRestante_t

    Mide si los flujos futuros hasta el vencimiento del préstamo
    alcanzan para cubrir la deuda pendiente.

    Interpretación:
    - LLCR > 1: Flujos futuros cubren deuda restante (proyecto solvente)
    - LLCR < 1: Flujos insuficientes (riesgo de incumplimiento)

    Args:
        cfads_future: CFADS desde el año actual hasta fin del préstamo
        debt_outstanding: Deuda restante al final del año anterior
        discount_rate: Tasa de descuento (típicamente WACC)

    Returns:
        LLCR (np.inf si debt_outstanding = 0)
    """
    if debt_outstanding <= 0:
        return float(np.inf)

    vp = present_value(cfads_future, discount_rate)
    return vp / debt_outstanding


def compute_plcr(
    cfads_full: np.ndarray,
    debt_initial: float,
    discount_rate: float,
) -> float:
    """
    PLCR = VP(CFADS vida total del proyecto) / DeudaInicial

    Mide si el proyecto puede generar suficiente dinero durante
    toda su vida para pagar la deuda inicial.

    Interpretación:
    - PLCR > 1: Proyecto genera suficiente para pagar deuda + margen
    - PLCR < 1: Flujos totales no cubren deuda inicial

    Args:
        cfads_full: CFADS para toda la vida útil del proyecto
        debt_initial: Monto total del préstamo tomado
        discount_rate: Tasa de descuento (típicamente WACC)

    Returns:
        PLCR (np.inf si debt_initial = 0)
    """
    if debt_initial <= 0:
        return float(np.inf)

    vp = present_value(cfads_full, discount_rate)
    return vp / debt_initial


def extract_debt_service(
    debt_schedule: pd.DataFrame,
    year: int,
) -> float:
    """
    Extrae servicio de deuda total para un año dado.

    ServicioDeuda = Σ(intereses + principal) para todas las tranches

    Args:
        debt_schedule: DataFrame con columnas: year, tranche_name, interest_due, principal_due
        year: Año para el cual calcular servicio de deuda

    Returns:
        Servicio de deuda total (intereses + principal)
    """
    mask = debt_schedule['year'] == year
    if not mask.any():
        return 0.0

    year_data = debt_schedule.loc[mask]
    interest = year_data['interest_due'].sum()
    principal = year_data['principal_due'].sum()

    return float(interest + principal)


def compute_remaining_debt(
    debt_schedule: pd.DataFrame,
    from_year: int,
) -> float:
    """
    Calcula deuda restante sumando todos los pagos de principal futuros.

    DeudaRestante = Σ(principal_due) para year >= from_year

    Args:
        debt_schedule: DataFrame con columnas: year, tranche_name, principal_due
        from_year: Año desde el cual calcular deuda restante (inclusive)

    Returns:
        Deuda pendiente total
    """
    mask = debt_schedule['year'] >= from_year
    if not mask.any():
        return 0.0

    return float(debt_schedule.loc[mask, 'principal_due'].sum())


def calculate_coverage_ratios(
    params: ProjectParameters,
    scenario: Optional[CFADSScenarioInputs] = None,
) -> CoverageRatioResults:
    """
    Calcula ratios de cobertura (DSCR, LLCR, PLCR) para todos los años del proyecto.

    Integra:
    - T-003: CFADS calculation
    - T-006: Debt service from waterfall/schedule
    - Covenant thresholds from ProjectParameters

    Args:
        params: Parámetros validados del proyecto
        scenario: Modificadores de escenario opcionales

    Returns:
        CoverageRatioResults con métricas por año y métodos de análisis
    """
    # Configuración
    discount_rate = params.financials.target_wacd
    min_dscr = params.covenants.min_dscr
    min_llcr = params.covenants.min_llcr

    # Calcular deuda inicial total
    debt_initial = sum(tranche.notional for tranche in params.debt.tranches)

    # Arrays para almacenar resultados
    years = list(params.timeline_years)
    cfads_array = np.zeros(len(years))
    debt_service_array = np.zeros(len(years))

    # Calcular CFADS y servicio de deuda para cada año
    for i, year in enumerate(years):
        # CFADS del año (T-003)
        cfads_stmt = calculate_cfads(params, year, scenario)
        cfads_array[i] = cfads_stmt.cfads

        # Servicio de deuda del año (T-006)
        debt_service_array[i] = extract_debt_service(params.debt_service_schedule, year)

    # Calcular DSCR para todos los años
    dscr_array = compute_dscr(
        cfads_array,
        debt_service_array,
        min_threshold=min_dscr,
        warn=True,
    )

    # Calcular LLCR y PLCR para cada año
    results = []
    for i, year in enumerate(years):
        # LLCR: VP de CFADS futuros / Deuda restante
        cfads_future = cfads_array[i:]
        debt_outstanding = compute_remaining_debt(params.debt_service_schedule, year)
        llcr = compute_llcr(cfads_future, debt_outstanding, discount_rate)

        # PLCR: VP de todo CFADS futuro / Deuda inicial
        plcr = compute_plcr(cfads_future, debt_initial, discount_rate)

        # Advertir sobre violaciones de LLCR
        if llcr < min_llcr and llcr != np.inf:
            warnings.warn(
                f"Año {year}: LLCR={llcr:.2f} < {min_llcr} (riesgo elevado)",
                UserWarning,
            )

        result = CoverageRatioResult(
            year=year,
            cfads=float(cfads_array[i]),
            debt_service=float(debt_service_array[i]),
            debt_outstanding=debt_outstanding,
            dscr=float(dscr_array[i]),
            llcr=llcr,
            plcr=plcr,
        )
        results.append(result)

    return CoverageRatioResults(
        results=results,
        covenant_min_dscr=min_dscr,
        covenant_min_llcr=min_llcr,
    )


__all__ = [
    'CoverageRatioResult',
    'CoverageRatioResults',
    'present_value',
    'compute_dscr',
    'compute_llcr',
    'compute_plcr',
    'extract_debt_service',
    'compute_remaining_debt',
    'calculate_coverage_ratios',
]
