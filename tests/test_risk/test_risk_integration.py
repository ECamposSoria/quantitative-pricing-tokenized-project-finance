import numpy as np

from pftoken.pipeline import FinancialPipeline


def test_pipeline_includes_risk_metrics_when_requested():
    pipeline = FinancialPipeline(data_dir="data/input/leo_iot")
    risk_inputs = {
        "pd": {"senior": 0.01, "mezzanine": 0.03, "subordinated": 0.10},
        "lgd": {"senior": 0.4, "mezzanine": 0.55, "subordinated": 1.0},
        "correlation": np.eye(3),
        "simulations": 500,
        "seed": 123,
    }
    result = pipeline.run(include_risk=True, risk_inputs=risk_inputs)
    assert "risk_metrics" in result
    assert result["risk_metrics"] is not None
    assert "tranches" in result["risk_metrics"]
    assert len(result["risk_metrics"]["tranches"]) == 3
