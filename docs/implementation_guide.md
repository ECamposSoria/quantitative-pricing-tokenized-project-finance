# GUÍA COMPLETA DE IMPLEMENTACIÓN - VERSIÓN ACTUALIZADA
Modelo Cuantitativo de Project Finance Tokenizado para Constelación LEO IoT  
67 Tareas Totales — Roadmap Rev. 4-Nov-2025

> Baseline consolidado con `README.md`, `memory.md` (11-nov-2025), `TP_Quant_Validation.xlsx`, `data/input/leo_iot/*.csv` y los módulos activos en `pftoken/`. La guía prioriza tareas ejecutables en la iteración actual y marca explícitamente los entregables ya cubiertos.

## Convenciones y fuentes

- **Estados**: `Hecho` (cumple alcance actual), `En progreso` (parcial, faltan gaps), `Pendiente` (sin implementación), `Fuera de alcance (esta iteración)` solo cuando existe bloqueo externo real.
- **Referencias**:
  - Dataset calibrado (`data/input/leo_iot/`) alineado con `Proyecto LEO IOT.xlsx` vía `scripts/validate_input_data.py`.
  - Pipeline determinístico y dashboards (`pftoken/pipeline.py`, `pftoken/viz/dashboards.py`).
  - Placeholders identificables por `not_implemented()` en módulos de riesgo, stress y pricing estocástico.
  - Material del curso “Blockchain y Criptomonedas” (`docs/crypto_material/`) con notas (`notas_crypto.txt`) y notebooks (`practico/Clase_*`) para alinear los módulos cripto/de liquidez.
- **Secciones por tarea**: Objetivo, Dependencias, Entregables (con rutas), Notas teóricas (contexto cuantitativo) y Alcance (qué cubre/no cubre la iteración).

---

## WP-01 · Setup y Arquitectura (T-001, T-002, T-012)

### T-001 · Setup inicial proyecto
**Estado actual:** Hecho (estructura del repo + Docker + CI documentados en `README.md`).
- **Objetivo:** Mantener un esqueleto Python reproducible (venv, Docker, CI) que habilite el resto del roadmap.
- **Dependencias:** Ninguna (prerrequisito de todos los WP).
- **Entregables:** `requirements.txt`, `setup.py`, `quant-token-compose.yml`, `Dockerfile`, workflows en `.github/workflows/`, guía de entorno en `README.md`.
- **Notas teóricas:** Buenas prácticas DevOps para modelos cuantitativos (control de versiones, entornos aislados, reproducibilidad).
- **Alcance:** En alcance scripts de bootstrap y pipelines CI; fuera de alcance despliegues productivos en nube.

### T-002 · Documentación de requerimientos
**Estado actual:** Hecho (`docs/requirements.md` consolida requerimientos funcionales/no funcionales y métricas; README/user_guide están alineados a alto nivel).
- **Objetivo:** Explicar objetivos académicos del caso LEO IoT, métricas (DSCR>1.25, LLCR>1.0, VaR95%), alcance cuantitativo y metodología.
- **Dependencias:** T-001.
- **Entregables:** README extendido, documento de requerimientos funcionales/no funcionales (`docs/requirements.md`) y diagrama conceptual en `docs/architecture.md`.
- **Notas teóricas:** Referencias IFC/IPFA, Gatti (2018) y Yescombe (2013) para métricas de cobertura y performance (<5 min para 10k escenarios).
- **Alcance:** Documentación textual y diagramas; fuera de alcance aprobación externa formal.

### T-012 · Arquitectura de módulos
**Estado actual:** En progreso (`docs/architecture.md` ahora describe flujo CFADS → Waterfall → Pricing, contratos clave y gaps de colateral; faltan diagramas UML/PlantUML y despliegue).
- **Objetivo:** Diseñar arquitectura modular (CFADS → Waterfall → Pricing → Risk → AMM) con interfaces tipadas y responsabilidades únicas.
- **Dependencias:** T-001, T-002.
- **Entregables:** Diagramas UML/PlantUML, definición de inputs/outputs/excepciones para cada paquete (`pftoken.models`, `waterfall`, `pricing`, `simulation`, `risk`, `amm`), convenciones (PEP8, docstrings NumPy) y guía de logging.
- **Notas teóricas:** Principio de responsabilidad única, patrones Builder/Strategy/Factory aplicados al pipeline, logging estructurado para eventos críticos.
- **Alcance:** Diseño de software; fuera de alcance implementación (se cubre en los demás WP).

---

## WP-02 · Módulo CFADS y Ratios (T-003, T-003B, T-004, T-005, T-005B, T-013, T-046, T-047)

### T-013 · Dataclass de parámetros
**Estado actual:** Hecho (`pftoken/models/params.py`, `ProjectParameters.from_directory`).
- **Objetivo:** Cargar de forma tipada e inmutable todos los parámetros (proyecto, tramos, CFADS, calendario de deuda y RCAPEX).
- **Dependencias:** T-001, T-012.
- **Entregables:** Dataclasses `ProjectParams`, `DebtTrancheParams`, `CFADSProjectionParams`, loaders CSV (`project_params.csv`, `tranches.csv`, `revenue_projection.csv`, `debt_schedule.csv`, `rcapex_schedule.csv`) y métodos `to_dict`, `cfads_dataframe`.
- **Notas teóricas:** Tipificación fuerte reduce sesgos y facilita reproducibilidad en pipelines de riesgo.
- **Alcance:** Loaders y validaciones; fuera de alcance ingesta directa de fuentes externas.

### T-003 · Cálculo CFADS determinístico
**Estado actual:** Hecho (`pftoken/models/cfads_components.py`, `CFADSCalculator`).
- **Objetivo:** Implementar `CFADSCalculator` completo con cálculos de ingresos/OPEX/EBITDA/CAPEX/impuestos/CFADS por período.
- **Dependencias:** T-013, T-046.
- **Entregables:** Dataclass `CFADSResult`, validaciones numéricas <0.01 % contra Excel, hardcode del RCAPEX diet (años 6‑15) y DSRA inicial 18 MUSD, trazabilidad revenue→OPEX→CAPEX→tax→CFADS.
- **Notas teóricas:** Curvas S/logísticas para adopción IoT, degradación satelital, pérdidas fiscales arrastrables.
- **Alcance:** Modelado anual/semestral; fuera de alcance integración directa con ERP.

### T-003B · Grace period y ramping
**Estado actual:** Hecho (`CFADSCalculator.apply_grace_period_adjustment`, `RatioCalculator`).
- **Objetivo:** Incorporar mecánicas de gracia/ramping en CFADS y servicio de deuda (intereses vs principal, DSCR ajustado por fase).
- **Dependencias:** T-003, T-013, T-014.
- **Entregables:** DSCR thresholds centralizados (grace 1.0×, ramp 1.15×, steady 1.25×), reporte de fases con heatmap, validaciones (gracia+ramp ≤ tenor) y colorización para dashboards.
- **Notas teóricas:** DSCR objetivo por fase según Gatti/Yescombe.
- **Alcance:** Lógica financiera + reporting; fuera de alcance cambios en dataset base.

### T-004 · Ratios DSCR/LLCR/PLCR
**Estado actual:** Hecho (`pftoken/models/ratios.py`).
- **Objetivo:** Implementar `RatioCalculator` con DSCR por fase, LLCR por tramo, PLCR total y detección de breaches.
- **Dependencias:** T-003B, T-014, T-015.
- **Entregables:** Dataclasses `RatioObservation`/`LLCRObservation`, `RatioResults`, cálculo de LLCR/PLCR por seniority, integración con `CovenantEngine` y visualizaciones <0.01 % tolerancia vs Excel.
- **Notas teóricas:** Valor presente descontado al costo de deuda; PLCR>1 implica valor económico positivo.
- **Alcance:** Métricas por tramo; fuera de alcance calificaciones externas.

### T-005 · Modelo Merton PD
**Estado actual:** Hecho (`pftoken/models/merton.py` vectorizado).
- **Objetivo:** Implementar `MertonModel` que valore activos vía CFADS esperados y calcule PD/LGD/EL basado en distancia a default.
- **Dependencias:** T-003B, T-014, T-047.
- **Entregables:** PD/LGD/EL por tramo usando numpy, consumo de parámetros desde `calibration.py`, pruebas de monotonía y sumas EL, integración futura con Monte Carlo.
- **Notas teóricas:** Merton (1973) para la base teórica de valoración de opciones, Merton (1974) para la aplicación a deuda corporativa (Distance to Default), modelo KMV, referencia drift/volatilidad de telecom satelital.
- **Alcance:** Modelo estructural single-period; fuera de alcance calibración multi-factor avanzada.

### T-005B · Excel validation model
**Estado actual:** Hecho (`scripts/export_excel_validation.py`, `tests/test_excel_validation.py`, `tests/test_integration/test_pipeline_e2e.py`).
- **Objetivo:** Mantener workbook espejo para QA/explicación académica del pipeline.
- **Dependencias:** T-003B, T-004, T-005.
- **Entregables:** Export deterministic de CFADS/Ratios/Waterfall a `data/output/excel_exports/`, comparación Python↔Excel con tolerancia <0.01 %, documentación de flujo manual.
- **Notas teóricas:** Excel como “oráculo” para comparar Python vs hoja, uso de NPV/NORM.DIST.
- **Alcance:** Workbook offline; fuera de alcance sincronización bidireccional automática.

### T-046 · Dataset LEO IoT
**Estado actual:** Hecho (`data/input/leo_iot/` + `scripts/validate_input_data.py` sincronizados con `Proyecto LEO IOT.xlsx`).
- **Objetivo:** Mantener dataset base (360 MUSD ingresos, CFADS 214.5 MUSD, deuda 72 MUSD, DSCR objetivo 1.45x) como fuente única.
- **Dependencias:** T-013.
- **Entregables:** CSV calibrados, script de validación, documentación de escenarios (base/optimista/pesimista).
- **Notas teóricas:** Benchmark Starlink/OneWeb/Iridium; DSRA inicial 18 MUSD y RCAPEX diet (18 MUSD años 6‑15) según `memory.md`.
- **Alcance:** Dataset + escenarios; fuera de alcance ingesta automática de fuentes externas.

### T-047 · Calibraciones adicionales
**Estado actual:** Hecho (`data/derived/leo_iot/stochastic_params.yaml`, `docs/calibration.md`, `pftoken/models/calibration.py`).
- **Objetivo:** Calibrar parámetros estocásticos (distribuciones, correlaciones, spreads, recoveries) para Monte Carlo, Merton y stress.
- **Dependencias:** T-046, T-022, T-023.
- **Entregables:** YAML con PD/LGD/vols + definiciones de distribuciones y matriz de correlación, loader reutilizable (`RandomVariableConfig`, `CorrelationConfig`), documentación metodología.
- **Notas teóricas:** Métodos Delphi/benchmark, spread = base + α·PD + β·LGD, sensibilidad de parámetros críticos.
- **Alcance:** Calibración paramétrica; fuera de alcance scraping automático.

---

## WP-03 · Waterfall de Pagos y Gobernanza (T-006, T-014, T-015, T-016, T-017, T-020)

### T-014 · Clase DebtStructure
**Estado actual:** Hecho (`pftoken/waterfall/debt_structure.py` con serialización `to_dicts/from_dicts`).
- **Objetivo:** Modelar tramos con seniority, tasas y amortización para alimentar waterfall y pricing.
- **Dependencias:** T-013.
- **Entregables:** Clases `Tranche`, `DebtStructure`, métodos `from_csv`, `from_tranche_params`, cálculo WACD, validaciones de seniority, serialización `to_dicts/from_dicts`.
- **Notas teóricas:** Esculpido y pesos (senior 60%, mezz 25%, sub 15%).
- **Alcance:** Modelado off-chain; fuera de alcance contratos tokenizados (WP-14).

### T-015 · Covenants y triggers
**Estado actual:** Hecho (`pftoken/waterfall/covenants.py`).
- **Objetivo:** Evaluar covenants (DSCR, LLCR, LTV) y accionar bloqueos (dividendos, sweep, default técnico).
- **Dependencias:** T-004, T-017.
- **Entregables:** Dataclasses `Covenant`, `CovenantBreach`, integración con `RatioCalculator`, historial de breaches, acciones automáticas parametrizables, heatmaps DSCR/LLCR.
- **Notas teóricas:** Covenants IFC/IPFA, severidades por rangos (1.25 / 1.15 / 1.0).
- **Alcance:** Lógica y reporting; fuera de alcance negociación legal.

### T-016 · Comparador de estructuras
**Estado actual:** Hecho (`StructureComparator` extendido).
- **Objetivo:** Comparar estructura bancaria vs tokenizada (costo, riesgo, liquidez, gobernanza).
- **Dependencias:** T-014, T-009.
- **Entregables:** Métricas de costo (delta WACD), riesgo (HHI), liquidez secundaria (DSRA/MRA coverage), radar charts, sensibilidades ±50 bps.
- **Notas teóricas:** Índice Herfindahl, secondary liquidity, governance (agente vs token holders).
- **Alcance:** Comparación cuantitativa/cualitativa; fuera de alcance encuestas reales.

### T-017 · Implementación detallada del Waterfall
**Estado actual:** Hecho (`pftoken/waterfall/waterfall_engine.py`, `tests/test_waterfall/test_full_waterfall.py`).
- **Objetivo:** Ejecutar prelación completa con trazabilidad anual y validaciones de conservación de cash.
- **Dependencias:** T-014, T-015, T-003B.
- **Entregables:** `WaterfallResult` enriquecido (draws DSRA/MRA, cash sweep, eventos), pruebas de extremos, logging DSRA/MRA lifecycle.
- **Notas teóricas:** Prelación estándar, DSRA target = servicio próximo, MRA = 50 % RCAPEX.
- **Alcance:** Modelo determinístico; fuera de alcance contabilidad IFRS.

### T-006 · Clase Waterfall con MRA (orquestador)
**Estado actual:** Hecho (`pftoken/waterfall/full_waterfall.py`, `FinancialPipeline`).
- **Objetivo:** Coordinar todos los períodos, gestionar DSRA/MRA, calcular distribuciones a equity y métricas (equity IRR, cobertura por tramo).
- **Dependencias:** T-017, T-015.
- **Entregables:** `WaterfallOrchestrator`, `FullWaterfallResult`, equity IRR, series DSRA/MRA y comparador de escenarios, integración con pipeline y dashboards.
- **Notas teóricas:** Cash sweep según DSCR, liberación de reservas tras repago.
- **Alcance:** Simulación anual/mensual; fuera de alcance integración con MC (WP-07).

### T-020 · Gobernanza digital
**Estado actual:** Hecho (`pftoken/waterfall/governance_interfaces.py`, `pftoken/waterfall/governance.py`, `docs/governance.md`).
- **Objetivo:** Diseñar framework on-chain (roles, votaciones, oráculos) para automatizar ajustes de waterfall/token governance.
- **Dependencias:** T-017, T-053.
- **Entregables:** Interfaces `IOracle`, `IGovernanceAction`, `GovernancePolicy`, `GovernanceController` con logging de acciones, documentación de roles/oráculos/flows.
- **Notas teóricas:** Gobernanza on-chain vs tradicional, oráculos, timelocks.
- **Alcance:** Diseño conceptual; fuera de alcance despliegue blockchain real.

---

## WP-04 · Pricing y Curvas (T-007, T-008, T-009, T-018, T-019)

### T-007 · Módulo de valuación de tramos
**Estado actual:** Hecho (`pftoken/pricing/base_pricing.py`).
- **Objetivo:** Construir `PricingEngine` que descuente flujos por tramo usando curva spot y calcule precio/YTM/duración/convexidad.
- **Dependencias:** T-006, T-008, T-019.
- **Entregables:** `PricingEngine`, `TranchePricingMetrics`, extracción de flujos desde `WaterfallResult`, solver YTM (`scipy.optimize.brentq`), duración/convexidad, LGD opcional vía `CollateralAnalyzer`, visualizaciones (`plot_tranche_cashflows`, `plot_discount_curve`).
- **Notas teóricas:** DCF con DF(t)=1/(1+r)^t, spreads ajustados por PD×LGD; tolerancia <0.01 % (config en `pftoken/pricing/constants.py`).
- **Alcance:** Pricing determinístico; pricing estocástico permanece en WP-08.

### T-008 · Curva zero-coupon
**Estado actual:** Hecho (`pftoken/pricing/zero_curve.py`).
- **Objetivo:** Bootstrapping de curva spot (depósitos, swaps, bonos) con interpolación log-lineal y forwards.
- **Dependencias:** T-007.
- **Entregables:** `ZeroCurve`, `CurveInstrument`, `CurvePoint`, métodos `bootstrap`, `spot_rate`, `discount_factor`, `forward_rate`, `apply_shock` (paralelo/buckets), serialización `to_dict/from_dict`.
- **Notas teóricas:** Bootstrapping secuencial (Hull), day-count simplificado, no arbitraje via CIP; se apoyó en `scipy.optimize.brentq` para resolver swaps.
- **Alcance:** Curvas determinísticas (USD base + fixtures EUR); datos en vivo siguen fuera de alcance.

### T-009 · WACD
**Estado actual:** Hecho (`pftoken/pricing/wacd.py`).
- **Objetivo:** Calcular WACD tradicional vs tokenizado con ajustes por fees/impuestos.
- **Dependencias:** T-007, T-014, T-016.
- **Entregables:** `WACDCalculator`, `WACDScenario`, comparación `compare_traditional_vs_tokenized`, after-tax configurable vía `PricingContext`.
- **Notas teóricas:** WACD = Σ(weight_i × cost_i); after-tax se aplica según tasa corporativa por defecto 25 %.
- **Alcance:** Comparaciones analíticas y reporting; optimización estructural se mantiene para WP-10.

### T-019 · Ajuste LGD por colateral
**Estado actual:** Hecho (`pftoken/pricing/collateral_adjust.py`).
- **Objetivo:** Modelar recoveries según valor liquidable de satélites/licencias/contratos para ajustar LGD y pricing.
- **Dependencias:** T-005, T-047.
- **Entregables:** `CollateralAnalyzer`, `CollateralResult`, waterfall de recoveries con haircuts/time-to-liquidation (`PricingContext`), hooks directos para `PricingEngine`.
- **Notas teóricas:** Recoveries PF Moody’s, absolute priority rule aplicada a `DebtStructure`, descuento por tiempo a liquidar vía `ZeroCurve`.
- **Alcance:** Análisis off-chain; tasaciones reales continúan fuera de alcance y falta inventario granular por activo (gap WP-05/06).

---

## WP-05 · Riesgo Crediticio (T-010, T-033, T-034, T-035, T-037)

### T-010 · Módulo EL/VaR/CVaR
**Estado actual:** Hecho (determinístico, listo para Monte Carlo) (`pftoken/risk/credit_risk.py`).
- **Objetivo:** Calcular EL, VaR y CVaR por tramo usando PD/LGD dinámicos y generar reportes.
- **Dependencias:** T-005, T-021.
- **Entregables:** `RiskMetricsCalculator`, métodos `calculate_expected_loss`, `calculate_var`, `calculate_cvar`, `calculate_marginal_risk`, soporte de escenarios empíricos y draws paramétricos cuando no hay MC.
- **Notas teóricas:** Artzner (coherent risk), Basilea III capital económico.
- **Alcance:** Métricas estadísticas; reporting regulatorio real sigue fuera de alcance.

### T-033 · Pérdida esperada agregada
**Estado actual:** Hecho (Gaussian copula, SPD bump) (`pftoken/risk/el_calculator.py`).
- **Objetivo:** Sumar pérdidas esperadas considerando interdependencias y waterfall de recuperación.
- **Dependencias:** T-010, T-029.
- **Entregables:** `AggregateRiskCalculator`, simulación correlacionada (Cholesky + validación SPD), tabla de contribuciones y métricas portafolio (VaR/CVaR).
- **Notas teóricas:** Tranching efficiency, distribución de pérdidas en CDOs.
- **Alcance:** Análisis cuantitativo; fuera de alcance rating oficial.

### T-034 · Métricas de cola VaR/CVaR
**Estado actual:** Hecho (empírico + EVT opcional con fallback) (`pftoken/risk/var_cvar.py`).
- **Objetivo:** Analizar tails empíricas (VaR/CVaR 90/95/99/99.9) y ajustar modelos EVD.
- **Dependencias:** T-031, T-010.
- **Entregables:** `TailRiskAnalyzer`, métodos empíricos, ajuste GPD/GEV con KS y QQ residuals, backtesting stubs.
- **Notas teóricas:** Teoría de valores extremos (Embrechts), expected shortfall Basel.
- **Alcance:** Análisis estadístico; aprobación regulatoria sigue fuera de alcance.

### T-035 · Frontera eficiente
**Estado actual:** Hecho (grid/Dirichlet + filtro de dominancia) (`pftoken/risk/efficient_frontier.py`).
- **Objetivo:** Analizar trade-off riesgo-retorno (WACD vs CVaR) para configuraciones de tramos.
- **Dependencias:** T-028, T-034, T-036.
- **Entregables:** `EfficientFrontierAnalysis`, generación de portafolios, cálculo de riesgo (VaR/CVaR/vol) y retorno (WACD/IRR proxy), filtro de eficiencia, integración opcional en `FinancialPipeline.run` para comparar estructura actual vs frontera.
- **Notas teóricas:** Frontera de Markowitz aplicada a deuda tranched.
- **Alcance:** Simulación analítica; fuera de alcance optimización multiobjetivo compleja.

### T-037 · Índice Herfindahl
**Estado actual:** Hecho (`pftoken/risk/hhi.py`).
- **Objetivo:** Medir concentración de riesgo por tranche mediante HHI y número equivalente de tramos homogéneos.
- **Dependencias:** T-033.
- **Entregables:** `RiskConcentrationAnalysis`, métricas de participación, `calculate_equivalent_n`, hooks de reporte.
- **Notas teóricas:** Uso de HHI en securitizaciones y riesgo sistémico.
- **Alcance:** Métricas analíticas; fuera de alcance métricas regulatorias adicionales.

---

## WP-06 · Stress Testing (T-038, T-038B, T-039, T-040, T-041, T-042, T-043)

### T-038 · Diseño escenarios estrés
**Estado actual:** Hecho (librería S1–S6 + C1–C3 en `pftoken/stress/scenarios.py`).
- **Objetivo:** Definir librería `StressScenarioLibrary` con S1–S5 (demanda, tasas, lanzamiento, degradación, regulatorio) incluyendo shocks, duración y racionales.
- **Dependencias:** T-002, T-046.
- **Entregables:** Escenarios parametrizados (JSON/CSV), documentación con probabilidades subjetivas y antecedentes históricos.
- **Notas teóricas:** Basel stress guidelines, correlación de shocks macro/operativos.
- **Alcance:** Diseño; fuera de alcance ejecución (T-040).

### T-038B · Escenario S6 CAPEX Failure
**Estado actual:** Hecho (S6 CAPEX overrun en librería, shortfall MRA parametrizado).
- **Objetivo:** Modelar fallo CAPEX (RCAPEX inesperado 25 MUSD vs MRA 12 MUSD) con opciones (diferir, violar waterfall, bridge loan).
- **Dependencias:** T-038, T-017.
- **Entregables:** Escenario S6 en librería, análisis trade-offs/probabilidad insuficiencia MRA, visualización de saldos MRA vs RCAPEX.
- **Notas teóricas:** Riesgo de CAPEX overruns (caso OneWeb), mitigantes (MRA mayor, seguros).
- **Alcance:** Simulación determinística; fuera de alcance financiación puente real.

### T-039 · Escenarios combinados
**Estado actual:** Hecho (C1–C3 combinados en librería).
- **Objetivo:** Construir combos C1–C3 (Perfect Storm, Launch Failure+Rate Shock, Operational Cascade) con correlaciones temporales y factores de compounding.
- **Dependencias:** T-038.
- **Entregables:** Método `sample_correlated_shocks`, matriz de interacción, narrativas en `docs/stress_scenarios.md`, visualización timeline.
- **Notas teóricas:** Dependencia en tails, precedentes Iridium 2000.
- **Alcance:** Simulación; fuera de alcance hedging real.

### T-040 · Motor de estrés
**Estado actual:** Hecho (motor v1 + runner/deltas en `pftoken/stress/stress_engine.py`).
- **Objetivo:** Implementar `StressTestEngine` que aplique shocks, re-ejecute CFADS/Waterfall/Pricing y compare con baseline.
- **Dependencias:** T-006, T-007, T-038.
- **Entregables:** Métodos `apply_stress_scenario`, `run_stressed_simulation`, `calculate_stress_metrics`, `generate_stress_dashboard`, batch runner.
- **Notas teóricas:** Basel stress testing, propagación de shocks.
- **Alcance:** Motor offline; fuera de alcance ejecución en tiempo real.

### T-041 · Resultados de estrés
**Estado actual:** Hecho (`StressResultsAnalyzer` para ranking/near-miss).
- **Objetivo:** Agregar análisis agregados (ranking de escenarios, heatmaps, comparaciones Traditional vs Tokenized, near-misses).
- **Dependencias:** T-040.
- **Entregables:** `StressResultsAnalyzer`, tablas comparativas, radar de resiliencia, histogramas de time-to-default.
- **Notas teóricas:** Métricas de resiliencia (tiempo a default, severidad).
- **Alcance:** Reporting; fuera de alcance presentaciones externas.

### T-042 · Reverse stress testing
**Estado actual:** Hecho (búsqueda 1D + grid en `reverse_stress.py`).
- **Objetivo:** Encontrar combinaciones mínimas de shocks que llevan a default inevitable (distance-to-failure).
- **Dependencias:** T-041, T-040.
- **Entregables:** `ReverseStressTester` con `find_breaking_point`, `identify_minimal_fatal_combo`, `map_failure_surface`, visualizaciones safe/unsafe.
- **Notas teóricas:** Reverse stress testing (FSA), hazard condicionada.
- **Alcance:** Análisis; fuera de alcance pronósticos macro reales.

### T-043 · Stress híbridas
**Estado actual:** Hecho (hibridación de draws MC en `hybrid_stress.py`).
- **Objetivo:** Combinar shocks determinísticos con Monte Carlo condicional (stress-conditional MC, path-dependent stress).
- **Dependencias:** T-031, T-040.
- **Entregables:** `HybridStressTester` con `stress_conditional_mc`, `progressive_stress_mc`, `adaptive_stress_scenario`, `variance_decomposition`, fan charts bajo stress.
- **Notas teóricas:** Conditional VaR, stress probabilista.
- **Alcance:** Simulación offline; fuera de alcance ejecución en producción.

---

## WP-07 · Simulación Monte Carlo (T-021, T-022, T-023, T-024, T-025, T-029, T-030, T-031)

### T-021 · Motor Monte Carlo
**Estado actual:** Hecho (motor vectorizado v1 en `pftoken/simulation/monte_carlo.py`).
- **Objetivo:** Implementar `MonteCarloEngine` vectorizado (10 k escenarios, <5 min) con seeds reproducibles y almacenamiento de resultados.
- **Dependencias:** T-022, T-023, T-006.
- **Entregables:** Métodos `run_simulation`, `aggregate_results`, `calculate_confidence_intervals`, paralelización y checkpointing, exportación CSV/HDF5.
- **Notas teóricas:** Reducción de varianza, vectorización NumPy.
- **Alcance:** Pipeline offline; fuera de alcance cluster distribuido.

### T-022 · Variables aleatorias
**Estado actual:** Hecho (generadores + antithetic en `stochastic_vars.py`).
- **Objetivo:** Definir distribuciones marginales (lognormal ingresos, beta churn, OU tasas, Bernoulli eventos discretos) y sampling con validaciones.
- **Dependencias:** T-047.
- **Entregables:** Clase `StochasticVariables`, generadores con antithetic variates, visualizaciones (histogramas, QQ-plots).
- **Notas teóricas:** Selección adecuada de distribuciones para proporciones/crecimientos/tasas.
- **Alcance:** Sampling; fuera de alcance calibración automática.

### T-023 · Matriz de correlación
**Estado actual:** Hecho (validación/Cholesky + antithetic en `correlation.py`).
- **Objetivo:** Construir matriz ρ PD y generación de muestras correlacionadas (Cholesky/Gaussian copula).
- **Dependencias:** T-022, T-047.
- **Entregables:** Validación de matriz (simetría, eigenvalores positivos), `generate_correlated_samples`, `transform_to_target_distributions`, heatmaps.
- **Notas teóricas:** Copulas gaussianas y efecto en tail risk.
- **Alcance:** Correlaciones estáticas; fuera de alcance correlaciones dinámicas.

### T-024 · Merton en Monte Carlo
**Estado actual:** Hecho (PD/LGD pathwise + pérdidas en `merton_integration.py`).
- **Objetivo:** Integrar cálculo de PD/LGD endógeno en cada trayectoria MC (trajectorias V(t), D(t), distance-to-default).
- **Dependencias:** T-021, T-005.
- **Entregables:** Cálculo de PD_t, LGD_t, triggers V<D, visualizaciones V vs D, term structure promedio de PD.
- **Notas teóricas:** Modelo estructural dinámico, path dependence.
- **Alcance:** Integración analítica; fuera de alcance calibraciones multi-factor complejas.

### T-025 · Flags de default
**Estado actual:** Hecho (`DefaultDetector`/`DefaultFlags` en `default_flags.py`).
- **Objetivo:** Detectar y clasificar eventos de default (técnico, pago, insolvencia, cross-default) durante MC.
- **Dependencias:** T-024, T-015.
- **Entregables:** `DefaultDetector`, probabilidades por tipo, timeline por escenario, heatmaps período × tipo.
- **Notas teóricas:** Tipologías de default en Project Finance, cure periods.
- **Alcance:** Lógica y reporting; fuera de alcance gestión legal.

### T-029 · DSCR/LLCR por trayectoria
**Estado actual:** Hecho (resúmenes percentiles + headroom en `ratio_simulation.py`).
- **Objetivo:** Calcular distribuciones de DSCR/LLCR por período y fan charts con percentiles, headroom y persistencia de breaches.
- **Dependencias:** T-021, T-004.
- **Entregables:** `RatioDistributions`, fan charts, análisis de headroom y persistencia, overlays stress vs base.
- **Notas teóricas:** Interpretación percentiles DSCR y headroom relativo.
- **Alcance:** Análisis cuantitativo; fuera de alcance reporting regulatorio.

### T-030 · Probabilidades de breach
**Estado actual:** Hecho (`BreachProbabilityAnalyzer` en `breach_probability.py`).
- **Objetivo:** Estimar P(breach) por período/covenant, survival/hazard y segmentación por características.
- **Dependencias:** T-029.
- **Entregables:** `BreachProbabilityAnalyzer`, probabilidades condicionales, survival (Kaplan-Meier), hazard h(t), heatmaps y bootstrap CIs.
- **Notas teóricas:** Survival analysis aplicada a covenants.
- **Alcance:** Métricas; fuera de alcance capital regulatorio.

### T-031 · Pipeline end-to-end MC
**Estado actual:** Hecho (pipeline MC→PD/LGD→pérdidas/ratios en `pipeline.py`).
- **Objetivo:** Orquestar pasos (init, escenarios, trayectorias, pricing, riesgo, exportación, resumen) con logging/caching.
- **Dependencias:** T-021–T-030.
- **Entregables:** `MonteCarloPipeline.run_complete_analysis`, validaciones de outputs, `generate_executive_summary`, comparador de estructuras, analizador de sensibilidad.
- **Notas teóricas:** Buenas prácticas de pipelines cuantitativos (idempotencia, logging, seeds).
- **Alcance:** Pipeline offline; fuera de alcance UI interactiva (WP-09/12).

---

## WP-08 · Pricing Estocástico (T-026, T-027, T-028, T-044)

### T-026 · Valuación estocástica
**Estado actual:** Entregado (`pftoken/pricing_mc/stochastic_pricing.py`).
- **Objetivo:** Calcular distribución de precios por tramo usando cashflows MC y spreads condicionales.
- **Dependencias:** T-031, T-007.
- **Entregables:** `StochasticPricing` (precio esperado, volatilidad, percentiles, P(Precio<Par)), descomposición de incertidumbre y comparación determinístico vs estocástico.
- **Notas teóricas:** Jensen’s inequality, risk-neutral vs physical probabilities.
- **Alcance:** Análisis; fuera de alcance integración mercado real.

### T-027 · Duration y convexidad
**Estado actual:** Entregado (`pftoken/pricing_mc/duration_convexity.py`).
- **Objetivo:** Calcular duration efectiva, Macaulay, convexidad y key-rate durations por tramo.
- **Dependencias:** T-007, T-008.
- **Entregables:** Métodos `calculate_effective_duration`, `calculate_effective_convexity`, `calculate_key_rate_durations`, gráficos precio-yield con tangente/curvatura.
- **Notas teóricas:** Sensibilidad a tasas (DV01), efectos de prepayment.
- **Alcance:** Análisis; fuera de alcance trading de hedges.

### T-028 · Calibración de spreads
**Estado actual:** Entregado (`pftoken/pricing_mc/spread_calibration.py`).
- **Objetivo:** Relacionar spreads con PD/LGD/ilicuidez mediante regresión/modelos reducidos.
- **Dependencias:** T-005, T-010.
- **Entregables:** `SpreadCalibrator`, calibraciones por rating/tenor, visualización de composición de spread, análisis de sensibilidad.
- **Notas teóricas:** Modelos reducidos de crédito, spread ≈ PD×LGD + premium.
- **Alcance:** Calibración; fuera de alcance data live.

### T-044 · Sensibilidad a tasas
**Estado actual:** Entregado (`pftoken/pricing_mc/sensitivity.py`).
- **Objetivo:** Evaluar impacto de movimientos de curva en precios, DSCR y WACD (shifts paralelos, twist, escenarios Fed).
- **Dependencias:** T-027, T-007.
- **Entregables:** `InterestRateSensitivity` (shifts, non-parallel, Fed scenarios), tornado chart, matriz break-even rate vs DSCR.
- **Notas teóricas:** Duration gap, elasticidad precio-tasa.
- **Alcance:** Simulación; fuera de alcance ejecución de hedges (T-045).

**Integración de pipeline (opción B – cashflows determinísticos):** `MonteCarloPipeline.run_complete_analysis` acepta `zero_curve`, `debt_structure`, `tranche_cashflows` y opcionalmente `spread_calibrator` para poblar `pricing_mc` (precios MC, duration/convexidad, sensibilidad de tasas) reutilizando los cashflows determinísticos y spreads/PD/LGD simulados.

**Cashflows estocásticos (opción C simplificada):** `build_financial_path_callback(..., debt_structure=..., include_tranche_cashflows=True)` emite `tranche_cashflows` vectorizados por trayectoria usando un waterfall simplificado (senior-first, sin DSRA/MRA). `MonteCarloPipeline.run_complete_analysis` expone estos cashflows en `pricing_mc` cuando están presentes.

**Nota de capital structure:** La estructura actual permanece en ~70% deuda (72M). Se prevé revisar un deleveraging a ~50% LTV (55/34/11 ≈ 27.5/17/5.5 MUSD) según decisión del equipo; pendiente de aprobación antes de implementar.

---

## WP-09 · Visualizaciones (T-032)

### T-032 · Dashboard de resultados
**Estado actual:** En progreso (`pftoken/viz/dashboards.py` cubre CFADS vs servicio, DSCR, estructura, reservas; faltan fan charts, stress, AMM y export HTML).
- **Objetivo:** Proveer dashboard interactivo con KPIs, cascadas, comparaciones y stress/AMM panels.
- **Dependencias:** T-006, T-041, T-043, WP-14.
- **Entregables:** Notebook `notebooks/dashboard.ipynb` o módulo `dashboards.py` extendido (Panel 1–9), widgets (ipywidgets/Plotly), export HTML estático y documentación interpretativa.
- **Notas teóricas:** Storytelling cuantitativo, visualizaciones profesionales (Matplotlib/Plotly).
- **Alcance:** Dashboards offline; fuera de alcance apps web productivas.

---

## WP-10 · Optimización (T-036)

### T-036 · Búsqueda de WACD mínimo
**Estado actual:** COMPLETO (vía WP-05 EfficientFrontierAnalysis, Pareto 3D riesgo-retorno-WACD).
- **Objetivo logrado:** Optimizar pesos de tramos usando optimización multiobjetivo (Pareto) que respeta simultáneamente riesgo, retorno y WACD; se evitó degradar riesgo por minimizar solo costo.
- **Dependencias:** T-028, T-009, T-035, WP-05 (frontier + CVaR/EL).
- **Entregables:** Estructura tokenizada 55/34/12 ya adoptada, ~70 bps de mejora WACD after-tax documentada en WP-04/WP-05, ranking de carteras dominantes y reporte comparativo tradicional vs tokenizado.
- **Notas teóricas:** La frontera eficiente (Pareto) domina un enfoque SLSQP single-objective para problemas con trade-offs riesgo–retorno–costo; refinamiento SLSQP se consideró innecesario.
- **Alcance:** Optimización offline completa; estructura tradicional 60/25/15 permanece como baseline fija.

---

## WP-11 · Derivados (T-045)

### T-045 · Modelo Interest Rate Cap
**Estado actual:** Pendiente (`pftoken/derivatives/interest_rate_cap.py` placeholder).
- **Objetivo:** Implementar pricer de caps/caplets (Black) y analizar cobertura vs sensibilidad a tasas.
- **Dependencias:** T-027, T-044.
- **Entregables:** Clase `InterestRateCap`, calibración de volatilidad, análisis de carry cost, escenarios con/ sin cap y comparación con swaps.
- **Notas teóricas:** Fórmula de Black, selección de strike, break-even rate.
- **Alcance:** Modelado financiero; fuera de alcance contratación real.

---

## WP-14 · AMM Simplificado (T-053, TAMM01, TAMM02, TAMM05, TAMM06, TAMM09, TAMM11)

### T-053 · Diseño arquitectura AMM
**Estado actual:** Hecho (`docs/amm/architecture.md`, `docs/amm/amm_overview.md`, `docs/amm/integration_guide.md` + módulos core/análisis implementados).
- **Objetivo:** Definir alcance teórico del AMM académico (V2/V3, pricing DCF vs mercado, stress de liquidez) y documentar supuestos/limitaciones.
- **Dependencias:** T-007, T-020.
- **Entregables:** Documento `docs/amm/architecture.md`, interfaces base (`Pool`, `PoolState`, `PoolConfig`), diagrama de flujo DCF↔Pool↔Arbitrage↔Stress.
- **Notas teóricas:** Invariantes Uniswap v2/v3, oráculos TWAP, limitaciones sin MEV/gas.
- **Alcance:** Diseño y APIs; fuera de alcance smart contracts reales.

### TAMM01 · Pool V2 Constant Product
**Estado actual:** Hecho (`pftoken/amm/core/pool_v2.py` implementa swaps/add/remove/liquidez, probado en `tests/test_amm`).
- **Objetivo:** Simular mercado x·y=k para tokens de deuda vs USDC.
- **Dependencias:** T-053.
- **Entregables:** Métodos `simulate_swap`, `execute_swap`, `add_liquidity`, `remove_liquidity`, invariantes validados; documentación matemática (pendiente `docs/amm/pool_v2.md`).
- **Notas teóricas:** Invariante x·y=k, slippage proporcional al tamaño relativo de la orden.
- **Alcance:** Simulador off-chain; fuera de alcance despliegue on-chain.

### TAMM02 · Pool V3 Concentrated Liquidity
**Estado actual:** Hecho (`pftoken/amm/core/pool_v3.py` con simulate_swap tick-crossing Q64.96, helpers `sqrt_price_math`, tests `tests/test_amm/test_pool_v3.py`).
- **Objetivo:** Modelar liquidez concentrada con rangos [P_low, P_high], tick math y capital efficiency.
- **Dependencias:** TAMM01.
- **Entregables:** Swaps atravesando rangos, `tick_spacing`, cálculo de eficiencia/APR, visualización de distribución de liquidez.
- **Notas teóricas:** Fórmulas Uniswap v3 (√P mapping), riesgo de rango estrecho.
- **Alcance:** Simulador académico; fuera de alcance implementación completa Uniswap.

### TAMM05 · Market Price Calculator
**Estado actual:** Hecho (`pftoken/amm/pricing/market_price.py` con spot/TWAP/exec price/depth/arbitrage_signal; slippage curves in `pricing/slippage.py`; tests `tests/test_amm/test_market_pricing.py`, `test_slippage.py`).
- **Objetivo:** Extraer precios observables (spot, TWAP, ejecución por tamaño) y compararlos con precio DCF para detectar arbitrajes.
- **Dependencias:** TAMM01, T-007.
- **Entregables:** Funciones `calculate_execution_price`, `market_depth_curve`, `detect_arbitrage_opportunity`, tracking histórico y visualización dual (mercado vs DCF).
- **Notas teóricas:** Slippage, TWAP geométrico, spreads expresados en bps.
- **Alcance:** Análisis; fuera de alcance conexión con exchanges reales.

### TAMM06 · DCF Integration Convergence
**Estado actual:** Hecho (`pftoken/amm/pricing/arbitrage_engine.py`, convergence hooks in `dcf_integration.py`, tests `tests/test_amm/test_arbitrage_engine.py`).
- **Objetivo:** Simular traders que cierran brechas precio mercado vs DCF, midiendo velocidad de convergencia, capital y ganancias.
- **Dependencias:** TAMM05, T-007.
- **Entregables:** `ArbitrageEngine` (sizing α·liq·spread, constraints de capital), escenarios de shock ±10 %, métricas de convergencia (half-life).
- **Notas teóricas:** Market microstructure, price discovery, mean reversion.
- **Alcance:** Simulación; fuera de alcance bots reales.

### TAMM09 · Impermanent Loss Calculator
**Estado actual:** Hecho (`impermanent_loss.py` v2/v3 range, surfaces, breakeven; `lp_pnl.py` decomposition; docs `docs/amm/impermanent_loss.md`; tests `tests/test_amm/test_impermanent_loss.py`, `test_lp_pnl.py`).
- **Objetivo:** Cuantificar IL para LPs V2/V3, break-even de fees y recomendaciones de rango.
- **Dependencias:** TAMM01, TAMM02.
- **Entregables:** Funciones IL v2/v3, `calculate_fees_earned`, simulaciones de trayectorias y `recommend_lp_strategy`, visualizaciones IL vs price_ratio y superficies rango×volatilidad.
- **Notas teóricas:** IL = 2√r/(1+r) − 1, trade-off eficiencia vs riesgo.
- **Alcance:** Simulación; fuera de alcance incentivos token reales.

### TAMM11 · Liquidity Stress Testing
**Estado actual:** Hecho (`pftoken/stress/liquidity_stress.py` panic sell/LP withdrawal/flash crash, `amm_stress_scenarios.py`, `amm_metrics_export.py`, CLI `scripts/run_amm_stress.py`, viz hooks in `pftoken/viz/amm_viz.py`, test `tests/test_integration/test_amm_stress.py`).
- **Objetivo:** Simular eventos extremos (panic sells coordinados, retiro de liquidez, flash crash) y evaluar resiliencia de pools V2/V3.
- **Dependencias:** TAMM01, TAMM02, TAMM06.
- **Entregables:** `LiquidityStressTester` con escenarios 1–4, métricas (max price impact, recovery time, LP losses, arbitraje), dashboard comparativo y análisis de circuit breakers.
- **Notas teóricas:** Stress de liquidez en DeFi, cascadas de retiro.
- **Alcance:** Simulación; fuera de alcance backtesting on-chain real.

---

## WP-15 · Fundamentos Crypto y Liquidez (T-054, T-055, T-056, T-057, T-058, T-059, T-060)

**Estado:** Alcance mínimo completado (documentación + prima regulatoria). El modelo ahora descuenta 7.5 bps por riesgo regulatorio y mantiene los beneficios de tokenización/AMM existentes.

- **T-054 · Benchmark finality y throughput multi-chain — COMPLETO:** `docs/crypto/chain_selection.md` documenta la elección Centrifuge/Polkadot (finalidad ~6s, sin prima de finality por ser mucho más rápida que la frecuencia de reporting). Notebook resumen: `notebooks/wp15_crypto_fundamentals_summary.ipynb`.
- **T-055 · Token mapping — OMITIDO:** No se requiere bridging ni mapping; se operará en tokens nativos de Centrifuge.
- **T-056 · Liquidez CeFi vs DEX — OMITIDO:** Se mantiene la integración V3 AMM con reducción de slippage 83%; volumen CeFi adicional no es necesario para el caso.
- **T-057 · Riesgo stablecoin — OMITIDO:** CFADS usa oráculos con fallback; depegs no afectan el modelo de deuda spot.
- **T-058 · Funding rates — OMITIDO:** El instrumento es spot (no perps); funding no aplica.
- **T-059 · MEV/mempool — OMITIDO:** Riesgos ya se reflejan en la prima de liquidez (70 bps) y no se modelan extra.
- **T-060 · Macro correlaciones — OMITIDO:** Riesgo proyecto domina; correlaciones cripto agregan ruido.

### Entregables WP-15 (alcance mínimo)
- Documentación: `docs/crypto/chain_selection.md`, `docs/crypto/platform_comparison.md`, `docs/crypto/regulatory_risk.md`.
- Notebook: `notebooks/wp15_crypto_fundamentals_summary.ipynb` (markdown-only).
- Modelo: `wacd_synthesis` resta `regulatory_risk_bps = 7.5`; `amm_liquidity.platform_comparison` y `platform_analysis` documentan Centrifuge vs Maple/Goldfinch/SPV. Prima de auditoría (10–20 bps one-time) explicitada en `tokenization_analysis.mechanisms`.

---

## WP-12 · Entregables (T-048, T-049, T-050)

### T-048 · Notebook final integrado
**Estado actual:** En progreso (`notebooks/01_final_report.ipynb` existe pero no cubre todas las secciones ni ejecuta pipeline completo).
- **Objetivo:** Notebook ejecutable con narrativa completa (resumen, metodología, base case, MC, riesgo, stress, AMM, comparación, conclusiones).
- **Dependencias:** WP técnicos (mínimo WP-03 + WP-14 base).
- **Entregables:** `notebooks/TP_Quant_Final.ipynb` con TOC, celdas Markdown, figuras de alta resolución, sección de reproducibilidad, export HTML.
- **Notas teóricas:** Storytelling académico y citas APA.
- **Alcance:** Notebook; fuera de alcance publicación externa.

### T-049 · Informe PDF
**Estado actual:** Pendiente (no hay LaTeX/Word en `docs/`).
- **Objetivo:** Documento formal (10–15 páginas) con capítulos introducción → marco teórico → metodología → resultados → discusión → conclusiones → referencias.
- **Dependencias:** T-048.
- **Entregables:** `docs/TP_Quant_Informe.tex/.docx` + PDF, tablas/figuras numeradas, referencias APA, apéndices con parámetros.
- **Notas teóricas:** Estilo APA/IEEE, narrativa balanceada.
- **Alcance:** Informe académico; fuera de alcance maquetado editorial.

### T-050 · README y documentación final
**Estado actual:** En progreso (README actual cubre visión general; faltan quick start completo, estructura detallada, badges, CONTRIBUTING/API/USER_GUIDE finales).
- **Objetivo:** Dejar documentación pública lista (README, CONTRIBUTING, API.md, USER_GUIDE.md).
- **Dependencias:** T-002, T-048.
- **Entregables:** README ampliado (descripción, features, instalación, quick start, estructura, casos de uso, testing, contribución, licencia, changelog, badges), `CONTRIBUTING.md`, `API.md`, `USER_GUIDE.md` actualizados, verificación de links.
- **Notas teóricas:** Buenas prácticas OSS, docstrings NumPy.
- **Alcance:** Documentación textual; fuera de alcance sitio web dedicado.

---

## WP-13 · Testing y QA (T-051, T-052)

### T-051 · Suite completa de tests
**Estado actual:** En progreso (existen tests para CFADS/parámetros/waterfall/AMM/Excel; faltan pricing, riesgo, stress, MC; muchos módulos son placeholders).
- **Objetivo:** Alcanzar cobertura >80 % en módulos críticos con Pytest, fixtures compartidos y marcado de tests lentos.
- **Dependencias:** T-003–T-017, T-021–T-045 según módulo.
- **Entregables:** Estructura `tests/` paralela a `pftoken/`, fixtures en `tests/conftest.py`, parametrizaciones/mocks, integración CI (`pytest --cov`), tests de performance/regresión (`@pytest.mark.slow`).
- **Notas teóricas:** QA cuantitativa, TDD para modelos financieros.
- **Alcance:** Tests automatizados; fuera de alcance validaciones manuales (cubiertas por T-005B).

### T-052 · Code review y refactor final
**Estado actual:** Pendiente (no se ha ejecutado ciclo de linting/refactor; hay placeholders y estilos mixtos).
- **Objetivo:** Pasar linters (pylint/flake8/mypy), reducir complejidad, eliminar duplicados y mejorar logging/docstrings.
- **Dependencias:** T-051.
- **Entregables:** Config de linters (`pyproject.toml`/`.flake8`), reporte radon, formateo black/isort, caching selectivo (`functools.lru_cache`), logging consistente, changelog de refactors.
- **Notas teóricas:** Clean code aplicado a modelos cuantitativos, control de complejidad ciclomática.
- **Alcance:** Refactor offline; fuera de alcance cambios funcionales mayores (cubiertos en otros WP).

---

Esta guía debe mantenerse sincronizada con el código, los datos (`data/input/leo_iot/`) y la memoria del sistema. Cada actualización mayor en módulos o datasets debe reflejarse aquí para preservar trazabilidad entre roadmap y estado real del proyecto.
