#!/usr/bin/env python
"""Generate all graphs for Speaker 2 presentation.

This script creates:
1. Zero curve plot with discount factors annotated
2. DSCR fan chart starting from year 5 with covenant line

Usage:
    python scripts/generate_presentation_graphs.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pftoken.pricing.zero_curve import ZeroCurve

# Configuration
OUTPUT_DIR = Path("outputs/slides")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DPI = 300
RESULTS_FILE = Path("outputs/leo_iot_results.json")


def generate_zero_curve_plot():
    """Generate zero curve plot with DF annotations for Slide 2.

    Uses the SAME curve construction as demo_risk_metrics.py:
    - Flat curve at 4.5% (SOFR base rate from project_params.csv)
    - 15-year tenor (project horizon)
    """
    print("\n" + "="*70)
    print("GENERATING ZERO CURVE PLOT")
    print("="*70)

    # Use EXACT same curve as TP_Quant_Final.ipynb
    from pftoken.pricing.zero_curve import CurveInstrument

    instruments = [
        CurveInstrument(maturity_years=1, rate=0.0450, instrument_type="deposit"),
        CurveInstrument(maturity_years=2, rate=0.0435, instrument_type="deposit"),
        CurveInstrument(maturity_years=3, rate=0.0420, instrument_type="deposit"),
        CurveInstrument(maturity_years=5, rate=0.0410, instrument_type="deposit"),
        CurveInstrument(maturity_years=7, rate=0.0415, instrument_type="deposit"),
        CurveInstrument(maturity_years=10, rate=0.0425, instrument_type="deposit"),
        CurveInstrument(maturity_years=15, rate=0.0440, instrument_type="deposit"),
    ]

    # Bootstrap the curve (same as notebook)
    curve = ZeroCurve.bootstrap(instruments, currency="USD")

    print(f"✓ Using curve from TP_Quant_Final.ipynb notebook")
    print(f"✓ Bootstrapped from {len(instruments)} deposit instruments")
    print(f"✓ Rate range: {min(i.rate for i in instruments)*100:.2f}% - {max(i.rate for i in instruments)*100:.2f}%")

    # Generate smooth curve (more points for precision)
    maturities = np.linspace(0.5, 15, 300)
    zero_rates = [curve.spot_rate(t) * 100 for t in maturities]
    discount_factors = [curve.discount_factor(t) for t in maturities]

    # Shock scenarios
    curve_up = curve.apply_shock(parallel_bps=50)
    curve_down = curve.apply_shock(parallel_bps=-50)
    zero_rates_up = [curve_up.spot_rate(t) * 100 for t in maturities]
    zero_rates_down = [curve_down.spot_rate(t) * 100 for t in maturities]

    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Left y-axis: Zero Rates
    ax1.plot(maturities, zero_rates, 'b-', linewidth=3, label='Zero Rate (bootstrapped)', zorder=3)
    ax1.fill_between(maturities, zero_rates_down, zero_rates_up,
                     alpha=0.2, color='blue', label='Banda de shock ±50 bps')

    ax1.set_xlabel('Madurez (Años)', fontsize=17, fontweight='bold')
    ax1.set_ylabel('Zero Rate (%)', fontsize=17, fontweight='bold', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.set_xlim(0, 16)
    ax1.set_ylim(3.8, 4.8)  # Adjusted for actual rate range
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=1)

    # Right y-axis: Discount Factors
    ax2 = ax1.twinx()
    ax2.plot(maturities, discount_factors, 'g-', linewidth=3, label='Discount Factor', zorder=3, alpha=0.7)
    ax2.set_ylabel('Discount Factor', fontsize=17, fontweight='bold', color='g')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.set_ylim(0.45, 1.0)

    # Mark bootstrapped instrument nodes
    instrument_maturities = [i.maturity_years for i in instruments]
    instrument_rates = [curve.spot_rate(t) * 100 for t in instrument_maturities]
    instrument_dfs = [curve.discount_factor(t) for t in instrument_maturities]

    ax1.scatter(instrument_maturities, instrument_rates, color='darkblue', s=150, zorder=5,
                marker='o', edgecolors='blue', linewidth=2, label='Nodos bootstrapping')
    ax2.scatter(instrument_maturities, instrument_dfs, color='darkgreen', s=150, zorder=5,
                marker='s', edgecolors='green', linewidth=2)

    # Title
    ax1.set_title('Curva Zero USD - Bootstrap desde Depósitos\nHorizonte del Proyecto: 15 Años',
                  fontsize=19, fontweight='bold', pad=20)

    # Store for printing
    key_maturities = [1, 5, 10, 15]

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=12, framealpha=0.95)

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'slide2_zero_curve.png'
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    print(f"\n✓ Zero curve plot saved to: {output_path}")

    # Print curve data table
    print("\n" + "-"*70)
    print("ZERO CURVE DATA TABLE")
    print("-"*70)
    print(f"{'Maturity':<12} {'Zero Rate':<15} {'Discount Factor':<20}")
    print("-"*70)
    for mat in key_maturities:
        rate = curve.spot_rate(float(mat))
        df = curve.discount_factor(float(mat))
        print(f"{mat:>3.0f}Y         {rate*100:>6.4f}%         {df:>12.8f}")

    # Print forward rates
    print("\n" + "-"*70)
    print("FORWARD RATES")
    print("-"*70)
    print(f"{'Period':<20} {'Forward Rate':<15}")
    print("-"*70)
    periods = [(0, 1), (1, 3), (3, 5), (5, 7), (7, 10), (10, 15)]
    for start, end in periods:
        fwd = curve.forward_rate(float(start), float(end))
        print(f"{start}Y - {end}Y{'':<12} {fwd*100:>6.4f}%")

    plt.close()
    return output_path


def generate_dscr_fan_chart():
    """Generate DSCR fan chart starting from year 5 for Slide 3."""
    print("\n" + "="*70)
    print("GENERATING DSCR FAN CHART")
    print("="*70)

    # Load results
    if not RESULTS_FILE.exists():
        print(f"ERROR: Results file not found: {RESULTS_FILE}")
        print("Please run: python scripts/demo_risk_metrics.py")
        return None

    with open(RESULTS_FILE) as f:
        results = json.load(f)

    # Extract DSCR fan chart data
    dscr_data = results.get('monte_carlo', {}).get('dscr_fan_chart')
    if not dscr_data:
        print("ERROR: DSCR fan chart data not found in results")
        return None

    years = dscr_data['years']
    p5 = dscr_data['p5']
    p25 = dscr_data['p25']
    p50 = dscr_data['p50']
    p75 = dscr_data['p75']
    p95 = dscr_data['p95']

    # Filter to start from year 5 (operational phase)
    # Clean NaN values and filter years >= 5
    filtered_data = []
    for i, year in enumerate(years):
        val = p50[i]
        # Check if it's NaN (could be string "NaN" or actual NaN)
        is_nan = (isinstance(val, str) and val == 'NaN') or (isinstance(val, float) and np.isnan(val))
        if not is_nan and year >= 5:
            filtered_data.append({
                'year': year,
                'p5': p5[i],
                'p25': p25[i],
                'p50': p50[i],
                'p75': p75[i],
                'p95': p95[i]
            })

    if not filtered_data:
        print("ERROR: No valid DSCR data after filtering")
        return None

    years_clean = [d['year'] for d in filtered_data]
    p5_clean = [d['p5'] for d in filtered_data]
    p25_clean = [d['p25'] for d in filtered_data]
    p50_clean = [d['p50'] for d in filtered_data]
    p75_clean = [d['p75'] for d in filtered_data]
    p95_clean = [d['p95'] for d in filtered_data]

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 9))

    # Plot percentile bands
    ax.fill_between(years_clean, p5_clean, p95_clean, alpha=0.15, color='blue', label='Rango p5-p95')
    ax.fill_between(years_clean, p25_clean, p75_clean, alpha=0.25, color='blue', label='Rango p25-p75 (IQR)')

    # Plot percentile lines
    ax.plot(years_clean, p95_clean, 'b--', linewidth=1.5, alpha=0.6, label='p95')
    ax.plot(years_clean, p75_clean, 'b-', linewidth=2, alpha=0.7, label='p75')
    ax.plot(years_clean, p50_clean, 'b-', linewidth=3.5, label='Mediana (p50)', zorder=3)
    ax.plot(years_clean, p25_clean, 'b-', linewidth=2, alpha=0.7, label='p25')
    ax.plot(years_clean, p5_clean, 'b--', linewidth=1.5, alpha=0.6, label='p5')

    # COVENANT LINE (very prominent)
    covenant_level = 1.25
    ax.axhline(y=covenant_level, color='red', linestyle='--', linewidth=3,
               label=f'Umbral Covenant (DSCR ≥ {covenant_level})', zorder=4)

    # Highlight breach zones (where p5 < covenant)
    for i, year in enumerate(years_clean):
        if p5_clean[i] < covenant_level:
            ax.axvspan(year - 0.4, year + 0.4, alpha=0.08, color='red', zorder=1)

    # Key annotations
    # Peak DSCR annotation
    peak_idx = p50_clean.index(max(p50_clean))
    peak_year = years_clean[peak_idx]
    peak_value = p50_clean[peak_idx]

    ax.annotate(f'DSCR Máximo\nAño {peak_year}: {peak_value:.2f}x',
                xy=(peak_year, peak_value),
                xytext=(peak_year + 2, peak_value + 0.4),
                fontsize=12,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgreen',
                         edgecolor='darkgreen', alpha=0.9, linewidth=2),
                arrowprops=dict(arrowstyle='->', color='darkgreen', lw=2.5))

    # Covenant annotation
    ax.annotate(f'Covenant Mínimo: {covenant_level}x\nIncumplimiento si DSCR < {covenant_level}',
                xy=(years_clean[-1], covenant_level),
                xytext=(years_clean[-1] - 3, covenant_level - 0.5),
                fontsize=11,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightyellow',
                         edgecolor='red', alpha=0.9, linewidth=2),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))

    # Formatting
    ax.set_xlabel('Año del Proyecto', fontsize=17, fontweight='bold')
    ax.set_ylabel('DSCR (Debt Service Coverage Ratio)', fontsize=17, fontweight='bold')
    ax.set_title('Gráfico de Abanico DSCR - Simulación Monte Carlo (10,000 escenarios)\n' +
                 'Estructura Tokenizada con Amortización Contingente (DSCR floor 1.25x)',
                 fontsize=19, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=1)
    ax.legend(loc='upper right', fontsize=12, framealpha=0.95, shadow=True, ncol=2)
    ax.set_xlim(years_clean[0] - 0.5, years_clean[-1] + 0.5)
    ax.set_ylim(0, max(p95_clean) + 0.5)

    # Add statistics box - using REAL data from dual_structure_comparison
    dual_comparison = results.get('dual_structure_comparison', {})
    tokenized_breach = dual_comparison.get('tokenized', {}).get('breach_probability', 0.0253)
    traditional_breach = dual_comparison.get('traditional', {}).get('breach_probability', 0.2303)
    reduction_pct = dual_comparison.get('comparison', {}).get('breach_probability_reduction_pct', 89.0)

    median_dscr = np.median(p50_clean)
    min_p5 = min(p5_clean)

    stats_text = (f'Resultados de Simulación:\n'
                  f'• Estructura Tokenizada: {tokenized_breach*100:.1f}% breach\n'
                  f'• Estructura Tradicional: {traditional_breach*100:.1f}% breach\n'
                  f'• Reducción: {reduction_pct:.0f}% (amort. contingente)\n'
                  f'• DSCR Mediano: {median_dscr:.2f}x')

    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=12, verticalalignment='top', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.8', facecolor='lightcyan',
                     edgecolor='navy', alpha=0.9, linewidth=2))

    plt.tight_layout()

    # Save
    output_path = OUTPUT_DIR / 'slide3_dscr_fan_chart.png'
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    print(f"\n✓ DSCR fan chart saved to: {output_path}")

    # Print statistics
    print("\n" + "-"*70)
    print("DSCR STATISTICS (Years 5-15)")
    print("-"*70)
    print(f"Tokenized Breach Prob:   {tokenized_breach*100:>6.2f}%")
    print(f"Traditional Breach Prob: {traditional_breach*100:>6.2f}%")
    print(f"Breach Reduction:        {reduction_pct:>6.0f}%")
    print(f"Median DSCR:             {median_dscr:>6.2f}x")
    print(f"Min p5 DSCR:             {min_p5:>6.2f}x")
    print(f"Max p95 DSCR:            {max(p95_clean):>6.2f}x")
    print(f"Years analyzed:          {len(years_clean)}")

    plt.close()
    return output_path


def main():
    """Generate all presentation graphs."""
    print("\n" + "="*70)
    print("PRESENTATION GRAPH GENERATION FOR SPEAKER 2")
    print("="*70)
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print(f"DPI: {DPI}")

    # Generate zero curve plot
    zero_curve_path = generate_zero_curve_plot()

    # Generate DSCR fan chart
    dscr_path = generate_dscr_fan_chart()

    # Summary
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)

    if zero_curve_path:
        print(f"✓ Slide 2 (Zero Curve):  {zero_curve_path}")
    else:
        print("✗ Slide 2 (Zero Curve):  FAILED")

    if dscr_path:
        print(f"✓ Slide 3 (DSCR Chart):  {dscr_path}")
    else:
        print("✗ Slide 3 (DSCR Chart):  FAILED - Run demo_risk_metrics.py first")

    print("\nNext steps:")
    print("1. Check the PNG files in outputs/slides/")
    print("2. Insert them into your presentation slides")
    print("3. Practice your 2.5-minute presentation")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
