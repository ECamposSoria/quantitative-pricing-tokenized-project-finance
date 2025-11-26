"""Interest rate sensitivity utilities (WP-08 T-044)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, TYPE_CHECKING

from pftoken.derivatives import InterestRateCap
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.pricing_mc.contracts import RateScenarioDefinition, StochasticPricingInputs
from pftoken.pricing_mc.spread_calibration import SpreadCalibrator
from pftoken.pricing_mc.stochastic_pricing import StochasticPricing

if TYPE_CHECKING:  # pragma: no cover
    HedgeInstrument = InterestRateCap
else:
    HedgeInstrument = InterestRateCap


@dataclass(frozen=True)
class ScenarioPriceDelta:
    scenario: str
    tranche: str
    delta_mean_price: float


@dataclass(frozen=True)
class HedgeComparisonResult:
    """Portfolio-level comparison between naked and hedged outcomes."""

    scenario: str
    base_total_price: float
    hedged_total_price: float
    hedge_value: float
    delta_vs_base: float


class InterestRateSensitivity:
    """Evaluates curve-shock scenarios using existing stochastic pricing."""

    def __init__(
        self,
        inputs: StochasticPricingInputs,
        *,
        spread_calibrator: SpreadCalibrator | None = None,
    ):
        self.inputs = inputs
        self.spread_calibrator = spread_calibrator

    def scenario_library(self) -> List[RateScenarioDefinition]:
        """Return default scenarios (parallel/twist/steepener/Fed-like)."""

        return [
            RateScenarioDefinition(name="Base", parallel_bps=0.0),
            RateScenarioDefinition(name="+50bps", parallel_bps=50.0),
            RateScenarioDefinition(name="-50bps", parallel_bps=-50.0),
            RateScenarioDefinition(name="Bear Steepener", bucket_shocks={(0, 2): 25.0, (2, 10): 75.0, (10, 30): 100.0}),
            RateScenarioDefinition(name="Bull Flattener", bucket_shocks={(0, 2): -50.0, (2, 10): -25.0, (10, 30): 0.0}),
            RateScenarioDefinition(name="Fed Hike Path", bucket_shocks={(0, 5): 100.0, (5, 30): 50.0}),
        ]

    def run(
        self,
        scenarios: Sequence[RateScenarioDefinition] | None = None,
    ) -> Dict[str, object]:
        """Run curve scenarios and return deltas vs base."""

        scenarios = list(scenarios) if scenarios is not None else self.scenario_library()
        if not scenarios:
            raise ValueError("At least one scenario must be provided.")

        base_inputs = self.inputs
        base_result = StochasticPricing(base_inputs, spread_calibrator=self.spread_calibrator).price()
        base_means = {k: v.mean for k, v in base_result.tranche_prices.items()}

        scenario_results: Dict[str, Dict[str, float]] = {}
        deltas: List[ScenarioPriceDelta] = []
        for scenario in scenarios:
            shocked_curve = self._apply_scenario(base_inputs.base_curve, scenario)
            scenario_inputs = StochasticPricingInputs(
                mc_outputs=base_inputs.mc_outputs,
                base_curve=shocked_curve,
                debt_structure=base_inputs.debt_structure,
                tranche_cashflows=base_inputs.tranche_cashflows,
                scenarios=base_inputs.scenarios,
                batch_size=base_inputs.batch_size,
            )
            priced = StochasticPricing(scenario_inputs, spread_calibrator=self.spread_calibrator).price()
            scenario_means = {k: v.mean for k, v in priced.tranche_prices.items()}
            scenario_results[scenario.name] = scenario_means
            for tranche, mean_price in scenario_means.items():
                deltas.append(
                    ScenarioPriceDelta(
                        scenario=scenario.name,
                        tranche=tranche,
                        delta_mean_price=mean_price - base_means.get(tranche, 0.0),
                    )
                )

        tornado = self._tornado_chart_data(deltas)
        dscr_break_even = self._dscr_break_even_matrix(base_inputs)
        return {
            "base": base_means,
            "scenarios": scenario_results,
            "price_deltas": [delta.__dict__ for delta in deltas],
            "tornado": tornado,
            "dscr_break_even": dscr_break_even,
        }

    def analyze_with_hedge(
        self,
        hedge_instrument: HedgeInstrument,
        *,
        upfront_premium: float | None = None,
        volatility_override: float | None = None,
        scenarios: Sequence[RateScenarioDefinition] | None = None,
    ) -> Dict[str, object]:
        """Compare naked vs hedged exposure across rate scenarios."""

        scenarios = list(scenarios) if scenarios is not None else self.scenario_library()
        baseline = self.run(scenarios=scenarios)
        base_curve = self.inputs.base_curve
        base_priced = hedge_instrument.price(base_curve, volatility=volatility_override)
        premium = upfront_premium if upfront_premium is not None else self._premium(base_priced)
        base_total = float(sum(baseline["base"].values()))

        results: List[HedgeComparisonResult] = []
        for scenario in scenarios:
            shocked_curve = self._apply_scenario(base_curve, scenario)
            priced = hedge_instrument.price(shocked_curve, volatility=volatility_override)
            hedge_price = self._premium(priced)
            hedge_value = hedge_price - premium
            tranche_prices = baseline["scenarios"].get(scenario.name, {})
            scenario_total = float(sum(tranche_prices.values()))
            hedged_total = scenario_total + hedge_value
            results.append(
                HedgeComparisonResult(
                    scenario=scenario.name,
                    base_total_price=base_total,
                    hedged_total_price=hedged_total,
                    hedge_value=hedge_value,
                    delta_vs_base=hedged_total - base_total,
                )
            )

        return {
            "upfront_premium": premium,
            "hedge_results": [r.__dict__ for r in results],
            "baseline": baseline,
        }

    # --------------------------------------------------------------- Internals
    @staticmethod
    def _apply_scenario(curve: ZeroCurve, scenario: RateScenarioDefinition) -> ZeroCurve:
        return curve.apply_shock(parallel_bps=scenario.parallel_bps, bucket_shocks=scenario.bucket_shocks)

    @staticmethod
    def _tornado_chart_data(deltas: Iterable[ScenarioPriceDelta]) -> Dict[str, List[Dict[str, float | str]]]:
        tornado: Dict[str, List[Dict[str, float | str]]] = {}
        for delta in deltas:
            tornado.setdefault(delta.tranche, []).append(
                {"scenario": delta.scenario, "delta_mean_price": delta.delta_mean_price}
            )
        for tranche in tornado:
            tornado[tranche].sort(key=lambda item: abs(item["delta_mean_price"]), reverse=True)
        return tornado

    @staticmethod
    def _dscr_break_even_matrix(inputs: StochasticPricingInputs) -> Dict[str, object]:
        """DSCR paths are assumed invariant to rate shocks; expose breach rates."""

        ratio_summary = inputs.mc_outputs.ratio_summary
        breach = None
        if ratio_summary and "breach_rate" in ratio_summary:
            raw = ratio_summary["breach_rate"]
            if hasattr(raw, "tolist"):
                raw = raw.tolist()
            breach = raw
        return {
            "breach_rate": breach,
            "note": "DSCR paths assumed invariant to rate shocks; rate scenarios only affect pricing.",
        }

    @staticmethod
    def _premium(priced: object) -> float:
        """Extract premium from cap/floor/collar results."""

        for attr in ("total_value", "net_premium"):
            if hasattr(priced, attr):
                return float(getattr(priced, attr))
        raise ValueError("Hedge instrument price result missing total_value/net_premium.")


__all__ = ["HedgeComparisonResult", "InterestRateSensitivity", "ScenarioPriceDelta"]
