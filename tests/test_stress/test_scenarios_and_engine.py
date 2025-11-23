from pftoken.stress.results_analyzer import StressResultsAnalyzer
from pftoken.stress.scenarios import StressScenarioLibrary
from pftoken.stress.stress_engine import StressRunResult, StressTestEngine


def test_scenario_library_contains_catalog():
    lib = StressScenarioLibrary()
    all_codes = set(lib.list_all().keys())
    assert {"S1", "S6", "C1", "C3"}.issubset(all_codes)


def test_stress_engine_applies_shocks_and_ranks():
    lib = StressScenarioLibrary()
    baseline_inputs = {"revenue_growth": 0.06}
    baseline_metrics = {"dscr_min": 1.3}
    engine = StressTestEngine(baseline_inputs, baseline_metrics)

    scenario = lib.get("S1")
    stressed_inputs = engine.apply_stress_scenario(scenario)
    assert stressed_inputs["revenue_growth"] < baseline_inputs["revenue_growth"]

    def runner(inputs):
        return {"dscr_min": baseline_metrics["dscr_min"] + inputs["revenue_growth"] - baseline_inputs["revenue_growth"]}

    run = engine.run_stressed_simulation(scenario, runner)
    analyzer = StressResultsAnalyzer()
    ranked = analyzer.rank_by_metric([run], metric="dscr_min")
    assert ranked[0].code == "S1"
