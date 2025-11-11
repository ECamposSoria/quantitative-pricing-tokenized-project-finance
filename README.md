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
