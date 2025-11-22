# Collateral Data Sources & Mapping (LEO PF Token)

This note lists the sources/evidence to populate the collateral inventory CSV (asset_id, asset_type, value basis, haircut, time-to-liquidation, priority) and ties them to empirical cases (2015–2024).

## Dataset reminder (columns)
- asset_id (e.g., Sat-01, Spectrum-FCC-KuKa, Ground-TX-01, Contract-DoD-2025, Policy-Launch)
- asset_type (satellite, spectrum_license, ground_station, contract, insurance, cash_reserve, inventory_wip, ip)
- jurisdiction (US unless noted; FCC/ITU for spectrum)
- value_basis (replacement_cost, EV_multiple, insured_value, NPV_contract, scrap)
- book_cost, estimated_recoverable_value (USD)
- haircut_pct (base), time_to_liquidation_months (base)
- holding_cost_monthly, insurance_coverage_pct, insurer_rating
- priority_allocation (senior/mezz/sub/pro-rata), legal_perfection_notes, reference_source

## Sources by asset class

### Spectrum & regulatory assets
- Straight Path mmWave clean sale ($3.1B, 2017) vs FiberTower distressed sale ($207M → vouchers): regulatory forfeiture risk; >90% discount when milestones missed. Sources: Verizon/Straight Path 2017 sale; FCC DA 18-78; AT&T FiberTower acquisition and Auction 103 vouchers.
- Intelsat C-band accelerated relocation ($4.87B clearing payments): regulatory arbitrage creates floor value. Source: FCC C-band order / Intelsat Ch.11 docs.
- Ligado/LightSquared L-band interference: discounted vs clean terrestrial spectrum; ~$0.60–0.90/MHz-pop non-distressed; distressed << when approval uncertain. Source: Ligado court/agency filings.
**Application:** For US FCC Ku/Ka rights: use clean-license haircuts 15–25% base; time-to-liquidation 9–12m if milestones met; stressed haircut 80–90% if at risk of forfeiture. Document FCC/ITU milestone status in legal_perfection_notes.

### Ground segment (gateways/teleports)
- Eutelsat–EQT carve-out 2024: €790m EV, 80% sold, TowerCo-like multiples (10–15× EBITDA) with anchor MSA. Source: Eutelsat/EQT announcements, WTA notes.
- Speedcast 2020 Ch.11: value preserved via recap; leases/contracts curated; highlights contract quality dependence. Source: Speedcast filings.
- Verestar/Digital Teleport early 2000s: piecemeal hardware liquidation 10–20% of book.
**Application:** For TX/FL/CA ground stations:
  - Base: operator-neutral/PropCo assumption → haircut 20–30%, time 6–9m (infra buyers).
  - Stressed (piecemeal hardware) → haircut 80–90%, time 12–18m.
  - Small gateway footprints (single-site Ku/Ka) justify lower book values; full teleports should be higher. Note anchor contracts (government/enterprise) in priority_allocation.

### In-orbit satellites
- OneWeb 74 sats pre-MVC (2020): standalone liquidation ≈0; value only in going-concern sale ($1B package with spectrum/ground/IP). Source: OneWeb Ch.11 sale docs.
- Globalstar early bankruptcy: satellites with technical impairment sold at scrap + spectrum option value.
- Sky and Space Global (2020): nanosats written to nil; creditor dividend negligible.
**Application:** Base liquidation haircut ~100% (0 residual) if below MVC; going-concern scenario only if funded buyer steps in. time_to_liquidation not applicable; use “binary value” note.

### Inventory / WIP
- OneWeb/Airbus JV WIP: valuable only to step-in buyer; otherwise scrap 0–10%.
- SAS “near-term rocket builds” written down to zero. 
**Application:** Base haircut 90–100%, time 3–6m; going-concern (if buyer continues build) 30–60% with note.

### Contracts / backlog / IP
- Speedcast: executory contract rejection; unsecured recoveries low; highlights volatility.
- Intelsat assuming Gogo ($400m) during Ch.11: critical contracts are protected/assumed.
- Iridium saved by $72m DoD contract; government contracts create floor value.
- OneWeb Seller Notes wiped (0% recovery): vendor financing highly subordinated.
- BlackSky/LeoSat: IP portable, can be sold even if hardware fails; LeoSat filings lapsed → zero.
**Application:** Government contracts: base haircut 10–20%, time 3–6m; commercial non-anchor: 40–60% haircut, time 6–9m; vendor debt: 90–100% haircut. Document assignability/novation in legal_perfection_notes. Add explicit backlog/contract bucket in the inventory.

### Insurance / reserves
- Launch/orbital insurance: use insured_value as value_basis; haircut linked to claimability and insurer rating (e.g., 10–20% haircut if policy is in-force). Cash DSRA/MRA: 0–5% haircut, time 1m.

## Traceability to report
- Spectrum valuations: Straight Path vs FiberTower, Intelsat C-band, Ligado (sections 2.1–2.3).
- Ground infra: Eutelsat–EQT (€790m), Speedcast, Verestar (section 3).
- Satellites/In-orbit: OneWeb 74 sats, Globalstar, SAS (section 4).
- Contracts/IP: Speedcast rejections, Intelsat-Gogo assumption, Iridium DoD, Seller Notes wipe, LeoSat IP (section 5).
- WIP: OneWeb/Airbus JV, SAS write-down (section 6).

## Next steps to populate CSV
1) Create `data/derived/collateral_inventory.csv` with the columns above.
2) For each US asset bucket: add base/stress haircuts and time-to-liquidation per class using the ranges noted; cite the specific precedent in reference_source.
3) Flag regulatory status (clean/at-risk) for spectrum and contract assignability for ground/GSaaS; include any government anchor contracts in priority_allocation.
