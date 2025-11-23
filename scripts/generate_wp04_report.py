#!/usr/bin/env python3
"""
WP-04 Comprehensive Analysis Report Generator

Generates a full pricing analysis with:
- Zero curve from market data
- Debt tranche structure
- Pricing metrics (YTM, Duration, PV, LGD)
- Spread decomposition (traditional vs tokenized)
- Delta breakdown by component
- WACD comparison (traditional vs tokenized)
- Full source traceability

All values are computed dynamically from actual data - no hardcoded placeholders.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pftoken.models.merton import MertonModel, MertonResult
from pftoken.models.params import ProjectParameters
from pftoken.pipeline import FinancialPipeline
from pftoken.constants import TOKENIZED_OPTIMAL_STRUCTURE
from pftoken.pricing.base_pricing import PricingEngine, TranchePricingMetrics
from pftoken.pricing.collateral_adjust import CollateralAnalyzer
from pftoken.pricing.constants import DEFAULT_PRICING_CONTEXT, PricingContext
from pftoken.pricing.curve_loader import load_zero_curve_from_csv
from pftoken.pricing.spreads import TokenizedSpreadConfig, TokenizedSpreadModel
from pftoken.pricing.spreads.tinlake import (
    TINLAKE_METADATA_PATH,
    TINLAKE_SNAPSHOT_PATH,
    fetch_tinlake_metrics,
)
from pftoken.pricing.wacd import WACDCalculator
from pftoken.pricing.zero_curve import ZeroCurve
from pftoken.waterfall.debt_structure import DebtStructure

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data" / "input" / "leo_iot"
MARKET_CURVES_DIR = PROJECT_ROOT / "data" / "derived" / "market_curves"
INFRA_COSTS_PATH = PROJECT_ROOT / "data" / "derived" / "tokenized_infra_costs.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def find_latest_curve(curves_dir: Path) -> Path:
    """Find the most recent USD curve CSV in the directory."""
    curves = sorted(curves_dir.glob("usd_combined_curve_*.csv"), reverse=True)
    if not curves:
        raise FileNotFoundError(f"No USD curve found in {curves_dir}")
    return curves[0]


def format_currency(value: float) -> str:
    """Format a number as USD currency."""
    return f"${value:,.2f}"


def format_pct(value: float, decimals: int = 4) -> str:
    """Format a decimal as percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_bps(value: float, decimals: int = 2) -> str:
    """Format a number as basis points."""
    return f"{value:.{decimals}f} bps"


# -----------------------------------------------------------------------------
# Report Sections
# -----------------------------------------------------------------------------

def section_zero_curve(curve: ZeroCurve, curve_path: Path) -> Dict[str, Any]:
    """Generate zero curve section data."""
    # Spot rates at key tenors
    tenors = [1, 2, 3, 5, 7, 10, 15, 20, 30]
    spots = {}
    for t in tenors:
        try:
            rate = curve.spot_rate(t)
            spots[f"{t}Y"] = format_pct(rate, 2)
        except Exception:
            spots[f"{t}Y"] = "N/A"

    # Forward rates
    forwards = {}
    forward_pairs = [(1, 2), (2, 3), (5, 10), (10, 20)]
    for start, end in forward_pairs:
        try:
            fwd = curve.forward_rate(start, end)
            label = f"{start}Y{end-start}Y"
            forwards[label] = format_pct(fwd, 3)
        except Exception:
            pass

    return {
        "source_file": str(curve_path.name),
        "source_path": str(curve_path),
        "currency": curve.currency,
        "num_points": len(curve.points),
        "spot_rates": spots,
        "forward_rates": forwards,
        "loader": "load_zero_curve_from_csv (pftoken/pricing/curve_loader.py)",
    }


def section_tranches(debt_structure: DebtStructure) -> Dict[str, Any]:
    """Generate tranche structure section data."""
    tranches_data = []
    for tranche in debt_structure.tranches:
        weight = tranche.principal / debt_structure.total_principal
        tranches_data.append({
            "name": tranche.name.title(),
            "principal": format_currency(tranche.principal),
            "principal_raw": tranche.principal,
            "coupon": format_pct(tranche.rate, 1),
            "coupon_raw": tranche.rate,
            "weight": format_pct(weight, 0),
            "weight_raw": weight,
            "grace_years": tranche.grace_period_years,
            "tenor_years": tranche.tenor_years,
            "amortization": tranche.amortization_style.title(),
            "seniority": tranche.seniority,
        })

    return {
        "tranches": tranches_data,
        "total_principal": format_currency(debt_structure.total_principal),
        "total_principal_raw": debt_structure.total_principal,
        "source": "data/input/leo_iot/tranches.csv",
    }


def section_pricing(
    pricing_metrics: Dict[str, TranchePricingMetrics],
    collateral_results: Dict[str, Any],
    pricing_context: PricingContext,
) -> Dict[str, Any]:
    """Generate pricing section data."""
    pricing_data = []
    for name, metrics in pricing_metrics.items():
        lgd = collateral_results.get(name, {}).lgd if hasattr(collateral_results.get(name, {}), 'lgd') else (metrics.lgd or 0.0)
        pricing_data.append({
            "tranche": name.title(),
            "price_per_par": f"{metrics.price_per_par:.5f}",
            "price_per_par_raw": metrics.price_per_par,
            "present_value": format_currency(metrics.present_value),
            "present_value_raw": metrics.present_value,
            "ytm": format_pct(metrics.ytm, 4),
            "ytm_raw": metrics.ytm,
            "duration": f"{metrics.macaulay_duration:.4f}",
            "duration_raw": metrics.macaulay_duration,
            "lgd": f"{lgd:.3f}",
            "lgd_raw": lgd,
        })

    return {
        "metrics": pricing_data,
        "haircut": format_pct(pricing_context.collateral_haircut, 0),
        "time_to_liquidation": f"{pricing_context.time_to_liquidation_years} años",
        "sources": [
            "FinancialPipeline + PricingEngine + CollateralAnalyzer",
            "Haircut from PricingContext",
            "LGD derived from CollateralAnalyzer waterfall",
        ],
        "ytm_note": "YTM solved against risk-free curve; credit/liquidity spreads in TokenizedSpreadModel",
    }


def section_spreads(
    scenario_spreads: Dict[str, Dict[str, float]],
    breakdowns: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate spreads section data."""
    traditional = scenario_spreads.get("traditional", {})
    tokenized = scenario_spreads.get("tokenized", {})

    spreads_data = []
    for tranche_name in traditional.keys():
        trad_bps = traditional.get(tranche_name, 0.0)
        token_bps = tokenized.get(tranche_name, 0.0)
        delta = token_bps - trad_bps
        spreads_data.append({
            "tranche": tranche_name.title(),
            "traditional_bps": format_bps(trad_bps),
            "traditional_bps_raw": trad_bps,
            "tokenized_bps": format_bps(token_bps),
            "tokenized_bps_raw": token_bps,
            "delta_bps": format_bps(delta),
            "delta_bps_raw": delta,
        })

    return {
        "spreads": spreads_data,
        "sources": [
            "Crédito/Liquidez: stochastic_params.yaml",
            "Infraestructura: tokenized_infra_costs.csv",
            "Lógica: pftoken/pricing/spreads/",
        ],
    }


def section_delta_decomposition(
    delta_decomp: Dict[str, Any],
    spread_config: TokenizedSpreadConfig,
) -> Dict[str, Any]:
    """Generate delta decomposition section data."""
    weighted = delta_decomp.get("weighted_totals", {})

    components = [
        {
            "name": "Crédito",
            "delta_bps": format_bps(weighted.get("delta_credit_bps", 0.0)),
            "delta_bps_raw": weighted.get("delta_credit_bps", 0.0),
            "source": f"Floor {spread_config.credit_spread_floor_bps} bps + transparencia {spread_config.credit_transparency_delta_bps} bps",
        },
        {
            "name": "Liquidez",
            "delta_bps": format_bps(weighted.get("delta_liquidity_bps", 0.0)),
            "delta_bps_raw": weighted.get("delta_liquidity_bps", 0.0),
            "source": "Tinlake TVL calibration (DeFiLlama)",
        },
        {
            "name": "Originación",
            "delta_bps": format_bps(weighted.get("delta_origination_bps", 0.0)),
            "delta_bps_raw": weighted.get("delta_origination_bps", 0.0),
            "source": f"β = {spread_config.origination_beta} ({spread_config.origination_beta*100:.0f}% automation)",
        },
        {
            "name": "Servicing",
            "delta_bps": format_bps(weighted.get("delta_servicing_bps", 0.0)),
            "delta_bps_raw": weighted.get("delta_servicing_bps", 0.0),
            "source": f"γ = {spread_config.servicing_gamma} + residual {spread_config.servicing_residual_bps} bps",
        },
        {
            "name": "Infraestructura",
            "delta_bps": format_bps(weighted.get("delta_infrastructure_bps", 0.0)),
            "delta_bps_raw": weighted.get("delta_infrastructure_bps", 0.0),
            "source": f"{spread_config.blockchain_network} gas/oracle/monitoring",
        },
    ]

    total_delta = weighted.get("total_weighted_delta_bps", 0.0)

    return {
        "components": components,
        "total_delta_bps": format_bps(total_delta),
        "total_delta_bps_raw": total_delta,
        "adjustments": [
            f"Credit floor de {spread_config.credit_spread_floor_bps} bps",
            "Infraestructura uniforme via infra_reference_principal",
            f"Transparencia ({spread_config.credit_transparency_delta_bps} bps) aplica sobre piso",
        ],
    }


def section_wacd(
    wacd_result: Dict[str, Any],
    pricing_context: PricingContext,
) -> Dict[str, Any]:
    """Generate WACD section data."""
    traditional = wacd_result.get("traditional", 0.0)
    tokenized = wacd_result.get("tokenized", 0.0)
    delta = wacd_result.get("delta", 0.0)

    # Get delta info
    details = wacd_result.get("details", {})
    delta_decomp = details.get("delta_decomposition", {})
    weighted = delta_decomp.get("weighted_totals", {})
    total_delta_bps = weighted.get("total_weighted_delta_bps", 0.0)

    delta_after_tax_bps = delta * 10000  # Convert to bps

    return {
        "traditional_after_tax": format_pct(traditional, 4),
        "traditional_after_tax_raw": traditional,
        "tokenized_after_tax": format_pct(tokenized, 4),
        "tokenized_after_tax_raw": tokenized,
        "delta_after_tax": format_pct(delta, 4),
        "delta_after_tax_bps": format_bps(delta_after_tax_bps),
        "delta_after_tax_bps_raw": delta_after_tax_bps,
        "delta_before_tax_bps": format_bps(total_delta_bps),
        "delta_before_tax_bps_raw": total_delta_bps,
        "tax_rate": format_pct(pricing_context.corporate_tax_rate, 0),
        "tax_rate_raw": pricing_context.corporate_tax_rate,
        "verification": f"Delta after-tax = {total_delta_bps:.2f} × (1 - {pricing_context.corporate_tax_rate}) = {total_delta_bps * (1 - pricing_context.corporate_tax_rate):.2f} bps",
        "sources": [
            "WACDCalculator — pftoken/pricing/wacd.py",
            f"Tax Rate: {pricing_context.corporate_tax_rate*100:.0f}% — constants.py",
        ],
    }


def section_structure_scenarios(
    wacd_result: Dict[str, Any],
    structure_comparison: Dict[str, Any],
    optimized_wacd: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Compare traditional, tokenized current, and tokenized optimized structures."""

    traditional_struct = {"senior": 0.60, "mezzanine": 0.25, "subordinated": 0.15}
    tokenized_struct = traditional_struct
    tokenized_optimized_struct = TOKENIZED_OPTIMAL_STRUCTURE
    tokenized_wacd = wacd_result.get("tokenized")
    traditional_wacd = wacd_result.get("traditional")
    benefit_tokenized = (tokenized_wacd - traditional_wacd) * 10_000 if tokenized_wacd and traditional_wacd else None

    optimized_section = None
    if optimized_wacd:
        benefit_opt = None
        if optimized_wacd.get("wacd_after_tax") is not None and traditional_wacd is not None:
            benefit_opt = (optimized_wacd["wacd_after_tax"] - traditional_wacd) * 10_000
        optimized_section = {
            "structure": tokenized_optimized_struct,
            "wacd_after_tax": optimized_wacd.get("wacd_after_tax"),
            "benefit_vs_traditional_bps": benefit_opt,
            "constraint_violation": structure_comparison.get("tokenized", {}).get("constraint_check"),
        }

    return {
        "traditional": {
            "structure": traditional_struct,
            "wacd_after_tax": traditional_wacd,
            "can_rebalance": False,
        },
        "tokenized_current": {
            "structure": tokenized_struct,
            "wacd_after_tax": tokenized_wacd,
            "benefit_vs_traditional_bps": benefit_tokenized,
        },
        "tokenized_optimized": optimized_section,
    }


def section_tinlake() -> Dict[str, Any]:
    """Generate Tinlake metrics section data."""
    metrics = fetch_tinlake_metrics()

    # Read metadata
    metadata = {}
    if TINLAKE_METADATA_PATH.exists():
        try:
            metadata = json.loads(TINLAKE_METADATA_PATH.read_text())
        except Exception:
            pass

    if metrics:
        return {
            "tvl_usd": format_currency(metrics.tvl_usd),
            "tvl_usd_raw": metrics.tvl_usd,
            "avg_daily_volume_usd": format_currency(metrics.avg_daily_volume_usd),
            "avg_daily_volume_usd_raw": metrics.avg_daily_volume_usd,
            "avg_pool_ticket_usd": format_currency(metrics.avg_pool_ticket_usd),
            "avg_pool_ticket_usd_raw": metrics.avg_pool_ticket_usd,
            "datapoints": metrics.datapoints,
            "source": metadata.get("source", "api"),
            "api_endpoint": metadata.get("api_endpoint", "https://api.llama.fi/protocol/centrifuge"),
            "timestamp_utc": metadata.get("timestamp_utc", "unknown"),
            "snapshot_path": str(TINLAKE_SNAPSHOT_PATH),
        }

    return {"error": "Tinlake metrics unavailable"}


def section_infrastructure() -> Dict[str, Any]:
    """Generate infrastructure costs section data."""
    if not INFRA_COSTS_PATH.exists():
        return {"error": f"Infrastructure costs file not found: {INFRA_COSTS_PATH}"}

    df = pd.read_csv(INFRA_COSTS_PATH)

    networks = []
    for _, row in df.iterrows():
        networks.append({
            "network": row.get("network", "Unknown"),
            "reference_principal": format_currency(row.get("reference_principal", 0)),
            "annual_tx_count": int(row.get("annual_tx_count", 0)),
            "gas_per_tx": int(row.get("gas_per_tx", 0)),
            "gas_price_gwei": row.get("gas_price_gwei", 0),
            "oracle_bps": row.get("oracle_bps", 0),
            "monitoring_bps": row.get("monitoring_bps", 0),
            "total_bps": row.get("total_bps", 0),
        })

    return {
        "networks": networks,
        "source_file": str(INFRA_COSTS_PATH),
        "sources": ["Etherscan V2 Gas Tracker", "Chainlink public docs"],
    }


def section_traceability(
    curve_path: Path,
    pricing_metrics: Dict[str, TranchePricingMetrics],
    collateral_results: Dict[str, Any],
    pricing_context: PricingContext,
    spread_config: TokenizedSpreadConfig,
) -> Dict[str, Any]:
    """Generate traceability section data."""
    rows = []

    # Curve
    rows.append({"item": "Curva Spots", "value": "Ver sección 1", "source": str(curve_path.name) + " (FRED DGS)"})

    # Tranche principals
    for name, metrics in pricing_metrics.items():
        rows.append({"item": f"{name.title()} Principal", "value": format_currency(metrics.present_value / metrics.price_per_par if metrics.price_per_par else 0), "source": "tranches.csv"})
        rows.append({"item": f"{name.title()} YTM", "value": format_pct(metrics.ytm, 4), "source": "PricingEngine con curva de mercado"})
        rows.append({"item": f"{name.title()} PV", "value": format_currency(metrics.present_value), "source": "PricingEngine discounting"})
        rows.append({"item": f"{name.title()} Duration", "value": f"{metrics.macaulay_duration:.4f}", "source": "Macaulay duration calculation"})
        lgd = collateral_results.get(name, None)
        if lgd:
            rows.append({"item": f"{name.title()} LGD", "value": f"{lgd.lgd:.3f}", "source": "CollateralAnalyzer"})

    # Context params
    rows.append({"item": "Tax Rate", "value": format_pct(pricing_context.corporate_tax_rate, 0), "source": "constants.py"})
    rows.append({"item": "Haircut", "value": format_pct(pricing_context.collateral_haircut, 0), "source": "PricingContext"})
    rows.append({"item": "T_liquidation", "value": f"{pricing_context.time_to_liquidation_years} años", "source": "PricingContext"})
    rows.append({"item": "Credit Floor", "value": f"{spread_config.credit_spread_floor_bps} bps", "source": "credit.py"})
    rows.append({"item": "Credit Transparency", "value": f"{spread_config.credit_transparency_delta_bps} bps", "source": "Allen et al. 2022"})
    rows.append({"item": "Infra Reference", "value": format_currency(spread_config.infra_reference_principal or 0), "source": "base.py (infra_reference_principal)"})

    return {"items": rows}


# -----------------------------------------------------------------------------
# Report Formatters
# -----------------------------------------------------------------------------

def print_header(title: str, char: str = "=") -> None:
    """Print a section header."""
    print(f"\n{char * 80}")
    print(f" {title}")
    print(f"{char * 80}")


def print_table(headers: list, rows: list, col_widths: list = None) -> None:
    """Print a formatted table."""
    if not col_widths:
        col_widths = [max(len(str(h)), max(len(str(row[i])) for row in rows)) + 2 for i, h in enumerate(headers)]

    # Header
    header_line = "| " + " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths)) + " |"
    separator = "|-" + "-|-".join("-" * w for w in col_widths) + "-|"
    print(header_line)
    print(separator)

    # Rows
    for row in rows:
        row_line = "| " + " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)) + " |"
        print(row_line)


def generate_markdown_report(report_data: Dict[str, Any]) -> str:
    """Generate a markdown version of the report."""
    lines = []
    timestamp = report_data.get("timestamp", datetime.now(timezone.utc).isoformat())

    lines.append(f"# Análisis WP-04 Actualizado ({timestamp[:10]})")
    lines.append("")

    # Section 1: Zero Curve
    curve = report_data.get("zero_curve", {})
    lines.append("## 1. CURVA ZERO CUPÓN (Actualizada)")
    lines.append(f"**Fuente:** [{curve.get('source_file', 'N/A')}]({curve.get('source_path', '')}) — FRED DGS")
    lines.append("")
    lines.append("### Spot Rates (%)")
    lines.append("")
    spots = curve.get("spot_rates", {})
    headers = list(spots.keys())
    values = list(spots.values())
    lines.append("| Tenor | " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * (len(headers) + 1)) + "|")
    lines.append("| **Rate** | " + " | ".join(values) + " |")
    lines.append("")

    # Section 2: Tranches
    tranches = report_data.get("tranches", {})
    lines.append("## 2. ESTRUCTURA DE TRAMOS")
    lines.append(f"**Fuente:** [{tranches.get('source', 'tranches.csv')}]({tranches.get('source', '')})")
    lines.append("")
    lines.append("| Tramo | Principal | Cupón | Peso | Gracia | Tenor | Amortización |")
    lines.append("|-------|-----------|-------|------|--------|-------|--------------|")
    for t in tranches.get("tranches", []):
        lines.append(f"| **{t['name']}** | {t['principal']} | {t['coupon']} | {t['weight']} | {t['grace_years']} años | {t['tenor_years']} años | {t['amortization']} |")
    lines.append(f"| **Total** | {tranches.get('total_principal', 'N/A')} | - | 100% | - | - | - |")
    lines.append("")

    # Section 3: Pricing
    pricing = report_data.get("pricing", {})
    lines.append("## 3. PRICING POR TRAMO (Con Curva de Mercado)")
    lines.append(f"**Haircut:** {pricing.get('haircut', 'N/A')} — **Time to Liquidation:** {pricing.get('time_to_liquidation', 'N/A')}")
    lines.append("")
    lines.append("| Tramo | Price/Par | Present Value | YTM | Duración | LGD |")
    lines.append("|-------|-----------|---------------|-----|----------|-----|")
    for m in pricing.get("metrics", []):
        lines.append(f"| **{m['tranche']}** | {m['price_per_par']} | {m['present_value']} | {m['ytm']} | {m['duration']} | {m['lgd']} |")
    lines.append("")

    # Section 4: Spreads
    spreads = report_data.get("spreads", {})
    lines.append("## 4. SPREADS POR TRAMO (bps)")
    lines.append("")
    lines.append("| Tramo | Tradicional | Tokenizado | Delta |")
    lines.append("|-------|-------------|------------|-------|")
    for s in spreads.get("spreads", []):
        lines.append(f"| **{s['tranche']}** | {s['traditional_bps']} | {s['tokenized_bps']} | {s['delta_bps']} |")
    lines.append("")

    # Section 5: Delta Decomposition
    delta = report_data.get("delta_decomposition", {})
    lines.append("## 5. DELTA DECOMPOSITION PONDERADA")
    lines.append("")
    lines.append("| Componente | Delta (bps) | Fuente |")
    lines.append("|------------|-------------|--------|")
    for c in delta.get("components", []):
        lines.append(f"| **{c['name']}** | {c['delta_bps']} | {c['source']} |")
    lines.append(f"| **TOTAL** | **{delta.get('total_delta_bps', 'N/A')}** | Before-tax weighted |")
    lines.append("")

    # Section 6: WACD
    wacd = report_data.get("wacd", {})
    lines.append("## 6. WACD FINAL")
    lines.append(f"**Tax Rate:** {wacd.get('tax_rate', 'N/A')}")
    lines.append("")
    lines.append("| Métrica | Valor |")
    lines.append("|---------|-------|")
    lines.append(f"| **WACD Tradicional (after-tax)** | {wacd.get('traditional_after_tax', 'N/A')} |")
    lines.append(f"| **WACD Tokenizado (after-tax)** | {wacd.get('tokenized_after_tax', 'N/A')} |")
    lines.append(f"| **Delta After-Tax** | {wacd.get('delta_after_tax', 'N/A')} ({wacd.get('delta_after_tax_bps', 'N/A')}) |")
    lines.append(f"| **Delta Before-Tax** | {wacd.get('delta_before_tax_bps', 'N/A')} |")
    lines.append("")
    lines.append(f"**Verificación:** {wacd.get('verification', '')}")
    lines.append("")

    # Section 7: Structure Scenarios
    struct = report_data.get("structure_scenarios", {})
    lines.append("## 7. COMPARACIÓN DE ESTRUCTURAS")
    lines.append("")
    lines.append("| Escenario | Estructura | WACD (after-tax) | Δ vs Trad (bps) |")
    lines.append("|-----------|------------|------------------|-----------------|")
    trad = struct.get("traditional", {})
    token = struct.get("tokenized_current", {})
    opt = struct.get("tokenized_optimized", {})
    lines.append(f"| Tradicional | {trad.get('structure')} | {trad.get('wacd_after_tax')} | - |")
    lines.append(f"| Tokenizado (actual) | {token.get('structure')} | {token.get('wacd_after_tax')} | {token.get('benefit_vs_traditional_bps')} |")
    if opt:
        lines.append(f"| Tokenizado (óptimo) | {opt.get('structure')} | {opt.get('wacd_after_tax')} | {opt.get('benefit_vs_traditional_bps')} |")
        if opt.get("constraint_violation"):
            lines.append("")
            lines.append(f"**Nota:** Viola restricciones tradicionales: {opt['constraint_violation']}")
    lines.append("")

    # Section 8: Tinlake
    tinlake = report_data.get("tinlake", {})
    if "error" not in tinlake:
        lines.append("## 8. DATOS TINLAKE (DeFiLlama)")
        lines.append("")
        lines.append("| Métrica | Valor |")
        lines.append("|---------|-------|")
        lines.append(f"| TVL | {tinlake.get('tvl_usd', 'N/A')} |")
        lines.append(f"| Daily Volume | {tinlake.get('avg_daily_volume_usd', 'N/A')} |")
        lines.append(f"| Avg Pool Ticket | {tinlake.get('avg_pool_ticket_usd', 'N/A')} |")
        lines.append(f"| Source | {tinlake.get('source', 'N/A')} |")
        lines.append(f"| Timestamp | {tinlake.get('timestamp_utc', 'N/A')} |")
        lines.append("")

    # Section 9: Infrastructure
    infra = report_data.get("infrastructure", {})
    if "error" not in infra and infra.get("networks"):
        lines.append("## 9. COSTOS INFRAESTRUCTURA BLOCKCHAIN")
        lines.append("")
        lines.append("| Network | TX/año | Gas/TX | Gas Price | Oracle | Monitoring | Total |")
        lines.append("|---------|--------|--------|-----------|--------|------------|-------|")
        for n in infra.get("networks", []):
            lines.append(f"| {n['network']} | {n['annual_tx_count']} | {n['gas_per_tx']:,} | {n['gas_price_gwei']} gwei | {n['oracle_bps']} bps | {n['monitoring_bps']} bps | **{n['total_bps']:.2f} bps** |")
        lines.append("")

    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Main Report Generator
# -----------------------------------------------------------------------------

def generate_report(
    curve_path: Path | None = None,
    output_json: bool = True,
    output_markdown: bool = True,
    print_console: bool = True,
) -> Dict[str, Any]:
    """
    Generate the complete WP-04 analysis report.

    Args:
        curve_path: Path to the zero curve CSV. If None, uses latest.
        output_json: Write JSON report to outputs/
        output_markdown: Write markdown report to outputs/
        print_console: Print report to console

    Returns:
        Complete report data as a dictionary.
    """
    timestamp = datetime.now(timezone.utc)

    # Find latest curve if not specified
    if curve_path is None:
        curve_path = find_latest_curve(MARKET_CURVES_DIR)

    if print_console:
        print_header("WP-04 ANÁLISIS COMPLETO - PRICING STACK")
        print(f"Timestamp: {timestamp.isoformat()}")
        print(f"Curve: {curve_path.name}")

    # 1. Load zero curve
    if print_console:
        print("\n[1/8] Loading zero curve...")
    curve = load_zero_curve_from_csv(curve_path)

    # 2. Run financial pipeline
    if print_console:
        print("[2/8] Running financial pipeline...")
    pipeline = FinancialPipeline(data_dir=DATA_DIR)
    pipeline_result = pipeline.run()
    debt_structure = pipeline.debt_structure
    waterfall_results = pipeline_result["waterfall"]
    cfads_vector = pipeline_result["cfads"]

    # 2b. Run Merton model for credit metrics
    if print_console:
        print("[2b/8] Running Merton credit model...")
    params = ProjectParameters.from_directory(DATA_DIR)
    merton_model = MertonModel(
        cfads_vector=cfads_vector,
        tranches=params.tranches,
        discount_rate=0.08,  # Base discount rate for EV calculation
    )
    merton_results = merton_model.run()

    # 3. Configure pricing context and spread config
    pricing_context = DEFAULT_PRICING_CONTEXT
    spread_config = TokenizedSpreadConfig(
        market_price_of_risk=0.1,
        liquidity_alpha=0.5,
        origination_beta=0.5,
        servicing_gamma=1.0,
        blockchain_network="Ethereum",
        auto_calibrate_liquidity=True,
        credit_transparency_delta_bps=-30.0,
        credit_spread_floor_bps=5.0,
        infra_reference_principal=debt_structure.total_principal,
    )

    # 4. Run collateral analyzer
    if print_console:
        print("[3/8] Running collateral analysis...")
    collateral_analyzer = CollateralAnalyzer(
        debt_structure=debt_structure,
        zero_curve=curve,
        pricing_context=pricing_context,
    )
    collateral_results = collateral_analyzer.analyze()

    # 5. Run pricing engine
    if print_console:
        print("[4/8] Running pricing engine...")
    pricing_engine = PricingEngine(
        zero_curve=curve,
        pricing_context=pricing_context,
        collateral_analyzer=collateral_analyzer,
    )
    pricing_metrics = pricing_engine.price_from_waterfall(
        waterfall_results=waterfall_results,
        debt_structure=debt_structure,
        as_dict=False,
    )

    # 6. Run WACD calculator
    if print_console:
        print("[5/8] Running WACD calculator...")
    wacd_calc = WACDCalculator(
        debt_structure=debt_structure,
        pricing_context=pricing_context,
        spread_config=spread_config,
    )
    wacd_result = wacd_calc.compare_traditional_vs_tokenized(
        merton_results=merton_results,
        tranche_metrics=pricing_metrics,
    )

    # Extract scenario spreads and breakdowns
    scenario_spreads = wacd_result.get("scenario_breakdowns", {})
    details = wacd_result.get("details", {})
    delta_decomp = details.get("delta_decomposition", {})

    # 6b. Run risk frontier to capture optimized structure
    risk_inputs = {
        "pd": {"senior": 0.01, "mezzanine": 0.03, "subordinated": 0.10},
        "lgd": {"senior": 0.40, "mezzanine": 0.55, "subordinated": 1.00},
        "correlation": np.eye(len(debt_structure.tranches)),
        "simulations": 5000,
        "seed": 42,
        "run_frontier": True,
        "frontier_samples": 300,
        "tranche_returns": {t.name: t.rate for t in debt_structure.tranches},
        "compare_structures": True,
        "wacd_calc": wacd_calc,
        "merton_results": merton_results,
        "tranche_metrics": pricing_metrics,
    }
    risk_result = pipeline.run(include_risk=True, risk_inputs=risk_inputs)
    structure_comparison = risk_result.get("risk_metrics", {}).get("structure_comparison", {})
    optimized_wacd = None
    target_structure = structure_comparison.get("tokenized", {}).get("target_structure")
    if target_structure:
        try:
            optimized_wacd = wacd_calc.compute_with_weights(
                target_structure,
                merton_results=merton_results,
                tranche_metrics=pricing_metrics,
                apply_tokenized_deltas=True,
            )
        except Exception:
            optimized_wacd = None

    # 7. Fetch Tinlake metrics
    if print_console:
        print("[6/8] Fetching Tinlake metrics...")
    tinlake_data = section_tinlake()

    # 8. Load infrastructure costs
    if print_console:
        print("[7/8] Loading infrastructure costs...")
    infra_data = section_infrastructure()

    # 9. Compile report
    if print_console:
        print("[8/8] Compiling report...")

    report_data = {
        "timestamp": timestamp.isoformat(),
        "curve_file": str(curve_path.name),
        "zero_curve": section_zero_curve(curve, curve_path),
        "tranches": section_tranches(debt_structure),
        "pricing": section_pricing(pricing_metrics, collateral_results, pricing_context),
        "spreads": section_spreads(scenario_spreads, details.get("breakdowns", {})),
        "delta_decomposition": section_delta_decomposition(delta_decomp, spread_config),
        "wacd": section_wacd(wacd_result, pricing_context),
        "structure_scenarios": section_structure_scenarios(wacd_result, structure_comparison, optimized_wacd),
        "tinlake": tinlake_data,
        "infrastructure": infra_data,
        "traceability": section_traceability(
            curve_path, pricing_metrics, collateral_results, pricing_context, spread_config
        ),
        "raw": {
            "wacd_result": {
                "traditional": wacd_result.get("traditional"),
                "tokenized": wacd_result.get("tokenized"),
                "delta": wacd_result.get("delta"),
            },
            "delta_sensitivity": wacd_result.get("delta_sensitivity", {}),
        },
    }

    # Output files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if output_json:
        json_path = OUTPUT_DIR / "wp04_report.json"
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        if print_console:
            print(f"\nJSON report saved to: {json_path}")

    if output_markdown:
        md_content = generate_markdown_report(report_data)
        md_path = OUTPUT_DIR / "wp04_report.md"
        with open(md_path, "w") as f:
            f.write(md_content)
        if print_console:
            print(f"Markdown report saved to: {md_path}")

    # Console output
    if print_console:
        print_header("RESUMEN EJECUTIVO")
        wacd = report_data["wacd"]
        print(f"\nWACD Tradicional (after-tax):  {wacd['traditional_after_tax']}")
        print(f"WACD Tokenizado (after-tax):   {wacd['tokenized_after_tax']}")
        print(f"Delta After-Tax:               {wacd['delta_after_tax']} ({wacd['delta_after_tax_bps']})")
        print(f"Delta Before-Tax:              {wacd['delta_before_tax_bps']}")

        print("\n--- Delta Decomposition ---")
        for c in report_data["delta_decomposition"]["components"]:
            print(f"  {c['name']:15} {c['delta_bps']:>12}")
        print(f"  {'TOTAL':15} {report_data['delta_decomposition']['total_delta_bps']:>12}")

        print_header("REPORT COMPLETE", "=")

    return report_data


# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate WP-04 Pricing Analysis Report")
    parser.add_argument(
        "--curve",
        type=str,
        default=None,
        help="Path to zero curve CSV (default: latest in market_curves/)",
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip JSON output",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip Markdown output",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )

    args = parser.parse_args()

    curve_path = Path(args.curve) if args.curve else None

    report = generate_report(
        curve_path=curve_path,
        output_json=not args.no_json,
        output_markdown=not args.no_markdown,
        print_console=not args.quiet,
    )
