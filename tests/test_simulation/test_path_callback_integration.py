import numpy as np

from pftoken.pipeline import FinancialPipeline
from pftoken.simulation import (
    MonteCarloConfig,
    MonteCarloPipeline,
    PipelineInputs,
    build_financial_path_callback,
)


def test_financial_path_callback_shapes():
    fp = FinancialPipeline(data_dir="data/input/leo_iot")
    cfads = fp.cfads_calculator.calculate_cfads_vector()
    years = [y for y in sorted(cfads.keys()) if y <= fp.params.project.tenor_years]

    callback = build_financial_path_callback(
        baseline_cfads=cfads,
        debt_schedule=fp.params.debt_schedule,
        years=years,
        base_discount_rate=fp.params.project.base_rate_reference,
        grace_period_years=fp.params.project.grace_period_years,
    )

    debt_by_tranche = {t.name: t.principal / 1_000_000.0 for t in fp.debt_structure.tranches}
    mc_config = MonteCarloConfig(simulations=10, seed=1, antithetic=True)
    inputs = PipelineInputs(
        debt_by_tranche=debt_by_tranche,
        discount_rate=fp.params.project.base_rate_reference,
        horizon_years=fp.params.project.tenor_years,
        tranche_ead=debt_by_tranche,
        dscr_threshold=fp.params.project.min_dscr_covenant,
        llcr_threshold=fp.params.project.min_llcr_covenant,
    )
    pipeline = MonteCarloPipeline(mc_config, inputs, path_callback=callback)
    outputs = pipeline.run_complete_analysis()

    dscr_paths = outputs.monte_carlo.derived["dscr_paths"]
    assert dscr_paths.shape == (10, len(years))
    finite_mask = ~np.isnan(dscr_paths)
    assert np.isfinite(dscr_paths[finite_mask]).all()
    finite_values = dscr_paths[finite_mask]
    if finite_values.size:
        median_dscr = np.percentile(finite_values, 50)
        assert median_dscr > 0.8, "Median DSCR too low"
        assert median_dscr < 2.5, "Median DSCR unrealistically high"
    assert outputs.pd_lgd_paths is not None
