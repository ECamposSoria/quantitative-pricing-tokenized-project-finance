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
    assert _relative_error(dscr[4]["value"], 1.3559322033898304) <= 1e-4
    assert _relative_error(dscr[5]["value"], 1.5061420838568895) <= 1e-4

    # Interest schedule reconciliation for year 5 senior tranche
    year5 = results["waterfall"][5]
    assert year5.interest_payments["senior"] > 0
    assert year5.principal_payments["senior"] > 0
