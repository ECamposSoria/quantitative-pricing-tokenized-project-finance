import pytest


EXPECTED_CFADS = {
    1: -0.6,
    2: -1.2,
    3: 0.3,
    4: 5.0,
    5: 12.4,
    6: 16.8,
    7: 20.6,
    8: 22.45,
    9: 23.6,
    10: 21.25,
    11: 17.6,
    12: 17.45,
    13: 15.4,
    14: 13.7,
    15: 11.75,
}


def test_cfads_year_1(cfads_calculator):
    vector = cfads_calculator.calculate_cfads_vector()
    assert vector[1] == pytest.approx(EXPECTED_CFADS[1], abs=0.01)


def test_cfads_year_5(cfads_calculator):
    vector = cfads_calculator.calculate_cfads_vector()
    assert vector[5] == pytest.approx(12.4, abs=0.01)


def test_cfads_sum_matches_spec(cfads_calculator):
    vector = cfads_calculator.calculate_cfads_vector()
    total = sum(vector.values())
    assert total == pytest.approx(196.5, abs=0.01)
