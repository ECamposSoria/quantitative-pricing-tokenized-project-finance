"""Stress scenario definitions for WP-06 (T-038/T-038B/T-039)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class StressShock:
    target: str
    mode: str  # "add" or "mult"
    value: float
    note: str | None = None


@dataclass(frozen=True)
class StressScenario:
    code: str
    name: str
    description: str
    shocks: Sequence[StressShock]
    duration_years: int | None = None
    probability: float | None = None
    category: str = "base"


class StressScenarioLibrary:
    """Catalog of deterministic stress scenarios and combined variants."""

    def __init__(self):
        self.base_scenarios = self._build_base()
        self.combined_scenarios = self._build_combinations(self.base_scenarios)
        self.tokenization_scenarios = self._build_tokenization()
        self.upside_scenarios = self._build_upside()

    def list_all(self, include_tokenization: bool = True) -> Dict[str, StressScenario]:
        scenarios = {**self.base_scenarios, **self.combined_scenarios}
        if include_tokenization:
            scenarios.update(self.tokenization_scenarios)
        scenarios.update(self.upside_scenarios)
        return scenarios

    def get(self, code: str) -> StressScenario:
        library = self.list_all()
        if code not in library:
            raise KeyError(f"Unknown stress scenario '{code}'.")
        return library[code]

    def _build_base(self) -> Dict[str, StressScenario]:
        return {
            "S1": StressScenario(
                code="S1",
                name="Demanda débil",
                description="Caída de ingresos y mayor churn por retrasos comerciales.",
                duration_years=3,
                probability=0.15,
                shocks=[
                    StressShock("revenue_growth", "add", -0.02, "Ingresos -200 bps"),
                    StressShock("churn_rate", "add", 0.0125, "Churn +125 bps"),
                ],
            ),
            "S2": StressScenario(
                code="S2",
                name="Shock de tasas",
                description="Incremento paralelo de curva de +200 bps.",
                duration_years=2,
                probability=0.10,
                shocks=[
                    StressShock("rate_shock", "add", 0.02, "Curva +200 bps"),
                ],
            ),
            "S3": StressScenario(
                code="S3",
                name="Fallo de lanzamiento",
                description="Evento binario de fallo crítico de lanzamiento satelital.",
                duration_years=1,
                probability=0.07,
                shocks=[
                    StressShock("launch_failure", "add", 1.0, "Probabilidad de fallo 100%"),
                    StressShock("revenue_growth", "add", -0.01, "Demora en revenue ramp"),
                ],
            ),
            "S4": StressScenario(
                code="S4",
                name="Degradación operativa",
                description="OPEX + inflación por degradación de flota/terreno.",
                duration_years=4,
                probability=0.12,
                shocks=[
                    StressShock("opex_inflation", "add", 0.01, "Inflación OPEX +100 bps"),
                    StressShock("maintenance_capex", "add", 0.015, "RCAPEX diet +150 bps"),
                ],
            ),
            "S5": StressScenario(
                code="S5",
                name="Regulatorio adverso",
                description="Licencias demoradas y presión fiscal.",
                duration_years=2,
                probability=0.05,
                shocks=[
                    StressShock("revenue_growth", "add", -0.01, "Demoras por licencias"),
                    StressShock("tax_rate", "add", 0.02, "Impuesto efectivo +200 bps"),
                ],
            ),
            "S6": StressScenario(
                code="S6",
                name="CAPEX overrun",
                description="RCAPEX inesperado 25M vs MRA 12M (gap 13M).",
                duration_years=1,
                probability=0.08,
                shocks=[
                    StressShock("capex_overrun", "add", 25.0, "CAPEX adicional (MMUSD)"),
                    StressShock("mra_shortfall", "add", -12.0, "MRA disponible"),
                ],
            ),
        }

    def _build_combinations(self, base: Dict[str, StressScenario]) -> Dict[str, StressScenario]:
        combos: Dict[str, StressScenario] = {}

        def merge_shocks(*codes: str) -> List[StressShock]:
            combined: List[StressShock] = []
            for code in codes:
                combined.extend(base[code].shocks)
            return combined

        combos["C1"] = StressScenario(
            code="C1",
            name="Perfect Storm",
            description="Demanda débil + shock de tasas + fallo de lanzamiento.",
            shocks=merge_shocks("S1", "S2", "S3"),
            category="combined",
        )
        combos["C2"] = StressScenario(
            code="C2",
            name="Launch + Rates",
            description="Fallo de lanzamiento + shock de tasas.",
            shocks=merge_shocks("S2", "S3"),
            category="combined",
        )
        combos["C3"] = StressScenario(
            code="C3",
            name="Operational Cascade",
            description="Demanda débil + degradación OPEX + CAPEX overrun.",
            shocks=merge_shocks("S1", "S4", "S6"),
            category="combined",
        )
        return combos

    def _build_tokenization(self) -> Dict[str, StressScenario]:
        tok: Dict[str, StressScenario] = {}
        tok["T1"] = StressScenario(
            code="T1",
            name="DeFi Liquidity Crisis",
            description="Secondary market freeze with smart contract concerns.",
            shocks=[
                StressShock("secondary_market_depth", "mult", -0.90, "90% reduction in depth"),
                StressShock("smart_contract_risk", "add", 0.05, "Elevated smart contract failure probability"),
            ],
            duration_years=1,
            probability=0.03,
            category="tokenization",
        )
        tok["T2"] = StressScenario(
            code="T2",
            name="Smart Contract Exploit",
            description="Critical vulnerability discovered in token contract.",
            shocks=[
                StressShock("smart_contract_risk", "add", 1.0, "Certain failure event"),
                StressShock("secondary_market_depth", "mult", -0.50, "50% depth reduction"),
            ],
            duration_years=1,
            probability=0.005,
            category="tokenization",
        )
        tok["T3"] = StressScenario(
            code="T3",
            name="Security Token Regulatory Ban",
            description="Regulatory prohibition on security token trading.",
            shocks=[
                StressShock("secondary_market_depth", "mult", -1.0, "Complete market closure"),
                StressShock("regulatory_delay", "add", 1.0, "Regulatory trigger"),
            ],
            duration_years=2,
            probability=0.02,
            category="tokenization",
        )
        tok["CT1"] = StressScenario(
            code="CT1",
            name="Perfect Token Storm",
            description="DeFi crisis + traditional demand shock.",
            shocks=[
                StressShock("secondary_market_depth", "mult", -0.90),
                StressShock("smart_contract_risk", "add", 0.05),
                StressShock("revenue_growth", "add", -0.02),
                StressShock("churn_rate", "add", 0.0125),
            ],
            duration_years=2,
            probability=0.01,
            category="combined_tokenization",
        )
        return tok

    def _build_upside(self) -> Dict[str, StressScenario]:
        up: Dict[str, StressScenario] = {}
        up["U1"] = StressScenario(
            code="U1",
            name="Competitor Exit",
            description="Major competitor exits LEO IoT market.",
            shocks=[
                StressShock("revenue_growth", "mult", 0.15, "Market share gain +15%"),
                StressShock("churn_rate", "mult", -0.50, "Churn halved"),
            ],
            probability=0.05,
            category="upside",
        )
        up["U2"] = StressScenario(
            code="U2",
            name="Spectrum Award",
            description="Favorable spectrum award accelerates uptake.",
            shocks=[
                StressShock("revenue_growth", "mult", 0.10, "Revenue +10%"),
                StressShock("regulatory_delay", "add", -1.0, "Regulatory delay removed"),
            ],
            probability=0.08,
            category="upside",
        )
        up["U3"] = StressScenario(
            code="U3",
            name="Technology Breakthrough",
            description="Operational efficiency gains from tech upgrade.",
            shocks=[
                StressShock("opex_inflation", "mult", -0.20, "OPEX inflation -20%"),
                StressShock("satellite_degradation", "mult", -0.50, "Degradation -50%"),
            ],
            probability=0.03,
            category="upside",
        )
        return up


__all__ = ["StressScenario", "StressScenarioLibrary", "StressShock"]
