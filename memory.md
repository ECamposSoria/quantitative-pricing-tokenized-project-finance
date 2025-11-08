markdown# System Memory

## Last Updated: 2025-11-02 14:20 UTC
## Version: 0.4.0

### Current Architecture
- `ProjectParameters` ahora es un loader liviano (dataclasses) que alimenta CFADS, ratios y el nuevo `FinancialPipeline` (CFADS → waterfall → covenants → viz).
- Dataset LEO IoT (T-047) regenerado directamente desde `Proyecto LEO IOT.xlsx`; `scripts/validate_input_data.py` garantiza coherencia.
- Viz package genera dashboard expandido (cascada waterfall, reservas DSRA/MRA, heatmap de covenants, radar de estructura) usando resultados del pipeline.

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
- CFADS vector exacto a T-047 (anual) + DSCR phase-aware (`compute_dscr_by_phase`).
- Waterfall engine (interés → DSRA → principal → MRA → sweep/dividendos) con seguimiento de reservas y covenants.
- Financial pipeline + comparator tradicional/tokenizado, Excel validation suite (`tests/test_excel_validation.py`) y TP_Quant_Validation.xlsx.
- Dashboard extendido con nuevas visualizaciones enlazadas al pipeline.

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

### Recent Changes
- 2025-11-02: WP-02/WP-03 entrega parcial → datasets regenerados, pipeline integrado, Excel validation workbook, dashboard extendido.

### Known Issues
- Stress/Monte Carlo y pricing AMM siguen placeholders; waterfall no ejecuta LLCR/PLCR ni ajustes PIK.
- Excel workbook compara métricas principales pero falta automatizar importación bidireccional.

### Next Steps
- Implementar stress/Monte Carlo (T-021) usando nuevo pipeline como core.
- Añadir LLCR/PLCR dentro del waterfall + reportes (T-015/T-017) y optimización de capital (T-036).
