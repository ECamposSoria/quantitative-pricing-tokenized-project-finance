"""
DSCR-Contingent Amortization Engine (WP-12)

A tokenization-native debt structure where principal payments automatically
adjust based on realized CFADS to maintain a minimum DSCR floor.

This is the core innovation for the tokenized vs traditional structure comparison.

Academic Contribution:
    First application of DSCR-contingent amortization to:
    1. Tokenized project finance
    2. Satellite constellation financing
    3. Smart contract-enforced debt service
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence

import numpy as np


# Tolerance for floating point comparisons
FLOAT_TOLERANCE = 1e-6


class AmortizationType(Enum):
    """Amortization structure type."""

    TRADITIONAL = "traditional"  # Fixed schedule
    CONTINGENT = "contingent"  # DSCR-responsive


@dataclass(frozen=True)
class ContingentAmortizationConfig:
    """
    Configuration for DSCR-contingent amortization.

    Parameters
    ----------
    dscr_floor : float
        Minimum DSCR maintained (hard floor). Default 1.25x.
    dscr_target : float
        Target DSCR for 100% scheduled principal payment. Default 1.50x.
    dscr_accelerate : float
        Threshold for catch-up payments on deferred principal. Default 2.00x.
    deferral_rate : float
        Interest rate on deferred principal (subordinated rate). Default 12%.
    max_deferral_pct : float
        Maximum cumulative deferral as percentage of original principal. Default 30%.
    balloon_year : int
        Year for balloon payment. Default 15.
    catch_up_enabled : bool
        Allow accelerated repayment of deferred principal in good years. Default True.
    balloon_cap_pct : Optional[float]
        Hard cap on total balloon (principal + accrued) as % of original principal. Default 50%.
    extension_years : int
        Optional extension years (documentation only; not modeled in engine).
    extension_rate_spread : float
        Additional spread applied during extension (documentation only; not modeled).
    """

    dscr_floor: float = 1.25
    dscr_target: float = 1.50
    dscr_accelerate: float = 2.00
    deferral_rate: float = 0.12
    max_deferral_pct: float = 0.30
    balloon_year: int = 15
    catch_up_enabled: bool = True
    balloon_cap_pct: Optional[float] = 0.50
    extension_years: int = 5
    extension_rate_spread: float = 0.02

    def validate(self) -> None:
        """Validate configuration parameters."""
        if not 1.0 <= self.dscr_floor <= self.dscr_target:
            raise ValueError("dscr_floor must be between 1.0 and dscr_target")
        if not 0 < self.max_deferral_pct <= 0.50:
            raise ValueError("max_deferral_pct must be between 0 and 50%")
        if self.deferral_rate < 0:
            raise ValueError("deferral_rate cannot be negative")
        if self.dscr_accelerate < self.dscr_target:
            raise ValueError("dscr_accelerate must be >= dscr_target")
        if self.balloon_cap_pct is not None and self.balloon_cap_pct <= 0:
            raise ValueError("balloon_cap_pct must be positive when provided")


@dataclass
class PeriodPaymentResult:
    """Result of payment calculation for a single period."""

    year: int
    cfads: float

    # Interest
    interest_due: float
    interest_paid: float

    # Principal
    principal_scheduled: float
    principal_paid: float
    principal_deferred: float
    principal_catch_up: float

    # Cumulative state
    cumulative_deferred: float
    deferred_interest_accrued: float
    remaining_balance: float

    # Metrics
    realized_dscr: float
    effective_dscr: float  # Including deferred as "paid"
    is_breach: bool
    breach_type: Optional[str]  # "hard_interest" or "soft_covenant"

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "cfads": self.cfads,
            "interest_paid": self.interest_paid,
            "principal_scheduled": self.principal_scheduled,
            "principal_paid": self.principal_paid,
            "principal_deferred": self.principal_deferred,
            "principal_catch_up": self.principal_catch_up,
            "cumulative_deferred": self.cumulative_deferred,
            "remaining_balance": self.remaining_balance,
            "realized_dscr": self.realized_dscr,
            "is_breach": self.is_breach,
            "breach_type": self.breach_type,
        }


@dataclass
class PathSimulationResult:
    """Result of simulating a full CFADS path."""

    period_results: List[PeriodPaymentResult]
    final_balloon: float
    total_interest_paid: float
    total_principal_paid: float
    total_deferred: float
    min_dscr: float
    breach_occurred: bool
    breach_year: Optional[int]
    breach_type: Optional[str]

    def to_dict(self) -> dict:
        return {
            "periods": [p.to_dict() for p in self.period_results],
            "final_balloon": self.final_balloon,
            "total_interest_paid": self.total_interest_paid,
            "total_principal_paid": self.total_principal_paid,
            "total_deferred": self.total_deferred,
            "min_dscr": self.min_dscr,
            "breach_occurred": self.breach_occurred,
            "breach_year": self.breach_year,
            "breach_type": self.breach_type,
        }


@dataclass
class StructureComparisonResult:
    """Comparison of traditional vs tokenized structures."""

    traditional: Dict
    tokenized: Dict
    delta: Dict

    def to_dict(self) -> dict:
        return {
            "traditional": self.traditional,
            "tokenized": self.tokenized,
            "delta": self.delta,
        }


class ContingentAmortizationEngine:
    """
    Engine for DSCR-contingent amortization.

    Key innovation: Principal payments automatically adjust to maintain
    DSCR floor, with deferrals accumulated for balloon payment.

    Smart Contract Logic:
        1. Interest is always paid first (mandatory)
        2. Principal = min(scheduled, available_after_dscr_floor)
        3. Shortfall deferred to balloon at subordinated rate
        4. In good years (DSCR > target), catch-up payments allowed

    Note:
        This class is NOT thread-safe. Create separate instances
        for parallel simulations.

    Parameters
    ----------
    principal : float
        Total debt principal in USD.
    interest_rate : float
        Annual interest rate (decimal, e.g., 0.055 for 5.5%).
    tenor : int
        Total loan tenor in years.
    grace_years : int
        Number of grace period years (interest-only).
    config : ContingentAmortizationConfig, optional
        Configuration for contingent amortization parameters.
    """

    def __init__(
        self,
        principal: float,
        interest_rate: float,
        tenor: int,
        grace_years: int,
        config: Optional[ContingentAmortizationConfig] = None,
    ):
        self.principal = principal
        self.interest_rate = interest_rate
        self.tenor = tenor
        self.grace_years = grace_years
        self.config = config or ContingentAmortizationConfig()
        self.config.validate()

        # Calculate scheduled amortization (baseline)
        amort_years = tenor - grace_years
        if amort_years <= 0:
            raise ValueError("Tenor must exceed grace period")
        self.scheduled_principal_per_year = principal / amort_years

        # State variables (reset for each simulation)
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset internal state for new simulation."""
        self._cumulative_deferred = 0.0
        self._deferred_interest_accrued = 0.0
        self._remaining_balance = self.principal

    def calculate_period_payment(
        self,
        year: int,
        cfads: float,
        covenant: float = 1.20,
    ) -> PeriodPaymentResult:
        """
        Calculate payment for a single period under contingent amortization.

        Parameters
        ----------
        year : int
            Current year (1-indexed)
        cfads : float
            Cash Flow Available for Debt Service (USD)
        covenant : float
            Contractual DSCR covenant (for breach determination)

        Returns
        -------
        PeriodPaymentResult
            Detailed payment breakdown and metrics
        """
        # Interest due on remaining balance
        interest_due = self._remaining_balance * self.interest_rate

        # Add accrued interest on deferred principal
        deferred_interest_due = self._cumulative_deferred * self.config.deferral_rate
        total_interest_due = interest_due + deferred_interest_due

        # Grace period: construction phase financing
        if year <= self.grace_years:
            # During construction phase (satellite deployment), equity covers any interest shortfall
            # This is standard construction financing - negative CFADS is expected and planned
            # Interest is ALWAYS paid (from project CFADS if available, else from equity/reserves)
            interest_paid = total_interest_due

            # Calculate DSCR for informational purposes only
            # Negative or low DSCR during construction is expected and does not constitute breach
            realized_dscr = cfads / total_interest_due if total_interest_due > FLOAT_TOLERANCE else float("inf")

            # NO BREACH during grace period - this is construction financing
            # Breach determination only applies post-COD (Commercial Operation Date)
            is_breach = False
            breach_type = None

            return PeriodPaymentResult(
                year=year,
                cfads=cfads,
                interest_due=total_interest_due,
                interest_paid=interest_paid,
                principal_scheduled=0,
                principal_paid=0,
                principal_deferred=0,
                principal_catch_up=0,
                cumulative_deferred=self._cumulative_deferred,
                deferred_interest_accrued=self._deferred_interest_accrued,
                remaining_balance=self._remaining_balance,
                realized_dscr=realized_dscr,
                effective_dscr=realized_dscr,
                is_breach=is_breach,
                breach_type=breach_type,
            )

        # Amortization period
        scheduled_principal = self.scheduled_principal_per_year

        # Step 1: Pay interest first (mandatory)
        if cfads < total_interest_due:
            # Hard breach: can't even pay interest
            interest_paid = cfads
            self._cumulative_deferred += scheduled_principal
            return PeriodPaymentResult(
                year=year,
                cfads=cfads,
                interest_due=total_interest_due,
                interest_paid=interest_paid,
                principal_scheduled=scheduled_principal,
                principal_paid=0,
                principal_deferred=scheduled_principal,
                principal_catch_up=0,
                cumulative_deferred=self._cumulative_deferred,
                deferred_interest_accrued=self._deferred_interest_accrued,
                remaining_balance=self._remaining_balance,
                realized_dscr=cfads / total_interest_due if total_interest_due > FLOAT_TOLERANCE else 0.0,
                effective_dscr=cfads / total_interest_due if total_interest_due > FLOAT_TOLERANCE else 0.0,
                is_breach=True,
                breach_type="hard_interest",
            )

        interest_paid = total_interest_due
        remaining_cfads = cfads - interest_paid

        # Step 2: Calculate available for principal (maintaining DSCR floor)
        # DSCR = CFADS / (Interest + Principal)
        # Floor: CFADS / (Interest + Principal) >= dscr_floor
        # => Principal <= CFADS / dscr_floor - Interest
        max_principal_for_floor = (cfads / self.config.dscr_floor) - interest_paid
        max_principal_for_floor = max(0, max_principal_for_floor)

        # Step 3: Determine actual principal payment
        # Can't pay more than: remaining CFADS, scheduled amount, or floor-constrained amount
        principal_base = min(remaining_cfads, scheduled_principal, max_principal_for_floor)
        principal_base = min(principal_base, self._remaining_balance)  # Can't exceed balance

        # Step 4: Check for catch-up opportunity
        principal_catch_up = 0.0
        if self.config.catch_up_enabled and self._cumulative_deferred > FLOAT_TOLERANCE:
            # Calculate DSCR if we pay base principal
            test_service = interest_paid + principal_base
            test_dscr = cfads / test_service if test_service > FLOAT_TOLERANCE else float("inf")

            # If DSCR > accelerate threshold, pay down deferred
            if test_dscr > self.config.dscr_accelerate:
                excess_cfads = remaining_cfads - principal_base
                # Use half of excess for catch-up (conservative)
                catch_up_available = excess_cfads * 0.5
                principal_catch_up = min(catch_up_available, self._cumulative_deferred)

        # Step 5: Calculate deferral
        principal_paid = principal_base + principal_catch_up
        principal_deferred = max(0, scheduled_principal - principal_base)

        # Step 6: Check max deferral constraint
        new_cumulative_deferred = self._cumulative_deferred + principal_deferred - principal_catch_up
        max_deferral = self.principal * self.config.max_deferral_pct

        forced_payment = 0.0
        if new_cumulative_deferred > max_deferral:
            # Must force payment to stay within limit
            forced_payment = new_cumulative_deferred - max_deferral
            principal_paid += forced_payment
            new_cumulative_deferred = max_deferral

        # Step 7: Update state
        self._cumulative_deferred = max(0, new_cumulative_deferred)
        self._deferred_interest_accrued = self._cumulative_deferred * self.config.deferral_rate
        self._remaining_balance -= (principal_base + principal_catch_up + forced_payment)
        self._remaining_balance = max(0, self._remaining_balance)

        # Step 8: Balloon cap projection (if configured)
        balloon_breach = False
        if self.config.balloon_cap_pct and year < self.tenor:
            remaining_years = self.tenor - year
            baseline_amort = max(0.0, self._remaining_balance - self.scheduled_principal_per_year * remaining_years)
            projected_balloon = baseline_amort + self._cumulative_deferred * (
                (1 + self.config.deferral_rate) ** remaining_years
            )
            max_balloon = self.principal * self.config.balloon_cap_pct
            if projected_balloon > max_balloon:
                excess_balloon = projected_balloon - max_balloon
                discount_factor = (1 + self.config.deferral_rate) ** remaining_years
                forced_balloon_payment = excess_balloon / discount_factor
                paydown = forced_balloon_payment
                principal_paid += paydown
                # First reduce deferred, then remaining balance
                reduce_deferred = min(paydown, self._cumulative_deferred)
                self._cumulative_deferred = max(0, self._cumulative_deferred - reduce_deferred)
                remainder = paydown - reduce_deferred
                if remainder > 0:
                    self._remaining_balance = max(0, self._remaining_balance - remainder)
                balloon_breach = True
                # If forced payment exceeds residual CFADS, flag breach
                available_for_extra = max(0.0, remaining_cfads - principal_base - principal_catch_up)
                if paydown - available_for_extra > FLOAT_TOLERANCE:
                    balloon_breach = True

        # Step 8: Calculate metrics
        total_service = interest_paid + principal_paid
        realized_dscr = cfads / total_service if total_service > FLOAT_TOLERANCE else float("inf")

        # Effective DSCR treats deferred as "paid" (for comparison)
        effective_service = interest_paid + scheduled_principal
        effective_dscr = cfads / effective_service if effective_service > FLOAT_TOLERANCE else float("inf")

        # Soft breach: DSCR below covenant but interest paid
        is_soft_breach = realized_dscr < covenant
        breach_type = "soft_covenant" if is_soft_breach else None
        if balloon_breach:
            is_soft_breach = True
            breach_type = "balloon_cap_binding"

        return PeriodPaymentResult(
            year=year,
            cfads=cfads,
            interest_due=total_interest_due,
            interest_paid=interest_paid,
            principal_scheduled=scheduled_principal,
            principal_paid=principal_paid,
            principal_deferred=principal_deferred,
            principal_catch_up=principal_catch_up,
            cumulative_deferred=self._cumulative_deferred,
            deferred_interest_accrued=self._deferred_interest_accrued,
            remaining_balance=self._remaining_balance,
            realized_dscr=realized_dscr,
            effective_dscr=effective_dscr,
            is_breach=is_soft_breach,
            breach_type=breach_type,
        )

    def simulate_path(
        self,
        cfads_path: Sequence[float],
        covenant: float = 1.20,
    ) -> PathSimulationResult:
        """
        Simulate full debt service path with contingent amortization.

        Parameters
        ----------
        cfads_path : Sequence[float]
            CFADS for each year in USD (length = tenor)
        covenant : float
            DSCR covenant for breach determination

        Returns
        -------
        PathSimulationResult
            Complete simulation results
        """
        self._reset_state()

        period_results: List[PeriodPaymentResult] = []
        total_interest = 0.0
        total_principal = 0.0
        dscr_values: List[float] = []
        breach_occurred = False
        breach_year: Optional[int] = None
        breach_type: Optional[str] = None

        for year, cfads in enumerate(cfads_path, start=1):
            result = self.calculate_period_payment(year, cfads, covenant)
            period_results.append(result)

            total_interest += result.interest_paid
            total_principal += result.principal_paid
            if year > self.grace_years and not np.isnan(result.realized_dscr):
                dscr_values.append(result.realized_dscr)

            # Track breaches (balloon cap overrides soft breaches)
            if result.is_breach:
                if not breach_occurred or result.breach_type == "balloon_cap_binding":
                    breach_occurred = True
                    breach_year = year
                    breach_type = result.breach_type

        min_dscr = min(dscr_values) if dscr_values else self.config.dscr_floor

        # Final balloon = remaining balance + deferred with interest
        final_balloon = self._remaining_balance + self._cumulative_deferred * (
            1 + self.config.deferral_rate
        )

        if self.config.balloon_cap_pct and final_balloon > self.principal * self.config.balloon_cap_pct:
            if breach_type != "hard_interest":
                breach_occurred = True
                breach_year = self.tenor if breach_year is None else breach_year
                breach_type = "balloon_cap_binding"
            final_balloon = min(final_balloon, self.principal * self.config.balloon_cap_pct)

        return PathSimulationResult(
            period_results=period_results,
            final_balloon=final_balloon,
            total_interest_paid=total_interest,
            total_principal_paid=total_principal,
            total_deferred=self._cumulative_deferred,
            min_dscr=min_dscr,
            breach_occurred=breach_occurred,
            breach_year=breach_year,
            breach_type=breach_type,
        )


class TraditionalAmortizationEngine:
    """
    Traditional fixed-schedule amortization engine.

    Used as baseline comparison for tokenized contingent structure.

    Note:
        This class is NOT thread-safe. Create separate instances
        for parallel simulations.

    Parameters
    ----------
    principal : float
        Total debt principal in USD.
    interest_rate : float
        Annual interest rate (decimal).
    tenor : int
        Total loan tenor in years.
    grace_years : int
        Number of grace period years.
    """

    def __init__(
        self,
        principal: float,
        interest_rate: float,
        tenor: int,
        grace_years: int,
    ):
        self.principal = principal
        self.interest_rate = interest_rate
        self.tenor = tenor
        self.grace_years = grace_years

        amort_years = tenor - grace_years
        if amort_years <= 0:
            raise ValueError("Tenor must exceed grace period")
        self.scheduled_principal_per_year = principal / amort_years

        self._remaining_balance = principal

    def _reset_state(self) -> None:
        self._remaining_balance = self.principal

    def simulate_path(
        self,
        cfads_path: Sequence[float],
        covenant: float = 1.20,
    ) -> PathSimulationResult:
        """Simulate with fixed amortization schedule."""
        self._reset_state()

        period_results: List[PeriodPaymentResult] = []
        total_interest = 0.0
        total_principal = 0.0
        dscr_values: List[float] = []
        breach_occurred = False
        breach_year: Optional[int] = None
        breach_type: Optional[str] = None

        for year, cfads in enumerate(cfads_path, start=1):
            interest_due = self._remaining_balance * self.interest_rate

            if year <= self.grace_years:
                principal_due = 0
            else:
                principal_due = min(self.scheduled_principal_per_year, self._remaining_balance)

            total_service = interest_due + principal_due
            realized_dscr = cfads / total_service if total_service > FLOAT_TOLERANCE else float("inf")

            # Check breach (only during amortization period, not during construction)
            # During grace period (construction phase), equity covers interest shortfalls
            # Breach determination only applies post-COD (Year 5+)
            is_breach = False
            current_breach_type: Optional[str] = None

            if year > self.grace_years:
                # Only check breaches during amortization period
                is_breach = realized_dscr < covenant
                if cfads < interest_due:
                    current_breach_type = "hard_interest"
                    is_breach = True
                elif is_breach:
                    current_breach_type = "soft_covenant"

                if is_breach and not breach_occurred:
                    breach_occurred = True
                    breach_year = year
                    breach_type = current_breach_type

            # In traditional, payments are fixed regardless of CFADS
            # (breach is recorded but payments still "due")
            interest_paid = interest_due
            principal_paid = principal_due

            self._remaining_balance -= principal_paid
            self._remaining_balance = max(0, self._remaining_balance)

            total_interest += interest_paid
            total_principal += principal_paid
            if year > self.grace_years and not np.isnan(realized_dscr):
                dscr_values.append(realized_dscr)

            period_results.append(
                PeriodPaymentResult(
                    year=year,
                    cfads=cfads,
                    interest_due=interest_due,
                    interest_paid=interest_paid,
                    principal_scheduled=principal_due,
                    principal_paid=principal_paid,
                    principal_deferred=0,
                    principal_catch_up=0,
                    cumulative_deferred=0,
                    deferred_interest_accrued=0,
                    remaining_balance=self._remaining_balance,
                    realized_dscr=realized_dscr,
                    effective_dscr=realized_dscr,
                    is_breach=is_breach,
                    breach_type=current_breach_type,
                )
            )

        min_dscr = min(dscr_values) if dscr_values else covenant

        return PathSimulationResult(
            period_results=period_results,
            final_balloon=self._remaining_balance,
            total_interest_paid=total_interest,
            total_principal_paid=total_principal,
            total_deferred=0,
            min_dscr=min_dscr,
            breach_occurred=breach_occurred,
            breach_year=breach_year,
            breach_type=breach_type,
        )


class DualStructureComparator:
    """
    Compares traditional vs tokenized (contingent) amortization structures.

    Core deliverable for thesis: quantifies structural flexibility advantage.

    Parameters
    ----------
    principal : float
        Total debt principal in USD.
    interest_rate : float
        Weighted average interest rate.
    tenor : int
        Loan tenor in years.
    grace_years : int
        Grace period in years.
    contingent_config : ContingentAmortizationConfig, optional
        Configuration for the tokenized structure.
    """

    def __init__(
        self,
        principal: float,
        interest_rate: float,
        tenor: int,
        grace_years: int,
        contingent_config: Optional[ContingentAmortizationConfig] = None,
    ):
        self.traditional = TraditionalAmortizationEngine(
            principal, interest_rate, tenor, grace_years
        )
        self.tokenized = ContingentAmortizationEngine(
            principal, interest_rate, tenor, grace_years, contingent_config
        )

        self.principal = principal
        self.tenor = tenor

    def compare_single_path(
        self,
        cfads_path: Sequence[float],
        covenant: float = 1.20,
    ) -> StructureComparisonResult:
        """Compare both structures on a single CFADS path."""

        trad_result = self.traditional.simulate_path(cfads_path, covenant)
        token_result = self.tokenized.simulate_path(cfads_path, covenant)

        return StructureComparisonResult(
            traditional={
                "min_dscr": trad_result.min_dscr,
                "breach_occurred": trad_result.breach_occurred,
                "breach_year": trad_result.breach_year,
                "final_balloon": trad_result.final_balloon,
                "total_interest": trad_result.total_interest_paid,
            },
            tokenized={
                "min_dscr": token_result.min_dscr,
                "breach_occurred": token_result.breach_occurred,
                "breach_year": token_result.breach_year,
                "final_balloon": token_result.final_balloon,
                "total_interest": token_result.total_interest_paid,
                "total_deferred": token_result.total_deferred,
            },
            delta={
                "dscr_improvement": token_result.min_dscr - trad_result.min_dscr,
                "breach_avoided": trad_result.breach_occurred and not token_result.breach_occurred,
                "additional_balloon": token_result.final_balloon - trad_result.final_balloon,
                "additional_interest": token_result.total_interest_paid - trad_result.total_interest_paid,
            },
        )

    def run_monte_carlo_comparison(
        self,
        cfads_scenarios: np.ndarray,  # Shape: (n_simulations, n_years)
        covenant: float = 1.20,
    ) -> Dict:
        """
        Run Monte Carlo comparison of both structures.

        Returns comprehensive statistics for thesis presentation.

        Parameters
        ----------
        cfads_scenarios : np.ndarray
            CFADS scenarios with shape (n_simulations, n_years) in USD.
        covenant : float
            DSCR covenant threshold.

        Returns
        -------
        Dict
            Comprehensive comparison statistics.
        """
        n_sims, n_years = cfads_scenarios.shape

        # Storage
        trad_breaches: List[bool] = []
        token_breaches: List[bool] = []
        trad_min_dscr: List[float] = []
        token_min_dscr: List[float] = []
        trad_breach_years: List[int] = []
        token_breach_years: List[int] = []
        breaches_avoided = 0
        additional_balloons: List[float] = []

        for sim_idx in range(n_sims):
            cfads_path = cfads_scenarios[sim_idx, :].tolist()
            comparison = self.compare_single_path(cfads_path, covenant)

            trad_breaches.append(comparison.traditional["breach_occurred"])
            token_breaches.append(comparison.tokenized["breach_occurred"])
            trad_min_dscr.append(comparison.traditional["min_dscr"])
            token_min_dscr.append(comparison.tokenized["min_dscr"])

            if comparison.traditional["breach_year"]:
                trad_breach_years.append(comparison.traditional["breach_year"])
            if comparison.tokenized["breach_year"]:
                token_breach_years.append(comparison.tokenized["breach_year"])

            if comparison.delta["breach_avoided"]:
                breaches_avoided += 1

            additional_balloons.append(comparison.delta["additional_balloon"])

        # Calculate statistics
        trad_breach_prob = float(np.mean(trad_breaches))
        token_breach_prob = float(np.mean(token_breaches))

        # Guard against division by zero
        breach_reduction_pct = (
            (trad_breach_prob - token_breach_prob) / max(trad_breach_prob, FLOAT_TOLERANCE) * 100
        )

        return {
            "simulations": n_sims,
            "covenant": covenant,
            "traditional": {
                "breach_probability": trad_breach_prob,
                "breach_count": int(sum(trad_breaches)),
                "min_dscr_mean": float(np.mean(trad_min_dscr)),
                "min_dscr_std": float(np.std(trad_min_dscr)),
                "min_dscr_p5": float(np.percentile(trad_min_dscr, 5)),
                "min_dscr_p25": float(np.percentile(trad_min_dscr, 25)),
                "min_dscr_p50": float(np.percentile(trad_min_dscr, 50)),
                "min_dscr_p75": float(np.percentile(trad_min_dscr, 75)),
                "min_dscr_p95": float(np.percentile(trad_min_dscr, 95)),
                "avg_breach_year": float(np.mean(trad_breach_years)) if trad_breach_years else None,
            },
            "tokenized": {
                "breach_probability": token_breach_prob,
                "breach_count": int(sum(token_breaches)),
                "min_dscr_mean": float(np.mean(token_min_dscr)),
                "min_dscr_std": float(np.std(token_min_dscr)),
                "min_dscr_p5": float(np.percentile(token_min_dscr, 5)),
                "min_dscr_p25": float(np.percentile(token_min_dscr, 25)),
                "min_dscr_p50": float(np.percentile(token_min_dscr, 50)),
                "min_dscr_p75": float(np.percentile(token_min_dscr, 75)),
                "min_dscr_p95": float(np.percentile(token_min_dscr, 95)),
                "avg_breach_year": float(np.mean(token_breach_years)) if token_breach_years else None,
                "avg_additional_balloon": float(np.mean(additional_balloons)),
                "max_additional_balloon": float(np.max(additional_balloons)),
            },
            "comparison": {
                "breach_probability_reduction": float(trad_breach_prob - token_breach_prob),
                "breach_probability_reduction_pct": breach_reduction_pct,
                "breaches_avoided_count": breaches_avoided,
                "breaches_avoided_pct": float(breaches_avoided / n_sims * 100),
                "dscr_p25_improvement": float(
                    np.percentile(token_min_dscr, 25) - np.percentile(trad_min_dscr, 25)
                ),
            },
            "thesis_summary": {
                "traditional_bankable": trad_breach_prob < 0.20,
                "tokenized_bankable": token_breach_prob < 0.20,
                "tokenization_enables_bankability": (
                    not trad_breach_prob < 0.20 and token_breach_prob < 0.20
                ),
                "key_finding": self._generate_key_finding(trad_breach_prob, token_breach_prob),
            },
        }

    def _generate_key_finding(self, trad_prob: float, token_prob: float) -> str:
        """Generate thesis-ready key finding statement."""
        reduction = (
            (trad_prob - token_prob) / max(trad_prob, FLOAT_TOLERANCE) * 100
        )

        if trad_prob >= 0.20 and token_prob < 0.20:
            return (
                f"DSCR-contingent amortization reduces breach probability from "
                f"{trad_prob:.1%} to {token_prob:.1%} ({reduction:.0f}% reduction), "
                f"transforming the project from non-bankable to bankable status."
            )
        elif token_prob < trad_prob:
            return (
                f"Tokenized structure reduces breach probability by {reduction:.0f}% "
                f"({trad_prob:.1%} -> {token_prob:.1%})."
            )
        else:
            return "No significant improvement from contingent amortization."


__all__ = [
    "AmortizationType",
    "ContingentAmortizationConfig",
    "ContingentAmortizationEngine",
    "DualStructureComparator",
    "PathSimulationResult",
    "PeriodPaymentResult",
    "StructureComparisonResult",
    "TraditionalAmortizationEngine",
]
