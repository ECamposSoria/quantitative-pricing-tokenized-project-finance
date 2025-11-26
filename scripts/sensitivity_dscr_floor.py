#!/usr/bin/env python3
"""
Sensitivity Analysis: DSCR Floor and Max Deferral Variations

Tests how breach probability changes with:
- DSCR floor: 1.15x, 1.20x, 1.25x, 1.30x, 1.35x
- Max deferral: 15%, 20%, 25%, 30%, 35%, 40%

Generates a pivot table showing breach probability for each combination.
Critical for thesis defense to demonstrate robustness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd

# Ensure pftoken package is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pftoken.waterfall.contingent_amortization import (
    ContingentAmortizationConfig,
    ContingentAmortizationEngine,
    DualStructureComparator,
)


def generate_cfads_scenarios(n_sims: int = 1000, n_years: int = 15, seed: int = 42) -> np.ndarray:
    """
    Generate CFADS scenarios matching demo_dual_structure.py exactly.

    Uses lognormal shocks with systematic + idiosyncratic components
    to ensure CFADS is always positive and covers minimum interest.

    Returns:
        Array of shape (n_sims, n_years) with CFADS values in USD.
    """
    np.random.seed(seed)

    # Base CFADS trajectory (millions, will convert to USD)
    # Grace period: positive CFADS that covers interest comfortably
    # Ramp-up: increasing but with potential shortfall vs full debt service
    # Steady state: stable at ~1.5x debt service
    base_cfads = np.array([
        4.0, 4.5, 5.0, 5.5,        # Grace period (years 1-4): covers interest
        8.0, 11.0, 14.0, 17.0,     # Ramp-up (years 5-8): challenging transition
        20.0, 22.0, 24.0, 25.0,    # Stabilization (years 9-12)
        26.0, 27.0, 28.0,          # Steady state (years 13-15)
    ])

    # Volatility profile (higher during ramp-up when breach risk is highest)
    volatility = np.array([
        0.15, 0.15, 0.15, 0.15,    # Grace: moderate uncertainty
        0.35, 0.30, 0.25, 0.20,    # Ramp: HIGH uncertainty (thesis focus)
        0.15, 0.12, 0.10, 0.10,    # Stabilization: decreasing
        0.10, 0.10, 0.10,          # Steady: low uncertainty
    ])

    # Generate lognormal scenarios
    scenarios = np.zeros((n_sims, n_years))

    for i in range(n_sims):
        # Systematic shock (project-level risk, affects all years)
        systematic = np.random.normal(0, 0.20)

        # Idiosyncratic shocks per year
        idiosyncratic = np.random.normal(0, volatility)

        # Combined shock (lognormal to ensure positivity)
        total_shock = np.exp(systematic + idiosyncratic)

        # Apply to base CFADS and convert to USD
        scenarios[i, :] = base_cfads * total_shock * 1_000_000

    return scenarios


def run_sensitivity_grid(
    dscr_floors: List[float],
    max_deferral_pcts: List[float],
    n_sims: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run Monte Carlo comparison for all combinations of DSCR floor and max deferral.

    Returns:
        DataFrame with columns: dscr_floor, max_deferral_pct, breach_probability,
                                avg_balloon, max_balloon, dscr_p25
    """
    # Generate CFADS scenarios once (reuse for all configs)
    cfads_scenarios = generate_cfads_scenarios(n_sims=n_sims, seed=seed)

    # Fixed parameters
    principal = 50_000_000
    rate = 0.055
    tenor = 15
    grace = 4
    covenant = 1.20

    results = []

    total_configs = len(dscr_floors) * len(max_deferral_pcts)
    config_idx = 0

    for dscr_floor in dscr_floors:
        for max_deferral_pct in max_deferral_pcts:
            config_idx += 1
            print(f"[{config_idx}/{total_configs}] Testing DSCR floor={dscr_floor:.2f}x, max_deferral={max_deferral_pct:.0%}...")

            # Create config
            config = ContingentAmortizationConfig(
                dscr_floor=dscr_floor,
                dscr_target=1.50,
                dscr_accelerate=2.00,
                deferral_rate=0.12,
                max_deferral_pct=max_deferral_pct,
                catch_up_enabled=True,
            )

            # Run comparison
            comparator = DualStructureComparator(
                principal=principal,
                interest_rate=rate,
                tenor=tenor,
                grace_years=grace,
                contingent_config=config,
            )

            result = comparator.run_monte_carlo_comparison(
                cfads_scenarios=cfads_scenarios,
                covenant=covenant,
            )

            # Extract metrics
            results.append({
                'dscr_floor': dscr_floor,
                'max_deferral_pct': max_deferral_pct,
                'breach_probability': result['tokenized']['breach_probability'],
                'breach_count': result['tokenized']['breach_count'],
                'avg_balloon': result['tokenized']['avg_additional_balloon'],
                'max_balloon': result['tokenized']['max_additional_balloon'],
                'dscr_p25': result['tokenized']['min_dscr_p25'],
                'dscr_p50': result['tokenized']['min_dscr_p50'],
            })

    return pd.DataFrame(results)


def create_pivot_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create pivot table: rows = max_deferral, cols = dscr_floor, values = breach_probability."""
    pivot = df.pivot_table(
        index='max_deferral_pct',
        columns='dscr_floor',
        values='breach_probability',
        aggfunc='first',
    )
    return pivot


def main():
    parser = argparse.ArgumentParser(description="DSCR Floor & Max Deferral Sensitivity Analysis")
    parser.add_argument("--sims", type=int, default=1000, help="Monte Carlo simulations per config")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "sensitivity_dscr_floor.json")
    args = parser.parse_args()

    # Define sensitivity ranges
    dscr_floors = [1.15, 1.20, 1.25, 1.30, 1.35]
    max_deferral_pcts = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

    print("=== DSCR FLOOR & MAX DEFERRAL SENSITIVITY ANALYSIS ===")
    print(f"Simulations per config: {args.sims}")
    print(f"DSCR floors: {dscr_floors}")
    print(f"Max deferral %: {[f'{x:.0%}' for x in max_deferral_pcts]}")
    print(f"Total configs: {len(dscr_floors) * len(max_deferral_pcts)}\n")

    # Run sensitivity grid
    results_df = run_sensitivity_grid(
        dscr_floors=dscr_floors,
        max_deferral_pcts=max_deferral_pcts,
        n_sims=args.sims,
        seed=args.seed,
    )

    # Create pivot table
    pivot = create_pivot_table(results_df)

    # Display results
    print("\n=== BREACH PROBABILITY PIVOT TABLE ===")
    print("(rows = max_deferral %, cols = DSCR floor)\n")
    print(pivot.to_string(float_format=lambda x: f"{x:.1%}"))

    # Find optimal config (lowest breach probability)
    optimal_idx = results_df['breach_probability'].idxmin()
    optimal = results_df.loc[optimal_idx]

    print(f"\n=== OPTIMAL CONFIG ===")
    print(f"DSCR Floor: {optimal['dscr_floor']:.2f}x")
    print(f"Max Deferral: {optimal['max_deferral_pct']:.0%}")
    print(f"Breach Probability: {optimal['breach_probability']:.1%}")
    print(f"Avg Balloon: ${optimal['avg_balloon']:,.0f}")
    print(f"Max Balloon: ${optimal['max_balloon']:,.0f}")
    print(f"DSCR P25: {optimal['dscr_p25']:.2f}x")

    # Export full results
    output_data = {
        "metadata": {
            "simulations": args.sims,
            "seed": args.seed,
            "dscr_floors": dscr_floors,
            "max_deferral_pcts": max_deferral_pcts,
        },
        "results": results_df.to_dict(orient='records'),
        "pivot_breach_probability": pivot.to_dict(),
        "optimal_config": {
            "dscr_floor": float(optimal['dscr_floor']),
            "max_deferral_pct": float(optimal['max_deferral_pct']),
            "breach_probability": float(optimal['breach_probability']),
            "avg_balloon": float(optimal['avg_balloon']),
            "max_balloon": float(optimal['max_balloon']),
            "dscr_p25": float(optimal['dscr_p25']),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Full results exported to {args.output}")


if __name__ == "__main__":
    main()
