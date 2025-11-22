"""Weighted Average Cost of Debt helpers for traditional vs tokenized stacks."""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional

from datetime import datetime, timezone

from pftoken.models.merton import MertonResult
from pftoken.pricing.base_pricing import TranchePricingMetrics
from pftoken.pricing.constants import (
    DEFAULT_PRICING_CONTEXT,
    DEFAULT_TOKENIZED_SPREAD_CONFIG,
    PricingContext,
)
from pftoken.pricing.spreads import (
    ConsolidatedDeltaDecomposition,
    PerTrancheSpreadBreakdown,
    SensitivityScenario,
    TokenizedSpreadConfig,
    TokenizedSpreadModel,
)
from pftoken.waterfall.debt_structure import DebtStructure

BPS_TO_DECIMAL = 1 / 10_000.0


@dataclass(frozen=True)
class WACDScenario:
    """Configuration knobs for a capital structure scenario."""

    name: str
    spread_delta_bps: float = 0.0
    fee_delta_bps: float = 0.0
    tax_rate: float | None = None
    computed_spread_delta_bps: float | None = None
    computed_fee_delta_bps: float | None = None
    use_computed_deltas: bool = True


class WACDCalculator:
    """Computes after-tax weighted average cost of debt with modular spreads."""

    def __init__(
        self,
        debt_structure: DebtStructure,
        *,
        pricing_context: PricingContext = DEFAULT_PRICING_CONTEXT,
        spread_config: TokenizedSpreadConfig | None = None,
        spread_model: TokenizedSpreadModel | None = None,
    ):
        if debt_structure.total_principal <= 0:
            raise ValueError("Debt structure must have positive principal.")
        self.debt_structure = debt_structure
        self.pricing_context = pricing_context
        self.spread_config = (
            spread_config
            if spread_config is not None
            else deepcopy(DEFAULT_TOKENIZED_SPREAD_CONFIG)
        )
        if self.spread_config.infra_reference_principal is None:
            self.spread_config.infra_reference_principal = self.debt_structure.total_principal
        self.spread_model = spread_model or TokenizedSpreadModel(debt_structure, self.spread_config)
        self._breakdowns: Optional[Dict[str, PerTrancheSpreadBreakdown]] = None
        self._scenario_spreads: Optional[Dict[str, Dict[str, float]]] = None
        self._reporting_payload: Optional[Dict[str, dict]] = None
        self._delta_decomposition: Optional[ConsolidatedDeltaDecomposition] = None

    def compute(
        self,
        scenario: WACDScenario,
        *,
        merton_results: Mapping[str, MertonResult] | None = None,
        tranche_metrics: Mapping[str, TranchePricingMetrics] | None = None,
    ) -> float:
        """Return the after-tax WACD for the provided scenario."""

        self._ensure_breakdowns(merton_results, tranche_metrics)
        if not self._scenario_spreads:
            raise RuntimeError("Spread breakdowns were not generated.")
        scenario_key = "tokenized" if scenario.name.lower() == "tokenized" else "traditional"
        spreads_map = self._scenario_spreads.get(scenario_key, {})
        return self._weighted_cost(scenario, spreads_map)

    def compare_traditional_vs_tokenized(
        self,
        *,
        merton_results: Mapping[str, MertonResult] | None = None,
        tranche_metrics: Mapping[str, TranchePricingMetrics] | None = None,
    ) -> Dict[str, float | Dict[str, dict]]:
        """Return WACD tradicional vs tokenizado y la descomposición de deltas."""

        self._ensure_breakdowns(merton_results, tranche_metrics)
        if self._breakdowns is None:
            raise RuntimeError("Spread breakdowns not available.")
        delta_decomp = self.spread_model.compute_delta_decomposition(self._breakdowns, self.debt_structure)
        self._delta_decomposition = delta_decomp
        sensitivity_scenarios = self.spread_model.simulate_delta_scenarios(
            base_decomposition=delta_decomp,
            debt_structure=self.debt_structure,
            scenarios=None,
        )
        sensitivity_dir = Path("data/derived/sensitivities")
        delta_dir = Path("data/derived/delta_decomposition")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        sensitivity_path = sensitivity_dir / f"wacd_delta_sensitivity_{timestamp}.csv"
        self.spread_model.export_sensitivity_scenarios(sensitivity_scenarios, str(sensitivity_path))
        delta_dir.mkdir(parents=True, exist_ok=True)
        delta_path = delta_dir / f"wacd_delta_breakdown_{timestamp}.csv"
        metadata_path = delta_path.with_suffix(delta_path.suffix + ".meta.json")
        self.export_delta_decomposition(str(delta_path), str(metadata_path))

        traditional = self.compute(WACDScenario(name="traditional"), merton_results=merton_results, tranche_metrics=tranche_metrics)

        computed_spread_delta = delta_decomp.total_weighted_delta_bps
        computed_fee_delta = 0.0
        if self.pricing_context.use_computed_deltas:
            spread_delta = 0.0
            fee_delta = computed_fee_delta
            delta_source = "computed"
        else:
            spread_delta = self.pricing_context.tokenized_spread_delta_bps
            fee_delta = self.pricing_context.tokenized_origination_fee_bps
            delta_source = "override"

        tokenized_scenario = WACDScenario(
            name="tokenized",
            spread_delta_bps=spread_delta,
            fee_delta_bps=fee_delta,
            computed_spread_delta_bps=computed_spread_delta,
            computed_fee_delta_bps=computed_fee_delta,
            use_computed_deltas=self.pricing_context.use_computed_deltas,
        )
        tokenized = self.compute(
            tokenized_scenario,
            merton_results=merton_results,
            tranche_metrics=tranche_metrics,
        )
        delta = tokenized - traditional

        tax_rate = self.pricing_context.corporate_tax_rate
        for scenario in sensitivity_scenarios:
            after_tax_delta = scenario.total_delta_bps / 10_000.0 * (1.0 - tax_rate)
            scenario.tokenized_wacd = traditional + after_tax_delta
            scenario.wacd_delta_bps = after_tax_delta * 10_000.0
        delta_info = {
            "computed": computed_spread_delta,
            "override": self.pricing_context.tokenized_spread_delta_bps,
            "used": computed_spread_delta if self.pricing_context.use_computed_deltas else self.pricing_context.tokenized_spread_delta_bps,
            "source": delta_source,
        }
        sensitivity_payload = {
            "scenarios": [scenario.to_dict() for scenario in sensitivity_scenarios],
            "export_path": str(sensitivity_path),
        }
        delta_export_payload = {
            "csv_path": str(delta_path),
            "metadata_path": str(metadata_path),
        }
        return {
            "traditional": traditional,
            "tokenized": tokenized,
            "delta": delta,
            "details": {
                "breakdowns": self._reporting_payload or {},
                "scenario_spreads_bps": self._scenario_spreads or {},
                "delta_decomposition": delta_decomp.to_dict(),
                "delta_spread_bps": delta_info,
                "delta_decomposition_export": delta_export_payload,
            },
            "delta_sensitivity": sensitivity_payload,
            "scenario_breakdowns": self._scenario_spreads or {},
        }

    def spread_breakdowns(self) -> Optional[Dict[str, PerTrancheSpreadBreakdown]]:
        """Latest cached spread breakdowns."""

        return self._breakdowns

    def delta_decomposition(self) -> Optional[ConsolidatedDeltaDecomposition]:
        """Latest computed delta decomposition."""

        return self._delta_decomposition

    def export_delta_decomposition(
        self,
        filepath: str,
        metadata_path: str | None = None,
    ) -> Path:
        """Persist the latest delta decomposition for auditability."""

        if self._delta_decomposition is None:
            raise RuntimeError("No delta decomposition available. Run comparison first.")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for delta in self._delta_decomposition.per_tranche.values():
            row = asdict(delta)
            row["total_delta_bps"] = delta.total_delta_bps
            rows.append(row)
        with path.open("w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        metadata = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "config_hash": hash(str(self.spread_config)),
            "pricing_context": {
                "use_computed_deltas": self.pricing_context.use_computed_deltas,
                "override_spread_delta_bps": self.pricing_context.tokenized_spread_delta_bps,
                "override_fee_delta_bps": self.pricing_context.tokenized_origination_fee_bps,
            },
            "weighted_totals": self._delta_decomposition.to_dict()["weighted_totals"],
        }
        meta_path = Path(metadata_path) if metadata_path else path.with_suffix(path.suffix + ".meta.json")
        append_payload = []
        if meta_path.exists():
            try:
                append_payload = json.loads(meta_path.read_text())
                if not isinstance(append_payload, list):
                    append_payload = [append_payload]
            except json.JSONDecodeError:
                append_payload = []
        append_payload.append(metadata)
        meta_path.write_text(json.dumps(append_payload, indent=2))
        return path

    # ------------------------------------------------------------------ Internals
    def _ensure_breakdowns(
        self,
        merton_results: Mapping[str, MertonResult] | None,
        tranche_metrics: Mapping[str, TranchePricingMetrics] | None,
    ) -> None:
        should_recompute = self._breakdowns is None or merton_results is not None or tranche_metrics is not None
        if not should_recompute:
            return
        self._breakdowns = self.spread_model.compute_breakdowns(
            merton_results=merton_results,
            tranche_metrics=tranche_metrics,
            export_infra_csv=self._breakdowns is None,
        )
        self._scenario_spreads = self.spread_model.scenario_spreads(self._breakdowns)
        self._reporting_payload = self.spread_model.reporting_payload(self._breakdowns)

    def _weighted_cost(
        self,
        scenario: WACDScenario,
        additional_spreads_bps: Mapping[str, float],
    ) -> float:
        tax_rate = (
            scenario.tax_rate
            if scenario.tax_rate is not None
            else self.pricing_context.corporate_tax_rate
        )
        fee_delta = scenario.fee_delta_bps * BPS_TO_DECIMAL
        spread_delta = scenario.spread_delta_bps * BPS_TO_DECIMAL
        total = self.debt_structure.total_principal
        weighted_sum = 0.0
        for tranche in self.debt_structure.tranches:
            extra_spread = additional_spreads_bps.get(tranche.name, 0.0) * BPS_TO_DECIMAL
            effective_rate = (tranche.rate + extra_spread + spread_delta + fee_delta) * (1.0 - tax_rate)
            weighted_sum += tranche.principal / total * effective_rate
        return weighted_sum


__all__ = ["WACDCalculator", "WACDScenario"]
