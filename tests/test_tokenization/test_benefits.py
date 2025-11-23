from pftoken.tokenization import TokenizationBenefits, compute_tokenization_wacd_impact


def test_tokenization_benefits_totals():
    benefits = TokenizationBenefits()
    data = benefits.to_dict()
    assert data["mechanisms"]["liquidity_premium"]["reduction_bps"] == benefits.liquidity_benefit_bps
    assert data["total_benefit_bps"] == benefits.total_benefit_bps


def test_compute_tokenization_wacd_impact_depth_sensitivity():
    impact_low = compute_tokenization_wacd_impact(750, secondary_market_depth=0.1)
    impact_high = compute_tokenization_wacd_impact(750, secondary_market_depth=0.9)
    assert impact_high["total_reduction_bps"] > impact_low["total_reduction_bps"]
