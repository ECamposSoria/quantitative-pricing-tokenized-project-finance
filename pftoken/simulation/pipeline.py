"""Monte Carlo pipeline orchestrator (WP-07 T-031)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Mapping, Sequence

import numpy as np

from pftoken.models.calibration import CalibrationSet, load_placeholder_calibration
from pftoken.risk.credit_risk import RiskInputs, RiskMetricsCalculator
from pftoken.risk.var_cvar import TailRiskAnalyzer
from .breach_probability import BreachProbabilityAnalyzer
from .default_flags import DefaultDetector
from .merton_integration import compute_pathwise_pd_lgd, loss_paths_from_pd_lgd
from .monte_carlo import MonteCarloConfig, MonteCarloEngine, MonteCarloResult
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
    monte_carlo: MonteCarloResult
    pd_lgd_paths: Dict[str, Dict[str, np.ndarray]] | None = None
    loss_paths: np.ndarray | None = None
    tranche_names: Sequence[str] = field(default_factory=list)
    risk_metrics: Dict[str, object] | None = None
    ratio_summary: Dict[str, object] | None = None
    breach_curves: Dict[str, object] | None = None


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
    ) -> PipelineOutputs:
        mc_result = self.engine.run_simulation(self.config)

        pd_lgd_paths = None
        loss_paths = None
        tranche_names: list[str] = []
        risk_metrics: Dict[str, object] | None = None
        ratio_summary: Dict[str, object] | None = None
        breach_curves: Dict[str, object] | None = None

        # PD/LGD and loss generation if asset values are present.
        asset_values = mc_result.derived.get("asset_values")
        if asset_values is not None:
            pd_lgd = compute_pathwise_pd_lgd(
                asset_values,
                self.inputs.debt_by_tranche,
                discount_rate=self.inputs.discount_rate,
                horizon_years=self.inputs.horizon_years,
                calibration=self.calibration,
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

        return PipelineOutputs(
            monte_carlo=mc_result,
            pd_lgd_paths=pd_lgd_paths,
            loss_paths=loss_paths,
            tranche_names=tranche_names,
            risk_metrics=risk_metrics,
            ratio_summary=ratio_summary,
            breach_curves=breach_curves,
        )


__all__ = ["PipelineInputs", "PipelineOutputs", "MonteCarloPipeline"]
