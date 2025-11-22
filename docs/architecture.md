# System Architecture

Estado: Documentación actualizada para WP-01/WP-02, con interfaces pensadas para WP-03/WP-04. Las capas estocásticas y AMM se describen a nivel de contratos y quedan para iteraciones posteriores.

## Panorama General
- **Origen de datos:** `data/input/leo_iot/*.csv` (parámetros de proyecto, tramos, proyección CFADS, calendario de deuda, RCAPEX) validados contra `Proyecto LEO IOT.xlsx` mediante `scripts/validate_input_data.py`.
- **Pipeline determinístico (WP-02/WP-03):** carga de parámetros → CFADS → ratios → waterfall + reservas → pricing base (WP-04) → dashboards.
- **Extensiones futuras:** Monte Carlo y stress testing (WP-07/WP-06), pricing estocástico (WP-08), optimización (WP-10) y AMM (WP-14) reaprovechan las mismas interfaces de entrada/salida.

## Flujo de Datos
1) **Capa de parámetros:** `pftoken.models.params.ProjectParameters` agrega configuraciones de proyecto y tramos; loaders CSV producen dataclasses inmutables.  
2) **CFADS:** `pftoken.models.cfads_components.CFADSCalculator` suma ingresos, OPEX, CAPEX, impuestos y aplica gracia/ramping para obtener CFADS por período.  
3) **Ratios:** `pftoken.models.ratios.RatioCalculator` calcula DSCR por fase, LLCR/PLCR por tramo y marca breaches de covenants.  
4) **Waterfall:** `pftoken.waterfall.WaterfallOrchestrator` distribuye CFADS según prelación (interés/principal/DSRA/MRA/dividendos) y devuelve flujos por tramo + métricas (equity IRR, coberturas).  
5) **Pricing determinístico:** `pftoken.pricing` consume flujos por tramo y una curva libre de riesgo (`ZeroCurve`) para obtener precio/YTM/duración/convexidad y WACD tradicional vs tokenizado.  
6) **Visualización:** `pftoken.viz.dashboards` genera gráficos (CFADS vs servicio, DSCR, cascada, reservas, radar de estructura).

## Módulos y Contratos Clave
- **Modelos y datos (WP-02):**
  - `ProjectParameters.from_directory(data_dir)` → `ProjectParameters`: expone `cfads_dataframe`, `tranches`, `rcapex_schedule`.
  - `CFADSCalculator.run(params)` → `CFADSResult`: series de ingresos, OPEX, CAPEX, impuestos, CFADS.
- **Ratios y covenants (WP-02/WP-03):**
  - `RatioCalculator.compute(cfads, debt_structure)` → `RatioResults`: DSCR por fase, LLCR/PLCR, breaches.
  - `CovenantEngine.evaluate(ratios)` → lista de `CovenantBreach`.
- **Waterfall (WP-03):**
  - `DebtStructure.from_tranche_params(params.tranches)` → `DebtStructure`: pesos, tasas, calendario.
  - `WaterfallOrchestrator.run(cfads, debt_structure, params)` → `FullWaterfallResult`: flujos por tramo (interés/principal), DSRA/MRA movements, equity distributions.
- **Pricing (WP-04):**
  - `ZeroCurve.bootstrap(instruments)` → curva spot/forwards.
  - `PricingEngine.price_tranche(tranche_flows, zero_curve, pricing_context)` → `TranchePricingMetrics` (precio, YTM, duración, convexidad).
  - `WACDCalculator.compare_traditional_vs_tokenized(debt_structure, pricing_context)` → delta WACD (after-tax).
  - `CollateralAnalyzer.apply(tranche_cashflows, collateral_inputs, zero_curve)` ajusta LGD con haircuts y descuento temporal.
- **Puntos de extensión (WP-06/WP-07/WP-14):**
  - `pftoken.simulation` (Monte Carlo, correlaciones, flags de default) consumirá `ProjectParameters` y devolverá trayectorias de CFADS/ratios.
  - `pftoken.stress` aplicará shocks sobre parámetros/curva y reusará `WaterfallOrchestrator` + `PricingEngine`.
  - `pftoken.amm` conectará precios DCF (pricing) con precios de pool (Pool V2/V3) vía adaptadores.

## Supuestos de Colateral
- Colateral modelado de forma agregada: haircuts y tiempo de liquidación se fijan en `PricingContext` y se aplican con `CollateralAnalyzer`.
- Falta un inventario granular por activo (satélites/licencias/contratos/seguros) con valor liquidable y tiempos de realización. Este vacío debe cubrirse en WP-05/06; los resultados actuales se consideran preliminares.

## Dependencias Externas
- **Core:** numpy, pandas, scipy, matplotlib.
- **Infra:** sin servicios externos obligatorios; llamadas opt-in a APIs públicas (Etherscan/CoinGecko) sólo en scripts específicos.

## Deployment / Entorno
- Docker base `python:3.12-slim`, servicio único `quant_token_app`, usuario no root, healthcheck `python -m pftoken.healthcheck`, `PYTHONPATH=/app`.
- Ejecución típica: `docker compose -f quant-token-compose.yml -p qptf up -d` y `pytest` dentro del contenedor o venv local.
