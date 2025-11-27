# Regulatory Risk Premium (T-054/Phase 2)

## Rationale
- Tail risk: security token regulatory ban or unfavorable classification.
- Stress source: T3 scenario (“Security Token Regulatory Ban”) in WP-07/MC stress set.

## Premium
- Premium applied: **7.5 bps** (midpoint of 5–10 bps range).
- Nature: One-time spread add-on to tokenized scenarios; conservative offset to tokenization benefits.

## Interaction with Model
- Added to `wacd_synthesis` as `regulatory_risk_bps`.
- Tokenization benefits still include liquidity (AMM/Tinlake), operational (smart contract automation), and transparency; regulatory premium is subtracted from the total reduction to reflect tail risk.
