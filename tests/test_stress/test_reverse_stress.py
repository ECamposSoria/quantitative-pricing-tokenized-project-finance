from pftoken.stress.reverse_stress import ReverseStressTester


def test_reverse_stress_breaking_point_binary():
    tester = ReverseStressTester(tolerance=1e-3, max_iter=20)

    def evaluate(shock):
        # Metric decreases with shock; breach when <= 0.5
        return 1.0 - shock

    result = tester.find_breaking_point(evaluate, target=0.5, low=0.0, high=1.0)
    assert 0.49 <= result.shocks["shock"] <= 0.51
    assert result.target == 0.5


def test_reverse_stress_minimal_combo():
    tester = ReverseStressTester()

    def evaluate(combo):
        return 1.0 - sum(combo.values())

    shock_levels = {"a": [0.1, 0.2], "b": [0.1, 0.2]}
    result = tester.identify_minimal_fatal_combo(evaluate, shock_levels=shock_levels, target=0.7)
    # Minimal sum that breaches 0.7 should be ~0.3
    assert abs(sum(result.shocks.values()) - 0.3) < 1e-6
