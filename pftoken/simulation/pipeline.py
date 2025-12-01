"""Monte Carlo pipeline orchestrator (WP-07 T-031)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Mapping, Sequence, Optional

import numpy as np

from pftoken.models.calibration import CalibrationSet, load_placeholder_calibration
from pftoken.risk.credit_risk import RiskInputs, RiskMetricsCalculator
from pftoken.risk.var_cvar import TailRiskAnalyzer
from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import DebtStructure
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from pftoken.pricing_mc import (
        StochasticPricing,
        StochasticPricingInputs,
        DurationConvexityAnalyzer,
        InterestRateSensitivity,
        SpreadCalibrator,
    )
from .breach_probability import BreachProbabilityAnalyzer
from .default_flags import DefaultDetector
from .merton_integration import compute_pathwise_pd_lgd, loss_paths_from_pd_lgd
from .monte_carlo import MonteCarloConfig, MonteCarloEngine, MonteCarloResult
from .path_dependent import PathDependentConfig
from .regime_switching import RegimeConfig
from .ratio_simulation import RatioDistributions


PathCallback = Callable[[Dict[str, np.ndarray]], Dict[str, np.ndarray]]


@dataclass(frozen=True)
class PipelineInputs:
    debt_by_tranche: Mapping[str, float]
    discount_rate: float
    horizon_years: float
    tranche_ead: Mapping[str, float] | None = None
    dscr_threshold: float = 1.0
    llcr_threshold: float | None = None


@dataclass
class PipelineOutputs:
    """Outputs from MonteCarloPipeline including optional stochastic pricing results."""

    monte_carlo: MonteCarloResult
    pd_lgd_paths: Dict[str, Dict[str, np.ndarray]] | None = None
    loss_paths: np.ndarray | None = None
    tranche_names: Sequence[str] = field(default_factory=list)
    risk_metrics: Dict[str, object] | None = None
    ratio_summary: Dict[str, object] | None = None
    breach_curves: Dict[str, object] | None = None
    pricing_mc: Dict[str, object] | None = None


class MonteCarloPipeline:
    """End-to-end orchestrator for MC → PD/LGD → losses → ratios."""

    def __init__(
        self,
        config: MonteCarloConfig,
        inputs: PipelineInputs,
        *,
        calibration: CalibrationSet | None = None,
        path_callback: PathCallback | None = None,
    ):
        self.config = config
        self.inputs = inputs
        self.calibration = calibration or load_placeholder_calibration()
        self.engine = MonteCarloEngine(self.calibration, path_callback=path_callback)

    def run_complete_analysis(
        self,
        *,
        alpha_levels: Sequence[float] = (0.95, 0.99),
        analyze_ratios: bool = True,
        zero_curve: ZeroCurve | None = None,
        debt_structure: DebtStructure | None = None,
        tranche_cashflows: Mapping[str, Sequence[TrancheCashFlow]] | None = None,
        spread_calibrator: SpreadCalibrator | None = None,
        include_tranche_cashflows: bool = False,
    ) -> PipelineOutputs:
        mc_result = self.engine.run_simulation(self.config)
        if include_tranche_cashflows and "tranche_cashflows" not in (mc_result.derived or {}):
            warnings.warn(
                "include_tranche_cashflows=True but path_callback did not emit tranche_cashflows; "
                "build the financial path callback with include_tranche_cashflows=True."
            )

        pd_lgd_paths = None
        loss_paths = None
        tranche_names: list[str] = []
        risk_metrics: Dict[str, object] | None = None
        ratio_summary: Dict[str, object] | None = None
        breach_curves: Dict[str, object] | None = None
        pricing_mc: Dict[str, object] | None = None

        # PD/LGD and loss generation if asset values are present.
        asset_values = mc_result.derived.get("asset_values")
        if asset_values is not None:
            path_cfg = PathDependentConfig.from_dict(getattr(self.calibration, "path_dependent", None))
            regime_cfg = RegimeConfig.from_dict(getattr(self.calibration, "regime_switching", None))
            asset_value_paths = mc_result.derived.get("asset_value_paths")
            first_passage_default = mc_result.derived.get("first_passage_default")
            regime_recovery_adj = mc_result.derived.get("regime_recovery_adj")
            pd_lgd = compute_pathwise_pd_lgd(
                asset_values,
                self.inputs.debt_by_tranche,
                discount_rate=self.inputs.discount_rate,
                horizon_years=self.inputs.horizon_years,
                calibration=self.calibration,
                path_config=path_cfg,
                regime_config=regime_cfg,
                asset_paths=asset_value_paths,
                default_flags=first_passage_default,
                regime_recovery_adj=regime_recovery_adj,
            )
            pd_lgd_paths = {
                name: {
                    "pd": metrics.pd,
                    "lgd": metrics.lgd,
                    "distance_to_default": metrics.distance_to_default,
                }
                for name, metrics in pd_lgd.items()
            }
            pd_paths = {name: metrics["pd"] for name, metrics in pd_lgd_paths.items()}
            lgd_paths = {name: metrics["lgd"] for name, metrics in pd_lgd_paths.items()}
            tranche_names, loss_paths = loss_paths_from_pd_lgd(
                pd_paths, lgd_paths, self.inputs.tranche_ead, seed=self.config.seed
            )

            calculator = RiskMetricsCalculator(tranche_names)
            tail = TailRiskAnalyzer()
            risk_inputs = RiskInputs(
                pd={name: float(np.mean(metrics["pd"])) for name, metrics in pd_lgd_paths.items()},
                lgd={name: float(np.mean(metrics["lgd"])) for name, metrics in pd_lgd_paths.items()},
                ead=self.inputs.tranche_ead
                or {name: 1.0 for name in tranche_names},
                loss_scenarios=loss_paths,
            )
            risk_metrics = {
                "tranche": calculator.tranche_results(risk_inputs, alpha_levels=alpha_levels),
                "portfolio_var": tail.empirical_var(loss_paths.sum(axis=1), alpha_levels),
                "portfolio_cvar": tail.empirical_cvar(loss_paths.sum(axis=1), alpha_levels),
            }

        # Ratio summaries for fan charts.
        dscr_paths = mc_result.derived.get("dscr_paths")
        if analyze_ratios and dscr_paths is not None:
            ratio_calc = RatioDistributions()
            ratios = ratio_calc.summarize(
                dscr_paths,
                threshold=self.inputs.dscr_threshold,
            )
            ratio_summary = {
                "percentiles": ratios.percentiles,
                "breach_rate": ratios.breach_rate,
                "headroom": ratios.headroom,
            }
            detector = DefaultDetector(
                dscr_threshold=self.inputs.dscr_threshold,
                llcr_threshold=self.inputs.llcr_threshold,
            )
            flags = detector.classify(dscr_paths)
            breach_analyzer = BreachProbabilityAnalyzer()
            curves = breach_analyzer.compute(dscr_paths < self.inputs.dscr_threshold)
            breach_curves = {"curves": curves, "flags": flags}

        # Stochastic pricing (WP-08) using deterministic cashflow fallback.
        if zero_curve is not None and debt_structure is not None:
            partial_outputs = PipelineOutputs(
                monte_carlo=mc_result,
                pd_lgd_paths=pd_lgd_paths,
                loss_paths=loss_paths,
                tranche_names=tranche_names,
                risk_metrics=risk_metrics,
                ratio_summary=ratio_summary,
                breach_curves=breach_curves,
                pricing_mc=None,
            )
            from pftoken.pricing_mc import (
                StochasticPricing,
                StochasticPricingInputs,
                DurationConvexityAnalyzer,
                InterestRateSensitivity,
            )
            pricing_inputs = StochasticPricingInputs(
                mc_outputs=partial_outputs,
                base_curve=zero_curve,
                debt_structure=debt_structure,
                tranche_cashflows=tranche_cashflows,
            )
            pricing_engine = StochasticPricing(pricing_inputs, spread_calibrator=spread_calibrator)
            price_result = pricing_engine.price()

            duration_results: Dict[str, object] = {}
            if tranche_cashflows:
                duration_analyzer = DurationConvexityAnalyzer(zero_curve)
                for tranche in debt_structure.tranches:
                    if tranche_cashflows.get(tranche.name):
                        duration_results[tranche.name] = duration_analyzer.analyze(
                            tranche=tranche,
                            cashflows=tranche_cashflows[tranche.name],
                        )
            sensitivity = InterestRateSensitivity(pricing_inputs, spread_calibrator=spread_calibrator)
            sensitivity_results = sensitivity.run()

            pricing_mc = {
                "prices": price_result.to_dict(),
                "duration_convexity": {k: v.to_dict() for k, v in duration_results.items()},
                "rate_sensitivity": sensitivity_results,
                "metadata": {
                    "simulations": mc_result.metadata.get("simulations"),
                    "curve_currency": getattr(zero_curve, "currency", None),
                },
            }

        return PipelineOutputs(
            monte_carlo=mc_result,
            pd_lgd_paths=pd_lgd_paths,
            loss_paths=loss_paths,
            tranche_names=tranche_names,
            risk_metrics=risk_metrics,
            ratio_summary=ratio_summary,
            breach_curves=breach_curves,
            pricing_mc=pricing_mc,
        )


__all__ = ["PipelineInputs", "PipelineOutputs", "MonteCarloPipeline"]
