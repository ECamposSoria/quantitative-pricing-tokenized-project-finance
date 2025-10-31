markdown# System Memory

## Last Updated: 2025-02-14 12:00 UTC
## Version: 0.2.0

### Current Architecture
- `pftoken` now includes the new `amm` package (core pools, pricing, analysis, utils) and an `integration` package to bridge DCF outputs with AMM signals.
- Existing subpackages (config, models, waterfall, pricing, pricing_mc, risk, stress, simulation, optimization, derivatives, viz, utils) remain as placeholders but are wired for future work.
- Stress module gained `liquidity_stress`, and viz package exposes `amm_viz` and `liquidity_heatmap`.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- Libraries: numpy, pandas, scipy, matplotlib, pytest, jupyter, numpy-financial, eth-abi

### Container Setup
- Base Image: `python:3.12-slim`
- Services: `app` (simple HTTP server placeholder)
- Ports: `8000:8000`
- Volumes: project root bind-mounted to `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`

### Implemented Features
- AMM scaffolding: constant-product pool, concentrated liquidity placeholder, liquidity manager, swap engine, pricing/analysis utilities.
- Integration scaffolding: DCF → AMM liquidity instructions, scenario propagation, feedback loop helpers.
- CLI tools for AMM stress testing, range optimisation, and DCF vs. market comparison.
- Data templates, docs, notebooks, and tests expanded to cover AMM workflows (all currently placeholders).

### API Endpoints (if applicable)
- None yet (library-focused project).

### Database Schema (if applicable)
- Not applicable.

### Key Functions/Classes
- `pftoken.amm.core.pool_v2.ConstantProductPool`: functional swap/add/remove liquidity scaffold.
- `pftoken.amm.core.liquidity_manager.LiquidityManager`: simple LP share accounting.
- `pftoken.stress.liquidity_stress.stress_liquidity`: basic liquidity shock routine.

### Integration Points
- `pftoken.integration.dcf_to_amm.allocate_liquidity` bridges deterministic cashflows with AMM liquidity.
- Placeholder feedback loop adjusts discount curves from market spreads.

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `docker compose run --rm app pytest`

### Recent Changes
- 2025-02-14: Added AMM, integration, stress, viz scaffolding plus CLI tools, docs, data templates, and notebooks.

### Known Issues
- Most modules (including AMM) still operate as analytical placeholders; real business logic pending.
- Tests are placeholders with `pytest.skip`.

### Next Steps
- Implement production-grade AMM math (fees, slippage, liquidity accounting) and connect with DCF cashflows.
- Replace placeholder notebooks/docs/tests with executable workflows and automated coverage.
