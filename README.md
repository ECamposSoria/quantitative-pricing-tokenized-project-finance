# Project Finance Tokenization Simulator

Modelo cuantitativo para:
- modelar CFADS en una constelación LEO IoT,
- aplicar el waterfall de pagos por prioridad (senior / mezzanine / subordinado / equity),
- simular Monte Carlo (ingresos, OPEX, tasas),
- valorar cada tramo como instrumento de renta fija estructurada,
- calibrar spreads y WACD,
- medir EL, VaR, CVaR y stress testing,
- analizar redistribución de riesgo y eficiencia de capital bajo tokenización (BIS, 2023; OECD, 2024). :contentReference[oaicite:4]{index=4}

## Componentes principales
- `pftoken/` librería del modelo
- `notebooks/` walkthrough académico / demo
- `data/` inputs y outputs CSV
- `tests/` tests unitarios y de integración
- `scripts/` entrypoints reproducibles (cli)

## Referencias clave
Esty (2004), Gatti (2018), Reisin (2025), BIS (2023), OECD (2024). :contentReference[oaicite:5]{index=5}
