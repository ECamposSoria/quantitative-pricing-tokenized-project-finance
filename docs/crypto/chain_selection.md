# Chain Selection Summary (T-054)

## Why Centrifuge/Polkadot
- Finality ~6 seconds; more than sufficient for annual CFADS updates and quarterly reporting.
- Purpose-built for real-world assets with established Tinlake pools and CFG governance.
- Existing $1.45B+ TVL ecosystem reduces platform adoption risk.

## Finality & Gas Considerations
- Ethereum L1: probabilistic finality; fees ~$5–$20/tx → unacceptable for routine reporting.
- Arbitrum (as L2 reference): fees ~$0.10–$0.50/tx; finality faster than reporting cadence → no finality premium required.
- Polkadot/Centrifuge parachain: deterministic finality (~6s) and low fees; matches data/settlement frequency for the project.

## Decision
- Use Centrifuge/Tinlake rails; no additional finality premium priced because settlement frequency (annual CFADS, quarterly updates) is far slower than chain finality.
- Keep Arbitrum/EVM as contingency for interoperability; only documentation, no pricing impact.
