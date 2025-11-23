markdown# System Memory

## Last Updated: 2025-11-22 02:50 UTC
## Version: 0.7.0

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
- CFADS deterministic components (`pftoken.models.cfads_components`) verifican ingresos/OPEX/CAPEX/impuestos por año y se validan automáticamente contra Excel con tolerancia <0.01 %.
- `RatioCalculator` produce DSCR por fase y LLCR/PLCR por tramo usando los umbrales compartidos (grace 1.0x, ramp 1.15x, steady 1.25x); los resultados alimentan `CovenantEngine`.
- Placeholder de calibración T‑047 (`data/derived/leo_iot/stochastic_params.yaml`) consumido mediante `load_placeholder_calibration`; `MertonModel` ahora devuelve PD/LGD/EL vectorizados con pruebas unitarias.
- `WaterfallOrchestrator` coordina CFADS → WaterfallEngine → reservas con DSRA inicial fijo (18 MUSD) y MRA = 50 % del próximo RCAPEX; registra equity IRR y saldos DSRA/MRA por período.
- `StructureComparator` amplía el output con métricas de liquidez (cobertura DSRA/MRA) y la comparación global se integra en `FinancialPipeline`.
- Gobernanza offline documentada en `docs/governance.md` y soportada por `GovernanceController`, `ThresholdPolicy`, `StaticOracle` y `LoggingAction`.
- `StochasticVariables` + `CorrelatedSampler` (WP-07 T-022/T-023) generan distribuciones lognormal/beta/normal/bernoulli con antithetic variates y matrices de correlación validadas (Cholesky + eigenvalue check). Los parámetros provienen de `data/derived/leo_iot/stochastic_params.yaml`.
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
- Se agregó `scripts/demo_risk_metrics.py` para ejecutar WP-05 rápidamente con los inputs LEO IoT y guardar/emitir `outputs/wp05_risk_metrics.json`.
- Nota pendiente: conectar EVT tail fits y Efficient Frontier al output WP-05 cuando existan escenarios Monte Carlo (WP-07); hoy solo se expone EL/VaR/CVaR paramétrico y concentración.
- Hallazgo frontier (demo WP-05 actual, sin restricciones externas): con el mismo riesgo (CVaR ≈ 2.6M), la estructura eficiente es ~3% senior / 91% mezz / 6% sub vs la actual 60/25/15; retorno 8.61% vs 7.53% (+108 bps). Motivo: mezz (8.5% cupón, PD 3%, LGD 55%) ofrece mejor trade-off que senior (6.5% cupón, PD 1%, LGD 40%) y sub (12% cupón, PD 10%, LGD 100%). Caveat: en la realidad rating agencies/mandatos exigen 60% senior; esta es la “ineficiencia” cuantificada si se relaja esa restricción (tokenizado).
- Comparación dual tradicional vs tokenizado: `FinancialPipeline` puede devolver `structure_comparison` (opt-in vía `compare_structures`), descomponiendo valor recuperable por rebalancing (gap a la frontera) y premio de liquidez (`tokenization_spread_reduction_bps`), con chequeo opcional de restricciones tradicionales (`traditional_constraints`).
- Estructura tokenizada optimizada documentada: 55/34/12 (senior/mezz/sub) seleccionada vía Pareto 3D (riesgo, retorno, WACD) con tolerancia ±1%, 500 muestras, seed=42. Se integra en `generate_wp04_report.py` como fila “Tokenizado (óptimo)” sin alterar la estructura tradicional 60/25/15.
- WACD optimizado: `WACDCalculator.compute_with_weights` permite recalcular WACD con pesos alternativos; `generate_wp04_report.py` ahora ejecuta frontier WP-05 dentro del reporte y añade sección de escenarios de estructura (tradicional, tokenizado actual y tokenizado óptimo) con WACD after-tax y violaciones de restricciones si aplica.
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

### Known Issues
- T-047 calibración real (MC surfaces, correlaciones) pendiente de T-022/T-023; el YAML actual es determinístico.
- El governance controller es offline; falta vincularlo con contratos/token holders.
- Dockerfile no adopta aún el pipeline multi-stage/non-root descrito; se mantiene en backlog DevOps.
- Automatización bidireccional Excel ↔ Python sigue fuera de alcance (solo export manual vía script).
- Collateral pool aún se modela como monto agregado proporcional a la deuda; necesitamos un dataset granular (satélites, licencias, contratos, seguros) con valor liquidable, haircuts y tiempos de realización para futuras iteraciones (WP‑05/06, gobernanza on-chain).
- WP-05: el modo empírico/EVT de VaR/CVaR necesita escenarios Monte Carlo reales (WP-07); hoy se usa simulación paramétrica independiente o con copula gaussiana.

### Next Steps
- Implementar `MonteCarloEngine`/`merton_integration` (T-021/T-024) aprovechando las nuevas distribuciones y matriz de correlación para producir trayectorias de CFADS/PD.
- Integrar LLCR/PLCR y covenants extendidos directamente en `WaterfallEngine` (prioridades T-015/T-017) con reportes para dashboards.
- Desplegar pricing estocástico (WP-08) una vez que los outputs Monte Carlo estén disponibles para alimentar spreads y sensibilidades.
- Extender WP-04 hacia sensibilidades estocásticas/FX dinámicas y enlazar los outputs con dashboards tokenizados.
- WP-04 follow-up: derivar credit spreads endógenos (Merton/Monte Carlo) + liquidity spreads (microestructura tipo Amihud/Roll) para reemplazar los deltas tokenizados fijos en el WACD una vez completado WP‑05/06.
- Tokenización (spreads): calibrar α/β/γ y λ utilizando resultados Monte Carlo (WP‑05/06) y evidencia de microestructura / costos reales para actualizar `TokenizedSpreadConfig` y los CSV de infraestructura (extendiendo el script con datasets DeFiLlama/Uniswap cuando definamos los proxies).
