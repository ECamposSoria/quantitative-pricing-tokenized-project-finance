markdown# System Memory

## Last Updated: 2025-10-31 17:19 UTC
## Version: 0.3.1

### Current Architecture
- `pftoken` incluye el paquete `amm`, el módulo `integration` y un modelo de parámetros centralizado (`ProjectParameters`).
- Nuevas utilidades de visualización permiten construir dashboards determinísticos con matplotlib (CFADS vs servicio de deuda, DSCR, estructura de capital, ratios LLCR/PLCR).
- Subpaquetes para stress, viz y simulation conservan andamiaje pendiente de lógica de negocio.

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
- Cálculo CFADS con descomposición detallada y escenarios.
- Integración DCF↔AMM para decisiones de liquidez y feedback de spreads.
- Dashboard base (`pftoken.viz.dashboards.build_financial_dashboard`) que genera figuras para CFADS vs deuda, DSCR, ratios LLCR/PLCR y estructura de capital.
- CLI utilidades para estrés AMM, optimización de rangos y comparación DCF vs mercado.

### API Endpoints (if applicable)
- Ninguno (librería offline).

### Database Schema (if applicable)
- No aplica.

### Key Functions/Classes
- `ProjectParameters.from_directory` para cargar parámetros validados.
- `calculate_cfads` y `CFADSScenarioInputs` para estados de resultado proyectados.
- `build_financial_dashboard` para componer figuras de reporte.

### Integration Points
- `dcf_to_amm.allocate_liquidity` conecta CFADS con decisiones AMM.
- `feedback_loop.update_discount_rate` retroalimenta spreads de mercado.

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `pytest`

### Recent Changes
- 2025-02-14: Validated parameter model, CFADS pipeline e integración test.
- 2025-02-14: Dashboard base con matplotlib y actualización de docs/README.

### Known Issues
- Módulos de waterfall, stress avanzado, correlaciones y sensibilidad siguen como placeholders.
- Ratios LLCR/PLCR usan thresholds simplificados hasta definir covenants específicos.

### Next Steps
- Extender dashboard con resultados Monte Carlo (VaR/CVaR, heatmaps, tornado) una vez que los módulos estén implementados.
- Automatizar exportación a notebooks/reportes (T-048/T-049).
