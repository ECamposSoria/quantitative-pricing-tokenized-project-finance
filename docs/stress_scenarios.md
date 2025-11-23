# Stress Scenarios (WP-06)

This catalog aligns with `pftoken/stress/scenarios.py` and the implementation guide.

## Base Scenarios (S1–S6)
- **S1 – Demanda débil:** ingresos −200 bps, churn +125 bps (3 años, p=15%).
- **S2 – Shock de tasas:** curva +200 bps (2 años, p=10%).
- **S3 – Fallo de lanzamiento:** prob. fallo 100% + demora de ingresos −100 bps (1 año, p=7%).
- **S4 – Degradación operativa:** inflación OPEX +100 bps, RCAPEX diet +150 bps (4 años, p=12%).
- **S5 – Regulatorio adverso:** ingresos −100 bps, impuesto efectivo +200 bps (2 años, p=5%).
- **S6 – CAPEX overrun:** CAPEX extra 25 MMUSD vs MRA 12 MMUSD (gap 13 MM) (1 año, p=8%).

## Combined Scenarios (C1–C3)
- **C1 – Perfect Storm:** S1 + S2 + S3.
- **C2 – Launch + Rates:** S2 + S3.
- **C3 – Operational Cascade:** S1 + S4 + S6.

Each scenario stores shocks as additive/multiplicative deltas targeting keys used by MC/stress runners (`revenue_growth`, `churn_rate`, `rate_shock`, `launch_failure`, `opex_inflation`, `capex_overrun`, etc.). Use `StressScenarioLibrary` to retrieve structured definitions.
