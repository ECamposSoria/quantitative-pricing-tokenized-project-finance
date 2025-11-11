from pftoken.waterfall import (
    GovernanceController,
    LoggingAction,
    StaticOracle,
    ThresholdPolicy,
)


def test_governance_controller_executes_action():
    oracle = StaticOracle(name="dscr_oracle", payload={"dscr": 1.05})
    action = LoggingAction(name="block_dividends")
    policy = ThresholdPolicy(
        name="Low DSCR",
        metric="dscr",
        threshold=1.20,
        action_ids=["block_dividends"],
    )
    controller = GovernanceController(
        oracles=[oracle],
        policies=[policy],
        actions={action.name: action},
    )

    executed = controller.run_cycle(period=6)

    assert executed["block_dividends"] is True
    assert action.log[-1]["dscr"] == 1.05
    assert action.log[-1]["period"] == 6
