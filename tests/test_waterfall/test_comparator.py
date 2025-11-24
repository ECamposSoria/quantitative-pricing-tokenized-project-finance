import pytest

from pftoken.models import ProjectParameters
from pftoken.waterfall import DebtStructure, StructureComparator


def test_structure_comparator_returns_delta(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    comparator = StructureComparator()
    result = comparator.compare(
        debt_structure,
        dsra_target=9_000_000,
        dsra_balance=9_000_000,
        mra_target=4_000_000,
        mra_balance=3_900_000,
    )
    assert result.delta_wacd_bps is not None
    assert result.wacd_traditional > 0 and result.wacd_tokenized > 0
    assert result.concentration_tokenized < result.concentration_traditional
    assert result.dsra_coverage_ratio == pytest.approx(1.0, abs=1e-6)
    assert result.mra_funding_ratio == pytest.approx(0.975, abs=1e-6)
