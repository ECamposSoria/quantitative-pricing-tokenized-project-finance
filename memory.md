markdown# System Memory

## Last Updated: 2025-02-14 16:30 UTC
## Version: 0.3.0

### Current Architecture
- `pftoken` incluye el paquete `amm`, el módulo `integration` y ahora un modelo de parámetros centralizado (`ProjectParameters`) que valida entradas financieras/operativas con Pydantic.
- Subpaquetes existentes (config, models, waterfall, pricing, pricing_mc, risk, stress, simulation, optimization, derivatives, viz, utils) disponen de andamiaje; `models` contiene lógica CFADS y loaders de datos tipados.
- Stress module mantiene `liquidity_stress`; viz ofrece `amm_viz` y `liquidity_heatmap`.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- Libraries: numpy, pandas, scipy, matplotlib, pytest, jupyter, numpy-financial, eth-abi, pydantic

### Container Setup
- Base Image: `python:3.12-slim`
- Services: `app` (HTTP placeholder)
- Ports: `8000:8000`
- Volumes: repo bind-mounted en `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`

### Implemented Features
- AMM scaffolding (pools V2/V3, pricing/analysis utils, swap engine, LP management).
- Integración DCF↔AMM (pipelines, propagation, feedback loops).
- Validación completa de parámetros (`ProjectParameters.from_directory`) con utilidades CSV y comprobaciones de pesos de tramos, correlaciones Monte Carlo, reservas y covenants.
- Cálculo CFADS (`calculate_cfads`) con desglose de ingresos, EBITDA, impuestos, CAPEX, ΔWC y soporte de escenarios.
- CLI scripts para estrés AMM, optimización de rangos y comparación DCF vs. mercado.
- Datos, docs y notebooks incluyen configuraciones AMM y parámetros financieros extendidos.

### API Endpoints (if applicable)
- Ninguno (librería offline).

### Database Schema (if applicable)
- No aplica.

### Key Functions/Classes
- `pftoken.models.ProjectParameters`: modelo maestro validado de inputs financieros/operativos.
- `pftoken.models.calculate_cfads` & `CFADSModel`: motor CFADS con escenarios (`CFADSScenarioInputs`).
- `pftoken.amm.core.pool_v2.ConstantProductPool`: modelo de pool constante con swaps y gestión de liquidez.

### Integration Points
- `pftoken.integration.dcf_to_amm.allocate_liquidity` conecta CFADS con decisiones de liquidez AMM.
- `pftoken.integration.feedback_loop.update_discount_rate` retroalimenta spreads de mercado.

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `pytest`

### Recent Changes
- 2025-02-14: Creación del paquete AMM, integraciones y documentación inicial.
- 2025-02-14: Implementado `ProjectParameters` (Pydantic), loaders CSV y cálculo CFADS con nuevos tests.

### Known Issues
- La mayoría de módulos financieros (waterfall, ratios avanzados, stress complejo) siguen como placeholders.
- Tests de muchos paquetes continúan en `pytest.skip`; sólo parámetros/CFADS tienen cobertura real.

### Next Steps
- Completar lógica de waterfall, ratios y estrés aprovechando el modelo de parámetros validado.
- Añadir notebooks y tests funcionales que consuman `calculate_cfads` e integren Monte Carlo.
