markdown# System Memory

## Last Updated: 2025-10-29 13:27 UTC
## Version: 0.1.0

### Current Architecture
- Monolithic `pftoken` package with placeholder subpackages for waterfall, pricing, risk, stress, simulation, optimization, derivatives, and visualization modules.

### Technologies & Versions
- Python: 3.12 (container base image `python:3.12-slim`)
- NumPy / pandas / SciPy / Matplotlib / pytest / Jupyter (see `requirements.txt`)

### Container Setup
- Base Images: `python:3.12-slim`
- Services: `app` (development HTTP server placeholder)
- Ports: `8000:8000`
- Volumes: project root bind-mounted to `/app`
- Environment Variables: `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `PYTHONPATH=/app`

### Implemented Features
- Core configuration and data model placeholders established
- Repository skeleton matches target specification

### API Endpoints (if applicable)
- None yet (library-focused project)

### Database Schema (if applicable)
- Not applicable

### Key Functions/Classes
- Placeholder `not_implemented` functions across modules signalling pending work

### Integration Points
- None implemented

### Deployment Instructions
- Build: `docker compose build`
- Run: `docker compose up -d`
- Tests: `docker compose run --rm app pytest`

### Recent Changes
- 2025-10-29: Repository structure aligned with target spec; container assets added.

### Known Issues
- All business logic modules contain placeholder implementations.

### Next Steps
- Implement WP-specific analytics within the placeholder modules.
- Replace placeholder tests with real coverage.
