# Requerimientos Funcionales y No Funcionales

Este documento resume los requerimientos que rigen el modelo cuantitativo de project finance tokenizado. Cubre el alcance actual (WP-01/WP-02), las métricas objetivo y los supuestos de diseño, con énfasis en reproducibilidad y trazabilidad.

## Alcance
- **Dominio:** Proyecto LEO IoT tokenizado, con pipeline determinístico CFADS → Waterfall → Pricing.
- **Iteración vigente:** WP-01 (setup/documentación) y WP-02 (CFADS/ratios/datos). WP-03/WP-04 se apoyan en estos requisitos pero se documentan por separado.
- **Datasets:** `data/input/leo_iot/*.csv` sincronizados con `Proyecto LEO IOT.xlsx`; derivados en `data/derived/leo_iot/`.

## Requerimientos Funcionales
- **Carga y validación de datos**
  - RF-01: Cargar parámetros de proyecto, tramos de deuda, proyección CFADS y RCAPEX desde CSV mediante dataclasses tipadas.
  - RF-02: Validar coherencia contra la planilla canónica (`TP_Quant_Validation.xlsx` / `scripts/validate_input_data.py`) con tolerancia <0.01 %.
  - RF-03: Mantener DSRA inicial (18 MUSD, fondeado por equity) y esquema MRA = 50 % del próximo RCAPEX con acumulación 3 años antes.
- **Cálculo CFADS y ratios**
  - RF-04: Calcular ingresos/OPEX/CAPEX/impuestos/CFADS por período, incorporando gracia y ramping.
  - RF-05: Calcular DSCR por fase (grace/ramp/steady), LLCR y PLCR por tramo; detectar breaches de covenants.
  - RF-06: Exportar snapshots para validación Excel y pruebas automatizadas.
- **Waterfall determinístico (dependencia WP-03 pero requisito de interfaz)**
  - RF-07: Exponer flujos por tramo (interés/principal), DSRA/MRA movements y distribuciones a equity.
  - RF-08: Proveer métricas agregadas (equity IRR, cobertura DSRA/MRA) consumibles por pricing.
- **Pricing base (dependencia WP-04 pero requisito de datos)**
  - RF-09: Entregar flujos descontables y metadata de curva para `PricingEngine`/`WACDCalculator`.
  - RF-10: Ajustar LGD con `CollateralAnalyzer` usando haircuts y tiempo a realización.
- **Documentación y reproducibilidad**
  - RF-11: Mantener guía de implementación, requerimientos y arquitectura sincronizados con el código y `memory.md`.

## Requerimientos No Funcionales
- **Reproducibilidad:** Ejecución determinística (seeds fijados) y resultados validados con tolerancia <0.01 %.
- **Performance:** Capacidad de ejecutar pipelines determinísticos y exports en <60 s sobre hardware de desarrollo; presupuesto de 10k escenarios MC <5 min (para WPs futuros).
- **Trazabilidad:** Cada resultado debe mapear a inputs versionados; cambios en datos requieren revalidación automatizada.
- **Portabilidad:** Docker base `python:3.12-slim`, sin dependencias de GPU ni servicios externos obligatorios.
- **Seguridad:** Sin secretos en repositorio; variables de entorno para claves (e.g., Etherscan) y sin uso de `sudo`.
- **Operación offline:** Todas las rutas principales deben funcionar sin internet; llamadas externas solo en scripts opt-in (e.g., actualización de costos de infraestructura blockchain).

## Supuestos y Gaps de Colateral
- El colateral se modela **de forma agregada**: haircuts y tiempo de liquidación se parametrizan en `PricingContext` y se aplican via `CollateralAnalyzer`.
- **Gap:** No existe dataset granular por activo (satélites, licencias, contratos, seguros). Se requiere `data/derived/collateral_inventory.csv` (o similar) con valor liquidable, haircuts y horizonte de realización por activo para WP-05/06.
- **Riesgo:** Los LGD ajustados actuales representan un promedio conservador; los resultados deben etiquetarse como preliminares hasta contar con el inventario detallado.

## Métricas Objetivo
- DSCR mínimo: 1.25× en fase steady; 1.15× ramp; 1.0× grace.
- LLCR/PLCR: ≥1.0 por tramo (LLCR) y total (PLCR).
- Pricing: tolerancia numérica 0.01 %; YTM consistente con precio/par.
- QA: Cobertura de tests >80 % en módulos críticos (target WP-13); validaciones Excel-Python obligatorias en cada cambio de datos.

## Fuera de Alcance (iteración actual)
- Monte Carlo, stress testing y pricing estocástico (WP-07/08).
- Optimización de estructura de capital (WP-10) y derivados (WP-11).
- Arquitectura AMM completa y conexión on-chain (WP-14+).
