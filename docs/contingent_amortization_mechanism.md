# Contingent Amortization Mechanism (WP-12)

This document summarizes the DSCR-contingent amortization engine, including the balloon cap and the extension provision used for thesis scenarios.

## Balloon Cap

- **Hard cap:** Total balloon (principal + accrued deferral interest) is capped at 50% of original principal by default (`balloon_cap_pct=0.50`).
- The engine projects the balloon each period; if it exceeds the cap, it forces an incremental principal payment (up to the deferred balance). If CFADS cannot support the forced payment, the breach type is `balloon_cap_binding`.
- Tunable via `ContingentAmortizationConfig.balloon_cap_pct`; set to `None` to disable.

## Extension Provision (Documentation Only)

- Mini-perm style: 5-year extension window (`extension_years=5`) at `extension_rate_spread=+200 bps` over the base rate.
- Not modeled in cash flows; intended as a policy note for lenders to mitigate refinance risk when a balloon remains at maturity.

## DSCR Percentiles

- `min_dscr` is tracked per path (including grace years) and aggregated across simulations; percentiles now reflect actual minimum DSCR values instead of zeros.
- Breach types include `hard_interest`, `soft_covenant`, and `balloon_cap_binding` (when the cap forces unsustainable payments).
