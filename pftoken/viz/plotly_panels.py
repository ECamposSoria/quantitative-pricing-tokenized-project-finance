"""Plotly panels for WP-09 interactive dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import plotly.graph_objects as go
import plotly.io as pio


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")
    fig.update_layout(template="plotly_white", height=320)
    return fig


def cfads_vs_debt_service(results: Dict) -> go.Figure:
    cfads_map = {row["year"]: row["cfads_musd"] for row in results.get("cfads_components", [])}
    debt_by_year = results.get("debt_schedule", {}).get("by_year", [])
    if not cfads_map or not debt_by_year:
        return _empty_figure("CFADS / debt service data unavailable")

    years = sorted(cfads_map.keys())
    cfads = [cfads_map[y] for y in years]
    service_lookup = {int(row["year"]): row["interest_due"] + row["principal_due"] for row in debt_by_year}
    service = [float(service_lookup.get(y, 0.0)) for y in years]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Debt Service (MUSD)", x=years, y=service, marker_color="#9DB2CE", opacity=0.75))
    fig.add_trace(go.Scatter(name="CFADS (MUSD)", x=years, y=cfads, mode="lines+markers", line_color="#1f77b4"))
    fig.update_layout(
        title="CFADS vs Debt Service",
        barmode="group",
        template="plotly_white",
        yaxis_title="MUSD",
    )
    return fig


def dscr_fan_chart(results: Dict) -> go.Figure:
    fan = results.get("monte_carlo", {}).get("dscr_fan_chart")
    if not fan:
        return _empty_figure("DSCR fan chart not available")

    years = fan.get("years", [])
    fig = go.Figure()
    for percentile in ("p5", "p25", "p50", "p75", "p95"):
        series = fan.get(percentile)
        if series:
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=series,
                    mode="lines",
                    name=percentile.upper(),
                    line=dict(shape="spline", width=2 if percentile == "p50" else 1, dash="dot" if percentile != "p50" else None),
                )
            )
    fig.add_hline(y=results.get("coverage_ratios", {}).get("icr_summary", {}).get("icr_min", 1.25) or 1.25,
                  line_dash="dash", line_color="red", opacity=0.4)
    fig.update_layout(title="DSCR Fan Chart (Monte Carlo)", template="plotly_white", yaxis_title="DSCR")
    return fig


def coverage_ratios_panel(results: Dict) -> go.Figure:
    coverage = results.get("coverage_ratios", {})
    llcr = coverage.get("llcr", [])
    icr_years = coverage.get("icr_by_year", [])
    if not llcr and not icr_years:
        return _empty_figure("Coverage ratios unavailable")

    fig = go.Figure()
    if llcr:
        fig.add_trace(
            go.Bar(
                name="LLCR",
                x=[row["tranche"] for row in llcr],
                y=[row["llcr"] for row in llcr],
                marker_color="#1f77b4",
            )
        )
        fig.add_trace(
            go.Scatter(
                name="Threshold",
                x=[row["tranche"] for row in llcr],
                y=[row["threshold"] for row in llcr],
                mode="markers+text",
                text=[f"{row['threshold']:.2f}" for row in llcr],
                textposition="top center",
                marker=dict(color="#ff7f0e", symbol="diamond", size=10),
            )
        )
    if icr_years:
        icr_series = [row["icr"] for row in icr_years]
        fig.add_trace(
            go.Scatter(
                name="ICR by year",
                x=[row["year"] for row in icr_years],
                y=icr_series,
                mode="lines",
                line=dict(color="#2ca02c"),
                yaxis="y2",
            )
        )
    fig.update_layout(
        title="Coverage Ratios (LLCR & ICR)",
        template="plotly_white",
        yaxis_title="LLCR",
        yaxis2=dict(title="ICR", overlaying="y", side="right", showgrid=False),
        legend_orientation="h",
    )
    return fig


def capital_structure_panel(results: Dict) -> go.Figure:
    tokenized = results.get("structure_comparison", {}).get("tokenized", {})
    traditional = results.get("structure_comparison", {}).get("traditional", {})
    recommended = tokenized.get("recommended_structure") or {}
    current = results.get("current_structure") or {}
    if not recommended and not current:
        return _empty_figure("Capital structure data unavailable")

    labels = sorted(set(recommended.keys()) | set(current.keys()))
    fig = go.Figure()
    if recommended:
        fig.add_trace(
            go.Bar(
                name="Tokenizado (55/34/11)",
                x=labels,
                y=[recommended.get(label, 0.0) * 100 for label in labels],
                marker_color="#1f77b4",
            )
        )
    if current:
        fig.add_trace(
            go.Bar(
                name="Tradicional (60/25/15)",
                x=labels,
                y=[current.get(label, 0.0) * 100 for label in labels],
                marker_color="#9DB2CE",
            )
        )
    fig.update_layout(
        title="Estructura de Capital",
        template="plotly_white",
        barmode="group",
        yaxis_title="% del Notional de Deuda",
    )
    return fig


def waterfall_cascade_panel(results: Dict) -> go.Figure:
    cascade = results.get("waterfall_cascade", [])
    if not cascade:
        return _empty_figure("Waterfall cascade unavailable")

    years = [row["year"] for row in cascade]
    interest = [row["interest_paid_musd"] for row in cascade]
    principal = [row["principal_paid_musd"] for row in cascade]
    reserves = [row["dsra_funding_musd"] + row["mra_funding_musd"] for row in cascade]
    dividends = [row["dividends_musd"] for row in cascade]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Interest", x=years, y=interest, marker_color="#6C8DBF"))
    fig.add_trace(go.Bar(name="Principal", x=years, y=principal, marker_color="#A3C4F3"))
    fig.add_trace(go.Bar(name="Reserves", x=years, y=reserves, marker_color="#7CCBA2"))
    fig.add_trace(go.Bar(name="Dividends", x=years, y=dividends, marker_color="#F4A261"))
    fig.update_layout(
        title="Waterfall Cascade (MUSD)",
        template="plotly_white",
        barmode="stack",
        yaxis_title="MUSD",
    )
    return fig


def wacd_synthesis_panel(results: Dict) -> go.Figure:
    synthesis = results.get("wacd_synthesis", {})
    scenarios = synthesis.get("scenarios", {})
    if not scenarios:
        return _empty_figure("WACD synthesis unavailable")

    names = []
    totals = []
    for name, scenario in scenarios.items():
        names.append(name)
        totals.append(float(scenario.get("all_in_wacd_bps", 0.0)))

    fig = go.Figure(
        go.Bar(
            x=names,
            y=totals,
            marker_color="#1f77b4",
            text=[f"{val:.1f} bps" for val in totals],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="WACD Synthesis (All-in bps)",
        template="plotly_white",
        yaxis_title="bps",
    )
    return fig


def stress_heatmap_panel(results: Dict) -> go.Figure:
    ranking = results.get("stress_results", {}).get("ranking_by_dscr_impact") or []
    if not ranking:
        return _empty_figure("Stress results unavailable")

    codes = [row["code"] for row in ranking]
    deltas = [row.get("delta", 0.0) for row in ranking]
    fig = go.Figure(
        go.Bar(
            x=codes,
            y=deltas,
            marker_color="#ef6f6c",
            text=[row.get("name", "") for row in ranking],
        )
    )
    fig.update_layout(
        title="Stress Scenario Impact (Δ DSCR)",
        template="plotly_white",
        yaxis_title="Δ DSCR vs Base",
    )
    return fig


def amm_comparison_panel(results: Dict) -> go.Figure:
    comp = results.get("v2_v3_comparison", {})
    v2 = comp.get("v2_results") or []
    v3 = comp.get("v3_results") or []
    if not v2 or not v3:
        return _empty_figure("AMM comparison unavailable")

    x = [row["trade_pct"] for row in v2]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="V2 Slippage (%)",
            x=x,
            y=[row["slippage_pct"] for row in v2],
            marker_color="#ef6f6c",
        )
    )
    fig.add_trace(
        go.Bar(
            name="V3 Slippage (%)",
            x=x,
            y=[row["slippage_pct"] for row in v3],
            marker_color="#2a9d8f",
        )
    )
    summary = comp.get("comparison", {})
    title = (
        f"AMM V2 vs V3 (Slippage Reduction {summary.get('slippage_reduction_pct', '')}%, "
        f"CapEff {summary.get('capital_efficiency_multiple', '')}x)"
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        barmode="group",
        yaxis_title="Execution Slippage (%)",
    )
    return fig


def hedging_comparison_panel(results: Dict) -> go.Figure:
    hedging = results.get("hedging_comparison", {}).get("scenarios") or {}
    if not hedging:
        return _empty_figure("Hedging comparison unavailable")

    names = list(hedging.keys())
    breach = [hedging[name].get("breach_probability", 0.0) * 100 for name in names]
    cost = [hedging[name].get("cost", 0.0) / 1_000_000.0 for name in names]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Breach Probability (%)", x=names, y=breach, marker_color="#1f77b4"))
    fig.add_trace(
        go.Bar(
            name="Cost (MUSD)",
            x=names,
            y=cost,
            marker_color="#ffb703",
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Hedging Comparison",
        template="plotly_white",
        barmode="group",
        yaxis_title="Breach Probability (%)",
        yaxis2=dict(title="Cost (MUSD)", overlaying="y", side="right", showgrid=False),
    )
    return fig


def build_interactive_dashboard(results: Dict) -> Dict[str, go.Figure]:
    return {
        "cfads_vs_debt_service": cfads_vs_debt_service(results),
        "dscr_fan_chart": dscr_fan_chart(results),
        "coverage_ratios": coverage_ratios_panel(results),
        "capital_structure": capital_structure_panel(results),
        "waterfall_cascade": waterfall_cascade_panel(results),
        "wacd_synthesis": wacd_synthesis_panel(results),
        "stress_impact": stress_heatmap_panel(results),
        "amm_comparison": amm_comparison_panel(results),
        "hedging_comparison": hedging_comparison_panel(results),
    }


def export_dashboard_html(figures: Dict[str, go.Figure], output_path: str | Path) -> None:
    """Export a simple HTML page stacking the Plotly panels."""
    html_parts: List[str] = []
    for name, fig in figures.items():
        html_parts.append(f"<h2>{name.replace('_', ' ').title()}</h2>")
        html_parts.append(pio.to_html(fig, include_plotlyjs="cdn", full_html=False))
    html = "<br/>".join(html_parts)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


__all__ = [
    "build_interactive_dashboard",
    "export_dashboard_html",
    "cfads_vs_debt_service",
    "dscr_fan_chart",
    "coverage_ratios_panel",
    "capital_structure_panel",
    "waterfall_cascade_panel",
    "wacd_synthesis_panel",
    "stress_heatmap_panel",
    "amm_comparison_panel",
    "hedging_comparison_panel",
]
