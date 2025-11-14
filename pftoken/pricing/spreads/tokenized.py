"""Tokenized spread orchestrator combining all components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, MutableMapping, TYPE_CHECKING

import csv

from pftoken.waterfall.debt_structure import DebtStructure, Tranche
from pftoken.models.merton import MertonModel, MertonResult

from .base import (
    PerTrancheSpreadBreakdown,
    SpreadComponentResult,
    TokenizedSpreadConfig,
    TrancheSpreadInputs,
)
from .costs import OriginationServicingComponent
from .credit import CreditSpreadComponent
from .infrastructure import BlockchainInfrastructureTracker
from .liquidity import LiquiditySpreadComponent
from .delta_decomposition import (
    ConsolidatedDeltaDecomposition,
    PerTrancheDeltaBreakdown,
)


if TYPE_CHECKING:  # pragma: no cover
    from pftoken.pricing.base_pricing import TranchePricingMetrics


@dataclass
class SensitivityScenario:
    """Linear-scaling snapshot of delta components under alternate assumptions."""

    name: str
    liquidity_scale: float = 1.0
    beta_override: float | None = None
    infra_tx_multiplier: float = 1.0
    delta_credit_bps: float = 0.0
    delta_liquidity_bps: float = 0.0
    delta_origination_bps: float = 0.0
    delta_servicing_bps: float = 0.0
    delta_infrastructure_bps: float = 0.0
    total_delta_bps: float = 0.0
    tokenized_wacd: float | None = None
    wacd_delta_bps: float | None = None

    def to_dict(self) -> Dict[str, float | str | None]:
        return {
            "scenario": self.name,
            "liquidity_scale": self.liquidity_scale,
            "beta_override": self.beta_override,
            "infra_tx_multiplier": self.infra_tx_multiplier,
            "delta_credit_bps": self.delta_credit_bps,
            "delta_liquidity_bps": self.delta_liquidity_bps,
            "delta_origination_bps": self.delta_origination_bps,
            "delta_servicing_bps": self.delta_servicing_bps,
            "delta_infrastructure_bps": self.delta_infrastructure_bps,
            "total_delta_bps": self.total_delta_bps,
            "tokenized_wacd": self.tokenized_wacd,
            "wacd_delta_bps": self.wacd_delta_bps,
        }


@dataclass
class TokenizedSpreadModel:
    """Aggregates credit/liquidity/fee/infra components per tranche."""

    debt_structure: DebtStructure
    config: TokenizedSpreadConfig | None = None

    def __post_init__(self):
        if self.config is None:
            self.config = TokenizedSpreadConfig()
        self.credit_component = CreditSpreadComponent(self.config)
        self.liquidity_component = LiquiditySpreadComponent(self.config)
        self.cost_component = OriginationServicingComponent(self.config)
        self.infrastructure_component = BlockchainInfrastructureTracker(self.config)

    def compute_breakdowns(
        self,
        *,
        merton_results: Mapping[str, MertonResult] | None = None,
        tranche_metrics: Mapping[str, "TranchePricingMetrics"] | None = None,
        export_infra_csv: bool = True,
    ) -> Dict[str, PerTrancheSpreadBreakdown]:
        """Return per-tranche breakdowns with traditional/tokenized totals."""

        metrics = {name.lower(): value for name, value in (tranche_metrics or {}).items()}
        merton = self._resolve_merton_results(merton_results)
        breakdowns: Dict[str, PerTrancheSpreadBreakdown] = {}
        for tranche in self.debt_structure.tranches:
            inputs = self._build_inputs(tranche, metrics, merton)
            breakdown = PerTrancheSpreadBreakdown(tranche=tranche.name)
            self._add_component(breakdown, self.credit_component.compute(inputs))
            self._add_component(breakdown, self.liquidity_component.compute(inputs))
            self._add_component(breakdown, self.cost_component.compute_origination(inputs))
            self._add_component(breakdown, self.cost_component.compute_servicing(inputs))
            self._add_component(breakdown, self.infrastructure_component.compute(inputs))
            breakdowns[tranche.name] = breakdown
        if export_infra_csv:
            infra_path = Path(self.config.infrastructure_csv_path)
            if not infra_path.exists():
                self.infrastructure_component.export_cost_table()
        return breakdowns

    def scenario_spreads(self, breakdowns: Mapping[str, PerTrancheSpreadBreakdown]) -> Dict[str, Dict[str, float]]:
        """Return dict keyed by scenario -> tranche -> bps."""

        traditional: Dict[str, float] = {}
        tokenized: Dict[str, float] = {}
        for tranche, breakdown in breakdowns.items():
            traditional[tranche] = breakdown.traditional_total_bps
            tokenized[tranche] = breakdown.tokenized_total_bps
        return {"traditional": traditional, "tokenized": tokenized}

    def reporting_payload(self, breakdowns: Mapping[str, PerTrancheSpreadBreakdown]) -> Dict[str, dict]:
        """Structured payload for downstream reporting."""

        payload: Dict[str, dict] = {}
        for tranche, breakdown in breakdowns.items():
            payload[tranche] = {
                "traditional_total_bps": breakdown.traditional_total_bps,
                "tokenized_total_bps": breakdown.tokenized_total_bps,
                "components": {
                    name: {
                        "traditional_bps": result.traditional_bps,
                        "tokenized_bps": result.tokenized_bps,
                        "metadata": result.metadata,
                    }
                    for name, result in breakdown.components.items()
                },
            }
        return payload

    def compute_delta_decomposition(
        self,
        breakdowns: Mapping[str, PerTrancheSpreadBreakdown],
        debt_structure: DebtStructure,
    ) -> ConsolidatedDeltaDecomposition:
        """Return per-tranche and weighted deltas derived from component spreads."""

        per_tranche: Dict[str, PerTrancheDeltaBreakdown] = {}
        total_principal = sum(t.principal for t in debt_structure.tranches)
        weighted = {
            "credit": 0.0,
            "liquidity": 0.0,
            "origination": 0.0,
            "servicing": 0.0,
            "infrastructure": 0.0,
        }
        for tranche in debt_structure.tranches:
            breakdown = breakdowns[tranche.name]
            weight = tranche.principal / total_principal if total_principal else 0.0
            components = breakdown.components
            delta_credit = components["credit"].tokenized_bps - components["credit"].traditional_bps
            delta_liquidity = (
                components["liquidity"].tokenized_bps - components["liquidity"].traditional_bps
            )
            delta_origination = (
                components["origination"].tokenized_bps - components["origination"].traditional_bps
            )
            delta_servicing = (
                components["servicing"].tokenized_bps - components["servicing"].traditional_bps
            )
            delta_infra = (
                components["infrastructure"].tokenized_bps - components["infrastructure"].traditional_bps
            )
            per_tranche_breakdown = PerTrancheDeltaBreakdown(
                tranche=tranche.name,
                principal_usd=tranche.principal,
                delta_credit_bps=delta_credit,
                delta_liquidity_bps=delta_liquidity,
                delta_origination_bps=delta_origination,
                delta_servicing_bps=delta_servicing,
                delta_infrastructure_bps=delta_infra,
            )
            per_tranche[tranche.name] = per_tranche_breakdown
            weighted["credit"] += delta_credit * weight
            weighted["liquidity"] += delta_liquidity * weight
            weighted["origination"] += delta_origination * weight
            weighted["servicing"] += delta_servicing * weight
            weighted["infrastructure"] += delta_infra * weight
        return ConsolidatedDeltaDecomposition(
            per_tranche=per_tranche,
            weighted_delta_credit_bps=weighted["credit"],
            weighted_delta_liquidity_bps=weighted["liquidity"],
            weighted_delta_origination_bps=weighted["origination"],
            weighted_delta_servicing_bps=weighted["servicing"],
            weighted_delta_infrastructure_bps=weighted["infrastructure"],
        )

    # ---------------------------------------------------------------- Sensitivity
    def simulate_delta_scenarios(
        self,
        *,
        base_decomposition: ConsolidatedDeltaDecomposition,
        debt_structure: DebtStructure,
        scenarios: List[Dict[str, float | str | None]] | None = None,
    ) -> List[SensitivityScenario]:
        """Apply linear scaling to delta components under different assumptions."""

        del debt_structure  # reserved for future non-linear models
        if scenarios is None:
            scenarios = [
                {"name": "Base", "liquidity_scale": 1.0, "beta_override": None, "infra_tx_multiplier": 1.0},
                {"name": "Tinlake TVL -50%", "liquidity_scale": 0.5, "beta_override": None, "infra_tx_multiplier": 1.0},
                {"name": "Tinlake TVL +50%", "liquidity_scale": 1.5, "beta_override": None, "infra_tx_multiplier": 1.0},
                {"name": "Beta = 0.3", "liquidity_scale": 1.0, "beta_override": 0.3, "infra_tx_multiplier": 1.0},
                {"name": "Beta = 0.7", "liquidity_scale": 1.0, "beta_override": 0.7, "infra_tx_multiplier": 1.0},
                {"name": "Infra × 2", "liquidity_scale": 1.0, "beta_override": None, "infra_tx_multiplier": 2.0},
                {"name": "Stressed", "liquidity_scale": 0.5, "beta_override": 0.3, "infra_tx_multiplier": 2.0},
            ]

        results: List[SensitivityScenario] = []
        for params in scenarios:
            liquidity_scale = float(params.get("liquidity_scale", 1.0) or 1.0)
            infra_multiplier = float(params.get("infra_tx_multiplier", 1.0) or 1.0)
            beta_override = params.get("beta_override")

            delta_liquidity = base_decomposition.weighted_delta_liquidity_bps * liquidity_scale
            delta_infrastructure = base_decomposition.weighted_delta_infrastructure_bps * infra_multiplier
            if beta_override is not None:
                delta_origination = self._recompute_origination_delta(base_decomposition, beta_override)
            else:
                delta_origination = base_decomposition.weighted_delta_origination_bps

            delta_credit = base_decomposition.weighted_delta_credit_bps
            delta_servicing = base_decomposition.weighted_delta_servicing_bps
            total_delta = (
                delta_credit
                + delta_liquidity
                + delta_origination
                + delta_servicing
                + delta_infrastructure
            )
            results.append(
                SensitivityScenario(
                    name=str(params.get("name", "Scenario")),
                    liquidity_scale=liquidity_scale,
                    beta_override=beta_override if beta_override is None else float(beta_override),
                    infra_tx_multiplier=infra_multiplier,
                    delta_credit_bps=delta_credit,
                    delta_liquidity_bps=delta_liquidity,
                    delta_origination_bps=delta_origination,
                    delta_servicing_bps=delta_servicing,
                    delta_infrastructure_bps=delta_infrastructure,
                    total_delta_bps=total_delta,
                )
            )
        return results

    def export_sensitivity_scenarios(
        self,
        scenarios: List[SensitivityScenario],
        filepath: str,
    ) -> Path:
        """Persist simulated scenarios to CSV for audit trails."""

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "timestamp_utc",
            "scenario",
            "liquidity_scale",
            "beta_override",
            "infra_tx_multiplier",
            "delta_credit_bps",
            "delta_liquidity_bps",
            "delta_origination_bps",
            "delta_servicing_bps",
            "delta_infrastructure_bps",
            "total_delta_bps",
            "tokenized_wacd",
            "wacd_delta_bps",
        ]
        with path.open("w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for scenario in scenarios:
                payload = scenario.to_dict()
                payload["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
                writer.writerow(payload)
        return path

    def _recompute_origination_delta(
        self,
        base_decomposition: ConsolidatedDeltaDecomposition,
        beta_override: float,
    ) -> float:
        """Scale origination savings according to a beta override."""

        default_beta = max(self.config.origination_beta, 1e-6)
        override = max(float(beta_override), 0.0)
        scaling_factor = override / default_beta
        return base_decomposition.weighted_delta_origination_bps * scaling_factor

    def _resolve_merton_results(
        self,
        merton_results: Mapping[str, MertonResult] | None,
    ) -> MutableMapping[str, MertonResult]:
        if merton_results is None:
            model: MertonModel | None = self.config.merton_model
            if model is None:
                raise ValueError("TokenizedSpreadModel requires Merton results or a configured MertonModel.")
            merton_results = model.run()
        return {name.lower(): value for name, value in merton_results.items()}

    def _build_inputs(
        self,
        tranche: Tranche,
        tranche_metrics: Mapping[str, "TranchePricingMetrics"],
        merton_results: Mapping[str, MertonResult],
    ) -> TrancheSpreadInputs:
        key = tranche.name.lower()
        if key not in merton_results:
            raise KeyError(f"No Merton results found for tranche '{tranche.name}'")
        metrics = tranche_metrics.get(key)
        duration = metrics.macaulay_duration if metrics else None
        if metrics is None and not self.config.duration_fallback_use_tenor:
            raise ValueError(f"Missing pricing metrics for tranche '{tranche.name}' and duration fallback disabled.")
        result = merton_results[key]
        lgd = metrics.lgd if metrics and metrics.lgd is not None else result.lgd
        return TrancheSpreadInputs(
            name=tranche.name,
            principal=tranche.principal,
            tenor_years=tranche.tenor_years,
            duration_years=duration,
            pd=result.pd,
            lgd=lgd,
        )

    @staticmethod
    def _add_component(
        breakdown: PerTrancheSpreadBreakdown,
        result: SpreadComponentResult,
    ) -> None:
        breakdown.add_component(result)


__all__ = ["TokenizedSpreadModel", "SensitivityScenario"]
