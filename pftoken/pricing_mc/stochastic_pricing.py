"""Stochastic pricing models (WP-08 T-026)."""

from __future__ import annotations

from typing import Dict, Iterable, Mapping, Sequence, TYPE_CHECKING

import numpy as np

from pftoken.pricing.base_pricing import TrancheCashFlow
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.pricing_mc.contracts import PriceDistribution, StochasticPricingInputs, StochasticPricingResult
from pftoken.pricing_mc.spread_calibration import SpreadCalibrator
from pftoken.waterfall.debt_structure import Tranche

if TYPE_CHECKING:  # pragma: no cover
    from pftoken.simulation import PipelineOutputs


class StochasticPricing:
    """Compute price distributions per tranche from Monte Carlo outputs."""

    def __init__(
        self,
        inputs: StochasticPricingInputs,
        *,
        spread_calibrator: SpreadCalibrator | None = None,
    ):
        self.inputs = inputs
        self.spread_calibrator = spread_calibrator

    # ------------------------------------------------------------------ Public
    def price(self) -> StochasticPricingResult:
        mc_outputs = self.inputs.mc_outputs
        sims = _infer_simulations(mc_outputs)
        tranche_names = list(mc_outputs.tranche_names) if mc_outputs.tranche_names else [
            tranche.name for tranche in self.inputs.debt_structure.tranches
        ]
        loss_paths = mc_outputs.loss_paths

        spread_paths = self._resolve_spreads(mc_outputs, tranche_names)
        cashflow_paths = self._resolve_cashflows(tranche_names, sims)

        tranche_prices: Dict[str, PriceDistribution] = {}
        for idx, tranche_name in enumerate(tranche_names):
            tranche = self.inputs.debt_structure.get_tranche(tranche_name)
            spreads = spread_paths.get(tranche_name, np.zeros(sims, dtype=float))
            cashflows, maturities = cashflow_paths[tranche_name]
            defaults = self._default_mask(loss_paths, idx, sims)

            pv_paths = self._present_value_paths(
                cashflows=cashflows,
                maturities=maturities,
                zero_curve=self.inputs.base_curve,
                spread_bps=spreads,
                defaults=defaults,
            )
            distribution = _summarize_prices(
                pv_paths,
                principal=tranche.principal,
                deterministic_price=self._deterministic_price(
                    cashflows=cashflows[0],
                    maturities=maturities,
                    tranche=tranche,
                    base_curve=self.inputs.base_curve,
                    avg_spread_bps=float(np.mean(spreads)) if sims > 0 else 0.0,
                ),
            )
            tranche_prices[tranche_name] = distribution

        return StochasticPricingResult(
            tranche_prices=tranche_prices,
            scenario_metadata={"simulations": sims},
            notes=self._notes(mc_outputs),
        )

    # --------------------------------------------------------------- Internals
    def _resolve_spreads(
        self,
        mc_outputs: "PipelineOutputs",
        tranche_names: Sequence[str],
    ) -> Dict[str, np.ndarray]:
        """Resolve per-tranche spread paths from MC outputs or calibration."""

        spreads: Dict[str, np.ndarray] = {}
        derived = mc_outputs.monte_carlo.derived or {}
        spread_paths = derived.get("spread_paths", {})
        if isinstance(spread_paths, Mapping):
            for name in tranche_names:
                if name in spread_paths:
                    spreads[name] = np.asarray(spread_paths[name], dtype=float)

        # Calibrate from PD/LGD if spreads are missing and calibrator is available.
        if self.spread_calibrator and mc_outputs.pd_lgd_paths:
            for name in tranche_names:
                if name in spreads:
                    continue
                pd_path = mc_outputs.pd_lgd_paths.get(name, {}).get("pd")
                lgd_path = mc_outputs.pd_lgd_paths.get(name, {}).get("lgd")
                if pd_path is None or lgd_path is None:
                    continue
                spreads[name] = self._calibrate_spread_path(
                    name=name,
                    pd_path=pd_path,
                    lgd_path=lgd_path,
                    tranche=self.inputs.debt_structure.get_tranche(name),
                )

        sims = _infer_simulations(mc_outputs)
        for name in tranche_names:
            if name not in spreads:
                spreads[name] = np.zeros(sims, dtype=float)
        return spreads

    def _calibrate_spread_path(
        self,
        *,
        name: str,
        pd_path: np.ndarray,
        lgd_path: np.ndarray,
        tranche: Tranche,
    ) -> np.ndarray:
        """Vectorized calibration of spreads for a single tranche."""

        if self.spread_calibrator is None:
            return np.zeros_like(pd_path, dtype=float)
        if pd_path.shape != lgd_path.shape:
            raise ValueError(f"pd/lgd path shape mismatch for tranche {name}")

        result = self.spread_calibrator.calibration_result()
        if result is None:
            return np.zeros_like(pd_path, dtype=float)

        rating_key = "global"
        coef = result.coefficients.get(rating_key)
        if coef is None:
            coef = next(iter(result.coefficients.values()))
        pd_lgd = np.asarray(pd_path, dtype=float) * np.asarray(lgd_path, dtype=float)
        liquidity_proxy = 0.0
        base_spread = 0.0
        tenor = float(tranche.tenor_years)

        spreads = (
            coef["intercept"]
            + coef["pd_lgd"] * pd_lgd
            + coef["liquidity_proxy"] * liquidity_proxy
            + coef["tenor_years"] * tenor
            + coef["base_spread_bps"] * base_spread
        )
        return np.asarray(spreads, dtype=float)

    def _resolve_cashflows(
        self,
        tranche_names: Sequence[str],
        sims: int,
    ) -> Dict[str, tuple[np.ndarray, np.ndarray]]:
        """Return cashflow matrices and maturities per tranche."""

        derived = self.inputs.mc_outputs.monte_carlo.derived or {}
        provided: Mapping[str, np.ndarray] | None = derived.get("tranche_cashflows")
        outputs: Dict[str, tuple[np.ndarray, np.ndarray]] = {}

        for name in tranche_names:
            if provided and name in provided:
                cf_matrix = np.asarray(provided[name], dtype=float)
                maturities = np.arange(1, cf_matrix.shape[1] + 1, dtype=float)
                outputs[name] = (cf_matrix, maturities)
                continue
            fallback = None
            if self.inputs.tranche_cashflows:
                fallback = self.inputs.tranche_cashflows.get(name)
            if fallback is None:
                raise ValueError(
                    f"No cashflow paths found for tranche '{name}'. Provide 'tranche_cashflows' "
                    "or include 'tranche_cashflows' in MonteCarloResult.derived."
                )
            cf_matrix, maturities = _broadcast_cashflows(fallback, sims)
            outputs[name] = (cf_matrix, maturities)
        return outputs

    @staticmethod
    def _default_mask(loss_paths: np.ndarray | None, tranche_idx: int, sims: int) -> np.ndarray | None:
        if loss_paths is None:
            return None
        if loss_paths.ndim != 2 or loss_paths.shape[0] != sims:
            raise ValueError("loss_paths shape does not match number of simulations.")
        if tranche_idx >= loss_paths.shape[1]:
            raise IndexError(f"Tranche index {tranche_idx} out of bounds for loss_paths.")
        return loss_paths[:, tranche_idx] > 0

    @staticmethod
    def _present_value_paths(
        *,
        cashflows: np.ndarray,
        maturities: np.ndarray,
        zero_curve: ZeroCurve,
        spread_bps: np.ndarray,
        defaults: np.ndarray | None,
    ) -> np.ndarray:
        """Discount cashflow matrix (sims x periods) with per-scenario spreads."""

        if cashflows.shape[0] != len(spread_bps):
            raise ValueError("cashflows and spread paths must share the same number of simulations.")
        rates = np.array([zero_curve.spot_rate(float(t)) for t in maturities], dtype=float)
        spread_decimal = np.asarray(spread_bps, dtype=float)[:, None] / 10_000.0
        eff_rates = rates[None, :] + spread_decimal
        dfs = np.power(1.0 + eff_rates, -maturities[None, :])
        prices = np.sum(cashflows * dfs, axis=1)
        if defaults is not None:
            prices = np.where(defaults, 0.0, prices)
        return prices

    @staticmethod
    def _deterministic_price(
        *,
        cashflows: np.ndarray,
        maturities: np.ndarray,
        tranche: Tranche,
        base_curve: ZeroCurve,
        avg_spread_bps: float,
    ) -> float:
        """Baseline deterministic price with an average spread adjustment."""

        rates = np.array([base_curve.spot_rate(float(t)) for t in maturities], dtype=float)
        eff_rate = rates + avg_spread_bps / 10_000.0
        dfs = np.power(1.0 + eff_rate, -maturities)
        pv = float(np.sum(cashflows * dfs))
        return pv / tranche.principal if tranche.principal else 0.0

    @staticmethod
    def _notes(mc_outputs: PipelineOutputs) -> list[str]:
        notes: list[str] = []
        if mc_outputs.loss_paths is None:
            notes.append("loss_paths absent; defaults not applied.")
        if not mc_outputs.monte_carlo.derived.get("tranche_cashflows"):
            notes.append("cashflows sourced from deterministic fallback (no MC paths).")
        return notes


# ---------------------------------------------------------------------- helpers
def _summarize_prices(prices: np.ndarray, *, principal: float, deterministic_price: float | None) -> PriceDistribution:
    if principal <= 0:
        raise ValueError("Tranche principal must be positive for pricing.")
    price_per_par = prices / principal
    percentiles = np.percentile(price_per_par, [5, 50, 95, 99])
    prob_below_par = float(np.mean(price_per_par < 1.0))
    mean_price = float(np.mean(price_per_par))
    if mean_price < 0.01 or mean_price > 10.0:
        import warnings
        warnings.warn(f"Price {mean_price:.4f} outside expected [0.01, 10.0] - check units")
    return PriceDistribution(
        mean=mean_price,
        std=float(np.std(price_per_par, ddof=1)) if len(price_per_par) > 1 else 0.0,
        p5=float(percentiles[0]),
        p50=float(percentiles[1]),
        p95=float(percentiles[2]),
        p99=float(percentiles[3]),
        prob_below_par=prob_below_par,
        deterministic_price=deterministic_price,
        jensen_adjustment=(deterministic_price - mean_price) if deterministic_price is not None else None,
    )


def _infer_simulations(outputs: PipelineOutputs) -> int:
    mc = outputs.monte_carlo
    if mc.draws:
        return len(next(iter(mc.draws.values())))
    if mc.derived:
        first = next(iter(mc.derived.values()))
        if isinstance(first, Mapping):
            inner = next(iter(first.values()))
            return len(inner)
        return len(first)
    if outputs.loss_paths is not None:
        return outputs.loss_paths.shape[0]
    return 0


def _broadcast_cashflows(cashflows: Sequence[TrancheCashFlow], sims: int) -> tuple[np.ndarray, np.ndarray]:
    totals = np.array([cf.total for cf in cashflows], dtype=float)
    maturities = np.array([cf.year for cf in cashflows], dtype=float)
    matrix = np.tile(totals, (sims, 1)) if sims > 0 else totals.reshape(1, -1)
    return matrix, maturities


__all__ = ["StochasticPricing"]
