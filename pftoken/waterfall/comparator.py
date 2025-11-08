"""Traditional vs. tokenized debt structure comparison utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .debt_structure import DebtStructure


@dataclass(frozen=True)
class ComparisonResult:
    wacd_traditional: float
    wacd_tokenized: float
    delta_wacd_bps: float
    concentration_traditional: float
    concentration_tokenized: float
    recommendation: str


class StructureComparator:
    """Compare legacy banking structures with tokenized multi-tranche designs."""

    def __init__(self, traditional_wacd: float = 0.078, traditional_hhi: float = 0.65):
        self.traditional_wacd = traditional_wacd
        self.traditional_hhi = traditional_hhi

    @staticmethod
    def _herfindahl_index(debt_structure: DebtStructure) -> float:
        total = debt_structure.total_principal
        if total <= 0:
            return 0.0
        shares = [(tranche.principal / total) for tranche in debt_structure.tranches]
        return sum(share**2 for share in shares)

    def compare(self, debt_structure: DebtStructure) -> ComparisonResult:
        tokenized_wacd = debt_structure.calculate_wacd()
        tokenized_hhi = self._herfindahl_index(debt_structure)
        delta_wacd_bps = (self.traditional_wacd - tokenized_wacd) * 10_000
        recommendation = (
            "Tokenization beneficial if WACD delta realized"
            if delta_wacd_bps >= 0
            else "Traditional cheaper under supplied inputs"
        )
        return ComparisonResult(
            wacd_traditional=self.traditional_wacd,
            wacd_tokenized=tokenized_wacd,
            delta_wacd_bps=delta_wacd_bps,
            concentration_traditional=self.traditional_hhi,
            concentration_tokenized=tokenized_hhi,
            recommendation=recommendation,
        )


__all__ = ["StructureComparator", "ComparisonResult"]
