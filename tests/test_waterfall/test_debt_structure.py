import pytest

from pftoken.models import ProjectParameters
from pftoken.waterfall import DebtStructure


def test_debt_structure_from_tranches(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    assert len(debt_structure.tranches) == 3
    assert debt_structure.tranches[0].name == "senior"
    # Updated to match current LEO IoT project structure (50M post-deleveraging)
    assert pytest.approx(debt_structure.total_principal) == 50_000_000


def test_debt_structure_wacd(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    wacd = debt_structure.calculate_wacd(include_spreads=True)
    # WACD with coupon-inclusive rates (6.0% / 8.5% / 11.0%)
    assert pytest.approx(wacd, rel=1e-4) == 0.07375
