# Project Finance Tokenization Simulator

Proyecto académico/industrial para modelar la tokenización de deuda estructurada
en proyectos de infraestructura. La librería `pftoken` contiene los módulos
necesarios para:

- Modelar CFADS en proyectos satelitales (LEO IoT).
- Construir y evaluar cascadas de pagos (waterfall) con múltiples tramos.
- Ejecutar simulaciones Monte Carlo y escenarios de estrés.
- Valorar tramos bajo métodos determinísticos y estocásticos.
- Medir métricas de riesgo (EL, VaR, CVaR) y optimizar la estructura de capital.
- Centralizar parámetros financieros/operativos validados (Pydantic) con utilidades de carga desde CSV.
- Calcular CFADS con descomposición detallada por línea para escenarios determinísticos y shocks.
- Analizar pools AMM (Uniswap v2/v3) para comparar precios de mercado vs. DCF.
- Generar un dashboard base (matplotlib) con CFADS vs servicio de deuda, DSCR y estructura de capital.

> **Nota:** Todos los módulos se entregan como *placeholders*; sirven como
andamiaje para iteraciones futuras.

## Repository Structure

```
project-finance-tokenization/
├── Dockerfile
├── docker-compose.yml
├── memory.md
├── requirements.txt
├── setup.py
├── README.md
├── pftoken/
│   ├── amm/
│   │   ├── analysis/
│   │   ├── core/
│   │   ├── pricing/
│   │   └── utils/
│   ├── integration/
│   ├── config/
│   ├── models/
│   ├── waterfall/
│   ├── pricing/
│   ├── pricing_mc/
│   ├── risk/
│   ├── stress/
│   ├── simulation/
│   ├── optimization/
│   ├── derivatives/
│   ├── viz/
│   └── utils/
├── tests/
│   ├── test_amm/
│   └── test_integration/
├── data/
│   ├── input/
│   │   ├── amm_config/
│   │   └── templates/
│   └── output/
│       └── amm_simulations/
├── notebooks/
│   ├── 06_stress_testing.ipynb
│   ├── 08_amm_introduction.ipynb
│   └── ...
├── docs/
│   ├── amm/
│   └── examples/amm_examples/
├── scripts/
│   ├── compare_dcf_market.py
│   ├── optimize_pool_ranges.py
│   └── run_amm_stress.py
└── .github/workflows/
```

Cada directorio corresponde al plan entregado (WP-01 a WP-13). Los módulos
contienen `not_implemented()` como recordatorio explícito del trabajo pendiente.

## Local Development

### Entorno Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Contenedor Docker

```bash
docker compose -f quant-token-compose.yml build
docker compose -f quant-token-compose.yml up -d
# Ejecutar comandos dentro del contenedor
docker compose -f quant-token-compose.yml run --rm quant_token_app pytest
```

El contenedor expone el puerto `8000` (servidor HTTP simple) y monta el código
local en `/app` para permitir hot-reload durante el desarrollo.

## Tests

- Ejecución local: `pytest`
- Via Docker: `docker compose -f quant-token-compose.yml run --rm quant_token_app pytest`
- `tests/test_amm/`: nuevo paquete de tests placeholder para los módulos AMM.

Cada archivo en `tests/` está marcado con `pytest.skip()` hasta que los módulos
de negocio estén implementados.

## WP-04 Completeness Summary

### QF-1: Delta Sensitivity Analysis ✅
- 7 escenarios base (Base, Tinlake ±50 %, β 0.3/0.7, Infra×2, Stressed) con
  escalado lineal de componentes (`pftoken/pricing/spreads/tokenized.py`
  alrededor de las líneas 200‑250).
- Cada escenario exporta `delta_credit/liquidity/origination/servicing/infrastructure`,
  `total_delta_bps`, `tokenized_wacd` y `wacd_delta_bps` a
  `data/derived/sensitivities/wacd_delta_sensitivity_<timestamp>.csv`.
- El WACD after-tax se recalcula para cada caso usando la suma ponderada y el
  tax rate del `PricingContext`.

### QF-2: YTM Clarification ✅
- Los precios por tramo se descuentan contra la curva libre de riesgo
  (`pftoken/pricing/base_pricing.py:45-221`), serializando `ytm_label`,
  `risk_free_curve_rate`, `spread_over_curve` y `explanatory_note` cuando se
  invoca `price_from_waterfall(..., as_dict=True)`.
- `_calculate_ytm()` documenta explícitamente que el solver ignora spreads
  crediticios (`pftoken/pricing/base_pricing.py:224-243`).
- `tests/test_pricing/test_pricing_engine.py:test_ytm_is_below_coupon_when_price_above_par`
  garantiza que los YTM risk-free queden por debajo del cupón cuando el precio
  está sobre par.

### QF-3: Tinlake Snapshot Procedure ✅
- Operativa unificada en `scripts/manage_tinlake_snapshot.py`: `PYTHONPATH=.
  python scripts/manage_tinlake_snapshot.py --status|--force-refresh|--offline`
  muestra edad, estado y warnings (>7 días).
- El snapshot se guarda en `data/derived/liquidity/tinlake_metrics.json` con
  metadatos en `tinlake_metadata.json`; existe un fallback conservador cuando la
  API DeFiLlama no está disponible (`pftoken/pricing/spreads/tinlake.py`).
- `LiquiditySpreadComponent` consume automáticamente el snapshot y expone la
  data en la metadata de cada componente.

## Datos

- `data/input/leo_iot/`: CSVs de ejemplo para parámetros, tramos y proyecciones.
- `data/input/leo_iot/revenue_projection.csv`: ahora incluye columnas de `dsra_funding`, `dsra_release`, `mra_funding` y `mra_use` para rastrear reservas junto con `rcapex`.
- `data/input/`: **Inmutable**. Nunca se modifica desde scripts; toda salida derivada vive en `data/derived/` o `data/output/`.
- `data/input/amm_config/`: Configuraciones JSON/CSV para pools tokenizados.
- `data/input/templates/`: Plantillas para nuevos datasets.
- `data/derived/leo_iot/`: Parámetros de calibración generados (ej. `stochastic_params.yaml`), sincronizados manualmente desde Excel.
- `data/output/amm_simulations/`: Resultado esperado de simulaciones AMM (placeholders).
- `data/output/`: Destino esperado de resultados de simulación, estrés y reportes (incluyendo las exportaciones para Excel).

## Scripts

- `scripts/run_simulation.py`: Orquestación de simulaciones (placeholder).
- `scripts/generate_report.py`: Generación de dashboards (placeholder).
- `scripts/validate_data.py`: Validación de datasets (placeholder).
- `scripts/export_excel_validation.py`: Exporta snapshots CSV (CFADS, ratios, waterfall) a `data/output/excel_exports/<timestamp>/` para refrescar manualmente el workbook `TP_Quant_Validation.xlsx` respetando la tolerancia de 0.01 %.
- `scripts/run_amm_stress.py`: Stress de liquidez AMM (placeholder con métricas básicas).
- `scripts/optimize_pool_ranges.py`: Optimización de rangos Uniswap v3 mediante SciPy.
- `scripts/compare_dcf_market.py`: Comparación rápida de valuaciones DCF vs. precio de pool.
- `scripts/update_blockchain_infra.py`: Consulta Etherscan/Arbiscan/Polygonscan/Optimism/Basescan + CoinGecko para regenerar `data/derived/tokenized_infra_costs.csv`. Basta con exportar `ETHERSCAN_API_KEY` (V2 multi-chain); se mantienen env vars específicas (`ARBISCAN_API_KEY`, etc.) como overrides opcionales.
- Visualización: `pftoken.viz.dashboards.build_financial_dashboard` genera figuras base para reportes.
- Validación Excel ↔ Python: `TP_Quant_Validation.xlsx` compara CFADS/DSCR generados por el código contra la hoja T‑047. Ejecuta `pytest tests/test_excel_validation.py` o el notebook `notebooks/02_excel_vs_python.ipynb` para revisar las diferencias.

## WP-02/WP-03 Pipeline

- Regenera los CSV críticos a partir del Excel fuente con `python scripts/validate_input_data.py`. Este script verifica montos de tramos y la nueva proyección de CFADS (con DSRA/MRA/RCAPEX).
- Orquesta CFADS → waterfall → ratios mediante `pftoken.pipeline.FinancialPipeline`.
- Ejecuta todo dentro de Docker:
    - CFADS incluye un RCAPEX “diet” de 18 MUSD distribuidos entre los años 6‑15 ({1.2, 1.5, 1.65, 1.7, 1.55, 3.4, 2.25, 2.0, 1.5, 1.25} MUSD) equivalente a ~8% de la flota cada 3 años, desplazando la mayor parte del mantenimiento mayor al periodo post‑deuda.
    - Las reservas DSRA/MRA se modelan vía las columnas `dsra_*` y `mra_*` en `revenue_projection.csv` (DSRA inicial = 18 MUSD fondeada por equity al cierre para cubrir los 4 años de gracia, MRA = **50%** del próximo RCAPEX acumulado durante los 3 años previos con contribuciones solapadas).
    - Esta calibración eleva el CFADS total a 196.5 MUSD y mantiene DSCR en el rango 1.35‑1.65x durante los años operativos (6‑15), dejando >100 bps de colchón vs. el piso de 1.25x.
    - Fuentes y usos: 72 MUSD deuda + 54 MUSD equity; de este equity, 18 MUSD se depositan en el DSRA al cierre para cubrir los intereses del período de gracia sin recurrir a aportes posteriores.

```bash
docker compose -f quant-token-compose.yml -p qptf build
docker compose -f quant-token-compose.yml -p qptf up -d
docker compose -f quant-token-compose.yml -p qptf exec quant_token_app python scripts/validate_input_data.py
docker compose -f quant-token-compose.yml -p qptf exec quant_token_app pytest tests/ -v
```

- Los notebooks en `notebooks/0*_*.ipynb` documentan validación T‑047, comparación Excel vs Python y la mecánica del waterfall.
- El servicio Docker corre como usuario no root (`appuser`, UID configurable vía `UID/GID`) y expone un healthcheck (`python -m pftoken.healthcheck`). Compose aplica `restart: unless-stopped` y `mem_limit: 1g` para mantener la política de ejecución.


## WP-04 – Pricing & Curves

- **Curvas**: `pftoken.pricing.zero_curve.ZeroCurve` bootstrapea depósitos/swaps y permite shocks paralelos o por bucket. Usa `scipy.optimize.brentq` y mantiene la tolerancia de 0.01 %.
- **PricingEngine**: consume `FinancialPipeline.run()` (CFADS + waterfall) y descuenta cada tramo para obtener precio limpio, YTM, duración y convexidad. Incluye gráficos Matplotlib in-memory.
- **WACD / Tokenización**: `pftoken.pricing.wacd.WACDCalculator` compara escenarios tradicional vs. tokenizado. El delta tokenizado se deriva automáticamente de los componentes (liquidez, origination, servicing e infraestructura) y sólo recurre a overrides manuales si el `PricingContext` lo solicita.
- **Tokenized Spread Decomposition**: `pftoken.pricing.spreads.TokenizedSpreadModel` reemplaza los deltas fijos del WACD con componentes trazables (crédito, liquidez, originación, servicing e infraestructura). El tracker escribe `data/derived/tokenized_infra_costs.csv` y la documentación vive en `docs/tokenized_spread_decomposition.md`.
- **Sensibilidades Delta**: `TokenizedSpreadModel.simulate_delta_scenarios()` genera 7 escenarios estándar (Tinlake ±50 %, beta overrides, Infra ×2, stressed) y exporta CSVs auditables para alimentar `WACDCalculator`.
- **Colateral**: `pftoken.pricing.collateral_adjust.CollateralAnalyzer` aplica haircuts + descuento temporal y devuelve LGD ajustadas por tramo.
- **Curvas reales**: snapshots FRED (Par Yield DGS1–DGS30, swap rates DSWP* y curvas combinadas) viven en `data/derived/market_curves/` y se cargan con `pftoken.pricing.load_zero_curve_from_csv`.
- **Documentación**: ver `docs/pricing.md` para ejemplos detallados.
- **Tests**: `pytest tests/test_pricing tests/test_integration/test_pricing_pipeline.py`
  ejecuta el stack completo con la data canónica `data/input/leo_iot/`.

### Stochastic Calibration Snapshot

- `pftoken.models.calibration` carga tanto los parámetros estructurales (PD/LGD) como las distribuciones para variables aleatorias.
- `pftoken.simulation.StochasticVariables` genera lognormales/beta/bernoulli/normal con soporte para antithetic variates.
- `pftoken.simulation.CorrelatedSampler` utiliza la matriz `correlation.matrix` del YAML para producir muestras correlacionadas (Cholesky) y alimentar futuras simulaciones Monte Carlo.

## CI/CD

Workflows en `.github/workflows/` ejecutan pruebas (`tests.yml`) y análisis
estático (`lint.yml`) en GitHub Actions con Python 3.12.

## Referencias

- Esty (2004), Gatti (2018)
- BIS (2023), OECD (2024)
- Reisin (2025)
