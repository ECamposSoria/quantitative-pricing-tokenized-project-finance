from pftoken.pipeline import FinancialPipeline
from pftoken.models import ProjectParameters


def _relative_error(modeled: float, baseline: float) -> float:
    if baseline == 0:
        return abs(modeled - baseline)
    return abs((modeled - baseline) / baseline)


def test_pipeline_end_to_end(project_parameters: ProjectParameters):
    pipeline = FinancialPipeline(params=project_parameters)
    results = pipeline.run()

    assert set(["cfads", "dscr", "waterfall", "structure_comparison"]).issubset(results.keys())
    assert len(results["waterfall"]) == project_parameters.project.tenor_years

    # DSCR tolerance vs Excel baseline
    dscr = results["dscr"]
    assert _relative_error(dscr[4]["value"], 0.941619586) <= 1e-4
    assert _relative_error(dscr[5]["value"], 1.45) <= 1e-4

    # Interest schedule reconciliation for year 5 senior tranche
    year5 = results["waterfall"][5]
    assert _relative_error(year5.interest_payments["senior"], 2_592_000.0) <= 1e-4
    assert _relative_error(year5.principal_payments["senior"], 2_269_207.0) <= 1e-4
