# Project Finance Tokenization Simulator

Proyecto académico/industrial para modelar la tokenización de deuda estructurada
en proyectos de infraestructura. La librería `pftoken` contiene los módulos
necesarios para:

- Modelar CFADS en proyectos satelitales (LEO IoT).
- Construir y evaluar cascadas de pagos (waterfall) con múltiples tramos.
- Ejecutar simulaciones Monte Carlo y escenarios de estrés.
- Valorar tramos bajo métodos determinísticos y estocásticos.
- Medir métricas de riesgo (EL, VaR, CVaR) y optimizar la estructura de capital.
- Analizar pools AMM (Uniswap v2/v3) para comparar precios de mercado vs. DCF.

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
docker compose build
docker compose up -d
# Ejecutar comandos dentro del contenedor
docker compose run --rm app pytest
```

El contenedor expone el puerto `8000` (servidor HTTP simple) y monta el código
local en `/app` para permitir hot-reload durante el desarrollo.

## Tests

- Ejecución local: `pytest`
- Via Docker: `docker compose run --rm app pytest`
- `tests/test_amm/`: nuevo paquete de tests placeholder para los módulos AMM.

Cada archivo en `tests/` está marcado con `pytest.skip()` hasta que los módulos
de negocio estén implementados.

## Datos

- `data/input/leo_iot/`: CSVs de ejemplo para parámetros, tramos y proyecciones.
- `data/input/amm_config/`: Configuraciones JSON/CSV para pools tokenizados.
- `data/input/templates/`: Plantillas para nuevos datasets.
- `data/output/amm_simulations/`: Resultado esperado de simulaciones AMM (placeholders).
- `data/output/`: Destino esperado de resultados de simulación, estrés y reportes.

## Scripts

- `scripts/run_simulation.py`: Orquestación de simulaciones (placeholder).
- `scripts/generate_report.py`: Generación de dashboards (placeholder).
- `scripts/validate_data.py`: Validación de datasets (placeholder).
- `scripts/run_amm_stress.py`: Stress de liquidez AMM (placeholder con métricas básicas).
- `scripts/optimize_pool_ranges.py`: Optimización de rangos Uniswap v3 mediante SciPy.
- `scripts/compare_dcf_market.py`: Comparación rápida de valuaciones DCF vs. precio de pool.

## CI/CD

Workflows en `.github/workflows/` ejecutan pruebas (`tests.yml`) y análisis
estático (`lint.yml`) en GitHub Actions con Python 3.12.

## Referencias

- Esty (2004), Gatti (2018)
- BIS (2023), OECD (2024)
- Reisin (2025)
