import pytest

from pftoken.models import ProjectParameters
from pftoken.waterfall import DebtStructure


def test_debt_structure_from_tranches(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    assert len(debt_structure.tranches) == 3
    assert debt_structure.tranches[0].name == "senior"
    assert pytest.approx(debt_structure.total_principal) == 72_000_000


def test_debt_structure_wacd(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    wacd = debt_structure.calculate_wacd()
    assert pytest.approx(wacd, rel=1e-4) == 0.1185
