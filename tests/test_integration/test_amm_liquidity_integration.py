"""Test AMM -> liquidity premium integration (WP-14).

These tests verify that the AMM module correctly integrates with
the thesis output pipeline, deriving liquidity premiums that are
consistent with the Tinlake benchmark.
"""

from __future__ import annotations

import pytest

from pftoken.amm.core.pool_v2 import ConstantProductPool, PoolConfig, PoolState
from pftoken.amm.pricing.liquidity_premium import (
    AMMDerivedPremium,
    derive_liquidity_premium_from_amm,
)
from pftoken.stress.amm_metrics_export import get_stress_metrics
from pftoken.stress.amm_stress_scenarios import build_scenarios


class TestDeriveLiquidityPremium:
    """Tests for derive_liquidity_premium_from_amm function."""

    def test_returns_amm_derived_premium_dataclass(self) -> None:
        """Function should return AMMDerivedPremium instance."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert isinstance(premium, AMMDerivedPremium)

    def test_depth_score_in_valid_range(self) -> None:
        """Depth score should be between 0 and 1."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert 0 < premium.depth_score <= 1

    def test_slippage_reasonable_for_10pct_trade(self) -> None:
        """Slippage for 10% trade should be less than 100%."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert 0 < premium.slippage_10pct_trade < 1

    def test_derived_liquidity_bps_bounded(self) -> None:
        """Derived liquidity bps should be between 0 and baseline (75)."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert 0 <= premium.derived_liquidity_bps <= 75

    def test_reduction_bps_positive(self) -> None:
        """Reduction bps should be positive (tokenization benefit)."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert 0 < premium.reduction_bps <= 75

    def test_math_consistency(self) -> None:
        """reduction_bps + derived_liquidity_bps should equal baseline."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        assert abs(
            premium.reduction_bps + premium.derived_liquidity_bps - premium.traditional_equiv_bps
        ) < 0.01


class TestRelativeLiquidityModel:
    """Tests verifying the relative liquidity model behavior.

    Note: For constant product AMMs with fractional trades, slippage is
    scale-invariant. A 10% trade causes the same relative slippage regardless
    of whether the pool has $100k or $10M reserves. This is a property of
    the x*y=k invariant.

    The model therefore measures relative liquidity quality, not absolute
    depth. Pools of different sizes with the same fee structure produce
    identical premiums. Absolute depth sensitivity would require computing
    slippage for fixed USD trade sizes (e.g., $1M redemption).
    """

    def test_scale_invariance_of_constant_product(self) -> None:
        """Pools of different sizes with same config should give same premium.

        This test verifies that the model correctly reflects x*y=k scale invariance.
        """
        small = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=100_000, reserve1=100_000),
        )
        large = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=10_000_000, reserve1=10_000_000),
        )
        scenarios = build_scenarios()

        small_premium = derive_liquidity_premium_from_amm(
            get_stress_metrics(small, scenarios.values())
        )
        large_premium = derive_liquidity_premium_from_amm(
            get_stress_metrics(large, scenarios.values())
        )

        # Same config should give same relative premium (scale invariance)
        assert abs(small_premium.depth_score - large_premium.depth_score) < 0.001
        assert abs(small_premium.reduction_bps - large_premium.reduction_bps) < 0.01

    def test_fee_effect_on_premium_is_bounded(self) -> None:
        """Different fee structures should produce premiums in valid range.

        Note: Fees interact with slippage in a non-intuitive way since they
        reduce effective input, which can slightly reduce price impact.
        """
        low_fee = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=10),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        high_fee = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=100),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()

        low_fee_premium = derive_liquidity_premium_from_amm(
            get_stress_metrics(low_fee, scenarios.values())
        )
        high_fee_premium = derive_liquidity_premium_from_amm(
            get_stress_metrics(high_fee, scenarios.values())
        )

        # Both should produce valid premiums
        assert 0 < low_fee_premium.reduction_bps <= 75
        assert 0 < high_fee_premium.reduction_bps <= 75
        # The difference should be small (fee effect is secondary to price impact)
        assert abs(low_fee_premium.reduction_bps - high_fee_premium.reduction_bps) < 1.0


class TestTinlakeConsistency:
    """Tests verifying consistency with Tinlake benchmark (~54 bps)."""

    def test_typical_pool_within_range_of_tinlake(self) -> None:
        """A 10% depth pool on 50M notional should be within ±15 bps of Tinlake."""
        # Simulate the thesis case: $50M debt, 10% depth = $5M per side
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())
        premium = derive_liquidity_premium_from_amm(metrics)

        tinlake_benchmark = 54.21
        delta = abs(premium.reduction_bps - tinlake_benchmark)

        # Should be within ±15 bps for "consistent" validation
        assert delta < 15, f"AMM reduction {premium.reduction_bps:.2f} bps too far from Tinlake {tinlake_benchmark} bps"


class TestCustomBaseline:
    """Tests for custom baseline parameter."""

    def test_custom_baseline_affects_reduction(self) -> None:
        """Using a different baseline should affect reduction proportionally."""
        pool = ConstantProductPool(
            PoolConfig("DEBT", "USDC", fee_bps=30),
            PoolState(reserve0=5_000_000, reserve1=5_000_000),
        )
        scenarios = build_scenarios()
        metrics = get_stress_metrics(pool, scenarios.values())

        premium_75 = derive_liquidity_premium_from_amm(metrics, traditional_baseline_bps=75.0)
        premium_100 = derive_liquidity_premium_from_amm(metrics, traditional_baseline_bps=100.0)

        # Higher baseline should give higher reduction
        assert premium_100.reduction_bps > premium_75.reduction_bps
        # Traditional equiv should match input
        assert premium_75.traditional_equiv_bps == 75.0
        assert premium_100.traditional_equiv_bps == 100.0
