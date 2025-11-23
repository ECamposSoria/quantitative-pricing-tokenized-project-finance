import numpy as np
import pytest

from pftoken.risk.var_cvar import TailRiskAnalyzer


def test_empirical_var_cvar_matches_numpy():
    losses = np.arange(10, dtype=float)
    analyzer = TailRiskAnalyzer()
    res = analyzer.analyze_empirical(losses, levels=(0.9,))
    expected_var = np.quantile(losses, 0.9)
    expected_cvar = float(np.mean(losses[losses >= expected_var]))

    assert res.var_levels[0.9] == pytest.approx(expected_var)
    assert res.cvar_levels[0.9] == pytest.approx(expected_cvar)


def test_gpd_fallback_when_tail_too_small():
    losses = np.linspace(0.0, 1.0, 10)
    analyzer = TailRiskAnalyzer(min_tail_samples=20)
    fit = analyzer.fit_gpd(losses, threshold_quantile=0.8)

    assert fit.distribution == "empirical"
    assert fit.ks_pvalue is None
    assert fit.qq_residuals.size == 0
