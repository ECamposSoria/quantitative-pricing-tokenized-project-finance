"""High-level pipeline orchestrating CFADS → waterfall → ratios."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
import warnings

import pandas as pd
import numpy as np

from pftoken.config.defaults import DEFAULT_RESERVE_POLICY
from pftoken.models import CFADSCalculator, ProjectParameters, compute_dscr_by_phase
from pftoken.risk import (
    AggregateInputs,
    AggregateRiskCalculator,
    EfficientFrontierAnalysis,
    RiskConcentrationAnalysis,
    RiskInputs,
    RiskMetricsCalculator,
)
from pftoken.risk.utils import ensure_2d_losses
from pftoken.waterfall import (
    ComparisonResult,
    CovenantEngine,
    DebtStructure,
    StructureComparator,
    WaterfallOrchestrator,
    WaterfallResult,
)


class FinancialPipeline:
    """End-to-end deterministic pipeline for the WP-02/03 stack."""

    def __init__(
        self,
        data_dir: Optional[str | Path] = None,
        params: Optional[ProjectParameters] = None,
    ):
        if params is None:
            if data_dir is None:
                raise ValueError("Either data_dir or params must be provided.")
            params = ProjectParameters.from_directory(data_dir)
        self.params = params
        self.debt_structure = DebtStructure.from_tranche_params(params.tranches)
        self.cfads_calculator = CFADSCalculator.from_project_parameters(params)
        self.covenant_engine = CovenantEngine()
        self.comparator = StructureComparator()

    def run(
        self,
        *,
        include_risk: bool = False,
        risk_inputs: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        cfads_vector = self.cfads_calculator.calculate_cfads_vector()
        dscr_results = compute_dscr_by_phase(
            cfads_vector,
            self.params.debt_schedule,
            grace_years=self.params.project.grace_period_years,
            tenor_years=self.params.project.tenor_years,
        )

        orchestrator = WaterfallOrchestrator(
            cfads_vector=cfads_vector,
            debt_structure=self.debt_structure,
            debt_schedule=self.params.debt_schedule,
            rcapex_schedule=self.params.rcapex_schedule,
            grace_period_years=self.params.project.grace_period_years,
            tenor_years=self.params.project.tenor_years,
            reserve_policy=DEFAULT_RESERVE_POLICY,
            covenant_engine=self.covenant_engine,
        )
        full_result = orchestrator.run()
        waterfall_results: Dict[int, WaterfallResult] = {
            period.year: period for period in full_result.periods
        }

        last_period = full_result.periods[-1]
        comparison = self.comparator.compare(
            self.debt_structure,
            dsra_target=last_period.dsra_target,
            dsra_balance=last_period.dsra_balance,
            mra_target=last_period.mra_target,
            mra_balance=last_period.mra_balance,
        )

        risk_metrics = None
        if include_risk:
            risk_metrics = self._compute_risk_metrics(risk_inputs or {})

        return {
            "cfads": cfads_vector,
            "dscr": dscr_results,
            "waterfall": waterfall_results,
            "breaches": self.covenant_engine.breach_history,
            "reserves": {
                "dsra_balance": full_result.dsra_series[-1],
                "mra_balance": full_result.mra_series[-1],
                "equity_irr": full_result.equity_irr,
            },
            "structure_comparison": comparison,
            "waterfall_equity_cashflows": full_result.equity_cashflows,
            "risk_metrics": risk_metrics,
        }

    # ---------------------------------------------------------------- private
    def _compute_risk_metrics(self, risk_inputs: Dict[str, object]) -> Dict[str, object]:
        """Guarded risk computation to avoid breaking existing consumers."""

        tranche_names = [tranche.name for tranche in self.debt_structure.tranches]
        pd_map = risk_inputs.get("pd")
        lgd_map = risk_inputs.get("lgd")
        if pd_map is None or lgd_map is None:
            return {"note": "pd/lgd not provided, risk metrics skipped"}

        ead_map = risk_inputs.get("ead") or {t.name: t.principal for t in self.debt_structure.tranches}
        loss_scenarios = risk_inputs.get("loss_scenarios")
        simulations = int(risk_inputs.get("simulations", 5000))
        seed = risk_inputs.get("seed")
        alpha_levels = risk_inputs.get("alpha_levels", (0.95, 0.99))

        inputs = RiskInputs(
            pd=pd_map,
            lgd=lgd_map,
            ead=ead_map,
            loss_scenarios=loss_scenarios,
            simulations=simulations,
            seed=seed,
        )
        metrics = RiskMetricsCalculator(tranche_names).tranche_results(inputs, alpha_levels=alpha_levels)
        risk_output: Dict[str, object] = {"tranches": [result.to_dict() for result in metrics]}

        correlation = risk_inputs.get("correlation")
        lgd_provider = risk_inputs.get("lgd_provider")
        agg_losses = None
        if correlation is not None:
            agg_calc = AggregateRiskCalculator(tranche_names)
            agg_inputs = AggregateInputs(
                pd=pd_map,
                lgd=lgd_map,
                ead=ead_map,
                correlation=np.asarray(correlation, dtype=float),
                simulations=simulations,
                seed=seed,
                lgd_provider=lgd_provider,
            )
            agg_losses = agg_calc.simulate_losses(agg_inputs) if loss_scenarios is None else ensure_2d_losses(
                loss_scenarios, expected_cols=len(tranche_names)
            )
            risk_output["contributions"] = agg_calc.contribution_table(agg_losses)
            risk_output["aggregate"] = agg_calc.summarize_portfolio(agg_losses, alpha_levels=alpha_levels).to_dict()
            risk_output["concentration"] = RiskConcentrationAnalysis(tranche_names).losses_hhi(agg_losses)
            frontier_result = self._maybe_frontier(
                tranche_names=tranche_names,
                risk_inputs=risk_inputs,
                agg_losses=agg_losses,
                alpha_levels=alpha_levels,
                seed=seed,
            )
            risk_output.update(frontier_result)
            # Structure comparison (traditional vs tokenized)
            if frontier_result.get("frontier"):
                risk_output.update(
                    self._structure_comparison(
                        tranche_names=tranche_names,
                        risk_inputs=risk_inputs,
                        frontier_result=frontier_result.get("frontier", {}),
                    )
                )
        elif loss_scenarios is not None:
            agg_losses = ensure_2d_losses(loss_scenarios, expected_cols=len(tranche_names))
            risk_output["contributions"] = AggregateRiskCalculator(tranche_names).contribution_table(agg_losses)
            risk_output["concentration"] = RiskConcentrationAnalysis(tranche_names).losses_hhi(agg_losses)
            frontier_result = self._maybe_frontier(
                tranche_names=tranche_names,
                risk_inputs=risk_inputs,
                agg_losses=agg_losses,
                alpha_levels=alpha_levels,
                seed=seed,
            )
            risk_output.update(frontier_result)
            # Structure comparison (traditional vs tokenized)
            if frontier_result.get("frontier"):
                risk_output.update(
                    self._structure_comparison(
                        tranche_names=tranche_names,
                        risk_inputs=risk_inputs,
                        frontier_result=frontier_result.get("frontier", {}),
                    )
                )

        return risk_output

    def _maybe_frontier(
        self,
        *,
        tranche_names: list[str],
        risk_inputs: Dict[str, object],
        agg_losses: np.ndarray,
        alpha_levels,
        seed,
    ) -> Dict[str, object]:
        """Optional efficient frontier calculation."""

        if not risk_inputs.get("run_frontier"):
            return {}
        if agg_losses is None:
            return {"frontier": {"note": "run_frontier enabled but no loss scenarios available"}}

        frontier_alpha = float(risk_inputs.get("frontier_alpha", min(alpha_levels) if alpha_levels else 0.95))
        frontier_samples = int(risk_inputs.get("frontier_samples", 300))
        risk_metric = risk_inputs.get("frontier_risk_metric", "cvar")
        wacd_calc = risk_inputs.get("wacd_calc")

        tranche_returns = self._build_tranche_returns(tranche_names, risk_inputs)
        frontier = EfficientFrontierAnalysis(tranche_names)
        weights = frontier.sample_weights(num=frontier_samples, seed=seed)
        points = frontier.evaluate(
            weights=weights,
            tranche_returns=tranche_returns,
            tranche_loss_scenarios=agg_losses,
            wacd_calc=wacd_calc,
            risk_metric=risk_metric,
            alpha=frontier_alpha,
        )

        efficient = sorted([p.to_dict() for p in points if p.is_efficient], key=lambda d: d["risk"])
        efficient_3d = []
        if any(p.wacd_after_tax is not None for p in points):
            efficient_3d = [
                p.to_dict() for p in frontier.mark_efficient_3d(points) if p.is_efficient
            ]
            efficient_3d = sorted(efficient_3d, key=lambda d: d["risk"])
        if not points:
            return {"frontier": {"note": "no frontier points generated"}}
        best_by_return = max(points, key=lambda p: p.expected_return).to_dict()
        best_by_risk = min(points, key=lambda p: p.risk).to_dict()
        best_by_wacd = None
        if any(p.wacd_after_tax is not None for p in points):
            best_by_wacd = min(
                [p for p in points if p.wacd_after_tax is not None],
                key=lambda p: p.wacd_after_tax,
                default=None,
            )
            best_by_wacd = best_by_wacd.to_dict() if best_by_wacd else None
        current_weights = self._current_weights()
        current_eval = None
        if current_weights:
            curr_vec = np.array([current_weights[name] for name in tranche_names], dtype=float)
            curr_point = frontier.evaluate(
                weights=curr_vec,
                tranche_returns=tranche_returns,
                tranche_loss_scenarios=agg_losses,
                wacd_calc=wacd_calc,
                risk_metric=risk_metric,
                alpha=frontier_alpha,
            )[0]
            dominated = any(
                (pt.risk <= curr_point.risk and pt.expected_return >= curr_point.expected_return)
                and (pt.risk < curr_point.risk or pt.expected_return > curr_point.expected_return)
                for pt in points
            )
            current_eval = curr_point.to_dict()
            current_eval["is_efficient"] = not dominated
        return {
            "frontier": {
                "efficient": efficient,
                "efficient_3d": efficient_3d,
                "frontier_points": [p.to_dict() for p in points],  # All sampled points
                "best_by_return": best_by_return,
                "best_by_risk": best_by_risk,
                "best_by_wacd": best_by_wacd,
                "current_weights": current_weights,
                "current_structure_evaluation": current_eval,
            }
        }

    def _build_tranche_returns(self, tranche_names: list[str], risk_inputs: Dict[str, object]) -> Dict[str, float]:
        """Validate/construct tranche returns with optional coupon fallback."""

        provided = risk_inputs.get("tranche_returns")
        fallback_enabled = bool(risk_inputs.get("tranche_return_fallback", True))
        name_lookup = {name.lower(): name for name in tranche_names}

        if provided is None:
            if not fallback_enabled:
                raise ValueError("tranche_returns missing and fallback disabled.")
            warnings.warn("tranche_returns not provided; falling back to coupon_rate.", RuntimeWarning)
            return {t.name: float(t.coupon_rate) for t in self.debt_structure.tranches}

        normalized = {k.lower(): float(v) for k, v in provided.items()}
        missing = [n for n in tranche_names if n.lower() not in normalized]
        extras = [k for k in provided.keys() if k.lower() not in name_lookup]

        if extras:
            warnings.warn(f"Ignoring tranche_returns entries not in structure: {extras}", RuntimeWarning)
        if missing and not fallback_enabled:
            raise ValueError(f"Missing tranche_returns for: {missing}")
        if missing and fallback_enabled:
            warnings.warn(f"Falling back to coupon_rate for missing tranches: {missing}", RuntimeWarning)
            for t in self.debt_structure.tranches:
                key = t.name.lower()
                if key in normalized:
                    continue
                normalized[key] = float(t.coupon_rate)

        return {name: normalized[name.lower()] for name in tranche_names}

    def _current_weights(self) -> Dict[str, float]:
        total = self.debt_structure.total_principal
        if total <= 0:
            return {}
        return {t.name: float(t.principal / total) for t in self.debt_structure.tranches}

    def _check_constraint_violation(
        self,
        target_weights: Dict[str, float],
        constraints: Dict[str, float],
    ) -> Dict[str, object]:
        """Check if target structure violates traditional constraints."""
        violations = []

        min_senior = constraints.get("min_senior_pct", 0)
        max_sub = constraints.get("max_sub_pct", 1)

        # Sum weights by tranche type (case-insensitive)
        senior_weight = sum(v for k, v in target_weights.items() if "senior" in k.lower())
        sub_weight = sum(v for k, v in target_weights.items() if "sub" in k.lower())

        if senior_weight < min_senior:
            violations.append(f"senior {senior_weight:.1%} < min {min_senior:.1%}")
        if sub_weight > max_sub:
            violations.append(f"subordinated {sub_weight:.1%} > max {max_sub:.1%}")

        return {
            "violates_constraints": len(violations) > 0,
            "violations": violations,
        }

    def _structure_comparison(
        self,
        *,
        tranche_names: list[str],
        risk_inputs: Dict[str, object],
        frontier_result: Dict[str, object],
    ) -> Dict[str, object]:
        """Compare traditional vs tokenized structure outcomes."""

        if not risk_inputs.get("compare_structures"):
            return {}

        current_eval = frontier_result.get("current_structure_evaluation", {})
        if not current_eval:
            return {"structure_comparison": {"note": "No current structure to compare"}}

        # Current structure metrics
        current_return = current_eval.get("expected_return", 0)
        current_risk = current_eval.get("risk", 0)
        is_efficient = current_eval.get("is_efficient", False)

        # Configurable risk tolerance
        risk_tolerance = float(risk_inputs.get("compare_risk_tolerance", 0.05))

        # Find nearest efficient point at same/lower risk (within tolerance)
        efficient_points = frontier_result.get("efficient", [])
        nearest_efficient = None
        for pt in efficient_points:
            if pt["risk"] <= current_risk * (1 + risk_tolerance):
                if nearest_efficient is None or pt["expected_return"] > nearest_efficient["expected_return"]:
                    nearest_efficient = pt

        # Handle case where no efficient point is within tolerance
        if nearest_efficient is None and not is_efficient:
            return {
                "structure_comparison": {
                    "note": "No efficient point found within risk tolerance",
                    "traditional": {
                        "can_rebalance": False,
                        "is_efficient": is_efficient,
                        "locked_inefficiency_bps": 0,
                        "wacd_bps": round(current_return * 10000),
                    },
                    "tokenized": {
                        "can_rebalance": True,
                        "recoverable_value_bps": 0,
                    },
                    "delta": {"total_tokenization_benefit_bps": 0},
                }
            }

        # Calculate inefficiency gap
        inefficiency_bps = 0
        if nearest_efficient and not is_efficient:
            inefficiency_bps = round((nearest_efficient["expected_return"] - current_return) * 10000)

        # Tokenization spread benefit
        spread_reduction_bps = int(risk_inputs.get("tokenization_spread_reduction_bps", 0))

        # Get constraints and check violations
        constraints = risk_inputs.get("traditional_constraints", {})
        constraint_check = None
        target_structure = None
        optimized_wacd = None
        wacd_calc = risk_inputs.get("wacd_calc")
        merton_results = risk_inputs.get("merton_results")
        tranche_metrics = risk_inputs.get("tranche_metrics")
        if nearest_efficient:
            target_structure = nearest_efficient.get("weights")
            if target_structure and constraints:
                constraint_check = self._check_constraint_violation(target_structure, constraints)
            if target_structure and wacd_calc is not None:
                try:
                    optimized_wacd = wacd_calc.compute_with_weights(
                        target_structure,
                        merton_results=merton_results,
                        tranche_metrics=tranche_metrics,
                        apply_tokenized_deltas=True,
                    )
                except Exception:
                    optimized_wacd = None

        return {
            "structure_comparison": {
                "traditional": {
                    "can_rebalance": False,
                    "is_efficient": is_efficient,
                    "locked_inefficiency_bps": inefficiency_bps,
                    "structure_constraints": constraints,
                    "wacd_bps": round(current_return * 10000),
                },
                "tokenized": {
                    "can_rebalance": True,
                    "is_efficient": True,  # Can move to frontier
                    "recoverable_value_bps": inefficiency_bps,
                    "spread_reduction_bps": spread_reduction_bps,
                    "total_benefit_bps": inefficiency_bps + spread_reduction_bps,
                    "target_structure": target_structure,
                    "constraint_check": constraint_check,
                    "optimized_wacd_after_tax": optimized_wacd.get("wacd_after_tax") if optimized_wacd else None,
                    "optimized_wacd_bps": round(optimized_wacd["wacd_after_tax"] * 10000) if optimized_wacd else None,
                },
                "delta": {
                    "rebalancing_value_bps": inefficiency_bps,
                    "liquidity_premium_bps": spread_reduction_bps,
                    "total_tokenization_benefit_bps": inefficiency_bps + spread_reduction_bps,
                },
            }
        }


__all__ = ["FinancialPipeline"]
