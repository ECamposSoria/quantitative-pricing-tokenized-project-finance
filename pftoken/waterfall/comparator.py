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
    dsra_coverage_ratio: float
    mra_funding_ratio: float


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

    def compare(
        self,
        debt_structure: DebtStructure,
        *,
        dsra_target: float | None = None,
        dsra_balance: float | None = None,
        mra_target: float | None = None,
        mra_balance: float | None = None,
    ) -> ComparisonResult:
        tokenized_wacd = debt_structure.calculate_wacd()
        tokenized_hhi = self._herfindahl_index(debt_structure)
        delta_wacd_bps = (self.traditional_wacd - tokenized_wacd) * 10_000
        recommendation = (
            "Tokenization beneficial if WACD delta realized"
            if delta_wacd_bps >= 0
            else "Traditional cheaper under supplied inputs"
        )
        dsra_target = dsra_target or 0.0
        dsra_balance = dsra_balance or 0.0
        mra_target = mra_target or 0.0
        mra_balance = mra_balance or 0.0
        dsra_ratio = 0.0 if dsra_target == 0 else min(dsra_balance / dsra_target, 1.5)
        mra_ratio = 0.0 if mra_target == 0 else min(mra_balance / mra_target, 1.5)
        return ComparisonResult(
            wacd_traditional=self.traditional_wacd,
            wacd_tokenized=tokenized_wacd,
            delta_wacd_bps=delta_wacd_bps,
            concentration_traditional=self.traditional_hhi,
            concentration_tokenized=tokenized_hhi,
            recommendation=recommendation,
            dsra_coverage_ratio=dsra_ratio,
            mra_funding_ratio=mra_ratio,
        )


__all__ = ["StructureComparator", "ComparisonResult"]
