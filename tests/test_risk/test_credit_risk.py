import numpy as np

from pftoken.risk.credit_risk import RiskInputs, RiskMetricsCalculator


def test_tranche_el_var_cvar_and_marginal():
    tranche_names = ["Senior", "Mezz", "Equity"]
    pd = {"Senior": 0.01, "Mezz": 0.03, "Equity": 0.10}
    lgd = {"Senior": 0.40, "Mezz": 0.55, "Equity": 1.00}
    ead = {"Senior": 60.0, "Mezz": 25.0, "Equity": 15.0}

    # Stable quantiles: columns repeat same non-zero values
    loss_scenarios = np.array(
        [
            [0.0, 0.0, 0.0],
            [10.0, 5.0, 15.0],
            [10.0, 5.0, 15.0],
            [10.0, 5.0, 15.0],
            [10.0, 5.0, 15.0],
        ]
    )
    inputs = RiskInputs(pd=pd, lgd=lgd, ead=ead, loss_scenarios=loss_scenarios, simulations=100, seed=7)

    calc = RiskMetricsCalculator(tranche_names)
    results = {r.tranche: r for r in calc.tranche_results(inputs)}

    expected_el = calc.calculate_expected_loss(pd, lgd, ead)
    assert set(results) == set(tranche_names)
    assert results["Senior"].el == expected_el["Senior"]
    assert results["Mezz"].el == expected_el["Mezz"]
    assert results["Equity"].el == expected_el["Equity"]

    assert results["Senior"].var_95 == 10.0
    assert results["Mezz"].var_95 == 5.0
    assert results["Equity"].var_95 == 15.0
    assert results["Senior"].cvar_95 == 10.0
    assert results["Mezz"].cvar_95 == 5.0
    assert results["Equity"].cvar_95 == 15.0

    # Marginal contributions follow tail expectation by column
    assert results["Senior"].marginal_contribution == 10.0
    assert results["Mezz"].marginal_contribution == 5.0
    assert results["Equity"].marginal_contribution == 15.0
