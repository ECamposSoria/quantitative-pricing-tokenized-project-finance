# User Guide

The user guide will provide onboarding instructions and usage examples for analysts.

## Status

> Placeholder: update once core modules are implemented.

## AMM Quick Start (Preview)

1. Instantiate a constant-product pool using `ConstantProductPool`.
2. Use `scripts/compare_dcf_market.py` to benchmark DCF vs. AMM prices.
3. Run `scripts/run_amm_stress.py` to evaluate liquidity drawdowns.
4. Optimise concentrated-liquidity ranges with `scripts/optimize_pool_ranges.py`.
5. Construir un dashboard determinístico con `pftoken.viz.dashboards.build_financial_dashboard(params)` para graficar CFADS, DSCR y estructura de capital.

This workflow will be expanded with full tutorials and notebooks.

## WP-02/WP-03 Snapshot

- **Entrada inmutable**: todos los CSV viven en `data/input/leo_iot/`. Los scripts nunca los sobreescriben; cualquier derivado se guarda en `data/derived/` o `data/output/`.
- **CFADS**: `CFADSCalculator` descompone ingresos, OPEX, CAPEX y taxes. Usa `cfads_calc.cfads_results` para rastrear cada componente y validar contra Excel con una tolerancia máxima de 0.01 %.
- **Ratios**: `RatioCalculator` produce DSCR/LLCR/PLCR por tramo y los compara con los pisos establecidos (gracia 1.0x, ramp 1.15x, steady 1.25x).
- **Waterfall**: `WaterfallOrchestrator` ejecuta el motor multi-periodo respetando el DSRA inicial de 18 MUSD y un MRA equivalente al 50 % del próximo RCAPEX. El resultado agrega equity IRR y saldos de reservas.
- **Exportar a Excel**: `python scripts/export_excel_validation.py` genera snapshots en `data/output/excel_exports/<timestamp>/` (archivos `cfads_components.csv`, `ratios.csv`, `waterfall.csv`) para actualizar manualmente `TP_Quant_Validation.xlsx`.
- **Stochastic toolkit**: `StochasticVariables` y `CorrelatedSampler` (WP‑07 T‑022/T‑023) producen distribuciones lognormal/beta/normal/bernoulli y aplican la matriz de correlación validada por Cholesky para alimentar Monte Carlo.

Consulte `docs/governance.md` para entender cómo se conectan los triggers de covenants con el bloque de gobernanza offline.
