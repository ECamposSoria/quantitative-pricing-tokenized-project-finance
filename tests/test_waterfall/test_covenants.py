from pftoken.waterfall import Covenant, CovenantEngine, CovenantSeverity, CovenantType


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
