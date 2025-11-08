from pftoken.models import ProjectParameters
from pftoken.waterfall import DebtStructure, StructureComparator


def test_structure_comparator_returns_delta(project_parameters: ProjectParameters):
    debt_structure = DebtStructure.from_tranche_params(project_parameters.tranches)
    comparator = StructureComparator()
    result = comparator.compare(debt_structure)
    assert result.delta_wacd_bps >= 0  # tokenized estructura más barata
    assert result.concentration_tokenized < result.concentration_traditional
