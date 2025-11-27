from pftoken.pipeline import FinancialPipeline
from pftoken.constants import TOKENIZED_OPTIMAL_STRUCTURE


def _make_pipeline_stub() -> FinancialPipeline:
    """Create a lightweight pipeline instance without full init."""

    stub = FinancialPipeline.__new__(FinancialPipeline)
    return stub


def test_structure_comparison_quantifies_inefficiency():
    pipe = _make_pipeline_stub()
    frontier = {
        "current_structure_evaluation": {
            "expected_return": 0.0753,
            "risk": 2.60,
            "is_efficient": False,
        },
        "efficient": [
            {
                "expected_return": 0.0861,
                "risk": 2.61,
                "weights": {"senior": 0.03, "mezzanine": 0.91, "subordinated": 0.06},
            }
        ],
    }
    risk_inputs = {
        "compare_structures": True,
        "tokenization_spread_reduction_bps": 50,
        "traditional_constraints": {"min_senior_pct": 0.55, "max_sub_pct": 0.20},
    }
    result = pipe._structure_comparison(
        tranche_names=["senior", "mezzanine", "subordinated"],
        risk_inputs=risk_inputs,
        frontier_result=frontier,
    )
    comparison = result["structure_comparison"]
    assert comparison["traditional"]["locked_inefficiency_bps"] == 108
    assert comparison["delta"]["total_tokenization_benefit_bps"] == 158
    assert comparison["tokenized"]["target_structure"]["mezzanine"] == 0.91
    assert comparison["tokenized"]["constraint_check"]["violates_constraints"] is True


def test_structure_comparison_zero_gap_for_efficient():
    pipe = _make_pipeline_stub()
    frontier = {
        "current_structure_evaluation": {
            "expected_return": 0.08,
            "risk": 2.5,
            "is_efficient": True,
        },
        "efficient": [
            {
                "expected_return": 0.08,
                "risk": 2.5,
                "weights": {"senior": 0.6, "mezzanine": 0.25, "subordinated": 0.15},
            }
        ],
    }
    risk_inputs = {"compare_structures": True}
    comparison = pipe._structure_comparison(
        tranche_names=["senior", "mezzanine", "subordinated"],
        risk_inputs=risk_inputs,
        frontier_result=frontier,
    )["structure_comparison"]
    assert comparison["traditional"]["locked_inefficiency_bps"] == 0
    assert comparison["tokenized"]["recoverable_value_bps"] == 0


def test_structure_comparison_contains_recommended_structure():
    pipe = _make_pipeline_stub()
    frontier = {
        "current_structure_evaluation": {
            "expected_return": 0.0753,
            "risk": 2.60,
            "is_efficient": False,
        },
        "efficient": [
            {
                "expected_return": 0.0861,
                "risk": 2.61,
                "weights": {"senior": 0.03, "mezzanine": 0.91, "subordinated": 0.06},
            }
        ],
    }
    risk_inputs = {
        "compare_structures": True,
        "tokenization_spread_reduction_bps": 50,
        "traditional_constraints": {"min_senior_pct": 0.55, "max_sub_pct": 0.20},
    }
    comparison = pipe._structure_comparison(
        tranche_names=["senior", "mezzanine", "subordinated"],
        risk_inputs=risk_inputs,
        frontier_result=frontier,
    )["structure_comparison"]
    recommended = comparison["tokenized"]["recommended_structure"]
    assert recommended == TOKENIZED_OPTIMAL_STRUCTURE
