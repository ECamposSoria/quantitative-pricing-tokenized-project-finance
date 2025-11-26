#!/usr/bin/env python3
"""Recalibrate cap/collar hedges after deleveraging."""

from __future__ import annotations

from pathlib import Path

from pftoken.derivatives import (
    CapletPeriod,
    InterestRateCap,
    InterestRateCollar,
    find_zero_cost_floor_strike,
)
from pftoken.pricing.curve_loader import load_zero_curve_from_csv


def build_schedule(years: int = 5) -> list[CapletPeriod]:
    return [CapletPeriod(start=i, end=i + 1.0) for i in range(years)]


def main() -> None:
    curve_path = Path("data/derived/market_curves/usd_combined_curve_2025-11-20.csv")
    curve = load_zero_curve_from_csv(curve_path)

    NOTIONAL = 50_000_000
    CAP_STRIKE = 0.04
    FLOOR_STRIKE = 0.03
    VOLATILITY = 0.20
    TOKENIZATION_BPS = 78.0

    schedule = build_schedule(5)

    cap = InterestRateCap(notional=NOTIONAL, strike=CAP_STRIKE, reset_schedule=schedule)
    cap_result = cap.price(curve, volatility=VOLATILITY)

    collar = InterestRateCollar(
        notional=NOTIONAL,
        cap_strike=CAP_STRIKE,
        floor_strike=FLOOR_STRIKE,
        reset_schedule=schedule,
    )
    collar_result = collar.price(curve, volatility=VOLATILITY)

    zero_cost_strike = find_zero_cost_floor_strike(
        NOTIONAL, CAP_STRIKE, schedule, curve, volatility=VOLATILITY
    )

    shock_up = curve.apply_shock(parallel_bps=50)
    shock_down = curve.apply_shock(parallel_bps=-50)
    collar_up = collar.price(shock_up, volatility=VOLATILITY)
    collar_down = collar.price(shock_down, volatility=VOLATILITY)

    print("=" * 60)
    print("POST-DELEVERAGING HEDGE ANALYSIS")
    print("=" * 60)
    print(f"Notional: ${NOTIONAL:,.0f} (reduced from $72M)")

    print("\n1. NAKED CAP:")
    print(f"   Premium: ${cap_result.total_value:,.0f}")
    print(f"   Carry cost: {cap_result.total_value / NOTIONAL / 5 * 10000:.1f} bps/year")
    print(f"   Break-even spread: {cap_result.break_even_spread_bps:.2f} bps")

    print("\n2. COLLAR (long cap / short floor):")
    print(f"   Cap premium: ${collar_result.cap_premium:,.0f}")
    print(f"   Floor premium: ${collar_result.floor_premium:,.0f}")
    print(f"   Net premium: ${collar_result.net_premium:,.0f}")
    print(f"   Carry cost: {collar_result.carry_cost_bps:.1f} bps/year")
    print(f"   Rate band: {collar_result.floor_strike*100:.2f}% - {collar_result.cap_strike*100:.2f}%")

    print("\n3. ZERO-COST COLLAR (approx):")
    if zero_cost_strike:
        print(f"   Floor strike: {zero_cost_strike*100:.2f}%")
        print(f"   Band: {zero_cost_strike*100:.2f}% - {CAP_STRIKE*100:.2f}%")
    else:
        print("   No zero-cost solution in searched range.")

    print("\n4. SCENARIO ANALYSIS (3% floor collar):")
    print(f"   Base net premium: ${collar_result.net_premium:,.0f}")
    print(f"   +50bps: ${collar_up.net_premium:,.0f} (Δ ${collar_up.net_premium - collar_result.net_premium:,.0f})")
    print(f"   -50bps: ${collar_down.net_premium:,.0f} (Δ ${collar_down.net_premium - collar_result.net_premium:,.0f})")

    print("\n5. SELF-FUNDING CHECK:")
    retained = TOKENIZATION_BPS - collar_result.carry_cost_bps
    print(f"   Tokenization benefit: {TOKENIZATION_BPS:.1f} bps/year")
    print(f"   Collar cost: {collar_result.carry_cost_bps:.1f} bps/year")
    print(f"   Net retained: {retained:.1f} bps/year")
    if collar_result.carry_cost_bps < TOKENIZATION_BPS:
        print("   ✅ Collar is SELF-FUNDING within tokenization benefits")
    else:
        print("   ❌ Collar exceeds tokenization benefits")


if __name__ == "__main__":
    main()
