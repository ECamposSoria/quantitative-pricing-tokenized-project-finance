import pytest

from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def test_debt_structure_to_from_dicts_roundtrip():
    tranches = [
        Tranche(
            name="Senior",
            principal=43_200_000,
            rate=0.06,
            seniority=1,
            tenor_years=15,
            grace_period_years=4,
            amortization_style="sculpted",
            spread_bps=100,
            rate_base_type="sofr",
        ),
        Tranche(
            name="Mezz",
            principal=18_000_000,
            rate=0.085,
            seniority=2,
            tenor_years=12,
            grace_period_years=3,
            amortization_style="sculpted",
            spread_bps=350,
            rate_base_type="sofr",
        ),
    ]
    structure = DebtStructure(tranches)
    serialized = structure.to_dicts()

    rebuilt = DebtStructure.from_dicts(serialized)
    assert [t.name for t in rebuilt.tranches] == ["Senior", "Mezz"]
    assert pytest.approx(rebuilt.tranches[0].rate) == 0.06
    assert rebuilt.tranches[0].spread_bps == 100
    assert rebuilt.tranches[1].tenor_years == 12
