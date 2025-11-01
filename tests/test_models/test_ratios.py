"""
Comprehensive tests for T-004: Financial coverage ratios (DSCR/LLCR/PLCR).
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pftoken.models.cfads import CFADSScenarioInputs
from pftoken.models.params import ProjectParameters
from pftoken.models.ratios import (
    CoverageRatioResult,
    CoverageRatioResults,
    calculate_coverage_ratios,
    compute_dscr,
    compute_llcr,
    compute_plcr,
    compute_remaining_debt,
    extract_debt_service,
    present_value,
)


class TestPresentValue:
    """Test present value calculation with t=1 start."""

    def test_empty_cashflows(self):
        """Empty cashflow array returns 0."""
        result = present_value(np.array([]), 0.1)
        assert result == 0.0

    def test_single_cashflow(self):
        """Single cashflow discounted by (1+r)^1."""
        # 100 / (1.1)^1 = 90.909...
        result = present_value(np.array([100.0]), 0.1)
        expected = 100.0 / 1.1
        assert abs(result - expected) < 1e-6

    def test_multiple_cashflows(self):
        """Multiple cashflows discounted from t=1, t=2, ..."""
        # CF1=100, CF2=100, CF3=100 at r=10%
        # PV = 100/1.1 + 100/1.1^2 + 100/1.1^3
        cashflows = np.array([100.0, 100.0, 100.0])
        result = present_value(cashflows, 0.1)
        expected = 100/1.1 + 100/(1.1**2) + 100/(1.1**3)
        assert abs(result - expected) < 1e-6

    def test_zero_discount_rate(self):
        """Zero discount rate returns sum of cashflows."""
        cashflows = np.array([100.0, 200.0, 300.0])
        result = present_value(cashflows, 0.0)
        # With r=0, all cashflows are at "present" value
        # But we still divide by (1+0)^t = 1, so sum is unchanged
        expected = 600.0
        assert abs(result - expected) < 1e-6


class TestComputeDSCR:
    """Test DSCR calculation."""

    def test_normal_case(self):
        """DSCR = CFADS / debt_service."""
        cfads = np.array([1000.0, 1200.0, 1500.0])
        debt_service = np.array([800.0, 1000.0, 1200.0])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_dscr(cfads, debt_service, warn=False)

        expected = np.array([1.25, 1.2, 1.25])
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_zero_debt_service(self):
        """Zero debt service returns np.inf (grace period)."""
        cfads = np.array([1000.0, 1200.0])
        debt_service = np.array([0.0, 1000.0])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_dscr(cfads, debt_service, warn=False)

        assert result[0] == np.inf
        assert abs(result[1] - 1.2) < 1e-6

    def test_dscr_below_one_warning(self):
        """DSCR < 1 triggers warning."""
        cfads = np.array([800.0, 1200.0])
        debt_service = np.array([1000.0, 1000.0])

        with pytest.warns(UserWarning, match="DSCR.*períodos.*Incumplimiento técnico"):
            compute_dscr(cfads, debt_service, min_threshold=1.0, warn=True)

    def test_negative_cfads_warning(self):
        """Negative CFADS triggers warning."""
        cfads = np.array([-100.0, 1200.0])
        debt_service = np.array([1000.0, 1000.0])

        with pytest.warns(UserWarning, match="CFADS negativo"):
            compute_dscr(cfads, debt_service, warn=True)


class TestComputeLLCR:
    """Test LLCR calculation."""

    def test_normal_case(self):
        """LLCR = PV(future CFADS) / debt_outstanding."""
        cfads_future = np.array([1000.0, 1000.0, 1000.0])
        debt_outstanding = 2000.0
        discount_rate = 0.1

        result = compute_llcr(cfads_future, debt_outstanding, discount_rate)

        # PV = 1000/1.1 + 1000/1.1^2 + 1000/1.1^3
        pv = 1000/1.1 + 1000/(1.1**2) + 1000/(1.1**3)
        expected = pv / 2000.0
        assert abs(result - expected) < 1e-6

    def test_zero_debt_outstanding(self):
        """Zero debt returns np.inf."""
        cfads_future = np.array([1000.0, 1000.0])
        result = compute_llcr(cfads_future, 0.0, 0.1)
        assert result == np.inf

    def test_llcr_above_one(self):
        """LLCR > 1 indicates sufficient coverage."""
        cfads_future = np.array([2000.0, 2000.0])
        debt_outstanding = 1000.0
        discount_rate = 0.1

        result = compute_llcr(cfads_future, debt_outstanding, discount_rate)
        assert result > 1.0


class TestComputePLCR:
    """Test PLCR calculation."""

    def test_normal_case(self):
        """PLCR = PV(full project CFADS) / debt_initial."""
        cfads_full = np.array([1000.0, 1000.0, 1000.0])
        debt_initial = 2000.0
        discount_rate = 0.1

        result = compute_plcr(cfads_full, debt_initial, discount_rate)

        pv = 1000/1.1 + 1000/(1.1**2) + 1000/(1.1**3)
        expected = pv / 2000.0
        assert abs(result - expected) < 1e-6

    def test_zero_debt_initial(self):
        """Zero initial debt returns np.inf."""
        cfads_full = np.array([1000.0, 1000.0])
        result = compute_plcr(cfads_full, 0.0, 0.1)
        assert result == np.inf


class TestExtractDebtService:
    """Test debt service extraction from schedule."""

    def test_extract_single_year(self):
        """Extract debt service for a given year."""
        schedule = pd.DataFrame({
            'year': [1, 1, 2, 2],
            'tranche_name': ['senior', 'mezzanine', 'senior', 'mezzanine'],
            'interest_due': [100, 50, 120, 60],
            'principal_due': [200, 100, 250, 150],
        })

        # Year 1: (100+50) + (200+100) = 450
        result = extract_debt_service(schedule, 1)
        assert abs(result - 450.0) < 1e-6

        # Year 2: (120+60) + (250+150) = 580
        result = extract_debt_service(schedule, 2)
        assert abs(result - 580.0) < 1e-6

    def test_extract_missing_year(self):
        """Missing year returns 0."""
        schedule = pd.DataFrame({
            'year': [1, 1],
            'tranche_name': ['senior', 'mezzanine'],
            'interest_due': [100, 50],
            'principal_due': [200, 100],
        })

        result = extract_debt_service(schedule, 99)
        assert result == 0.0


class TestComputeRemainingDebt:
    """Test remaining debt calculation."""

    def test_remaining_debt_from_year(self):
        """Sum all future principal payments."""
        schedule = pd.DataFrame({
            'year': [1, 2, 3, 4],
            'tranche_name': ['senior'] * 4,
            'principal_due': [100, 200, 300, 400],
        })

        # From year 2: 200 + 300 + 400 = 900
        result = compute_remaining_debt(schedule, 2)
        assert abs(result - 900.0) < 1e-6

        # From year 4: 400
        result = compute_remaining_debt(schedule, 4)
        assert abs(result - 400.0) < 1e-6

    def test_no_future_debt(self):
        """No future debt returns 0."""
        schedule = pd.DataFrame({
            'year': [1, 2],
            'tranche_name': ['senior'] * 2,
            'principal_due': [100, 200],
        })

        result = compute_remaining_debt(schedule, 99)
        assert result == 0.0


class TestCoverageRatioResults:
    """Test CoverageRatioResults dataclass methods."""

    def test_to_dataframe(self):
        """Convert results to DataFrame."""
        results = [
            CoverageRatioResult(1, 1000, 800, 5000, 1.25, 1.5, 2.0),
            CoverageRatioResult(2, 1200, 1000, 4000, 1.2, 1.4, 1.9),
        ]
        container = CoverageRatioResults(results, 1.0, 1.2)

        df = container.to_dataframe()
        assert len(df) == 2
        assert list(df.columns) == ['year', 'cfads', 'debt_service', 'debt_outstanding', 'dscr', 'llcr', 'plcr']
        assert df.iloc[0]['dscr'] == 1.25

    def test_get_dscr_violations(self):
        """Detect DSCR violations."""
        results = [
            CoverageRatioResult(1, 1000, 800, 5000, 1.25, 1.5, 2.0),
            CoverageRatioResult(2, 800, 1000, 4000, 0.8, 1.4, 1.9),  # DSCR < 1.0
        ]
        container = CoverageRatioResults(results, 1.0, 1.2)

        violations = container.get_dscr_violations()
        assert len(violations) == 1
        assert violations[0].year == 2

    def test_get_llcr_violations(self):
        """Detect LLCR violations."""
        results = [
            CoverageRatioResult(1, 1000, 800, 5000, 1.25, 1.5, 2.0),
            CoverageRatioResult(2, 1200, 1000, 4000, 1.2, 1.1, 1.9),  # LLCR < 1.2
        ]
        container = CoverageRatioResults(results, 1.0, 1.2)

        violations = container.get_llcr_violations()
        assert len(violations) == 1
        assert violations[0].year == 2

    def test_summary(self):
        """Generate summary statistics."""
        results = [
            CoverageRatioResult(1, 1000, 800, 5000, 1.25, 1.5, 2.0),
            CoverageRatioResult(2, 1200, 1000, 4000, 1.2, 1.4, 1.9),
        ]
        container = CoverageRatioResults(results, 1.0, 1.2)

        summary = container.summary()
        assert 'min_dscr' in summary
        assert 'avg_dscr' in summary
        assert summary['dscr_violations'] == 0


@pytest.mark.skipif(
    not Path("data/input/leo_iot/project_params.csv").exists(),
    reason="Test data not available"
)
class TestIntegrationWithRealData:
    """Integration tests using actual project data."""

    def test_calculate_coverage_ratios_base_case(self):
        """Calculate ratios for base case scenario."""
        data_path = Path("data/input/leo_iot")
        params = ProjectParameters.from_directory(data_path)

        # Calculate without warnings for clean test output
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = calculate_coverage_ratios(params)

        assert len(results.results) == params.financials.horizon_years
        assert results.covenant_min_dscr == params.covenants.min_dscr
        assert results.covenant_min_llcr == params.covenants.min_llcr

        # Check first year has data
        first = results.results[0]
        assert first.year == 1
        assert first.cfads > 0
        assert first.debt_service > 0

    def test_calculate_coverage_ratios_stress_scenario(self):
        """Calculate ratios with stress scenario."""
        data_path = Path("data/input/leo_iot")
        params = ProjectParameters.from_directory(data_path)

        # Stress: lower revenue, higher opex
        scenario = CFADSScenarioInputs(
            arpu_multiplier=0.8,
            opex_multiplier=1.2,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = calculate_coverage_ratios(params, scenario)

        # Stress scenario should result in lower ratios
        assert len(results.results) > 0

        # Get violations
        dscr_violations = results.get_dscr_violations()
        # Stress may cause violations (but not required for test to pass)

    def test_dataframe_conversion(self):
        """Convert results to DataFrame for analysis."""
        data_path = Path("data/input/leo_iot")
        params = ProjectParameters.from_directory(data_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = calculate_coverage_ratios(params)

        df = results.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == params.financials.horizon_years
        assert 'dscr' in df.columns
        assert 'llcr' in df.columns
        assert 'plcr' in df.columns

        # DSCR can be negative (CFADS shortfalls), positive, or inf (grace periods)
        # Just verify we have numeric values
        assert df['dscr'].notna().all()
        assert df['llcr'].notna().all()
        assert df['plcr'].notna().all()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_grace_period_handling(self):
        """Handle grace periods (zero debt service) correctly."""
        cfads = np.array([1000.0, 1000.0])
        debt_service = np.array([0.0, 0.0])  # Full grace period

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_dscr(cfads, debt_service, warn=False)

        # All periods are grace, should return inf
        assert np.all(result == np.inf)

    def test_negative_cfads(self):
        """Handle negative CFADS (cash shortfall)."""
        cfads = np.array([-500.0, 1000.0])
        debt_service = np.array([800.0, 800.0])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_dscr(cfads, debt_service, warn=False)

        # DSCR can be negative
        assert result[0] < 0
        assert result[1] > 1
