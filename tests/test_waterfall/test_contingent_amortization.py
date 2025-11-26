"""Tests for DSCR-contingent amortization engine (WP-12)."""

import numpy as np
import pytest

from pftoken.waterfall.contingent_amortization import (
    ContingentAmortizationConfig,
    ContingentAmortizationEngine,
    DualStructureComparator,
    TraditionalAmortizationEngine,
)


@pytest.fixture
def base_params():
    """Standard test parameters."""
    return {
        "principal": 50_000_000,
        "interest_rate": 0.055,
        "tenor": 15,
        "grace_years": 4,
    }


@pytest.fixture
def base_cfads_path():
    """Base case CFADS path (15 years) in USD."""
    return [
        -0.6e6, -1.2e6, 0.3e6, 5.0e6,  # Grace: years 1-4
        12.4e6, 18.5e6, 22.3e6, 25.1e6, 27.0e6, 28.5e6,  # Ramp: years 5-10
        29.5e6, 30.0e6, 30.5e6, 31.0e6, 31.5e6,  # Steady: years 11-15
    ]


@pytest.fixture
def stressed_cfads_path():
    """Stressed CFADS path (P25 scenario) in USD."""
    return [
        -0.6e6, -1.2e6, 0.3e6, 5.0e6,
        7.9e6, 11.8e6, 14.2e6, 16.0e6, 17.2e6, 18.2e6,
        18.9e6, 19.2e6, 19.5e6, 19.8e6, 20.1e6,
    ]


class TestContingentAmortizationConfig:
    """Tests for configuration validation."""

    def test_default_config_is_valid(self):
        """Default config should pass validation."""
        config = ContingentAmortizationConfig()
        config.validate()  # Should not raise

    def test_invalid_dscr_floor_raises(self):
        """DSCR floor above target should raise."""
        with pytest.raises(ValueError, match="dscr_floor must be between"):
            config = ContingentAmortizationConfig(dscr_floor=2.0, dscr_target=1.5)
            config.validate()

    def test_invalid_max_deferral_raises(self):
        """Max deferral > 50% should raise."""
        with pytest.raises(ValueError, match="max_deferral_pct"):
            config = ContingentAmortizationConfig(max_deferral_pct=0.75)
            config.validate()

    def test_negative_deferral_rate_raises(self):
        """Negative deferral rate should raise."""
        with pytest.raises(ValueError, match="deferral_rate"):
            config = ContingentAmortizationConfig(deferral_rate=-0.05)
            config.validate()

    def test_accelerate_below_target_raises(self):
        """Accelerate threshold below target should raise."""
        with pytest.raises(ValueError, match="dscr_accelerate"):
            config = ContingentAmortizationConfig(dscr_target=1.5, dscr_accelerate=1.3)
            config.validate()


class TestContingentAmortizationEngine:
    """Tests for contingent amortization engine."""

    def test_tenor_equals_grace_period_raises(self, base_params):
        """Tenor must exceed grace period."""
        params = {**base_params, "tenor": 4, "grace_years": 4}
        with pytest.raises(ValueError, match="Tenor must exceed grace period"):
            ContingentAmortizationEngine(**params)

    def test_grace_period_interest_only(self, base_params, base_cfads_path):
        """During grace, only interest is paid."""
        engine = ContingentAmortizationEngine(**base_params)
        result = engine.simulate_path(base_cfads_path)

        for period in result.period_results[:4]:  # Grace years
            assert period.principal_paid == 0
            assert period.principal_scheduled == 0

    def test_dscr_floor_maintained(self, base_params, stressed_cfads_path):
        """DSCR should never go below floor (except hard breach)."""
        config = ContingentAmortizationConfig(dscr_floor=1.25, balloon_cap_pct=None)
        engine = ContingentAmortizationEngine(**base_params, config=config)
        result = engine.simulate_path(stressed_cfads_path)

        for period in result.period_results[4:]:  # Amort years
            if period.breach_type != "hard_interest":
                # Allow small tolerance for floating point
                assert period.realized_dscr >= 1.24, f"Year {period.year}: DSCR {period.realized_dscr:.4f}"

    def test_principal_deferred_to_balloon(self, base_params, stressed_cfads_path):
        """Deferred principal should accumulate for balloon."""
        engine = ContingentAmortizationEngine(**base_params)
        result = engine.simulate_path(stressed_cfads_path)

        total_deferred = sum(p.principal_deferred for p in result.period_results)
        assert total_deferred > 0
        assert result.total_deferred > 0
        assert result.final_balloon > 0

    def test_catch_up_in_good_years(self, base_params, base_cfads_path):
        """Should catch up on deferred principal in good years."""
        config = ContingentAmortizationConfig(
            dscr_floor=1.25,
            dscr_accelerate=2.00,
            catch_up_enabled=True,
            balloon_cap_pct=None,
        )
        engine = ContingentAmortizationEngine(**base_params, config=config)

        # Create path with bad year 5, then very good years
        mixed_path = list(base_cfads_path)
        mixed_path[4] = 6.0e6  # Force deferral in year 5
        mixed_path[6] = 60.0e6  # Very good year 7 (DSCR > 2.0)

        result = engine.simulate_path(mixed_path)

        # Should have some catch-up
        catch_ups = [p.principal_catch_up for p in result.period_results]
        assert sum(catch_ups) > 0

    def test_max_deferral_constraint(self, base_params):
        """Cumulative deferral should not exceed max percentage when CFADS is sufficient."""
        config = ContingentAmortizationConfig(max_deferral_pct=0.20)
        engine = ContingentAmortizationEngine(**base_params, config=config)

        # Path where CFADS covers interest but not full principal
        # This allows the max deferral constraint to be tested properly
        moderate_stress = [5e6] * 4 + [10e6] * 11  # Covers interest but not full principal
        result = engine.simulate_path(moderate_stress)

        # If there's any deferral, check it doesn't exceed max
        max_allowed = base_params["principal"] * 0.20
        if result.total_deferred > 0:
            # Allow 1% tolerance for floating point
            assert result.total_deferred <= max_allowed * 1.01

    def test_zero_cfads_causes_hard_breach(self, base_params):
        """Zero CFADS should cause hard breach (can't pay interest)."""
        engine = ContingentAmortizationEngine(**base_params)
        zero_path = [0.0] * 15
        result = engine.simulate_path(zero_path)

        assert result.breach_occurred
        assert result.breach_type == "hard_interest"

    def test_very_high_cfads_no_deferral(self, base_params):
        """Very high CFADS should result in effectively zero deferral."""
        engine = ContingentAmortizationEngine(**base_params)
        high_path = [100e6] * 15
        result = engine.simulate_path(high_path)

        # Allow for floating point precision (should be essentially zero)
        assert result.total_deferred < 1.0  # Less than $1 is effectively zero
        assert result.final_balloon < 1.0

    def test_negative_cfads_during_amortization(self, base_params):
        """Negative CFADS should cause hard breach."""
        engine = ContingentAmortizationEngine(**base_params)
        path = [5e6] * 4 + [-1e6] * 11  # Negative after grace
        result = engine.simulate_path(path)

        assert result.breach_occurred
        assert result.breach_type == "hard_interest"

    def test_balloon_cap_constraint(self, base_params):
        """Balloon cap should trigger breach when projected balloon exceeds cap."""
        config = ContingentAmortizationConfig(
            dscr_floor=1.25,
            max_deferral_pct=0.30,
            balloon_cap_pct=0.50,
        )
        engine = ContingentAmortizationEngine(**base_params, config=config)
        low_path = [3.0e6] * 15  # Persistent stress to accumulate balloon

        result = engine.simulate_path(low_path, covenant=1.20)

        assert result.breach_occurred
        assert result.breach_type == "balloon_cap_binding"
        max_balloon = base_params["principal"] * 0.50
        assert result.final_balloon <= max_balloon * 1.01


class TestTraditionalAmortizationEngine:
    """Tests for traditional amortization engine."""

    def test_fixed_amortization_schedule(self, base_params, base_cfads_path):
        """Traditional should follow fixed schedule regardless of CFADS."""
        engine = TraditionalAmortizationEngine(**base_params)
        result = engine.simulate_path(base_cfads_path)

        # After grace, principal should be scheduled_principal_per_year
        expected_principal = base_params["principal"] / (base_params["tenor"] - base_params["grace_years"])
        for period in result.period_results[4:]:  # After grace
            assert abs(period.principal_scheduled - expected_principal) < 1.0

    def test_breach_on_low_cfads(self, base_params):
        """Should record breach when DSCR < covenant during amortization."""
        engine = TraditionalAmortizationEngine(**base_params)
        # CFADS = 3.0e6, Interest = 50e6 * 0.055 = 2.75e6
        # Year 5 (first amortization): CFADS / (Interest + Principal) < 1.20 covenant
        # With construction financing, breaches only occur post-COD (Year 5+)
        low_path = [3.0e6] * 15
        result = engine.simulate_path(low_path, covenant=1.20)

        assert result.breach_occurred
        # First breach happens in Year 5 (first amortization year, post-COD)
        assert result.breach_year == 5


class TestTraditionalVsTokenizedComparison:
    """Tests for dual-structure comparison."""

    def test_traditional_breaches_on_stressed_path(self, base_params, stressed_cfads_path):
        """Traditional structure should breach on stressed path."""
        trad = TraditionalAmortizationEngine(**base_params)
        result = trad.simulate_path(stressed_cfads_path, covenant=1.20)

        # The stressed path has negative CFADS in grace, so breach occurs early
        assert result.breach_occurred

    def test_tokenized_avoids_soft_breach_on_stressed_path(self, base_params):
        """Tokenized structure should avoid soft covenant breach via deferral."""
        # Create a path that breaches covenant but not hard breach
        # Grace years: cover interest, amort years: below full service but above interest
        moderate_stress = [5e6] * 4 + [10e6] * 11
        config = ContingentAmortizationConfig(dscr_floor=1.25)
        token = ContingentAmortizationEngine(**base_params, config=config)
        result = token.simulate_path(moderate_stress, covenant=1.20)

        # Tokenized maintains floor, so no soft breach in amort years
        soft_breaches = [
            p for p in result.period_results[4:]  # Only check amort years
            if p.breach_type == "soft_covenant"
        ]
        assert len(soft_breaches) == 0

    def test_comparison_shows_improvement_on_moderate_stress(self, base_params):
        """Comparison should show tokenized improvement on moderate stress."""
        # Path that causes traditional breach but tokenized can handle
        moderate_stress = [5e6] * 4 + [8e6] * 11
        comparator = DualStructureComparator(**base_params)
        comparison = comparator.compare_single_path(moderate_stress, covenant=1.20)

        # Tokenized should have higher min DSCR due to principal deferral
        assert comparison.tokenized["min_dscr"] >= comparison.traditional["min_dscr"]

    def test_monte_carlo_comparison(self, base_params):
        """Monte Carlo comparison should produce valid statistics."""
        comparator = DualStructureComparator(**base_params)

        # Generate synthetic scenarios
        np.random.seed(42)
        n_sims = 100
        n_years = 15

        # Base CFADS with lognormal variation (in USD)
        base = np.array([
            -0.6, -1.2, 0.3, 5.0, 12.4, 18.5, 22.3, 25.1,
            27.0, 28.5, 29.5, 30.0, 30.5, 31.0, 31.5
        ]) * 1e6

        scenarios = np.zeros((n_sims, n_years))
        for i in range(n_sims):
            shock = np.random.lognormal(0, 0.3, n_years)
            scenarios[i, :] = base * shock

        results = comparator.run_monte_carlo_comparison(scenarios, covenant=1.20)

        # Validate structure
        assert "traditional" in results
        assert "tokenized" in results
        assert "comparison" in results
        assert "thesis_summary" in results

        # Tokenized should have lower breach probability
        assert results["tokenized"]["breach_probability"] <= results["traditional"]["breach_probability"]

        # Key finding should be generated
        assert len(results["thesis_summary"]["key_finding"]) > 0

    def test_comparison_with_high_cfads(self, base_params):
        """With high CFADS, both structures should perform similarly."""
        comparator = DualStructureComparator(**base_params)
        high_path = [50e6] * 15  # Very high CFADS
        comparison = comparator.compare_single_path(high_path, covenant=1.20)

        # Neither should breach
        assert not comparison.traditional["breach_occurred"]
        assert not comparison.tokenized["breach_occurred"]

        # Essentially no additional balloon (allow floating point tolerance)
        assert abs(comparison.delta["additional_balloon"]) < 1.0  # Less than $1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_year_amortization(self):
        """Edge case: single year of amortization."""
        params = {
            "principal": 10_000_000,
            "interest_rate": 0.05,
            "tenor": 2,
            "grace_years": 1,
        }
        engine = ContingentAmortizationEngine(**params)
        path = [2e6, 15e6]  # Year 1: grace, Year 2: amort
        result = engine.simulate_path(path)

        assert len(result.period_results) == 2
        assert result.period_results[0].principal_paid == 0
        assert result.period_results[1].principal_paid > 0

    def test_exact_dscr_floor(self, base_params):
        """CFADS exactly at floor threshold."""
        config = ContingentAmortizationConfig(dscr_floor=1.25)
        engine = ContingentAmortizationEngine(**base_params, config=config)

        # Calculate exact CFADS for floor
        # DSCR = CFADS / (interest + principal)
        # At floor: CFADS = 1.25 * (interest + principal)
        interest = base_params["principal"] * base_params["interest_rate"]
        amort_years = base_params["tenor"] - base_params["grace_years"]
        principal = base_params["principal"] / amort_years
        exact_cfads = 1.25 * (interest + principal)

        # Grace years + exact floor
        path = [5e6] * 4 + [exact_cfads] * 11
        result = engine.simulate_path(path, covenant=1.20)

        # Should not breach (floor is maintained)
        for period in result.period_results[4:]:
            assert period.realized_dscr >= 1.24

    def test_deferred_interest_accumulation(self, base_params):
        """Verify deferred interest accrues correctly."""
        config = ContingentAmortizationConfig(dscr_floor=1.30, deferral_rate=0.12)
        engine = ContingentAmortizationEngine(**base_params, config=config)

        # Path that causes deferral
        stressed = [3e6] * 4 + [8e6] * 11
        result = engine.simulate_path(stressed)

        # Check deferred interest is tracked
        for period in result.period_results[5:]:  # After first deferral
            if period.cumulative_deferred > 0:
                expected_accrued = period.cumulative_deferred * config.deferral_rate
                assert abs(period.deferred_interest_accrued - expected_accrued) < 1.0


class TestThesisSummary:
    """Tests for thesis-ready output generation."""

    def test_key_finding_non_bankable_to_bankable(self, base_params):
        """Key finding when tokenization enables bankability."""
        comparator = DualStructureComparator(**base_params)

        # Generate scenarios that create ~40% traditional breach, ~5% tokenized
        np.random.seed(123)
        n_sims = 500
        n_years = 15

        # Base with significant variance
        base = np.array([
            -0.6, -1.2, 0.3, 5.0, 8.0, 12.0, 15.0, 17.0,
            18.5, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0
        ]) * 1e6

        scenarios = np.zeros((n_sims, n_years))
        for i in range(n_sims):
            shock = np.random.lognormal(0, 0.35, n_years)
            scenarios[i, :] = base * shock

        results = comparator.run_monte_carlo_comparison(scenarios, covenant=1.20)

        # Check thesis summary structure
        summary = results["thesis_summary"]
        assert "traditional_bankable" in summary
        assert "tokenized_bankable" in summary
        assert "tokenization_enables_bankability" in summary
        assert "key_finding" in summary

        # Key finding should be a non-empty string
        assert isinstance(summary["key_finding"], str)
        assert len(summary["key_finding"]) > 10

    def test_bankability_thresholds(self, base_params):
        """Bankability is defined as <20% breach probability."""
        comparator = DualStructureComparator(**base_params)

        # High CFADS - both bankable
        high_scenarios = np.ones((100, 15)) * 50e6
        high_results = comparator.run_monte_carlo_comparison(high_scenarios)
        assert high_results["thesis_summary"]["traditional_bankable"] is True
        assert high_results["thesis_summary"]["tokenized_bankable"] is True

        # Very low CFADS - neither bankable
        low_scenarios = np.ones((100, 15)) * 2e6
        low_results = comparator.run_monte_carlo_comparison(low_scenarios)
        assert low_results["thesis_summary"]["traditional_bankable"] is False
        assert low_results["thesis_summary"]["tokenized_bankable"] is False
