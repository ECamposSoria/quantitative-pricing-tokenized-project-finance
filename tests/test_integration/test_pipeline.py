from pftoken.pipeline import FinancialPipeline
from pftoken.models import ProjectParameters


def test_financial_pipeline_run(project_parameters: ProjectParameters):
    pipeline = FinancialPipeline(params=project_parameters)
    results = pipeline.run()
    assert "cfads" in results
    assert "waterfall" in results
    assert len(results["waterfall"]) == project_parameters.project.tenor_years
