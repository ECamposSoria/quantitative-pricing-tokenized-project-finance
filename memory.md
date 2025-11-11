markdown# System Memory

## Last Updated: 2025-11-11 02:05 UTC
## Version: 0.4.3

### Current Architecture
- `ProjectParameters` ahora es un loader liviano (dataclasses) que alimenta CFADS, ratios y el nuevo `FinancialPipeline` (CFADS → waterfall → covenants → viz).
- Dataset LEO IoT (T-047) regenerado directamente desde `Proyecto LEO IOT.xlsx`; `scripts/validate_input_data.py` garantiza coherencia (ahora valida CFADS + reservas).
- Hoja Excel + CSV incluyen financiamiento explícito de DSRA inicial (18 MUSD fondeados por equity en el cierre para cubrir los 4 años de gracia) y RCAPEX “diet” de 18 MUSD en los años 6‑15 (1.2/1.5/1.65/1.7/1.55/3.4/2.25/2/1.5/1.25) con un MRA que acumula 35% del próximo RCAPEX durante los 3 años previos (contribuciones solapadas) para emular reposiciones del 8% de la flota cada ciclo.
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
- CFADS vector actualizado (total 196.5 MUSD) con RCAPEX diet y campos `dsra_*`/`mra_*` para fondeo y uso de reservas; DSCR phase-aware (`compute_dscr_by_phase`) se sitúa entre 1.35x y 1.65x en operación, muy por encima del piso de 1.25x.
- Waterfall engine (interés → DSRA → principal → MRA → sweep/dividendos) con seguimiento de reservas y covenants.
- Financial pipeline + comparator tradicional/tokenizado, Excel validation suite (`tests/test_excel_validation.py`) y TP_Quant_Validation.xlsx sincronizados con el nuevo set de datos (CFADS total = 178.5 MUSD, DSCR años 6 y 10 estresados).
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
- 2025-11-11: RCAPEX diet (18 MUSD) adoptado para priorizar DSCR ≥ 1.35x; Excel/CSV/TP_Quant_Validation sincronizados, CFADS total pasa a 196.5 MUSD y suites de validación actualizadas. Se incrementa el DSRA inicial a 18 MUSD (equity) para cubrir íntegramente los 4 años de gracia.

### Known Issues
- Stress/Monte Carlo y pricing AMM siguen placeholders; waterfall no ejecuta LLCR/PLCR ni ajustes PIK.
- Excel workbook compara métricas principales pero falta automatizar importación bidireccional.

### Next Steps
- Implementar stress/Monte Carlo (T-021) usando nuevo pipeline como core.
- Añadir LLCR/PLCR dentro del waterfall + reportes (T-015/T-017) y optimización de capital (T-036).
