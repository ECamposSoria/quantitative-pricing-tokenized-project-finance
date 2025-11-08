import pytest


EXPECTED_CFADS = {
    1: -0.6,
    2: -1.2,
    3: 0.3,
    4: 5.0,
    5: 12.4,
    6: 18.0,
    7: 22.1,
    8: 24.1,
    9: 25.3,
    10: 22.8,
    11: 21.0,
    12: 19.7,
    13: 17.4,
    14: 15.2,
    15: 13.0,
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
    assert total == pytest.approx(214.5, abs=0.01)
