"""Spread calibration routines (WP-08 T-028).

Focuses on calibrating observed market spreads to reduced-form drivers and
re-using TokenizedSpreadModel outputs, instead of recomputing component logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class CalibrationPoint:
    """Single observation used for spread calibration."""

    rating: str | None
    tenor_years: float
    pd: float
    lgd: float
    observed_spread_bps: float
    liquidity_proxy: float | None = None
    base_spread_bps: float | None = None  # from TokenizedSpreadModel output


@dataclass(frozen=True)
class SpreadCalibrationResult:
    """Persisted calibration surface and diagnostics."""

    coefficients: Dict[str, Dict[str, float]]
    rmse: float
    r2: float
    num_points: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "coefficients": self.coefficients,
            "rmse": self.rmse,
            "r2": self.r2,
            "num_points": self.num_points,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "SpreadCalibrationResult":
        return cls(
            coefficients=dict(payload["coefficients"]),  # type: ignore[arg-type]
            rmse=float(payload["rmse"]),
            r2=float(payload["r2"]),
            num_points=int(payload["num_points"]),
        )


class SpreadCalibrator:
    """Fits reduced-form spreads to observed market data.

    Notes:
        - Consumes TokenizedSpreadModel outputs via `base_spread_bps` in each
          CalibrationPoint; it does not recompute spread components.
        - Provides per-rating intercepts with shared slope coefficients, which
          is compatible with S&P/Moody's style mappings.
    """

    def __init__(self, *, lambda_ridge: float = 0.0):
        self.lambda_ridge = max(float(lambda_ridge), 0.0)
        self._result: SpreadCalibrationResult | None = None

    # --------------------------------------------------------------- Public API
    def fit(self, points: Sequence[CalibrationPoint]) -> SpreadCalibrationResult:
        if not points:
            raise ValueError("SpreadCalibrator.fit requires at least one calibration point.")

        y = np.array([pt.observed_spread_bps for pt in points], dtype=float)
        X, rating_labels = self._build_features(points)

        coefs = self._ridge_regression(X, y, self.lambda_ridge)
        preds = X @ coefs
        residuals = y - preds
        rmse = float(np.sqrt(np.mean(residuals**2)))
        tss = float(np.sum((y - np.mean(y)) ** 2))
        rss = float(np.sum(residuals**2))
        r2 = 0.0 if np.isclose(tss, 0.0) else float(1.0 - rss / tss)

        residual_by_rating = self._residual_by_rating(residuals, rating_labels)
        coefficients = self._pack_coefficients(coefs, rating_labels, residual_by_rating)
        self._result = SpreadCalibrationResult(coefficients=coefficients, rmse=rmse, r2=r2, num_points=len(points))
        return self._result

    def predict(
        self,
        *,
        pd: float,
        lgd: float,
        tenor_years: float,
        liquidity_proxy: float | None = None,
        base_spread_bps: float | None = None,
        rating: str | None = None,
    ) -> float:
        """Predict a spread (bps) given calibrated coefficients."""

        if self._result is None:
            raise ValueError("SpreadCalibrator has not been fitted.")
        rating_key = (rating or "global").lower()
        coef = self._result.coefficients.get(rating_key) or self._result.coefficients.get("global")
        if coef is None:
            raise KeyError(f"No coefficients found for rating '{rating_key}'.")
        features = self._feature_vector(pd=pd, lgd=lgd, tenor_years=tenor_years, liquidity_proxy=liquidity_proxy, base_spread_bps=base_spread_bps)
        intercept = coef["intercept"]
        return float(intercept + sum(features[name] * coef[name] for name in features))

    def calibration_result(self) -> SpreadCalibrationResult | None:
        return self._result

    # -------------------------------------------------------------- Internals
    def _build_features(self, points: Sequence[CalibrationPoint]) -> tuple[np.ndarray, list[str]]:
        rows: list[list[float]] = []
        ratings: list[str] = []
        for pt in points:
            rows.append(
                [
                    1.0,  # intercept
                    pt.pd * pt.lgd,
                    pt.liquidity_proxy if pt.liquidity_proxy is not None else 0.0,
                    pt.tenor_years,
                    pt.base_spread_bps if pt.base_spread_bps is not None else 0.0,
                ]
            )
            ratings.append((pt.rating or "global").lower())
        return np.asarray(rows, dtype=float), ratings

    def _ridge_regression(self, X: np.ndarray, y: np.ndarray, lambda_ridge: float) -> np.ndarray:
        # Shared slope coefficients; rating-specific intercept handled separately later.
        # We first fit a global model to derive slope coefficients; intercept adjustments per rating
        # are computed from residual means.
        XtX = X.T @ X
        if lambda_ridge > 0:
            XtX += lambda_ridge * np.eye(XtX.shape[0])
        XtY = X.T @ y
        coefs, *_ = np.linalg.lstsq(XtX, XtY, rcond=None)
        return coefs

    def _pack_coefficients(
        self,
        coefs: np.ndarray,
        ratings: Sequence[str],
        residual_by_rating: Mapping[str, float],
    ) -> Dict[str, Dict[str, float]]:
        # Shared slopes; per-rating intercept offset computed from average residual for that rating.
        intercept_global = float(coefs[0])
        slopes = {
            "pd_lgd": float(coefs[1]),
            "liquidity_proxy": float(coefs[2]),
            "tenor_years": float(coefs[3]),
            "base_spread_bps": float(coefs[4]),
        }
        coeffs: Dict[str, Dict[str, float]] = {}
        unique = sorted(set(ratings))
        for rating in unique:
            offset = residual_by_rating.get(rating, 0.0)
            coeffs[rating] = {"intercept": intercept_global + offset, **slopes}
        coeffs["global"] = {"intercept": intercept_global, **slopes}
        return coeffs

    def _residual_by_rating(self, residuals: np.ndarray, ratings: Sequence[str]) -> Dict[str, float]:
        residual_by_rating: Dict[str, float] = {}
        for rating in set(ratings):
            mask = np.array([r == rating for r in ratings], dtype=bool)
            if not mask.any():
                continue
            residual_by_rating[rating] = float(np.mean(residuals[mask]))
        return residual_by_rating

    def _feature_vector(
        self,
        *,
        pd: float,
        lgd: float,
        tenor_years: float,
        liquidity_proxy: float | None,
        base_spread_bps: float | None,
    ) -> Dict[str, float]:
        return {
            "pd_lgd": float(pd * lgd),
            "liquidity_proxy": float(liquidity_proxy or 0.0),
            "tenor_years": float(tenor_years),
            "base_spread_bps": float(base_spread_bps or 0.0),
        }


__all__ = ["CalibrationPoint", "SpreadCalibrator", "SpreadCalibrationResult"]
