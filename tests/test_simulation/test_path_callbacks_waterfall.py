import numpy as np
import pandas as pd

from pftoken.simulation.path_callbacks import (
    _vectorized_tranche_cashflows,
    build_financial_path_callback,
)
from pftoken.waterfall.debt_structure import DebtStructure, Tranche


def _debt_structure():
    return DebtStructure(
        [
            Tranche(name="Senior", principal=100, rate=0.06, seniority=1, tenor_years=5, grace_period_years=0, amortization_style="sculpted"),
            Tranche(name="Mezz", principal=50, rate=0.08, seniority=2, tenor_years=5, grace_period_years=0, amortization_style="sculpted"),
        ]
    )


def _debt_schedule():
    data = [
        {"year": 1, "tranche_name": "Senior", "interest_due": 6, "principal_due": 20},
        {"year": 1, "tranche_name": "Mezz", "interest_due": 4, "principal_due": 10},
        {"year": 2, "tranche_name": "Senior", "interest_due": 5, "principal_due": 20},
        {"year": 2, "tranche_name": "Mezz", "interest_due": 3, "principal_due": 10},
    ]
    return pd.DataFrame(data)


def test_vectorized_cashflows_sum_to_cfads_when_sufficient():
    debt_structure = _debt_structure()
    schedule = _debt_schedule()
    years = [1, 2]
    shocked_cfads = np.array([[100.0, 100.0]])
    cashflows = _vectorized_tranche_cashflows(
        shocked_cfads,
        schedule,
        debt_structure,
        years,
        usd_per_million=1.0,
    )
    total_paid = sum(cashflows[t] for t in cashflows)
    expected = schedule.groupby("year")[["interest_due", "principal_due"]].sum().sum(axis=1).to_numpy()
    np.testing.assert_allclose(total_paid[0], expected)


def test_vectorized_cashflows_shortfall_allocation():
    debt_structure = _debt_structure()
    schedule = _debt_schedule()
    years = [1, 2]
    shocked_cfads = np.array([[30.0, 30.0]])  # insufficient vs total scheduled 50/38
    cashflows = _vectorized_tranche_cashflows(
        shocked_cfads,
        schedule,
        debt_structure,
        years,
        usd_per_million=1.0,
    )
    # Senior gets paid first, Mezz gets residual (possibly zero)
    senior_pay = cashflows["Senior"]
    mezz_pay = cashflows["Mezz"]
    assert np.all(senior_pay >= 0)
    assert np.all(mezz_pay >= 0)
    assert np.all(senior_pay + mezz_pay <= shocked_cfads)
    # Senior absorbs most of the shortfall
    assert senior_pay[0, 0] > mezz_pay[0, 0]


def test_senior_tranche_paid_first():
    debt_structure = _debt_structure()
    schedule = _debt_schedule()
    years = [1, 2]
    shocked_cfads = np.array([[10.0, 0.0]])  # tiny CFADS
    cashflows = _vectorized_tranche_cashflows(
        shocked_cfads,
        schedule,
        debt_structure,
        years,
        usd_per_million=1.0,
    )
    assert cashflows["Mezz"][0, 0] == 0.0
    assert cashflows["Senior"][0, 0] == min(10.0, schedule.query("tranche_name == 'Senior' and year == 1")[["interest_due", "principal_due"]].sum(axis=1).iloc[0])


def test_cashflows_shape_matches_simulations():
    debt_structure = _debt_structure()
    schedule = _debt_schedule()
    years = [1, 2]
    shocked_cfads = np.ones((5, 2)) * 50.0
    cashflows = _vectorized_tranche_cashflows(
        shocked_cfads,
        schedule,
        debt_structure,
        years,
        usd_per_million=1.0,
    )
    assert cashflows["Senior"].shape == (5, 2)
    assert cashflows["Mezz"].shape == (5, 2)


def test_callback_with_waterfall_enabled():
    debt_structure = _debt_structure()
    schedule = _debt_schedule()
    years = [1, 2]
    baseline_cfads = {1: 100.0, 2: 100.0}
    callback = build_financial_path_callback(
        baseline_cfads,
        schedule,
        years,
        base_discount_rate=0.05,
        debt_structure=debt_structure,
        include_tranche_cashflows=True,
        launch_failure_impact=0.0,
        usd_per_million=1.0,
        grace_period_years=0,
    )
    batch = {"revenue_growth": np.ones(3)}
    derived = callback(batch)
    assert "tranche_cashflows" in derived
    assert "Senior" in derived["tranche_cashflows"]
    assert derived["tranche_cashflows"]["Senior"].shape == (3, len(years))
