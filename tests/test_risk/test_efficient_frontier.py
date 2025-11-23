import numpy as np

from pftoken.risk.efficient_frontier import EfficientFrontierAnalysis


def test_efficient_frontier_marks_dominated_portfolio():
    names = ["S", "M"]
    tranche_returns = {"S": 0.05, "M": 0.08}
    loss_scenarios = np.array(
        [
            [1.0, 2.0],
            [1.0, 2.0],
            [1.0, 2.0],
            [5.0, 1.0],
        ]
    )
    weights = np.array([[0.5, 0.5], [0.2, 0.8]])
    ef = EfficientFrontierAnalysis(names)
    points = ef.evaluate(weights, tranche_returns, loss_scenarios, risk_metric="var", alpha=0.75)

    assert len(points) == 2
    # Second portfolio has higher return and lower risk → efficient
    assert points[0].is_efficient is False
    assert points[1].is_efficient is True
