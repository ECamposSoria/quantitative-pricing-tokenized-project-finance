markdown# System Memory

## Last Updated: 2025-11-12 04:15 UTC
## Version: 0.5.0

### Current Architecture
- `ProjectParameters` ahora es un loader liviano (dataclasses) que alimenta CFADS, ratios y el nuevo `FinancialPipeline` (CFADS → waterfall → covenants → viz).
- Dataset LEO IoT (T-047) regenerado directamente desde `Proyecto LEO IOT.xlsx`; `scripts/validate_input_data.py` garantiza coherencia (ahora valida CFADS + reservas).
- Hoja Excel + CSV incluyen financiamiento explícito de DSRA inicial (18 MUSD fondeados por equity en el cierre para cubrir los 4 años de gracia) y RCAPEX “diet” de 18 MUSD en los años 6‑15 (1.2/1.5/1.65/1.7/1.55/3.4/2.25/2/1.5/1.25) con un MRA que acumula 35% del próximo RCAPEX durante los 3 años previos (contribuciones solapadas) para emular reposiciones del 8% de la flota cada ciclo.
- Viz package genera dashboard expandido (cascada waterfall, reservas DSRA/MRA, heatmap de covenants, radar de estructura) usando resultados del pipeline.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- Libraries: numpy, pandas, scipy, matplotlib, pytest, jupyter, numpy-financial, eth-abi, pydantic, PyYAML

### Container Setup
- Base Image: `python:3.12-slim`
- Services: `app` (HTTP placeholder)
- Ports: `8000:8000`
- Volumes: repo bind-mounted en `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`, `MPLCONFIGDIR=/app/.mplconfig`

### Implemented Features
- CFADS deterministic components (`pftoken.models.cfads_components`) verifican ingresos/OPEX/CAPEX/impuestos por año y se validan automáticamente contra Excel con tolerancia <0.01 %.
- `RatioCalculator` produce DSCR por fase y LLCR/PLCR por tramo usando los umbrales compartidos (grace 1.0x, ramp 1.15x, steady 1.25x); los resultados alimentan `CovenantEngine`.
- Placeholder de calibración T‑047 (`data/derived/leo_iot/stochastic_params.yaml`) consumido mediante `load_placeholder_calibration`; `MertonModel` ahora devuelve PD/LGD/EL vectorizados con pruebas unitarias.
- `WaterfallOrchestrator` coordina CFADS → WaterfallEngine → reservas con DSRA inicial fijo (18 MUSD) y MRA = 50 % del próximo RCAPEX; registra equity IRR y saldos DSRA/MRA por período.
- `StructureComparator` amplía el output con métricas de liquidez (cobertura DSRA/MRA) y la comparación global se integra en `FinancialPipeline`.
- Gobernanza offline documentada en `docs/governance.md` y soportada por `GovernanceController`, `ThresholdPolicy`, `StaticOracle` y `LoggingAction`.
- `StochasticVariables` + `CorrelatedSampler` (WP-07 T-022/T-023) generan distribuciones lognormal/beta/normal/bernoulli con antithetic variates y matrices de correlación validadas (Cholesky + eigenvalue check). Los parámetros provienen de `data/derived/leo_iot/stochastic_params.yaml`.
- Docker multi-stage + healthcheck (`pftoken.healthcheck`), usuario no root (`appuser`), y Compose actualizado con `restart`/`mem_limit` para cumplir la política de operación.
- `scripts/export_excel_validation.py` genera snapshots (CFADS/Ratios/Waterfall) en `data/output/excel_exports/<timestamp>/` para refrescar `TP_Quant_Validation.xlsx` sin tocar los CSV fuente.
- README/user-guide actualizados para reflejar política de datos inmutable, DSRA/MRA baseline y el nuevo flujo de validación.

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
- Excel exports: `python scripts/export_excel_validation.py --data-dir data/input/leo_iot --output-root data/output/excel_exports`

### Recent Changes
- 2025-11-12: Implementado stack WP-02/WP-03 determinístico (CFADS components, RatioCalculator, placeholder Merton PD/LGD/EL, full Waterfall orchestrator, governance controller). Se agrega exportador para Excel, documentación (`docs/calibration.md`, `docs/governance.md`) y se actualizan pruebas con la tolerancia <0.01 %.

### Known Issues
- T-047 calibración real (MC surfaces, correlaciones) pendiente de T-022/T-023; el YAML actual es determinístico.
- El governance controller es offline; falta vincularlo con contratos/token holders.
- Dockerfile no adopta aún el pipeline multi-stage/non-root descrito; se mantiene en backlog DevOps.
- Automatización bidireccional Excel ↔ Python sigue fuera de alcance (solo export manual vía script).

### Next Steps
- Implementar `MonteCarloEngine`/`merton_integration` (T-021/T-024) aprovechando las nuevas distribuciones y matriz de correlación para producir trayectorias de CFADS/PD.
- Integrar LLCR/PLCR y covenants extendidos directamente en `WaterfallEngine` (prioridades T-015/T-017) con reportes para dashboards.
- Desplegar pricing estocástico (WP-08) una vez que los outputs Monte Carlo estén disponibles para alimentar spreads y sensibilidades.
