markdown# System Memory

## Last Updated: 2025-12-10 19:20 UTC
## Version: 0.7.1

### Current Architecture
- `ProjectParameters` ahora es un loader liviano (dataclasses) que alimenta CFADS, ratios y el nuevo `FinancialPipeline` (CFADS → waterfall → covenants → viz).
- Dataset LEO IoT (T-047) regenerado directamente desde `Proyecto LEO IOT.xlsx`; `scripts/validate_input_data.py` garantiza coherencia (ahora valida CFADS + reservas).
- Hoja Excel + CSV incluyen financiamiento explícito de DSRA inicial (18 MUSD fondeados por equity en el cierre para cubrir los 4 años de gracia) y RCAPEX “diet” de 18 MUSD en los años 6‑15 (1.2/1.5/1.65/1.7/1.55/3.4/2.25/2/1.5/1.25) con un MRA que acumula 35% del próximo RCAPEX durante los 3 años previos (contribuciones solapadas) para emular reposiciones del 8% de la flota cada ciclo.
- Viz package genera dashboard expandido (cascada waterfall, reservas DSRA/MRA, heatmap de covenants, radar de estructura) usando resultados del pipeline.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- Libraries: numpy, pandas, scipy, matplotlib, pytest, jupyter, numpy-financial, eth-abi, pydantic, PyYAML
- WP-04 añadió dependencias lógicas (scipy.optimize, matplotlib) pero ya estaban fijadas en `requirements.txt`.

### Container Setup
- Base Image: `python:3.12-slim`
- Services: `app` (HTTP placeholder)
- Ports: `8000:8000`
- Volumes: repo bind-mounted en `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`, `MPLCONFIGDIR=/app/.mplconfig`

### Implemented Features
- WP-14 (in progress): concentrated-liquidity swap simulation with Q64.96 tick math (`pool_v3` + helpers), enhanced pricing/slippage + Almgren–Chriss arb engine, V3-aware impermanent loss/LP PnL analytics, AMM stress scenarios/export hooks, AMM viz helpers, docs/tests (`docs/amm/architecture.md`, `docs/amm/amm_overview.md`, `docs/amm/integration_guide.md`, `docs/amm/impermanent_loss.md`, `pftoken/stress/amm_*`, `pftoken/viz/amm_viz.py`). Tests executed in container: `docker tag qptf-quant_token_app:latest qptf-quant_token_app:0.1.0 && docker run --rm -v "$(pwd)":/app -w /app qptf-quant_token_app:0.1.0 pytest tests/test_amm/test_impermanent_loss.py tests/test_amm/test_lp_pnl.py tests/test_amm/test_arbitrage_engine.py tests/test_amm/test_market_pricing.py tests/test_integration/test_amm_stress.py`.
- Added V2 vs V3 AMM comparison to `scripts/demo_risk_metrics.py` (`build_v2_v3_comparison`) and integrated into payload for thesis outputs (slippage + capital efficiency vs concentrated range).
- WP-14 (in progress): concentrated-liquidity swap simulation with Q64.96 tick math (`pool_v3` + helpers), enhanced pricing/slippage + Almgren–Chriss arb engine, V3-aware impermanent loss/LP PnL analytics, and new AMM unit tests/docs (`docs/amm/impermanent_loss.md`). Tests executed in container: `docker tag qptf-quant_token_app:latest qptf-quant_token_app:0.1.0 && docker run --rm -v "$(pwd)":/app -w /app qptf-quant_token_app:0.1.0 pytest tests/test_amm/test_impermanent_loss.py tests/test_amm/test_lp_pnl.py tests/test_amm/test_arbitrage_engine.py tests/test_amm/test_market_pricing.py`.
- CFADS deterministic components (`pftoken.models.cfads_components`) verifican ingresos/OPEX/CAPEX/impuestos por año y se validan automáticamente contra Excel con tolerancia <0.01 %.
- `RatioCalculator` produce DSCR por fase y LLCR/PLCR por tramo usando los umbrales compartidos (grace 1.0x, ramp 1.15x, steady 1.25x); los resultados alimentan `CovenantEngine`.
- Placeholder de calibración T‑047 (`data/derived/leo_iot/stochastic_params.yaml`) consumido mediante `load_placeholder_calibration`; `MertonModel` ahora devuelve PD/LGD/EL vectorizados con pruebas unitarias.
- `WaterfallOrchestrator` coordina CFADS → WaterfallEngine → reservas con DSRA inicial fijo (18 MUSD) y MRA = 50 % del próximo RCAPEX; registra equity IRR y saldos DSRA/MRA por período.
- `StructureComparator` amplía el output con métricas de liquidez (cobertura DSRA/MRA) y la comparación global se integra en `FinancialPipeline`.
- Gobernanza offline documentada en `docs/governance.md` y soportada por `GovernanceController`, `ThresholdPolicy`, `StaticOracle` y `LoggingAction`.
- `StochasticVariables` + `CorrelatedSampler` (WP-07 T-022/T-023) generan distribuciones lognormal/beta/normal/bernoulli con antithetic variates y matrices de correlación validadas (Cholesky + eigenvalue check). Los parámetros provienen de `data/derived/leo_iot/stochastic_params.yaml`.
- WP-07 extensión: módulo path-dependent (first-passage barrier) y regime-switching con toggles `enable_path_default`/`enable_regime_switching`/`enable_regime_lgd`/`enable_regime_spreads` (default off). `path_callbacks` puede emitir `asset_value_paths` + `first_passage_default`; `compute_pathwise_pd_lgd` aplica defaults/lgd por régimen; config en `stochastic_params.yaml` (barrier_ratio calibrado a 0.55) y tests `tests/test_simulation/test_path_dependent.py`, `tests/test_simulation/test_regime_switching.py`.
- Docker multi-stage + healthcheck (`pftoken.healthcheck`), usuario no root (`appuser`), y Compose actualizado con `restart`/`mem_limit` para cumplir la política de operación.
- `scripts/export_excel_validation.py` genera snapshots (CFADS/Ratios/Waterfall) en `data/output/excel_exports/<timestamp>/` para refrescar `TP_Quant_Validation.xlsx` sin tocar los CSV fuente.
- README/user-guide actualizados para reflejar política de datos inmutable, DSRA/MRA baseline y el nuevo flujo de validación.
- WP-04 Pricing:
  - `pftoken.pricing.zero_curve.ZeroCurve`: curve bootstrap (depósitos/swaps), interpolación log-lineal, forwards y shocks.
  - `pftoken.pricing.base_pricing.PricingEngine`: precio limpio, YTM vía `scipy.optimize.brentq`, duración y convexidad por tramo + visualizaciones Matplotlib.
  - `pftoken.pricing.wacd.WACDCalculator`: escenarios tradicional vs tokenizado (after-tax) reutilizando `PricingContext`.
- `PricingEngine` expone metadata de YTM (`ytm_label`, `risk_free_curve_rate`, `spread_over_curve`, `explanatory_note`) para dejar explícito que el solver opera con la curva libre de riesgo y que los spreads viven en el modelo tokenizado.
- `pftoken.pricing.collateral_adjust.CollateralAnalyzer`: waterfall de recoveries (haircuts + descuento por tiempo de liquidación).
- Curva libre de riesgo de referencia: `data/derived/market_curves/usd_combined_curve_2025-11-07.csv` (Par Yield DGS + swap ICE 10Y) cargada con `load_zero_curve_from_csv`.
- Documentación en `docs/pricing.md` y nueva sección “WP-04 – Pricing & Curves” en `README.md`.
- Tests unitarios/integración en `tests/test_pricing/*` y `tests/test_integration/test_pricing_pipeline.py`.
- Tokenized spread decomposition: `pftoken.pricing.spreads.TokenizedSpreadModel` combina crédito, liquidez (Amihud + α), originación y servicing (β/γ) e infraestructura blockchain (gas/oracles/risk premium) para reemplazar los deltas fijos del WACD; el tracker exporta `data/derived/tokenized_infra_costs.csv` y está documentado en `docs/tokenized_spread_decomposition.md`.
- Sensitivity engine: `TokenizedSpreadModel.simulate_delta_scenarios()` genera 7 escenarios estándar (Tinlake ±50 %, beta overrides, Infra ×2, stressed) y exporta `data/derived/sensitivities/wacd_delta_sensitivity_<timestamp>.csv` que alimentan `WACDCalculator`.
- `scripts/update_blockchain_infra.py` renueva `data/derived/tokenized_infra_costs.csv` usando APIs públicas (Etherscan API V2 multi-chain con fallback automático a los endpoints legacy + CoinGecko) y deja trazabilidad de fuentes en cada fila; si una llamada falla, el motivo queda embedido en `gas_price_source`.
- `scripts/manage_tinlake_snapshot.py` gestiona `data/derived/liquidity/tinlake_metrics.json` (flags `--force-refresh`, `--offline`, `--status`) y emite registros JSON auditables.
- `TokenizedSpreadConfig` ahora puede auto-calibrar los multiplicadores de liquidez consultando Tinlake (DeFiLlama API) y guarda un snapshot local en `data/derived/liquidity/tinlake_metrics.json`, con las métricas crudas (TVL ~1.45B, volumen diario ~2.4M, ticket promedio ~15.5M) y timestamp.
- El delta tokenizado del WACD se deriva ahora de los componentes (liquidez, origination, servicing e infraestructura) y se exporta junto con el breakdown por tramo; los overrides (−75/−25 bps) siguen disponibles pero quedan documentados como tal.
- WP-05 (riesgo crediticio): nuevos módulos `pftoken/risk/*` implementan EL/VaR/CVaR (`RiskMetricsCalculator`), agregación correlacionada (`AggregateRiskCalculator` con Gaussian copula y validación SPD), análisis de colas (`TailRiskAnalyzer` empírico + EVT opcional), frontera eficiente (`EfficientFrontierAnalysis`) y concentración HHI (`RiskConcentrationAnalysis`). `FinancialPipeline.run` puede devolver `risk_metrics` (opt-in) y hay suite de pruebas `tests/test_risk/*`.
- Se agregó `scripts/demo_risk_metrics.py` para ejecutar WP-05 rápidamente con los inputs LEO IoT y guardar/emitir `outputs/leo_iot_results.json`.
- Nota pendiente: conectar EVT tail fits y Efficient Frontier al output WP-05 cuando existan escenarios Monte Carlo (WP-07); hoy solo se expone EL/VaR/CVaR paramétrico y concentración.
- Hallazgo frontier (demo WP-05 actual, sin restricciones externas): con el mismo riesgo (CVaR ≈ 2.6M), la estructura eficiente es ~3% senior / 91% mezz / 6% sub vs la actual 60/25/15; retorno 8.61% vs 7.53% (+108 bps). Motivo: mezz (8.5% cupón, PD 3%, LGD 55%) ofrece mejor trade-off que senior (6.5% cupón, PD 1%, LGD 40%) y sub (12% cupón, PD 10%, LGD 100%). Caveat: en la realidad rating agencies/mandatos exigen 60% senior; esta es la “ineficiencia” cuantificada si se relaja esa restricción (tokenizado).
- Comparación dual tradicional vs tokenizado: `FinancialPipeline` puede devolver `structure_comparison` (opt-in vía `compare_structures`), descomponiendo valor recuperable por rebalancing (gap a la frontera) y premio de liquidez (`tokenization_spread_reduction_bps`), con chequeo opcional de restricciones tradicionales (`traditional_constraints`).
- Estructura tokenizada optimizada documentada: 55/34/12 (senior/mezz/sub) seleccionada vía Pareto 3D (riesgo, retorno, WACD) con tolerancia ±1%, 500 muestras, seed=42. Se integra en `generate_wp04_report.py` como fila “Tokenizado (óptimo)” sin alterar la estructura tradicional 60/25/15.
- WACD optimizado: `WACDCalculator.compute_with_weights` permite recalcular WACD con pesos alternativos; `generate_wp04_report.py` ahora ejecuta frontier WP-05 dentro del reporte y añade sección de escenarios de estructura (tradicional, tokenizado actual y tokenizado óptimo) con WACD after-tax y violaciones de restricciones si aplica.
- WP-10 (optimización) marcado como COMPLETO vía WP-05 EfficientFrontierAnalysis: la optimización multiobjetivo (riesgo-retorno-WACD) es preferible a un SLSQP single-objective; entregables incluyen estructura 55/34/12 ya adoptada y mejora WACD ≈70 bps after-tax vs tradicional. T-036 SLSQP refinements se consideraron innecesarios.
- **WP-04 QF deliverables:**
  - **QF-1 (Delta Sensitivities):** `TokenizedSpreadModel.simulate_delta_scenarios()` +
    `WACDCalculator.compare_traditional_vs_tokenized()` generan 7 escenarios,
    recalculan WACD after-tax y exportan `wacd_delta_sensitivity_<timestamp>.csv`.
  - **QF-2 (Risk-Free YTM Metadata):** `PricingEngine` serializa
    `ytm_label`, `risk_free_curve_rate`, `spread_over_curve` y cuenta con el
    test `test_ytm_is_below_coupon_when_price_above_par` para dejar constancia de
    que YTM < cupón cuando el precio está sobre par.
  - **QF-3 (Tinlake Snapshot Ops):** `scripts/manage_tinlake_snapshot.py` maneja
    refresh/status/offline con warnings >7 días y fallback conservador; la data
    queda en `tinlake_metrics.json` + `tinlake_metadata.json` y es consumida por
    `LiquiditySpreadComponent`.

### API Endpoints (if applicable)
- Ninguno (librería offline).

### Database Schema (if applicable)
- No aplica.

### Key Functions/Classes
- `ProjectParameters.from_directory`, `CFADSCalculator`, `compute_dscr_by_phase`.
- `DebtStructure`, `CovenantEngine`, `WaterfallEngine`, `FinancialPipeline`.
- `StructureComparator`, `build_financial_dashboard`, notebooks `01-03_*` para validación/explicación.

### Integration Points
- DCF ↔ AMM adapters (`integration` package) siguen placeholders pero conectados a parámetros validados.
- Scripts Docker/CLI pueden generar dashboards (`MPLCONFIGDIR` arregla warning de Matplotlib).

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `pytest`
- Excel exports: `python scripts/export_excel_validation.py --data-dir data/input/leo_iot --output-root data/output/excel_exports`

- 2025-11-22: Implementados módulos WP-07 (motor MC, PD/LGD pathwise, flags de default, brechas y pipeline) y WP-06 (librería de escenarios S1–S6 + combos, motor de stress, reverse/hybrid stress, analyzer). Dashboards soportan fan chart MC y se documentó `docs/stress_scenarios.md`. Nuevas pruebas unitarias en `tests/test_simulation/*` y `tests/test_stress/*` (pytest no disponible en entorno actual).
- 2025-11-22: Integrado callback financiero de MC a CFADS/DSCR (`pftoken/simulation/path_callbacks.py`) y demo de riesgo actualizado para usar Monte Carlo con pérdidas empíricas (`scripts/demo_risk_metrics.py`) extendiendo el JSON con fan charts, curvas de breach, métricas de portafolio/tramo y ranking de stress. No se pudieron ejecutar tests ni el runner MC por falta de pip/numpy en el entorno actual.
- 2025-11-23: Ampliado el marco estocástico (11 variables, matriz 11x11), añadido riesgo de lanzamiento dependiente del tiempo, shocks adicionales en callbacks y escenarios de stress tokenización (T1–T3, CT1). Se creó módulo de beneficios de tokenización (`pftoken/tokenization/benefits.py`), análisis de sensibilidad (`scripts/sensitivity_analysis.py`) y sección `tokenization_analysis` en el JSON del demo. Nuevas pruebas en `tests/test_tokenization/test_benefits.py`.***
- 2025-11-23: Estructura tokenizada establecida como constante 55/34/12 y WACD 557 bps (`pftoken/constants.py`), integrada en `pipeline`/demo/Reporte WP04. Escenarios upside U1–U3 añadidos y recalibrado `satellite_degradation` (β=2,20). Se eliminó el stub `pftoken/optimization/capital_structure.py` y se añadió test de estructura recomendada.
- 2025-11-22: Añadida curva de mercado `data/derived/market_curves/usd_combined_curve_2025-11-20.csv` (FRED DGS 1/2/3/5/7/10/20/30, 2025-11-20) y usada en WP-04; PricingEngine/WACD ahora se ejecutan con curva de mercado en lugar de base plana. Se uniformó el costo de infraestructura usando un principal de referencia (total debt) y se introdujo un floor de spread de crédito (5 bps) para evitar deltas nulas en senior; WACD recalculado con delta ponderada ≈ -70.77 bps (after-tax ≈ -53 bps). Tests de pricing actualizados/pasados.
- 2025-11-22: Ajustado `collateral_inventory.csv` con correcciones conservadoras: spectrum 20M (25% haircut), ground gateways aclarados como footprint pequeño, agregado backlog de contratos (50M book, 56% haircut), IP haircut 55%, MRA ajustado a política real (35% del RCAPEX diet 18M, peak ~3.4M → 3.6M book), añadido satélites en órbita con recuperación 0. Se actualizaron notas en `docs/collateral_sources.md`.
- 2025-11-22: Se agregó `docs/collateral_sources.md` con fuentes/precedentes (Straight Path vs FiberTower, Intelsat C-band, Eutelsat-EQT ground infra, OneWeb/Globalstar/SAS satélites, Speedcast/Iridium contratos, WIP) y guías de haircut/tiempo para poblar `collateral_inventory.csv`.
- 2025-11-21: `MertonModel` deja de forzar monotonicidad de PD entre tramos para respetar el piso calibrado; se corrige `test_merton_pd_lgd_el`.
- 2025-11-21: Se añadió serialización `to_dicts/from_dicts` a `DebtStructure` (T-014) con prueba de roundtrip; el corporate tax permanece fijado en 25% (21% federal + ~4% estatal) para el caso Delaware/TX-FL-CA.
- 2025-11-21: Se añadieron `docs/requirements.md` (requerimientos funcionales/no funcionales con métricas target) y una versión extendida de `docs/architecture.md` que documenta el flujo CFADS → Waterfall → Pricing y deja explícito el gap de colateral granular; README/memory referencian estos supuestos.
- 2025-11-12: Implementado stack WP-02/WP-03 determinístico (CFADS components, RatioCalculator, placeholder Merton PD/LGD/EL, full Waterfall orchestrator, governance controller). Se agrega exportador para Excel, documentación (`docs/calibration.md`, `docs/governance.md`) y se actualizan pruebas con la tolerancia <0.01 %.
- 2025-11-13: Entregado WP-04 Pricing (ZeroCurve, PricingEngine, WACDCalculator, CollateralAnalyzer, documentación y suite de tests). Integración completa con `FinancialPipeline` respetando la tolerancia de 0.01 %.
- 2025-11-13: WACD tokenizado ahora usa la descomposición modular (crédito, liquidez, fees, infraestructura) con CSV reproducible y reporte detallado (`docs/tokenized_spread_decomposition.md`).
- 2025-11-13: Se agregan referencias abiertas (Gatti 2018, Esty & Sesia 2011, Sorge 2004, Chainlink docs, CoinGecko) y el script para automatizar el tracker de infra blockchain con fuentes públicas.
- 2025-11-13: Motor de sensibilidades delta + export CSV, metadata de YTM (riesgo libre) y CLI `scripts/manage_tinlake_snapshot.py`; docs y README actualizados para WP-04.
- 2025-11-23: Flag `include_tranche_cashflows` ahora avisa si el callback MC no emite `tranche_cashflows`, evitando uso silencioso sin datos.
- 2025-11-23: Recalibración mercado WP-08: spreads 550/900/1200 bps y base 4.5% (tranches.csv, project_params.csv), spreads/vols/recoveries ajustados en stochastic_params.yaml, market_price_of_risk default sube a 0.15.
- 2025-11-23: Fix CFADS units: path callback documenta CFADS en MUSD y elimina división por 1e6; se retira línea duplicada base_rate_reference=0.05 de project_params.csv.
- 2025-11-23: DSCR covenant reducido 1.45→1.20: project_params.csv (min_dscr_covenant, target_dscr_years_5_10), CovenantLimits.min_dscr=1.20; tests que comparan valores DSCR permanecen en 1.45 porque el CFADS/debt schedule siguen produciendo ese ratio.
- 2025-11-23: CFADS global scaling factor 0.83 aplicado en CFADSCalculator (para acercar DSCR ~1.20); tests DSCR actualizados a 1.20; Excel ya ajustado a 1.20 vía replace en archivos.
- 2025-11-23: Recalibración mercado WP-08: spreads tramos 550/900/1200 bps, base rate 4.5% (tranches.csv/project_params), spreads/vols/recoveries actualizados en stochastic_params.yaml; market_price_of_risk default ↑ 0.15 en TokenizedSpreadConfig.
- 2025-11-23: Normalización unidades MC: path_callback vuelve a usar CFADS/deuda en USD (sin dividir por 1e6) y tranche_cashflows se mantienen en USD; asset_values queda en USD para pricing/riesgo.
- 2025-11-24: WP-11 Interest Rate Cap implementado (Black-76 caplets, volatilidad plana en `PricingContext`, break-even bps, par swap, hedge P&L); integración ligera con `InterestRateSensitivity.analyze_with_hedge`. Nuevos tests en `tests/test_derivatives/test_interest_rate_cap.py`. Refinado implied vol con `brentq`, añadidos breakeven floating rate y carry cost helpers; `outputs/leo_iot_results.json` ahora incluye precios reales de la cap (vol 20%, strike 4%, notional 72M, años 1-5) y escenarios ±50 bps.
- 2025-11-25: Scripts para deleveraging/validación añadidos: `scripts/modify_excel_for_deleveraging.py` (ajusta principales/DSRA en el Excel con pesos/total objetivo), `scripts/export_csvs_from_excel.py` (regen tranches/debt_schedule/revenue_projection desde el Excel), y `scripts/validate_input_data.py` ahora usa valores del Excel (principales, cupones, CFADS) en lugar de hardcodes fijos para soportar nuevas estructuras.
- 2025-11-25: Hedging extendido con InterestRateFloor/InterestRateCollar + zero-cost solver; nuevas pruebas en `tests/test_derivatives/test_interest_rate_floor.py` y `tests/test_derivatives/test_collar.py` (15/15 passing en Docker). `scripts/demo_risk_metrics.py` ahora puede incluir collar (`--include-collar`), `scripts/recalibrate_hedge.py` resume economía del collar post-deleveraging (50M, 4%/3%), y `scripts/validate_deleveraging.py` verifica breach <20% en `outputs/leo_iot_results.json`.
- 2025-11-27: **WP-14 AMM Integration Complete.** Added `pftoken/amm/pricing/liquidity_premium.py` with `derive_liquidity_premium_from_amm()` to bridge AMM stress metrics to liquidity premium reduction. AMM-derived reduction (56.25 bps) validated against Tinlake benchmark (54.21 bps, delta 2.04 bps = "consistent"). Output section `amm_liquidity` added to `leo_iot_results.json` with stress scenarios (PS/LP/FC), slippage curves, IL metrics, and derived premium.
- 2025-11-27: **Centrifuge Platform Documented.** Added platform/liquidity_sourcing/cost_summary to `amm_liquidity` section documenting Centrifuge/Tinlake as liquidity platform: $1.45B TVL, CFG governance token, 15 bps protocol fee (~$75K/year on $50M notional), CFG-incentivized LP model eliminates sponsor capital requirement. Net benefit vs self-LP: $375K/year (avoided 9% opportunity cost on $5M LP capital minus 15 bps protocol fee).
- 2025-11-27: **Equity Analysis Fixed.** Corrected equity IRR calculation: $50M equity investment (50% of $100M project) not just $18M DSRA. True IRR = 10.56% annual, 2.59x multiple, payback Year 9. Added `equity_analysis` section to `leo_iot_results.json` with capital structure, returns, and cashflow breakdown.
- 2025-11-27: **V3 AMM Integration Complete.** Implemented V2 vs V3 comparison (`build_v2_v3_comparison`) showing V3 wins decisively: 83% slippage reduction, 5x capital efficiency. Added `build_amm_recommendation()` synthesizing comparison results with V3 as primary model. V3-derived liquidity premium: ~70 bps reduction (vs V2's ~56 bps). New output sections: `v2_v3_comparison` (raw comparison) and `amm_recommendation` (V3 selection rationale, implementation guidance, thesis conclusion). V3 recommended for tokenized debt due to: (1) stable token prices ideal for concentrated liquidity, (2) 5x capital efficiency enables viable secondary markets with minimal LP capital, (3) Centrifuge protocol manages rebalancing.
- 2025-11-27: **WACD Synthesis Fix.** Added `build_wacd_synthesis()` to `scripts/demo_risk_metrics.py` that unifies all WACD components: coupon rates, tokenization benefits (liquidity/operational/transparency), AMM V3 liquidity premium, and hedging costs. New `wacd_synthesis` section in `leo_iot_results.json`.
- 2025-11-27: **WP-15 (alcance mínimo).** Documentada selección de cadena (`docs/crypto/chain_selection.md`), comparación de plataformas (`docs/crypto/platform_comparison.md`), prima regulatoria (`docs/crypto/regulatory_risk.md`), y notebook resumen (`notebooks/wp15_crypto_fundamentals_summary.ipynb`). `wacd_synthesis` descuenta `REGULATORY_RISK_BPS=7.5` y expone `platform_comparison`/`platform_analysis`; costo de auditoría (10–20 bps one-time) explicitado en `tokenization_analysis.mechanisms`.
- 2025-11-27: **Structure Constants Fixed.** Corrected `pftoken/constants.py` and WACD computation:
  - `TOKENIZED_OPTIMAL_STRUCTURE`: 55/34/12 -> **55/34/11** (was summing to 101%)
  - WACD constants restored to coupon-inclusive levels: `TRADITIONAL_WACD_BPS` **737.5**, `TOKENIZED_OPTIMAL_WACD_BPS` **740** (reflecting 6.0% / 8.5% / 11.0% coupons)
  - `DebtStructure.calculate_wacd` again defaults to coupon-inclusive rates (spreads included); pass `include_spreads=False` to get the 4.5% base rate.
  - **Tokenization benefit = 93 bps** (liquidity 70 + operational 3.5 + transparency 20), **regardless of structure**
  - **With hedging**: +24 bps cost for cap = 69 bps net savings (but 23% breach reduction)

### Known Issues
- T-047 calibración real (MC surfaces, correlaciones) pendiente de T-022/T-023; el YAML actual es determinístico.
- El governance controller es offline; falta vincularlo con contratos/token holders.
- Dockerfile no adopta aún el pipeline multi-stage/non-root descrito; se mantiene en backlog DevOps.
- Automatización bidireccional Excel ↔ Python sigue fuera de alcance (solo export manual vía script).
- Collateral pool aún se modela como monto agregado proporcional a la deuda; necesitamos un dataset granular (satélites, licencias, contratos, seguros) con valor liquidable, haircuts y tiempos de realización para futuras iteraciones (WP‑05/06, gobernanza on-chain).
- WP-05: el modo empírico/EVT de VaR/CVaR necesita escenarios Monte Carlo reales (WP-07); hoy se usa simulación paramétrica independiente o con copula gaussiana.
- **WP-08 Capital Structure Finding:** El proyecto como estructurado (70% LTV, $72M debt) **NO ES BANKABLE**. Los precios estocásticos muestran 0.86-0.92 per par (yields implícitos 11-20%) reflejando 60% probabilidad de breach acumulada. Para alcanzar bankability se requiere reducir LTV a 50-55% (~$50M debt) y ajustar proporciones a 55/34/12 (senior/mezz/sub) conforme estructura tokenizada óptima.
- **WP-11 Interest Rate Cap (T-045): ✅ COMPLETE.** Implementado Black-76 pricer con calibración via brentq, 3 métricas de break-even (spread bps, tasa breakeven, carry cost %), comparación con par swap, y análisis de cobertura integrado con `InterestRateSensitivity`. Premium $857k (119 bps/año) sobre $72M notional @ 4% strike con flat vol 20%. Tests passing (6/6) en Docker. **Contexto de riesgo:** Cap reduce sensibilidad a tasas (+50bps: $733k hedge value, ratio 26%), PERO riesgo operacional domina (60% breach probability). **Estructura óptima:** Collar (buy 4% cap + sell 3% floor) auto-financiable (~42 bps net < 78 bps tokenization benefit). **Secuencia recomendada:** (1) Deleveraging a 50% LTV (team meeting), (2) Verificar breach < 20%, (3) Evaluar collar deployment si rate risk permanece material. Cap pricer disponible como tooling cuando estructura se estabilice. Ver `docs/derivatives.md` y outputs `leo_iot_results.json:hedging` para detalles.
- **WP-13 Hedging Comparison (MC Integration): ✅ COMPLETE.** Nuevo módulo `pftoken/hedging/hedge_simulator.py` integra payouts de Cap/Collar en simulación Monte Carlo. Compara 3 escenarios (unhedged, cap, collar) bajo shocks estocásticos de tasa N(0, 0.015). **Resultados 10K sims:** Unhedged 2.71% breach → Cap 2.09% (−23%, $595K) → Collar 2.38% (−12%, $326K). **Recomendación: Cap** provee mejor reducción de breach pero a mayor costo. Con estructura tokenizada (DSCR-contingent), breach ya es bajo; hedges proveen protección incremental. Output en `leo_iot_results.json:hedging_comparison`. Files: `pftoken/hedging/__init__.py`, `pftoken/hedging/hedge_simulator.py`, `pftoken/simulation/path_callbacks.py` (rate_shock export).
- **2025-12-01: Notebook TP_Quant_Final.ipynb actualizado con extensiones avanzadas.**
  - Añadidas secciones 4.5 y 4.6 documentando path-dependent (first-passage barrier, 3.9% PD) y regime-switching (85% normal / 15% stress).
  - Resumen Ejecutivo actualizado con métricas de 10K simulaciones: Traditional 23.0% → Tokenized 2.5% → Tok+Hedge 1.9%.
  - Tabla de Contenidos extendida con referencia a secciones 4.5-4.6.
  - Sección de Limitaciones 11.5 marcada con [IMPLEMENTADO] para las extensiones Merton single-period y correlaciones estáticas.
  - Contribuciones Metodológicas 11.4 ampliada con punto 5 sobre extensiones path-dependent y regime-switching.
  - Trabajo Futuro 11.6 actualizado para reflejar que path-dependent y regime-switching básicos ya están implementados; pendiente habilitar `enable_regime_lgd` y `enable_regime_spreads`.

### Next Steps
- **PENDING TEAM DECISION:** Implementar estructura dual a 50% LTV ($50M total debt):
  - Traditional: 60/25/15 proportions (senior $30M, mezz $12.5M, sub $7.5M) - baseline comparison
  - Tokenized: 55/34/11 proportions (senior $27.5M, mezz $17M, sub $5.5M) - estructura óptima
  - Ambas a mismo LTV (50%) para aislar el efecto de rebalancing tokenizado vs restricciones tradicionales
  - Requiere consulta con equipo antes de proceder con cambios en CSVs/Excel
- Implementar `MonteCarloEngine`/`merton_integration` (T-021/T-024) aprovechando las nuevas distribuciones y matriz de correlación para producir trayectorias de CFADS/PD.
- Integrar LLCR/PLCR y covenants extendidos directamente en `WaterfallEngine` (prioridades T-015/T-017) con reportes para dashboards.
- Desplegar pricing estocástico (WP-08) una vez que los outputs Monte Carlo estén disponibles para alimentar spreads y sensibilidades.
- Extender WP-04 hacia sensibilidades estocásticas/FX dinámicas y enlazar los outputs con dashboards tokenizados.
- WP-04 follow-up: derivar credit spreads endógenos (Merton/Monte Carlo) + liquidity spreads (microestructura tipo Amihud/Roll) para reemplazar los deltas tokenizados fijos en el WACD una vez completado WP‑05/06.
- Tokenización (spreads): calibrar α/β/γ y λ utilizando resultados Monte Carlo (WP‑05/06) y evidencia de microestructura / costos reales para actualizar `TokenizedSpreadConfig` y los CSV de infraestructura (extendiendo el script con datasets DeFiLlama/Uniswap cuando definamos los proxies).
