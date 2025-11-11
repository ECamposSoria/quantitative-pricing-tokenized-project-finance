from pftoken.waterfall import Covenant, CovenantEngine, CovenantSeverity, CovenantType
from pftoken.models.ratios import LLCRObservation


def test_covenant_breach_detection():
    engine = CovenantEngine(
        [
            Covenant(
                name="DSCR Covenant",
                metric=CovenantType.DSCR,
                threshold=1.25,
                action="block_dividends",
                severity=CovenantSeverity.MEDIUM,
            )
        ]
    )
    breach = engine.check_breach(CovenantType.DSCR, 1.1, period=1)
    assert breach is not None
    enforcement = engine.apply_covenant_actions(1.1, period=1)
    assert enforcement["cash_sweep"] is True
    assert enforcement["block_dividends"] is True


def test_llcr_evaluation_creates_breach():
    engine = CovenantEngine([])
    llcr_results = {
        "senior": LLCRObservation(tranche="senior", value=1.2, threshold=1.35),
        "mezzanine": LLCRObservation(tranche="mezzanine", value=1.4, threshold=1.2),
    }
    breaches = engine.evaluate_llcr(llcr_results, period=5)
    assert len(breaches) == 1
    assert breaches[0].covenant.metric == CovenantType.LLCR
