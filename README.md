# Project Finance Tokenization Simulator

Proyecto académico/industrial para modelar la tokenización de deuda estructurada
en proyectos de infraestructura. La librería `pftoken` contiene los módulos
necesarios para:

- Modelar CFADS en proyectos satelitales (LEO IoT).
- Construir y evaluar cascadas de pagos (waterfall) con múltiples tramos.
- Ejecutar simulaciones Monte Carlo y escenarios de estrés.
- Valorar tramos bajo métodos determinísticos y estocásticos.
- Medir métricas de riesgo (EL, VaR, CVaR) y optimizar la estructura de capital.

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
├── .gitignore
├── .dockerignore
├── pftoken/
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
├── data/
├── notebooks/
├── docs/
├── scripts/
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

Cada archivo en `tests/` está marcado con `pytest.skip()` hasta que los módulos
de negocio estén implementados.

## Datos

- `data/input/leo_iot/`: CSVs de ejemplo para parámetros, tramos y proyecciones.
- `data/input/templates/`: Plantillas para nuevos datasets.
- `data/output/`: Destino esperado de resultados de simulación, estrés y reportes.

## Scripts

- `scripts/run_simulation.py`: Orquestación de simulaciones (placeholder).
- `scripts/generate_report.py`: Generación de dashboards (placeholder).
- `scripts/validate_data.py`: Validación de datasets (placeholder).

## CI/CD

Workflows en `.github/workflows/` ejecutan pruebas (`tests.yml`) y análisis
estático (`lint.yml`) en GitHub Actions con Python 3.12.

## Referencias

- Esty (2004), Gatti (2018)
- BIS (2023), OECD (2024)
- Reisin (2025)
