markdown# System Memory

## Last Updated: 2025-10-31 18:05 UTC
## Version: 0.3.2

### Current Architecture
- `pftoken` mantiene el modelo de parámetros validado (`ProjectParameters`) conectado a módulos determinísticos (CFADS, ratios, dashboard) y AMM/integration scaffolding.
- Dataset LEO IoT ajustado para representar un caso financiable (revenues mayores, RCAPEX moderado) preservando backups `*_ORIGINAL.csv`.
- Viz package expone dashboard matricial y scripts pueden generar PNGs vía Docker/venv con Matplotlib cache configurado.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- Libraries: numpy, pandas, scipy, matplotlib, pytest, jupyter, numpy-financial, eth-abi, pydantic

### Container Setup
- Base Image: `python:3.12-slim`
- Services: `app` (HTTP placeholder)
- Ports: `8000:8000`
- Volumes: repo bind-mounted en `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`, `MPLCONFIGDIR=/app/.mplconfig`

### Implemented Features
- CFADS pipeline con descomposición detallada, escenarios, y ratios (DSCR/LLCR/PLCR) integrados.
- Dashboard base (`build_financial_dashboard`) que grafica CFADS vs servicio de deuda, DSCR, ratios LLCR/PLCR y estructura de capital.
- LEO dataset reparametrizado: inicial ARPU/Devices mayores, OPEX/ΔWC moderados, RCAPEX de 120 MM en años 5/10.

### API Endpoints (if applicable)
- Ninguno (librería offline).

### Database Schema (if applicable)
- No aplica.

### Key Functions/Classes
- `ProjectParameters.from_directory` (carga validada de inputs).
- `calculate_cfads`, `compute_dscr`, `compute_llcr`, `compute_plcr`.
- `build_financial_dashboard`, `save_dashboard` (visualización determinística).

### Integration Points
- DCF ↔ AMM adapters (`integration` package) siguen placeholders pero conectados a parámetros validados.
- Scripts Docker/CLI pueden generar dashboards (`MPLCONFIGDIR` arregla warning de Matplotlib).

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `pytest`

### Recent Changes
- 2025-02-14: Dashboard base con Matplotlib, documentación y pruebas.
- 2025-10-31: Ajuste de CSV LEO IoT (revenues, RCAPEX, OPEX) → DSCR≥1.25 años 1-4, LLCR≈2.0, PLCR≈2.0.

### Known Issues
- Falta lógica de waterfall, stress avanzado y Monte Carlo (placeholders).
- RSCA (LLCR/PLCR) depende de supuestos simplificados; no hay optimización automática aún.

### Next Steps
- Implementar waterfall y stress loops para integrar dashboards avanzados.
- Desarrollar optimización de capital (T-036) y análisis de sensibilidad.
