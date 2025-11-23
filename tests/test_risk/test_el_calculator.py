import numpy as np
import pytest

from pftoken.risk.el_calculator import AggregateInputs, AggregateRiskCalculator


def test_correlated_loss_simulation_identity_correlation():
    names = ["S", "M", "E"]
    inputs = AggregateInputs(
        pd={"S": 0.01, "M": 0.03, "E": 0.10},
        lgd={"S": 0.4, "M": 0.55, "E": 1.0},
        ead={"S": 60.0, "M": 25.0, "E": 15.0},
        correlation=np.eye(3),
        simulations=2000,
        seed=1,
    )
    calc = AggregateRiskCalculator(names)
    losses = calc.simulate_losses(inputs)
    assert losses.shape == (inputs.simulations, len(names))
    summary = calc.summarize_portfolio(losses)
    # Mean loss should be positive and below deterministic worst case
    assert summary.portfolio_mean_loss > 0
    assert summary.portfolio_var_99 >= summary.portfolio_var_95
    contributions = calc.contribution_table(losses)
    assert pytest.approx(sum(contributions.values()), rel=1e-6, abs=1e-6) == 1.0


def test_correlation_matrix_with_ones_is_bumped_to_spd():
    names = ["S", "M", "E"]
    corr = np.ones((3, 3))
    inputs = AggregateInputs(
        pd={"S": 0.02, "M": 0.02, "E": 0.02},
        lgd={"S": 0.5, "M": 0.5, "E": 0.5},
        ead={"S": 10.0, "M": 10.0, "E": 10.0},
        correlation=corr,
        simulations=1000,
        seed=11,
    )
    calc = AggregateRiskCalculator(names)
    losses = calc.simulate_losses(inputs)
    # Perfect correlation should produce identical default flags across tranches
    default_counts = losses > 0
    row_sums = default_counts.sum(axis=1)
    assert np.all((row_sums == 0) | (row_sums == len(names)))
