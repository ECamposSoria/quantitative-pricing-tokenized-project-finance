# **GUÍA COMPLETA DE IMPLEMENTACIÓN \- VERSIÓN ACTUALIZADA**

## **Modelo Cuantitativo de Project Finance Tokenizado para Constelación LEO IoT**

## **62 Tareas Totales \- Roadmap Rev. 4-Nov-2025**

---

## **📋 ÍNDICE DE WORK PACKAGES**

* **WP-01:** Setup y Arquitectura (T-001, T-002, T-012)  
* **WP-02:** Módulo CFADS y Ratios \- CORREGIDO (T-003, T-003B, T-004, T-005, T-005B, T-013, T-046, T-047)  
* **WP-03:** Waterfall de Pagos \- CON MRA (T-006, T-014, T-015, T-016, T-017, T-020)  
* **WP-04:** Pricing y Curvas (T-007, T-008, T-009, T-018, T-019)  
* **WP-05:** Riesgo Crediticio (T-010, T-033, T-034, T-035, T-037)  
* **WP-06:** Stress Testing \- AMPLIADO (T-038, T-038B, T-039, T-040, T-041, T-042, T-043)  
* **WP-07:** Simulación Monte Carlo (T-021, T-022, T-023, T-024, T-025, T-029, T-030, T-031)  
* **WP-08:** Pricing Estocástico (T-026, T-027, T-028, T-044)  
* **WP-09:** Visualizaciones (T-032)  
* **WP-10:** Optimización (T-036)  
* **WP-11:** Derivados (T-045)  
* **WP-14:** AMM Simplificado \- REDEFINIDO (T-053, TAMM01, TAMM02, TAMM05, TAMM06, TAMM09, TAMM11)  
* **WP-12:** Entregables (T-048, T-049, T-050)  
* **WP-13:** Testing y QA (T-051, T-052)

---

## **WP-01: SETUP Y ARQUITECTURA**

### **T-001: Setup inicial proyecto**

**¿En qué consiste?**  
 Crear la estructura base del repositorio Python con todas las carpetas, archivos de configuración y control de versiones necesarios para el proyecto cuantitativo.

**Relaciones con otras tareas:**

* **Prerrequisito de:** TODAS las demás tareas (T-002 a TAMM11)  
* **Habilita directamente:** T-002 (Documentación de requerimientos), T-012 (Arquitectura de módulos)

**Qué se debe implementar:**

* Estructura completa de directorios incluyendo carpetas separadas para código fuente del modelo cuantitativo, suite de tests unitarios y de integración, datasets de entrada con parámetros calibrados, resultados de simulaciones y outputs, notebooks de análisis Jupyter, documentación técnica y académica  
* Sistema de gestión de dependencias mediante archivo requirements.txt que especifique todas las librerías necesarias para computación numérica científica, validación de datos mediante esquemas tipados, visualización avanzada de resultados financieros, testing automatizado y análisis estadístico  
* Configuración de control de versiones Git con archivo de exclusiones apropiado para proyectos Python cuantitativos, excluyendo archivos compilados, caches de Python, resultados de simulaciones pesadas, datos sensibles de calibración  
* Archivo setup.py para hacer el proyecto instalable como paquete Python denominado "pftoken" con definición de dependencias y metadata del proyecto  
* Inicialización de repositorio Git local con estructura de branches para desarrollo, testing y producción  
* Creación de entorno virtual Python aislado usando venv o conda para gestión independiente de dependencias sin contaminar entorno global  
* Configuración básica de integración continua mediante archivo de configuración para ejecutar tests automáticamente en cada commit

---

### **T-002: Documentación requerimientos**

**¿En qué consiste?**  
 Crear documentación inicial exhaustiva que explique los objetivos académicos del proyecto, alcance cuantitativo, métricas clave de evaluación y metodología general del modelo de Project Finance.

**Relaciones con otras tareas:**

* **Depende de:** T-001 (necesita estructura de carpetas para almacenar documentación)  
* **Se actualiza continuamente con:** T-048 (Notebook final integrado), T-049 (Informe PDF académico), T-050 (README y documentación final)  
* **Informa a:** Todo el equipo de desarrollo sobre visión y alcance del trabajo práctico

**Qué se debe implementar:**

* Documento README principal conteniendo descripción ejecutiva del proyecto de constelación satelital LEO para IoT, justificación del caso de uso seleccionado, objetivos cuantitativos específicos de comparación entre estructura de financiamiento tradicional bancaria versus estructura tokenizada descentralizada, métricas objetivo clave con valores umbrales específicos como DSCR mayor a 1.25, LLCR mayor a 1.0, VaR al 95%, roadmap de alto nivel del proyecto con Work Packages principales  
* Documento de requerimientos funcionales especificando funcionalidades mínimas viables del modelo como cálculo de CFADS con períodos de gracia y ramping, implementación de waterfall con MRA, simulación Monte Carlo con al menos 10,000 escenarios, pricing de tranches usando curva spot, cálculo de métricas de riesgo de crédito, ejecución de stress testing con mínimo 4 escenarios adversos  
* Documento de requerimientos no funcionales especificando características técnicas como performance del modelo ejecutándose en menos de 5 minutos para 10k simulaciones, precisión numérica de al menos 6 decimales en cálculos de pricing, reproducibilidad mediante semillas aleatorias fijas, modularidad del código con separación clara de responsabilidades, documentación inline con docstrings en formato NumPy  
* Documento de arquitectura inicial con diagrama conceptual de módulos principales mostrando flujo de datos desde parámetros de entrada, pasando por cálculo de CFADS, ejecución de waterfall, pricing determinístico, simulación estocástica, hasta generación de outputs y reportes finales  
* Especificación de decisiones de diseño preliminares justificadas como uso de dataclasses para estructuras de datos inmutables, uso de NumPy para operaciones vectorizadas eficientes, uso de Pandas para manipulación de series temporales de flujos de caja, uso de Matplotlib para visualizaciones de calidad académica

---

### **T-012: Arquitectura de módulos**

**¿En qué consiste?**  
 Diseñar en detalle la arquitectura completa de clases, interfaces y el flujo de datos entre todos los módulos del sistema cuantitativo. Define cómo se comunican las diferentes partes del modelo y establece contratos claros entre componentes.

**Relaciones con otras tareas:**

* **Depende de:** T-001 (estructura base), T-002 (requerimientos definidos)  
* **Informa diseño de:** T-013 (Dataclass de parámetros), T-014 (DebtStructure), T-021 (Motor Monte Carlo), T-026 (Pricing estocástico), T-053 (Diseño AMM)  
* **Genera:** Diagramas UML de clases y arquitectura que guían todo el desarrollo posterior

**Qué se debe implementar:**

* Documento de arquitectura detallada incluyendo diagrama de flujo completo del modelo cuantitativo desde carga de datos de entrada calibrados, pasando por cálculo de CFADS con ajustes de grace period y ramping, ejecución de waterfall con lógica de prelación y reservas MRA/DSRA, pricing determinístico de tranches usando DCF con curva spot, simulación Monte Carlo con variables estocásticas correlacionadas, cálculo de métricas de riesgo de crédito por tramo, ejecución de stress testing con escenarios adversos, análisis AMM de mercado secundario, hasta generación de reportes finales y visualizaciones  
* Definición de interfaces públicas entre módulos especificando qué datos se intercambian en qué formato, qué métodos son públicos versus privados, qué contratos de entrada y salida deben cumplirse, qué excepciones pueden lanzarse en cada operación  
* Especificación de responsabilidades únicas de cada módulo para mantener principio de responsabilidad única: módulo CFADS solo calcula flujos de caja, módulo Waterfall solo ejecuta lógica de distribución, módulo Pricing solo valúa instrumentos de deuda, módulo MonteCarlo solo genera trayectorias estocásticas, módulo Risk solo calcula métricas de riesgo  
* Documentación de decisiones de diseño fundamentales justificadas como uso de clases inmutables mediante dataclasses con frozen=True para estructuras de datos, uso de funciones puras sin efectos secundarios para operaciones de cálculo, estrategia de manejo de estado mediante objetos resultado que contienen toda la información calculada, separación clara entre lógica de negocio y presentación de resultados  
* Especificación de patrones de diseño aplicables como Builder para construcción incremental de objetos complejos como estructuras de deuda, Strategy para diferentes implementaciones de waterfall según tipo de estructura, Factory para generación de escenarios de stress testing, Observer para notificación de eventos en simulación  
* Configuración de archivos **init**.py en cada paquete para definir la librería pftoken como paquete Python modular con namespaces claros  
* Definición de convenciones de nomenclatura siguiendo PEP 8: snake\_case para funciones y variables, PascalCase para clases, UPPER\_CASE para constantes  
* Especificación obligatoria de anotaciones de tipos usando typing module para todos los parámetros de funciones y valores de retorno  
* Especificación de estrategia de manejo de errores mediante excepciones personalizadas heredando de Exception para errores de validación de datos, errores de cálculo numérico, errores de convergencia de algoritmos  
* Estrategia de logging estructurado en puntos críticos del flujo como inicio y fin de simulación, eventos de default en waterfall, cálculo de métricas de riesgo, detección de arbitraje en AMM

---

## **WP-02: MÓDULO CFADS Y RATIOS (CORREGIDO)**

### **T-013: Dataclass parámetros**

**¿En qué consiste?**  
 Crear una estructura de datos tipada e inmutable que contenga todos los parámetros de entrada del modelo cuantitativo, incluyendo parámetros del proyecto LEO IoT, estructura de deuda, configuración de waterfall y parámetros de simulación.

**Relaciones con otras tareas:**

* **Depende de:** T-001 (estructura de proyecto), T-012 (arquitectura definida)  
* **Utilizado por:** T-003 (CFADS), T-006 (Waterfall), T-021 (Monte Carlo), T-026 (Pricing), T-038 (Stress testing), T-053 (AMM)  
* **Es el contrato de datos:** para todo el modelo

**Qué se debe implementar:**

* Dataclass ProjectParams en archivo pftoken/core/params.py conteniendo parámetros técnicos del proyecto satelital como número de satélites en la constelación, masa por satélite en kg, costo unitario de fabricación y lanzamiento, vida útil operativa en años, tasa de degradación anual de capacidad  
* Dataclass RevenueParams conteniendo parámetros de generación de ingresos como número inicial de dispositivos IoT conectados, ARPU mensual promedio por dispositivo, tasa de crecimiento anual de base de usuarios, tasa de churn mensual estimada, precio por mensaje IoT transmitido  
* Dataclass CostParams conteniendo parámetros de estructura de costos como OPEX fijo mensual por satélite para operaciones y mantenimiento, OPEX variable por mensaje transmitido, costos de seguros anuales como porcentaje del valor de activos, costos de licencias de espectro y regulatorios  
* Dataclass CapexParams conteniendo estructura de inversiones de capital como CAPEX inicial en año 0 para fabricación y lanzamiento de constelación, RCAPEX planificado para reemplazo de satélites al final de vida útil, contingencias como porcentaje del CAPEX base, cronograma de desembolsos de CAPEX  
* Dataclass DebtParams conteniendo parámetros de estructura de deuda como monto total de deuda a financiar, porcentajes de cada tramo Senior/Mezzanine/Subordinado, tasas de interés base para cada tramo, spreads de riesgo ajustados, tenor de cada tramo en años, cronograma de amortización, periodicidad de pagos  
* Dataclass WaterfallParams conteniendo configuración de lógica de waterfall como tamaño objetivo de DSRA como fracción del próximo servicio de deuda, tamaño objetivo de MRA como fracción del próximo RCAPEX, umbral de DSCR para distribución de dividendos, reglas de fondeo de reservas, triggers de covenants financieros  
* Dataclass GracePeriodParams conteniendo parámetros de períodos especiales como duración de grace period en meses donde solo se pagan intereses, duración de ramping period en meses con amortización gradual de principal, funciones de ramping que definen cómo crece el porcentaje de principal pagado  
* Dataclass SimulationParams conteniendo configuración de simulación Monte Carlo como número de escenarios a generar, semilla aleatoria para reproducibilidad, distribuciones estadísticas para cada variable aleatoria, matriz de correlación entre variables estocásticas, horizonte temporal de proyección  
* Implementar validaciones automáticas en **post\_init** de cada dataclass verificando consistencia de parámetros como porcentajes sumando a 1.0, valores positivos donde corresponde, fechas en orden cronológico correcto, compatibilidad entre parámetros relacionados  
* Implementar métodos de clase @classmethod para cargar parámetros desde diferentes fuentes como from\_csv para leer desde archivo CSV calibrado, from\_dict para crear desde diccionario Python, from\_json para cargar desde archivo JSON de configuración  
* Implementar método to\_dict para serializar parámetros a diccionario Python para logging y debugging  
* Documentar cada campo con docstring explicando unidades de medida, rangos válidos esperados, fuente de calibración del parámetro

### **T-003: Cálculo CFADS**

**¿En qué consiste?**  
 Implementar la lógica central de cálculo del flujo de caja disponible para servicio de deuda (Cash Flow Available for Debt Service) período por período, que es el corazón del modelo de Project Finance.

**Relaciones con otras tareas:**

* **Depende de:** T-013 (necesita ProjectParams, RevenueParams, CostParams)  
* **Utilizado por:** T-004 (ratios), T-006 (waterfall), T-021 (Monte Carlo), T-026 (pricing), T-038 (stress)  
* **Continúa en:** T-003B (extensión con grace period y ramping)

**Qué se debe implementar:**

* Clase CFADSCalculator en archivo pftoken/core/cfads.py que encapsula toda la lógica de cálculo de flujos de caja operativos  
* Método calculate\_revenues que calcula ingresos período por período considerando base creciente de dispositivos IoT según tasa de crecimiento aplicada compuestamente cada período, churn mensual reduciendo base activa, ARPU multiplicado por base activa para obtener ingresos por subscripciones, ingresos adicionales por mensajes transmitidos según volumen esperado  
* Implementar curva de adopción realista no lineal: rápido crecimiento inicial en primeros años, desaceleración gradual hacia madurez, modelar mediante función logística o curva S para capturar dinámica de penetración de mercado  
* Método calculate\_opex que calcula costos operativos considerando componente fijo por satélite operativo en constelación, componente variable proporcional a tráfico de mensajes, costos de mantenimiento preventivo y correctivo, seguros calculados como porcentaje del valor de activos depreciados, licencias y regulatorios  
* Implementar degradación de eficiencia operativa: satélites se vuelven menos eficientes con el tiempo, aumentando OPEX por unidad de servicio, modelar mediante factor de degradación anual que incrementa OPEX  
* Método calculate\_ebitda que resta OPEX de ingresos para obtener EBITDA (Earnings Before Interest, Taxes, Depreciation and Amortization) que representa flujo de caja operativo antes de cargos financieros  
* Método calculate\_capex que aplica cronograma de CAPEX inicial en fase de construcción según calendario de desembolsos, más RCAPEX de reemplazo calculado como función del número de satélites que alcanzan fin de vida útil cada período  
* Método calculate\_cfads\_before\_tax que resta CAPEX de EBITDA para obtener flujo de caja antes de impuestos disponible para servicio de deuda y distribuciones  
* Método calculate\_tax aplicando tasa impositiva corporativa sobre base imponible considerando depreciación de activos según vida útil y reglas fiscales, créditos fiscales aplicables a proyectos de infraestructura de telecomunicaciones  
* Método calculate\_cfads\_final que resta impuestos del CFADS before tax para obtener el flujo de caja neto disponible para el waterfall de pagos  
* Implementar manejo de pérdidas arrastrables: si hay EBITDA negativo en períodos iniciales, acumular pérdidas fiscales que pueden compensarse contra utilidades futuras reduciendo impuestos  
* Crear estructura de datos CFADSResult como dataclass que contenga series temporales completas de ingresos por período, OPEX por período, EBITDA por período, CAPEX por período, impuestos por período, CFADS final por período, métricas agregadas como NPV de flujos, IRR del proyecto  
* Implementar validaciones numéricas verificando que flujos de caja no contienen valores NaN o infinitos, que CFADS puede volverse negativo en algunos períodos pero es realista, que suma de flujos descontados converge a valor finito  
* Implementar visualización de flujos mediante método plot\_cfads que genere gráfico de líneas mostrando evolución temporal de ingresos, OPEX, EBITDA y CFADS final destacando períodos críticos, utilizando Matplotlib con estilo profesional

---

### **T-003B: Grace Period y Ramping**

**¿En qué consiste?**  
 Extender el cálculo de CFADS y el servicio de deuda para incorporar explícitamente la mecánica de períodos de gracia (grace period) donde solo se pagan intereses y períodos de ramping con amortización gradual del principal.

**Relaciones con otras tareas:**

* **Depende de:** T-003 (cálculo base de CFADS), T-013 (GracePeriodParams)  
* **Crítico para:** T-004 (ratios ajustados), T-006 (waterfall con fases), T-021 (Monte Carlo realista)  
* **Duración estimada:** 3 días según Gantt

**Qué se debe implementar:**

* Extender clase CFADSCalculator agregando atributos que almacenen configuración de grace period como duración en meses del período de gracia, opción de capitalización de intereses durante gracia (PIK \- Payment In Kind) versus pago en efectivo desde DSRA, tasa de interés durante gracia  
* Implementar método calculate\_grace\_period\_service que para cada período dentro de grace window calcule solo servicio de intereses sin amortización de principal, si PIK está activo entonces capitalize intereses sumándolos al saldo de deuda principal incrementando deuda outstanding, si no PIK entonces pague intereses desde CFADS o extraiga desde DSRA  
* Implementar función de ramping phi(t) que defina fracción del principal programado que efectivamente se amortiza en cada período de ramping, usando función lineal donde phi va desde 0 al inicio del ramping hasta 1 al final del período de ramping, permitir configuración de diferentes curvas de ramping como lineal, exponencial acelerada, o customizada  
* Modificar cálculo de servicio de deuda total en cada período: durante grace period servicio \= solo intereses, durante ramping servicio \= intereses \+ principal × phi(t), después de ramping servicio \= intereses \+ principal completo  
* Implementar tracking de saldo de deuda ajustado: si hay capitalización PIK entonces saldo aumenta durante grace, durante ramping el saldo se amortiza gradualmente, después de ramping se amortiza al ritmo programado completo  
* Crear método calculate\_adjusted\_dscr que calcule ratio de cobertura ajustado por fase: durante grace DSCR\_grace \= CFADS / intereses con umbral objetivo \> 1.0x, durante ramping DSCR\_ramp \= CFADS / (intereses \+ principal × phi) con umbral \> 1.15x, en steady state DSCR \= CFADS / servicio total con umbral \> 1.25x  
* Implementar validaciones de consistencia verificando que duración de grace \+ duración de ramping no exceda tenor total de deuda, que CFADS durante grace sea suficiente para cubrir al menos intereses si no hay PIK, que DSRA tiene fondos suficientes si se requiere pagar intereses desde reserva  
* Generar reporte de transición de fases mostrando claramente en qué períodos termina grace, en qué períodos ocurre ramping, en qué período se alcanza steady state con servicio completo  
* Implementar visualización específica plotting servicio de deuda en el tiempo destacando fase de grace con barra de un color, fase de ramping con otro color, steady state con tercer color, superponer curva de CFADS para visualizar cobertura en cada fase  
* Documentar exhaustivamente la lógica de grace y ramping con ecuaciones LaTeX en docstrings explicando notación matemática, referencias a Gatti (2018) y Yescombe (2013) como literatura estándar de Project Finance

### **T-004: Ratios financieros DSCR/LLCR**

**¿En qué consiste?**  
 Implementar el cálculo de los ratios de cobertura de deuda más críticos en Project Finance: DSCR (Debt Service Coverage Ratio), LLCR (Loan Life Coverage Ratio) y PLCR (Project Life Coverage Ratio).

**Relaciones con otras tareas:**

* **Depende de:** T-003B (CFADS con grace y ramping completo)  
* **Utilizado por:** T-015 (covenants), T-021 (Monte Carlo con flags de default), T-038 (stress testing), T-041 (resultados de estrés)  
* **Continúa en:** T-029 (DSCR por trayectoria en MC)

**Qué se debe implementar:**

* Clase RatioCalculator en archivo pftoken/core/ratios.py que centraliza cálculo de todos los ratios de solvencia  
* Método calculate\_dscr que para cada período t calcula DSCR\_t \= CFADS\_t / DebtService\_t donde DebtService incluye tanto intereses como principal del período, considerando ajustes por fase de grace o ramping según T-003B, retornando serie temporal completa de DSCR por período  
* Implementar lógica especial para grace period: durante grace DSCR \= CFADS / solo\_intereses con umbral reducido de 1.0x pues principal no se amortiza aún  
* Implementar lógica especial para ramping period: durante ramping DSCR \= CFADS / (intereses \+ principal × phi) donde phi es fracción de ramping con umbral intermedio de 1.15x  
* Implementar lógica para steady state: después de ramping DSCR \= CFADS / servicio\_completo con umbral estándar de 1.25x establecido en covenants  
* Método calculate\_llcr que calcula Loan Life Coverage Ratio como cociente entre valor presente de CFADS futuros desde período t hasta vencimiento de deuda y saldo de deuda pendiente en período t: LLCR\_t \= NPV(CFADS\_future) / Outstanding\_Debt\_t, usando tasa de descuento igual al costo de deuda del tramo correspondiente  
* Implementar cálculo de NPV de flujos futuros aplicando factores de descuento correctos compuestos período por período: DF\_t \= 1 / (1 \+ r)^t donde r es costo de deuda anualizado  
* Calcular LLCR para cada tramo de deuda separadamente pues cada uno tiene costo y saldo diferente: LLCR\_senior, LLCR\_mezz, LLCR\_sub  
* Implementar interpretación: LLCR \> 1.0 significa que valor presente de flujos futuros cubre completamente deuda restante, LLCR \< 1.0 indica insuficiencia de flujos proyectados para pagar deuda  
* Método calculate\_plcr que calcula Project Life Coverage Ratio tomando valor presente de CFADS durante toda la vida del proyecto sin restricción a vida de préstamo: PLCR \= NPV(CFADS\_proyecto\_completo) / Total\_Debt, usando misma tasa de descuento que LLCR  
* Implementar PLCR para evaluar sostenibilidad financiera del proyecto completo más allá del préstamo específico, PLCR \> 1.0 indica que proyecto genera más valor que deuda total emitida  
* Implementar método de detección de breaches: check\_covenant\_breach que verifique en cada período si DSCR cae por debajo de umbral mínimo definido en covenants, retornando lista de períodos y magnitud de breach  
* Crear estructura de datos RatioResults como dataclass conteniendo series temporales de DSCR\_t, LLCR\_t, PLCR\_t por período, flags indicando períodos con covenant breach, estadísticas agregadas como DSCR mínimo observado, DSCR promedio ponderado por servicio, percentiles de distribución  
* Implementar visualización de ratios mediante plotting: gráfico de líneas mostrando evolución de DSCR en el tiempo con línea horizontal en umbral de covenant 1.25x, sombreado en rojo para períodos con breach, anotaciones destacando DSCR mínimo  
* Generar gráfico separado para LLCR y PLCR mostrando evolución y destacando momento donde LLCR alcanza 1.0 si es que ocurre  
* Implementar tests unitarios verificando que ratios se calculan correctamente en casos conocidos: si CFADS \= 150 y servicio \= 100 entonces DSCR \= 1.5x, verificar cálculo de NPV usando casos analíticos simples

### **T-005: Modelo Merton PD**

**¿En qué consiste?**  
 Implementar el modelo estructural de Merton para cálculo endógeno de probabilidad de default (PD) y loss given default (LGD) basado en comparación estocástica entre valor de activos del proyecto y valor de deuda outstanding.

**Relaciones con otras tareas:**

* **Depende de:** T-003B (CFADS base para valorar activos)  
* **Se integra en:** T-024 (Merton dentro de Monte Carlo para PD dinámica)  
* **Utilizado por:** T-010 (métricas de riesgo EL/VaR), T-033 (pérdida esperada por tramo)  
* **Continúa en:** T-005B (Excel validation)

**Qué se debe implementar:**

* Clase MertonModel en archivo pftoken/risk/merton.py que implementa modelo estructural de valoración de deuda riesgosa  
* Método calculate\_asset\_value que valora activos del proyecto como valor presente de CFADS esperados futuros: V\_assets \= NPV(CFADS\_future), usando tasa de descuento apropiada que refleja riesgo del proyecto como WACC o costo de capital de activos  
* Implementar simulación de trayectoria estocástica de valor de activos: asumir que activos siguen proceso geométrico browniano dV/V \= μ dt \+ σ dW donde μ es drift esperado, σ es volatilidad de activos, dW es Wiener process  
* Calibrar parámetros del proceso estocástico: estimar μ como retorno esperado del proyecto basado en EBITDA/valor activos, estimar σ como volatilidad histórica de proyectos comparables del sector telecomunicaciones satelitales  
* Método calculate\_default\_probability que implementa lógica de Merton: default ocurre si en horizonte T el valor de activos V\_T cae por debajo del valor facial de deuda D: PD \= P(V\_T \< D), calcular esta probabilidad usando fórmula analítica de Black-Scholes-Merton para distancia a default  
* Implementar cálculo de distance to default: DD \= \[ln(V\_0/D) \+ (μ \- σ²/2)T\] / (σ√T), este es número de desviaciones estándar que separan valor actual de activos del umbral de default  
* Calcular PD usando distribución normal: PD \= Φ(-DD) donde Φ es función de distribución acumulada normal estándar  
* Método calculate\_lgd que calcula Loss Given Default considerando que en caso de default los acreedores recuperan valor de activos residuales: Recovery \= V\_default / D, entonces LGD \= 1 \- Recovery  
* Implementar lógica de prioridad de recuperación: en estructura con múltiples tranches, Senior recupera primero hasta su monto nominal, luego Mezz recupera de lo restante, finalmente Sub recupera si queda algo  
* Calcular LGD específica por tramo: LGD\_senior típicamente baja (10-20%), LGD\_mezz media (30-50%), LGD\_sub alta (60-80%) reflejando subordinación  
* Método calculate\_expected\_loss que combina PD y LGD para obtener pérdida esperada: EL \= PD × LGD × Exposure, donde Exposure es saldo de deuda outstanding en momento de análisis  
* Implementar ajuste por horizonte temporal: PD aumenta con horizonte más largo, implementar curva de term structure de PD para diferentes tenores: PD\_1y, PD\_3y, PD\_5y, etc.  
* Crear estructura de datos MertonResult conteniendo PD estimada con intervalo de confianza, LGD por tramo, EL por tramo, distance to default, valor de activos simulado, sensibilidades del modelo a parámetros clave  
* Implementar análisis de sensibilidad: cómo varía PD ante cambios en volatilidad de activos σ, cómo varía ante cambios en leverage D/V, generar gráficos de tornado mostrando sensibilidades  
* Documentar supuestos del modelo: distribución lognormal de activos, volatilidad constante, deuda con valor facial fijo, ausencia de pagos intermedios en horizonte analizado  
* Incluir referencias académicas: Merton (1973) para la teoría de valoración de opciones, Merton (1974) para su aplicación a deuda corporativa, modelo KMV, y aplicaciones a Project Finance según literatura

---

### **T-005B: Excel Validation Model**

**¿En qué consiste?**  
 Crear un modelo de validación en Excel que replique los cálculos core del modelo Python para asegurar corrección numérica y servir como herramienta de debugging y explicación académica.

**Relaciones con otras tareas:**

* **Crítico: Depende de:** T-004 (ratios), T-005 (Merton), necesita resultados para comparar  
* **Valida:** T-003, T-003B, T-004, T-005, T-006 (módulos core)  
* **Duración:** 4 días según Gantt chart (tarea crítica)

**Qué se debe implementar:**

* Crear archivo Excel TP\_Quant\_Validation.xlsx con estructura modular en hojas separadas  
* Hoja "Inputs" conteniendo todos los parámetros del modelo exactamente como en ProjectParams de T-013: parámetros del proyecto satelital, parámetros de ingresos y costos, estructura de deuda, configuración de waterfall, parámetros de grace y ramping  
* Usar validación de datos en celdas de input para asegurar rangos válidos: porcentajes entre 0-100%, montos positivos, fechas consistentes  
* Usar nombres de rango en Excel para hacer fórmulas legibles: nombrar celda con CAPEX\_inicial, tasa\_senior, DSCR\_covenant, etc.  
* Hoja "CFADS\_Calc" replicando exactamente la lógica de T-003 y T-003B: columnas para cada período t desde 0 hasta horizonte, filas calculando ingresos por subscripciones IoT aplicando tasa de crecimiento compuesta y churn, ingresos por mensajes según volumen, OPEX fijo y variable, EBITDA, CAPEX y RCAPEX, impuestos con depreciación, CFADS final  
* Implementar cálculos de grace period: columnas adicionales mostrando saldo de deuda ajustado si hay capitalización PIK, intereses capitalizados sumándose al principal  
* Implementar ramping: columna con función phi(t) calculada según período, servicio de deuda ajustado por phi  
* Hoja "Ratios" calculando DSCR, LLCR y PLCR: DSCR simple dividiendo CFADS/servicio en cada período, LLCR usando función NPV de Excel para calcular valor presente de CFADS futuros desde cada período hasta maturity, PLCR calculando NPV de flujos completos del proyecto  
* Resaltar en formato condicional períodos donde DSCR \< 1.25 en color rojo indicando breach de covenant  
* Hoja "Merton\_PD" implementando modelo de T-005: calcular valor de activos como NPV de CFADS usando función VNA de Excel, implementar cálculo de distance to default usando fórmulas de Merton, calcular PD usando función NORM.DIST de Excel  
* Calcular LGD asumiendo diferentes recovery rates por tramo según jerarquía de prelación  
* Hoja "Waterfall" mostrando paso a paso la distribución de CFADS: empezar con CFADS disponible, restar OPEX, pagar intereses de cada tramo en orden de prelación, fondear DSRA si está por debajo de target, fondear MRA si está por debajo de target, amortizar principal de cada tramo según prelación, distribuir dividendos solo si DSCR \> 1.3 y reservas completas  
* Usar formato condicional para resaltar flujos: positivos en verde, negativos en rojo, ceros en gris  
* Hoja "Comparison" que importe resultados del modelo Python (copiar/pegar desde CSV exportado) y calcule diferencias: diferencia absoluta y diferencia porcentual para cada métrica clave  
* Establecer tolerancia aceptable: diferencias \< 0.01% indican match perfecto, diferencias 0.01-0.1% son aceptables por redondeo, diferencias \> 0.1% requieren investigación  
* Crear gráficos en Excel replicando visualizaciones del modelo Python: gráfico de líneas de CFADS en el tiempo, gráfico de DSCR con threshold, gráfico de waterfall en cascada mostrando flujo de pagos  
* Implementar macros VBA simples para automatizar comparación: botón que ejecute macro para importar CSV de Python, calcular diferencias automáticamente, generar reporte de validación  
* Documentar exhaustivamente cada celda con comentarios explicando la fórmula: qué calcula, por qué se calcula así, qué supuestos se hacen  
* Crear hoja "Documentation" con tabla explicativa de cada métrica: nombre, fórmula, interpretación, rangos típicos en Project Finance  
* Usar esta herramienta Excel para presentaciones académicas mostrando paso a paso la lógica del modelo de forma interactiva y visual

### **T-046: Dataset LEO IoT**

**¿En qué consiste?**  
 Crear y calibrar un dataset realista de parámetros para el proyecto de constelación LEO IoT que servirá como caso de estudio base para todo el trabajo práctico.

**Relaciones con otras tareas:**

* **Depende de:** T-013 (estructura de params definida)  
* **Alimenta a:** Todas las tareas de cálculo (T-003, T-006, T-021, T-026, T-038)  
* **Se complementa con:** T-047 (calibraciones adicionales)

**Qué se debe implementar:**

* Investigar proyectos de constelaciones LEO comparables: analizar Starlink de SpaceX, OneWeb, Iridium Next como benchmarks para parámetros técnicos y financieros  
* Crear archivo CSV input\_data\_leo\_iot.csv con estructura columnar conteniendo todos los parámetros necesarios  
* Calibrar parámetros técnicos del proyecto: número de satélites en constelación inicial \= 150 para cobertura global de IoT, masa promedio por satélite \= 200 kg típico de smallsats, costo unitario de fabricación \= $500k por satélite basado en producción en escala, costo de lanzamiento \= $1M por lanzamiento compartido rideshare, vida útil \= 7 años considerando degradación orbital en LEO  
* Calibrar parámetros de mercado IoT: base inicial de dispositivos \= 500,000 unidades en año 1, tasa de crecimiento \= 15% anual durante primeros 5 años reflejando adopción de IoT, ARPU \= $5/mes por dispositivo competitivo con redes terrestres, tasa de churn \= 2% mensual típica de servicios M2M  
* Calibrar estructura de costos: OPEX fijo \= $50k/mes por satélite para operaciones de control y telemetría, OPEX variable \= $0.01 por mensaje transmitido, seguros \= 2% anual del valor de activos, costos regulatorios \= $2M anuales por licencias de espectro  
* Calibrar CAPEX: inversión inicial \= $75M para fabricación de 150 satélites, $22.5M en lanzamientos, $10M en ground segment, total CAPEX inicial \= $107.5M, RCAPEX \= reemplazar 20% de flota cada año a partir de año 6  
* Calibrar estructura de deuda: monto total \= $90M equivalente a 85% del CAPEX inicial, tramo Senior \= 60% con tasa base \= 5.5%, tramo Mezzanine \= 25% con tasa base \= 8.0%, tramo Subordinado \= 15% con tasa base \= 12.0%, tenor \= 10 años con amortización bullet modificada  
* Calibrar waterfall: DSRA target \= 100% del próximo servicio semestral de deuda, MRA target \= 50% del próximo RCAPEX anual, covenant DSCR mínimo \= 1.25x, threshold para dividendos \= DSCR \> 1.30x  
* Calibrar grace period: duración \= 24 meses durante fase de construcción y ramping inicial, capitalización de intereses (PIK) durante grace \= SI para conservar caja, ramping period \= 24 meses con phi lineal desde 0 a 1  
* Documentar fuentes de calibración: citar fuentes públicas como presentaciones de earnings de SpaceX/OneWeb, reportes de analistas de la industria satelital como NSR o Euroconsult, benchmarking con proyectos de infraestructura comparables  
* Implementar análisis de sensibilidad sobre parámetros clave identificando cuáles tienen mayor impacto en viabilidad: tasa de adopción de IoT, ARPU, costo de lanzamiento, tasa de interés senior  
* Crear versiones alternativas del dataset: scenario\_optimista.csv con supuestos favorables (crecimiento 20%, ARPU $7, lanzamiento más barato), scenario\_pesimista.csv con supuestos adversos (crecimiento 10%, ARPU $4, costos mayores)  
* Validar consistencia interna: verificar que deuda no excede capacity to pay del proyecto, que DSCR en escenario base sea \> 1.25 en mayoría de períodos, que proyecto alcanza IRR \> WACC indicando creación de valor

---

### **T-047: Calibraciones adicionales**

**¿En qué consiste?**  
 Refinar y calibrar parámetros adicionales más sofisticados necesarios para simulación Monte Carlo, modelo de Merton, pricing de tranches y stress testing.

**Relaciones con otras tareas:**

* **Depende de:** T-046 (dataset base)  
* **Alimenta:** T-021 (MC necesita distribuciones y correlaciones), T-005 (Merton necesita volatilidad), T-028 (pricing necesita spreads)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Calibrar parámetros de simulación estocástica: distribución estadística para volatilidad de ingresos \= lognormal con media \= esperado y desviación estándar \= 15% anual reflejando incertidumbre en adopción de IoT, distribución para volatilidad de OPEX \= normal con desviación \= 10% considerando variabilidad operativa  
* Estimar matriz de correlación entre variables estocásticas: correlación entre ingresos y OPEX \= 0.4 positiva pues mayor tráfico implica mayores costos variables, correlación entre tasa de interés base y spread de riesgo \= \-0.3 negativa por flight to quality, correlación entre churn y competencia de precios \= 0.6 positiva  
* Utilizar métodos estadísticos para estimación: si hay datos históricos de proyectos comparables usar análisis de regresión, si no hay datos usar juicio experto estructurado mediante Delphi method, triangular entre diferentes fuentes  
* Calibrar parámetros del modelo de Merton: volatilidad de activos σ\_assets \= 25% anual basada en volatilidad de equity de empresas satelitales comparables ajustada por leverage usando fórmula de Merton σ\_assets \= σ\_equity × E/(E+D), drift esperado μ \= (EBITDA/Valor activos) \- tasa de depreciación estimando retorno sobre activos  
* Validar calibración de Merton: verificar que distance to default resultante es consistente con rating crediticio implícito del proyecto, comparar PD calculada con tasas de default históricas de Project Finance en sector telecomunicaciones  
* Calibrar spreads de riesgo sobre curva base: spread senior \= 150 bps sobre SOFR consistente con deuda senior garantizada de infraestructura, spread mezz \= 400 bps reflejando subordinación parcial, spread sub \= 800 bps por ser junior sin garantías  
* Relacionar spreads con métricas de riesgo: usar modelo simple spread \= base \+ α × PD \+ β × LGD donde α y β son coeficientes de sensibilidad calibrados mediante regresión sobre datos de mercado de bonos corporativos  
* Calibrar recovery rates para cada tramo: RR\_senior \= 75% dado garantías sobre activos satelitales físicos y prioridad absoluta, RR\_mezz \= 50% por ser mezanine sin garantía colateral específica, RR\_sub \= 25% por ser equity-like y absorber primeras pérdidas  
* Justificar recovery rates: satelites tienen valor de reventa limitado una vez en órbita (activos específicos), pero licencias de espectro y contratos con clientes tienen valor recuperable, ground stations tienen valor de liquidación  
* Calibrar parámetros de stress testing: magnitud de shocks realistas como caída de demanda de 20-30% en crisis económica, incremento de tasas de 200 bps en escenario de Fed hawkish, fallas de lanzamiento impactando 10-15% de flota, retraso de 12 meses en ramping operativo  
* Documentar incertidumbre de calibración: reportar intervalos de confianza para cada parámetro, realizar análisis de sensibilidad sobre valores plausibles, identificar parámetros con mayor incertidumbre que requieren escenarios múltiples

\#\#\# \*\*T-047: Dataset LEO IoT \- PARÁMETROS CALIBRADOS SEGÚN EXCEL\*\* **\*\*¿En qué consiste?\*\*** Este dataset contiene los parámetros EXACTOS del modelo Excel validado del proyecto LEO IoT. Estos números garantizan DSCR \= 1.45x en años operativos y replican el comportamiento financiero demostrado. \--- \#\# \*\*A. ESTRUCTURA DE DEUDA (Params)\*\* | Parámetro | Valor | Unidad | Descripción | |-----------|-------|--------|-------------| | \`Principal\_Senior\` | 43.2 | MUSD | Tramo Senior (60% de deuda total) | | \`Principal\_Mezz\` | 18.0 | MUSD | Tramo Mezzanine (25% de deuda total) | | \`Principal\_Sub\` | 10.8 | MUSD | Tramo Subordinado (15% de deuda total) | | \`Debt\_Total\` | **\*\*72.0\*\*** | MUSD | Deuda total del proyecto | | \`Rate\_Senior\` | 0.060 | % anual | Tasa de interés tramo Senior (6.0%) | | \`Rate\_Mezz\` | 0.085 | % anual | Tasa de interés tramo Mezzanine (8.5%) | | \`Rate\_Sub\` | 0.110 | % anual | Tasa de interés tramo Subordinado (11.0%) | | \`Grace\_Years\` | 4 | años | Período de gracia (solo intereses, años 1-4) | | \`Tenor\_Years\` | 15 | años | Plazo total del financiamiento | | \`DSCR\_Obj\` | 1.45 | ratio | DSCR objetivo para amortización esculpida | | \`Weight\_Senior\` | 0.70 | ratio | Peso relativo Senior | | \`Weight\_Mezz\` | 0.23 | ratio | Peso relativo Mezzanine | | \`Weight\_Sub\` | 0.07 | ratio | Peso relativo Subordinado | \--- \#\# \*\*B. PROYECCIÓN DE CFADS (por año, en MUSD)\*\* | Año | Revenue | OPEX | Maintenance | ΔWC | Tax | RCAPEX | \*\*CFADS\*\* | |-----|---------|------|-------------|-----|-----|--------|-----------| | 1 | 0.00 | 0.60 | 0.00 | 0.00 | 0.00 | 0.00 | **\*\*-0.60\*\*** | | 2 | 0.00 | 1.20 | 0.00 | 0.00 | 0.00 | 0.00 | **\*\*-1.20\*\*** | | 3 | 3.00 | 2.40 | 0.10 | 0.20 | 0.00 | 0.00 | **\*\*0.30\*\*** | | 4 | 10.00 | 4.50 | 0.20 | 0.30 | 0.00 | 0.00 | **\*\*5.00\*\*** | | 5 | 20.00 | 6.50 | 0.30 | 0.50 | 0.30 | 0.00 | **\*\*12.40\*\*** | | 6 | 28.00 | 8.50 | 0.40 | 0.50 | 0.60 | 0.00 | **\*\*18.00\*\*** | | 7 | 34.00 | 10.00 | 0.50 | 0.50 | 0.90 | 0.00 | **\*\*22.10\*\*** | | 8 | 38.00 | 11.50 | 0.60 | 0.60 | 1.20 | 0.00 | **\*\*24.10\*\*** | | 9 | 40.00 | 12.00 | 0.70 | 0.60 | 1.40 | 0.00 | **\*\*25.30\*\*** | | 10 | 38.00 | 12.00 | 1.20 | 0.60 | 1.40 | 0.00 | **\*\*22.80\*\*** | | 11 | 35.00 | 11.50 | 0.80 | 0.50 | 1.20 | 0.00 | **\*\*21.00\*\*** | | 12 | 33.00 | 11.00 | 0.80 | 0.40 | 1.10 | 0.00 | **\*\*19.70\*\*** | | 13 | 30.00 | 10.50 | 0.90 | 0.30 | 0.90 | 0.00 | **\*\*17.40\*\*** | | 14 | 27.00 | 10.00 | 0.80 | 0.20 | 0.80 | 0.00 | **\*\*15.20\*\*** | | 15 | 24.00 | 9.50 | 0.60 | 0.20 | 0.70 | 0.00 | **\*\*13.00\*\*** | **\*\*Totales:\*\*** \- Revenue Total: **\*\*360.00 MUSD\*\*** \- CFADS Total: **\*\*214.50 MUSD\*\*** \- OPEX Total: **\*\*121.70 MUSD\*\*** \--- \#\# \*\*C. WATERFALL Y SERVICIO DE DEUDA (por año, en MUSD)\*\* | Año | BOP\_Senior | BOP\_Mezz | BOP\_Sub | Int\_S | Int\_M | Int\_U | Amort\_S | Amort\_M | Amort\_U | \*\*Service\*\* | \*\*DSCR\*\* | |-----|------------|----------|---------|-------|-------|-------|---------|---------|---------|-------------|----------| | 1 | 43.20 | 18.00 | 10.80 | 2.59 | 1.53 | 1.19 | 0.00 | 0.00 | 0.00 | **\*\*5.31\*\*** | **\*\*-0.113\*\*** | | 2 | 43.20 | 18.00 | 10.80 | 2.59 | 1.53 | 1.19 | 0.00 | 0.00 | 0.00 | **\*\*5.31\*\*** | **\*\*-0.226\*\*** | | 3 | 43.20 | 18.00 | 10.80 | 2.59 | 1.53 | 1.19 | 0.00 | 0.00 | 0.00 | **\*\*5.31\*\*** | **\*\*0.057\*\*** | | 4 | 43.20 | 18.00 | 10.80 | 2.59 | 1.53 | 1.19 | 0.00 | 0.00 | 0.00 | **\*\*5.31\*\*** | **\*\*0.942\*\*** | | 5 | 43.20 | 18.00 | 10.80 | 2.59 | 1.53 | 1.19 | 2.27 | 0.75 | 0.23 | **\*\*8.55\*\*** | **\*\*1.450\*\*** ✓ | | 6 | 40.93 | 17.25 | 10.57 | 2.46 | 1.47 | 1.16 | 5.13 | 1.69 | 0.51 | **\*\*12.41\*\*** | **\*\*1.450\*\*** ✓ | | 7 | 35.80 | 15.57 | 10.06 | 2.15 | 1.32 | 1.11 | 7.46 | 2.45 | 0.75 | **\*\*15.24\*\*** | **\*\*1.450\*\*** ✓ | | 8 | 28.34 | 13.12 | 9.31 | 1.70 | 1.11 | 1.02 | 8.95 | 2.94 | 0.89 | **\*\*16.62\*\*** | **\*\*1.450\*\*** ✓ | | 9 | 19.39 | 10.18 | 8.42 | 1.16 | 0.87 | 0.93 | 10.15 | 3.33 | 1.01 | **\*\*17.45\*\*** | **\*\*1.450\*\*** ✓ | | 10 | 9.24 | 6.84 | 7.40 | 0.55 | 0.58 | 0.81 | 9.24 | 3.56 | 0.96 | **\*\*15.72\*\*** | **\*\*1.450\*\*** ✓ | | 11 | 0.00 | 3.28 | 6.44 | 0.00 | 0.28 | 0.71 | 0.00 | 3.28 | 6.44 | **\*\*10.71\*\*** | **\*\*1.962\*\*** ✓ | | 12 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **\*\*0.00\*\*** | **\*\*N/A\*\*** | **\*\*Métricas Clave:\*\*** \- DSCR Promedio (Años 5-11): **\*\*1.523\*\*** \- DSCR Objetivo: **\*\*1.450\*\*** (cumplido años 5-10) \- Grace Period: Años 1-4 (solo intereses) \- Amortización completa: Año 11 \--- \#\# \*\*D. PARÁMETROS IMPLÍCITOS DERIVADOS\*\* | Parámetro | Valor Calculado | Fuente | |-----------|-----------------|--------| | CAPEX Total Implícito | \~90-120 MUSD | Deuda \= 72 MUSD @ 60-80% ratio | | EBITDA/Revenue Ratio | \~62% | (Revenue \- OPEX) / Revenue | | Tax Rate Efectiva | \~25-30% | Tax / (Revenue \- OPEX \- Depreciation) | | NPV CFADS @ 7.4% | \~150 MUSD | Descuento de flujos futuros | | LLCR (estimado) | \~2.0x | NPV(CFADS) / Deuda Outstanding | | PLCR (estimado) | \~2.1x | NPV(CFADS\_proyecto) / Deuda Inicial | \--- \#\# \*\*E. ORDEN DE PRELACIÓN DEL WATERFALL\*\* \`\`\` 1\. OPEX (implícito, ya restado en CFADS) 2\. Intereses Senior (Int\_S) 3\. Intereses Mezzanine (Int\_M) 4\. Intereses Subordinado (Int\_U) 5\. Fondeo DSRA (target \= 100% próximo servicio) 6\. Amortización Principal Senior (Amort\_S) 7\. Amortización Principal Mezzanine (Amort\_M) 8\. Amortización Principal Subordinado (Amort\_U) 9\. Fondeo MRA (target \= 50% próximo RCAPEX) 10\. Cash Sweep (si DSCR \< 1.25) 11\. Dividendos (si DSCR \> 1.30) \`\`\` \--- \#\# \*\*F. FÓRMULAS CLAVE IMPLEMENTADAS\*\* **\*\*CFADS:\*\*** \`\`\` CFADS\_t \= Revenue\_t \- OPEX\_t \- Maintenance\_t \- ΔWC\_t \- Tax\_t \- RCAPEX\_t \`\`\` **\*\*DSCR:\*\*** \`\`\` DSCR\_t \= CFADS\_t / Service\_t donde: Service\_t \= (Int\_S \+ Int\_M \+ Int\_U) \+ (Amort\_S \+ Amort\_M \+ Amort\_U) \`\`\` **\*\*Amortización Esculpida (Años 5-10):\*\*** \`\`\` Service\_t ajustado para mantener DSCR\_t \= 1.45 Amort\_total\_t \= CFADS\_t / 1.45 \- Intereses\_t \`\`\` \--- \#\# \*\*G. VALIDACIONES IMPLEMENTADAS\*\* ✅ **\*\*Grace Period:\*\*** Años 1-4 sin amortización de principal ✅ **\*\*DSCR Target:\*\*** 1.45x mantenido consistentemente años 5-10 ✅ **\*\*Coherencia Matemática:\*\*** DSCR\_manual \= CFADS/Service (error \< 0.0001) ✅ **\*\*Prelación de Pagos:\*\*** Senior → Mezz → Sub respetada ✅ **\*\*Conservación de Cash:\*\*** Suma(Pagos) \+ Residual \= CFADS\_inicial ✅ **\*\*Repago Completo:\*\*** Deuda \= 0 en año 11 \--- \#\# \*\*H. ESTRUCTURA DE ARCHIVOS CSV REQUERIDA\*\* \#\#\# \*\*project\_params\_excel.csv\*\* \`\`\`csv param,value,unit,description principal\_senior,43.2,MUSD,Tramo Senior principal\_mezz,18.0,MUSD,Tramo Mezzanine principal\_sub,10.8,MUSD,Tramo Subordinado rate\_senior,0.060,ratio,Tasa anual Senior rate\_mezz,0.085,ratio,Tasa anual Mezz rate\_sub,0.110,ratio,Tasa anual Sub grace\_years,4,years,Período de gracia tenor\_years,15,years,Plazo total dscr\_obj,1.45,ratio,DSCR objetivo weight\_senior,0.70,ratio,Peso Senior weight\_mezz,0.23,ratio,Peso Mezz weight\_sub,0.07,ratio,Peso Sub \`\`\` \#\#\# \*\*cfads\_projection\_excel.csv\*\* \`\`\`csv year,revenue,opex,maintenance,wc\_change,tax,rcapex,cfads 1,0.0,0.6,0.0,0.0,0.0,0.0,\-0.6 2,0.0,1.2,0.0,0.0,0.0,0.0,\-1.2 3,3.0,2.4,0.1,0.2,0.0,0.0,0.3 4,10.0,4.5,0.2,0.3,0.0,0.0,5.0 5,20.0,6.5,0.3,0.5,0.3,0.0,12.4 6,28.0,8.5,0.4,0.5,0.6,0.0,18.0 7,34.0,10.0,0.5,0.5,0.9,0.0,22.1 8,38.0,11.5,0.6,0.6,1.2,0.0,24.1 9,40.0,12.0,0.7,0.6,1.4,0.0,25.3 10,38.0,12.0,1.2,0.6,1.4,0.0,22.8 11,35.0,11.5,0.8,0.5,1.2,0.0,21.0 12,33.0,11.0,0.8,0.4,1.1,0.0,19.7 13,30.0,10.5,0.9,0.3,0.9,0.0,17.4 14,27.0,10.0,0.8,0.2,0.8,0.0,15.2 15,24.0,9.5,0.6,0.2,0.7,0.0,13.0 \`\`\` \#\#\# \*\*debt\_schedule\_excel.csv\*\* \`\`\`csv year,bop\_senior,bop\_mezz,bop\_sub,int\_senior,int\_mezz,int\_sub,amort\_senior,amort\_mezz,amort\_sub,service,dscr 1,43.20,18.00,10.80,2.592,1.530,1.188,0.000,0.000,0.000,5.310,\-0.113 2,43.20,18.00,10.80,2.592,1.530,1.188,0.000,0.000,0.000,5.310,\-0.226 3,43.20,18.00,10.80,2.592,1.530,1.188,0.000,0.000,0.000,5.310,0.057 4,43.20,18.00,10.80,2.592,1.530,1.188,0.000,0.000,0.000,5.310,0.942 5,43.20,18.00,10.80,2.592,1.530,1.188,2.269,0.746,0.227,8.552,1.450 6,40.93,17.25,10.57,2.456,1.467,1.163,5.130,1.686,0.513,12.414,1.450 7,35.80,15.57,10.06,2.148,1.323,1.107,7.464,2.453,0.746,15.241,1.450 8,28.34,13.12,9.31,1.700,1.115,1.025,8.947,2.940,0.895,16.621,1.450 9,19.39,10.18,8.42,1.163,0.865,0.926,10.146,3.334,1.015,17.448,1.450 10,9.24,6.84,7.40,0.555,0.582,0.814,9.244,3.565,0.964,15.724,1.450 11,0.00,3.28,6.44,0.000,0.279,0.708,0.000,3.278,6.440,10.706,1.962 \`\`\` \--- \#\# \*\*✅ USO DE ESTE DATASET\*\* **\*\*Para implementar el código Python:\*\*** \`\`\`python *\# Cargar parámetros exactos del Excel* params \= pd.read\_csv('project\_params\_excel.csv') cfads \= pd.read\_csv('cfads\_projection\_excel.csv') debt \= pd.read\_csv('debt\_schedule\_excel.csv') *\# Estos números garantizan:* *\# \- DSCR \= 1.45 en años operativos* *\# \- Repago completo en año 11* *\# \- Coherencia matemática validada* \`\`\` **\*\*Validación cruzada:\*\*** \- Los tests deben comparar outputs del código vs estos valores \- Tolerancia: ±0.01% para métricas clave \- DSCR\_calculado debe igualar DSCR\_tabla con precisión de 4 decimales

---

## **WP-03: WATERFALL DE PAGOS (CON MRA)**

### **T-014: Clase DebtStructure**

**¿En qué consiste?**  
 Crear una clase que represente la estructura completa de deuda del proyecto incluyendo múltiples tranches con diferentes características de riesgo, prelación, tasas y términos.

**Relaciones con otras tareas:**

* **Depende de:** T-013 (DebtParams)  
* **Utilizado por:** T-006 (Waterfall necesita estructura), T-007 (Pricing usa tranches), T-026 (Pricing estocástico)  
* **Complementa:** T-016 (Comparador de estructuras)

**Qué se debe implementar:**

* Clase DebtStructure en archivo pftoken/waterfall/debt\_structure.py que encapsula toda la información de la estructura de deuda  
* Clase anidada Tranche representando cada tramo individual con atributos: name (Senior/Mezzanine/Subordinated), principal\_amount (monto nominal), interest\_rate (tasa nominal anual), spread\_over\_base (spread adicional sobre tasa base), tenor\_years (plazo en años), amortization\_type (bullet/amortizing/sculpted), seniority\_level (nivel de prelación numérico: 1=senior, 2=mezz, 3=sub), security\_type (secured/unsecured), covenants (lista de restricciones específicas)  
* Implementar método en Tranche calculate\_periodic\_rate que convierta tasa nominal anual a tasa por período considerando frecuencia de pagos: si semestral entonces rate\_period \= (1 \+ rate\_annual)^(1/2) \- 1  
* Implementar método en Tranche calculate\_amortization\_schedule que genere cronograma de amortización: para bullet solo un pago final, para amortizing cuotas constantes usando fórmula de anualidad, para sculpted permitir customización de perfil de principal por período  
* DebtStructure contiene lista de tranches ordenados por seniority: tranches\[0\] es más senior, tranches\[-1\] es más subordinado  
* Método add\_tranche que agregue nuevo tramo validando que seniority levels sean consecutivos y únicos, que suma de principals no exceda límite razonable del proyecto, que spreads sean crecientes con subordinación (mezz \> senior, sub \> mezz)  
* Método calculate\_wacd (Weighted Average Cost of Debt) que compute costo ponderado de deuda como suma de (weight\_i × rate\_i) donde weight \= principal\_i / total\_principal  
* Método calculate\_blended\_spread que compute spread promedio ponderado sobre curva base útil para comparaciones  
* Método get\_tranche\_by\_name que retorne objeto Tranche dado nombre como "Senior" para facilitar acceso  
* Método get\_total\_principal que sume principals de todos los tranches retornando deuda total del proyecto  
* Método compare\_structures que reciba otra DebtStructure y compute diferencias: delta en WACD, delta en monto total, delta en spreads por tramo, útil para comparar estructura tradicional vs tokenizada  
* Implementar validaciones: verificar que al menos hay un tranche senior, que seniority es estrictamente decreciente, que tasas reflejan riesgo con sub \> mezz \> senior  
* Crear estructura TraditionalStructure con factory method que genere estructura típica de Project Finance bancario: 70% senior secured, 30% mezz unsecured, sin tramo subordinado  
* Crear estructura TokenizedStructure con factory method que genere estructura granular: 50% senior, 30% mezz, 20% sub permitiendo más diversificación de riesgo  
* Implementar serialización to\_dict y from\_dict para persistir estructuras y compartir configuraciones  
* Documentar cada tramo con justificación de términos: por qué esa tasa, por qué ese plazo, qué tipo de inversor target

### **T-015: Covenants y triggers**

**¿En qué consiste?**  
 Implementar el sistema de covenants financieros y triggers que gobiernan el comportamiento del waterfall, limitando distribuciones cuando los ratios caen por debajo de umbrales críticos.

**Relaciones con otras tareas:**

* **Depende de:** T-006 (Waterfall base), T-004 (ratios DSCR/LLCR)  
* **Utilizado por:** T-021 (MC verifica breaches), T-038 (stress testing evalúa covenants), T-041 (resultados de estrés)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase CovenantEngine que centraliza toda la lógica de verificación y enforcement de covenants  
* Definir estructura Covenant como dataclass conteniendo: name (identificador del covenant), covenant\_type (DSCR/LLCR/LTV/otros), threshold\_value (valor umbral crítico), comparison\_operator (\>=, \<=, \==), action\_if\_breach (qué hacer si se viola), severity\_level (low/medium/high/critical)  
* Implementar covenants estándar de Project Finance: DSCR mínimo \= 1.25x para permitir distribución de dividendos, DSCR crítico \= 1.0x por debajo del cual se activa cash sweep, LLCR mínimo \= 1.0x para evitar default técnico, LTV máximo (Loan to Value) \= 85% para limitar apalancamiento  
* Método check\_covenant que para cada covenant verificar en cada período si se cumple o se viola: obtener valor actual de la métrica (ej. DSCR\_t), comparar contra threshold usando operator, retornar CovenanResult indicando si hay breach  
* Implementar lógica de acciones correctivas automáticas: si DSCR \< 1.25x entonces suspender dividendos y retener cash en reservas, si DSCR \< 1.15x entonces activar cash sweep forzando toda distribución residual a prepago de deuda, si DSCR \< 1.0x entonces declarar evento de default técnico requiriendo renegociación con acreedores  
* Crear jerarquía de severidad: breaches leves (DSCR entre 1.15-1.25) solo suspenden dividendos, breaches moderados (DSCR entre 1.0-1.15) activan cash sweep, breaches críticos (DSCR \< 1.0) pueden resultar en aceleración de deuda  
* Implementar cross-default provisions: si un tramo entra en default, otros tranches pueden declarar cross-default permitiendo aceleración de toda la deuda  
* Método apply\_covenant\_actions que ejecute automáticamente las acciones definidas cuando hay breach: modificar waterfall para retener cash, bloquear distribuciones a equity, desviar flujos a prepago de senior debt  
* Implementar cure periods: dar al proyecto ventana de tiempo para remediar breach antes de que se active enforcement, típicamente 60-90 días para corregir ratio por debajo de umbral  
* Método track\_covenant\_history que mantenga historial completo de cumplimiento/violación de covenants a lo largo del tiempo útil para análisis post-mortem  
* Crear estructura CovenantResult conteniendo: período evaluado, valor de métrica, threshold, si hay breach, acción tomada, severidad  
* Implementar visualización de covenants: gráfico mostrando evolución de DSCR con bandas de color verde (cumple), amarillo (warning), rojo (breach), líneas horizontales en thresholds críticos  
* Generar reporte de covenant compliance: tabla resumen mostrando para cada covenant cuántos períodos se cumplió, cuántos se violó, duración promedio de breaches, máxima magnitud de violación  
* Documentar estándares de industria: citar documentos de IFC (International Finance Corporation), guías de IPFA (Infrastructure Project Finance Association) sobre niveles típicos de covenants en Project Finance

### **T-016: Comparador estructuras**

**¿En qué consiste?**  
 Crear herramienta analítica que compare sistemáticamente estructura de deuda tradicional bancaria versus estructura tokenizada granular, evaluando diferencias en costo de capital, perfil de riesgo y flexibilidad.

**Relaciones con otras tareas:**

* **Depende de:** T-014 (DebtStructure con múltiples tranches)  
* **Utilizado por:** T-009 (cálculo WACD para comparación), T-036 (optimización necesita comparar estructuras), T-048 (notebook final incluye comparación)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase StructureComparator que encapsula toda la lógica de comparación entre estructuras alternativas  
* Método compare\_cost que calcule diferencias en costo de capital: delta\_WACD entre tradicional y tokenizada, diferencias en spreads por tramo comparable, diferencias en tasas all-in efectivas considerando fees y comisiones  
* Método compare\_risk\_profile que evalúe perfil de riesgo: comparar LGD esperada de cada estructura, comparar concentración de riesgo medida mediante índice Herfindahl, comparar diversificación de base de inversores  
* Implementar métricas de concentración: estructura tradicional típicamente tiene 2-3 tranches con pocos acreedores grandes, estructura tokenizada puede tener 3-5 tranches con cientos de tenedores pequeños, calcular índice Herfindahl H \= Σ(share\_i)² donde menor H indica mayor diversificación  
* Método compare\_flexibility que evalúe flexibilidad operativa: estructura tradicional tiene covenants más restrictivos pero permite renegociación bilateral, estructura tokenizada tiene covenants más laxos pero renegociación requiere mayorías calificadas dificultando restructuras  
* Implementar análisis de secondary market liquidity: tokens pueden ser más líquidos si hay AMM o exchange, préstamos bancarios tradicionales tienen mercado secundario limitado, evaluar bid-ask spreads esperados como proxy de liquidez  
* Método compare\_governance que analice diferencias en gobernanza: estructura tradicional tiene agente único representando acreedores facilitando decisiones, estructura tokenizada requiere votaciones on-chain de tokenholders con mayorías definidas en smart contract  
* Método compare\_transaction\_costs que estime costos de transacción: estructura tradicional tiene costos legales y due diligence elevados pero one-time, estructura tokenizada tiene costos de emisión de tokens y setup de smart contracts con costos operativos recurrentes menores  
* Implementar cálculo de all-in cost considerando no solo tasa de interés sino también: arrangement fees de bancos, legal fees, auditoría, costos de emisión de tokens, gas fees de blockchain, costos de market making si hay AMM  
* Crear estructura ComparisonResult como dataclass conteniendo: delta\_WACD absoluto y porcentual, diferencias en cada componente de costo, diferencias en métricas de riesgo con niveles de significancia estadística, scores cualitativos de flexibilidad y gobernanza  
* Método generate\_comparison\_table que produzca tabla lado a lado con todas las métricas: columna para estructura tradicional, columna para estructura tokenizada, columna de diferencias, highlighting visual de diferencias significativas  
* Implementar visualización de waterfall comparativo: dos gráficos de cascada lado a lado mostrando flujo de CFADS a través de cada estructura, destacando diferencias en retención de reservas y timing de distribuciones  
* Generar radar chart comparativo: ejes para diferentes dimensiones (costo, riesgo, liquidez, flexibilidad, gobernanza), área de estructura tradicional versus área de tokenizada, visualizar trade-offs multidimensionales  
* Implementar sensitivity analysis sobre comparación: cómo cambia conclusión si spreads tokenizados son 50 bps mayores/menores, si costos de transacción son 20% mayores/menores  
* Documentar supuestos críticos: suponer que mercado de tokens alcanza cierta madurez y liquidez, que costos de gas se mantienen en niveles actuales, que hay suficiente demanda de inversores retail para tokens  
* Generar reporte ejecutivo de comparación: síntesis de una página destacando si tokenización reduce WACD y bajo qué condiciones, identificar casos de uso donde tokenización es claramente superior versus donde tradicional es preferible

### **T-017: Implementación detallada waterfall**

**¿En qué consiste?**  
 Implementar la lógica completa y detallada del mecanismo de waterfall que distribuye CFADS siguiendo estricta prelación entre pagos de intereses, amortización de principal, fondeo de reservas y distribución de dividendos.

**Relaciones con otras tareas:**

* **Depende de:** T-015 (covenants definen reglas de distribución)  
* **Utilizado por:** T-006 (clase Waterfall principal), T-021 (MC ejecuta waterfall en cada trayectoria)  
* **Duración:** 4 días según Gantt (tarea compleja)

**Qué se debe implementar:**

* Clase WaterfallEngine que ejecuta la lógica completa de distribución de flujos período por período  
* Definir orden estricto de prelación siguiendo estándares de Project Finance: (1) OPEX del período actual, (2) Intereses tramo Senior, (3) Intereses tramo Mezz, (4) Intereses tramo Sub, (5) Fondeo DSRA hasta target, (6) Principal Senior según schedule, (7) Principal Mezz según schedule, (8) Principal Sub según schedule, (9) Fondeo MRA hasta target, (10) Sweep prepago de Senior si covenant breach, (11) Distribuciones a equity solo si DSCR \> threshold  
* Implementar método execute\_waterfall que tome CFADS del período y DebtStructure actual, ejecute pasos en orden secuencial, rastree disponibilidad de cash en cada paso, retorne WaterfallResult con detalle completo de distribuciones  
* Paso 1 \- Pago de OPEX: reservar monto necesario para cubrir costos operativos del período, si CFADS insuficiente entonces extraer desde DSRA, si aún insuficiente declarar evento de insolvencia operativa  
* Paso 2-4 \- Pago de intereses: para cada tranche en orden de seniority calcular intereses devengados del período \= saldo\_outstanding × tasa\_período, pagar intereses desde cash disponible, si insuficiente entonces extraer desde DSRA, si aún insuficiente acumular intereses impagos para carry-forward, registrar evento de default si intereses quedan impagos  
* Implementar accrual de intereses impagos: si no se pueden pagar intereses en un período, acumularlos en cuenta de intereses diferidos que se pagan con prioridad en períodos futuros  
* Paso 5 \- Fondeo DSRA: calcular target de DSRA \= 100% del próximo servicio de deuda (intereses \+ principal próximo período), comparar contra saldo actual de DSRA, si hay déficit entonces aportar desde cash disponible hasta alcanzar target o agotar cash  
* Paso 6-8 \- Amortización de principal: para cada tranche en orden de seniority obtener monto de principal programado según amortization schedule de T-014, durante grace period monto \= 0, durante ramping monto \= scheduled × phi(t), pagar principal desde cash disponible, si insuficiente entonces usar DSRA como último recurso, si aún insuficiente registrar evento de default por principal impago  
* Implementar tracking de saldos: después de cada pago de principal actualizar outstanding balance de cada tranche reduciendo saldo, validar que saldo nunca se vuelve negativo  
* Paso 9 \- Fondeo MRA: calcular target de MRA \= 50% del próximo RCAPEX planificado, comparar contra saldo actual de MRA, aportar desde cash residual hasta alcanzar target o agotar cash, MRA solo se fondea si DSCR \> 1.15 para priorizar servicio de deuda  
* Paso 10 \- Cash sweep: si hay breach de covenant DSCR \< umbral entonces activar mecanismo de sweep, todo cash residual después de fondeo de reservas se usa para prepago extraordinario de tranche Senior reduciendo saldo y acelerando amortización, cash sweep continúa hasta que DSCR se recupera por encima de umbral  
* Paso 11 \- Distribuciones a equity: solo si DSCR \> 1.30 y todas las reservas están en target completo y no hay covenants violados entonces distribuir cash residual como dividendos a equity holders, calcular dividend coverage ratio \= dividendos / equity contribution como métrica de retorno  
* Crear estructura WaterfallResult conteniendo: cash inicial disponible, monto pagado en cada paso de prelación (opex, intereses por tramo, principal por tramo, aportes a reservas), cash final residual, flags indicando eventos especiales (default, sweep activado, distribución bloqueada)  
* Implementar validación de conservación de cash: suma de todos los pagos y cash residual debe igualar cash inicial, cualquier discrepancia indica error en lógica  
* Método plot\_waterfall que genere visualización tipo cascada (waterfall chart) mostrando flujo de CFADS bajando por cada nivel de prelación con barras horizontales indicando montos retenidos en cada paso, coloreadas por tipo de pago  
* Implementar tests de escenarios extremos: qué pasa si CFADS es negativo, qué pasa si es insuficiente para cubrir OPEX, qué pasa si solo alcanza para pagar intereses senior, verificar que lógica no rompe en casos límite  
* Documentar exhaustivamente cada paso con referencias a documentos de Project Finance como Gatti (2018) "Project Finance in Theory and Practice", incluir diagramas de flujo mostrando decisiones en cada nodo del waterfall  
* Generar reporte detallado de ejecución: tabla mostrando período por período el resultado completo del waterfall, tracking de saldos de deuda, evolución de reservas, distribuciones acumuladas

### **T-006: Clase Waterfall con MRA**

**¿En qué consiste?**  
 Crear la clase principal que orquesta el mecanismo completo de waterfall integrando cálculo de CFADS, aplicación de prelación, gestión de reservas DSRA y MRA, y verificación de covenants.

**Relaciones con otras tareas:**

* **Crítico: Depende de:** T-003B (CFADS), T-005B (validación), T-014 (DebtStructure), T-017 (lógica detallada)  
* **Utilizado por:** T-021 (Monte Carlo), T-026 (Pricing), T-038 (Stress testing), T-040 (motor de estrés)  
* **Duración:** 4 días según Gantt (tarea crítica del path crítico)

**Qué se debe implementar:**

* Clase Waterfall que coordina todos los componentes del waterfall de pagos  
* Constructor que reciba ProjectParams, DebtStructure, WaterfallParams y CFADSResult como inputs, inicialice reservas DSRA y MRA en cero al comienzo del proyecto, configure covenants según T-015  
* Método run\_full\_waterfall que ejecute waterfall completo para todos los períodos del horizonte de proyección: iterar sobre cada período t, obtener CFADS\_t del CFADSResult, ejecutar WaterfallEngine de T-017 para distribuir el flujo, actualizar saldos de deuda y reservas, verificar covenants mediante CovenantEngine de T-015, acumular resultados en estructura de datos  
* Implementar gestión de DSRA (Debt Service Reserve Account): reserva que acumula cash para cubrir servicio de deuda en períodos con CFADS insuficiente, target típicamente \= 100% del próximo servicio semestral, en cada período verificar si DSRA está por debajo de target y fondear con prioridad después de pagar intereses, permitir extracción de DSRA solo para cubrir déficit en pagos de deuda  
* Implementar gestión de MRA (Maintenance Reserve Account): reserva específica para RCAPEX de reemplazo de satélites, target típicamente \= 50-100% del próximo RCAPEX planificado, fondear MRA solo después de cumplir servicio de deuda y alcanzar target de DSRA, extraer de MRA cuando llega período de RCAPEX para financiar reemplazo sin impactar CFADS operativo  
* Implementar lógica de liberación de reservas: al final del proyecto o cuando deuda está completamente pagada, liberar fondos acumulados en DSRA y MRA para distribución a equity, calcular retorno total a equity \= dividendos acumulados \+ liberación de reservas \+ valor residual de activos  
* Método calculate\_distributions\_to\_equity que sume todos los flujos que llegaron a equity holders: dividendos en períodos normales, distribuciones finales al vencimiento, retorno de reservas sobrantes  
* Implementar tracking de eventos de default: registrar si en algún período hubo impago de intereses o principal, duración del default, monto acumulado de pagos diferidos, eventual recuperación de default mediante cash sweep en períodos posteriores  
* Crear estructura FullWaterfallResult conteniendo: serie temporal completa de distribuciones período por período, evolución de saldos de deuda por tramo, evolución de reservas DSRA y MRA, registro de eventos de covenant breach y default, métricas agregadas como equity IRR  
* Método calculate\_equity\_irr que compute tasa interna de retorno para equity holders considerando equity contribution inicial como outflow negativo y todas las distribuciones como inflows positivos, usar algoritmo de Newton-Raphson para resolver ecuación de NPV \= 0  
* Método calculate\_debt\_coverage\_metrics que para cada tramo compute métricas de performance: porcentaje de períodos con intereses pagados completamente, porcentaje de períodos con principal amortizado según schedule, monto total de prepagos extraordinarios mediante cash sweep, recovery rate final si hubo default  
* Implementar análisis de sensibilidad del waterfall: cómo cambian distribuciones si CFADS aumenta/disminuye en 10%, cómo cambia equity IRR si DSRA target es 50% versus 150%, generar tornado chart mostrando sensibilidades  
* Método compare\_waterfall\_scenarios que ejecute waterfall bajo diferentes supuestos y compare resultados lado a lado: escenario base, escenario con grace period más largo, escenario sin MRA, escenario con DSCR covenant más estricto  
* Implementar visualización integrada: dashboard con múltiples paneles mostrando (1) CFADS en el tiempo, (2) waterfall de un período representativo, (3) evolución de reservas, (4) distribuciones acumuladas por categoría, (5) saldos de deuda amortizándose  
* Generar reporte ejecutivo de waterfall: resumen de una página con métricas clave (equity IRR, DSCR mínimo observado, períodos con default, total distribuido a equity, WACD efectivo), gráfico principal mostrando flujo de fondos agregado, tabla con escenarios comparativos  
* Documentar mecánica completa: incluir diagrama de flujo del waterfall, tabla explicativa de cada paso de prelación, glosario de términos técnicos (DSRA, MRA, cash sweep, PIK), referencias a estándares de Project Finance

### **T-020: Gobernanza digital**

**¿En qué consiste?**  
 Diseñar el framework conceptual de cómo funcionaría la gobernanza on-chain de una estructura de deuda tokenizada, incluyendo voting mechanisms, quorum requirements y enforcement automático mediante smart contracts.

**Relaciones con otras tareas:**

* **Depende de:** T-017 (waterfall implementado que sería automatizado)  
* **Complementa:** T-016 (comparación incluye diferencias en gobernanza)  
* **Informa:** T-053 (diseño AMM necesita considerar gobernanza)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Documento de diseño de gobernanza digital especificando roles y responsabilidades: token holders tienen derechos de voto proporcionales a holdings, servicer ejecuta operaciones rutinarias del waterfall, trustee o agente verifica compliance con covenants, oracle provider suministra datos externos como tasas de interés  
* Diseñar mecanismo de votación on-chain: cada token representa un voto, propuestas requieren mínimo de tokens para ser sometidas (ej. 5% del total), votación abierta durante período definido (ej. 7 días), aprobación requiere quorum mínimo (ej. 30% de participación) y mayoría calificada (ej. 66% a favor)  
* Definir tipos de decisiones que requieren votación: cambios a waterfall parameters como ajustar target de DSRA, modificación de covenants como relajar DSCR mínimo, aprobación de CAPEX extraordinario, restructura de deuda en caso de distress, reemplazo de servicer o auditores  
* Implementar jerarquía de mayorías requeridas: decisiones rutinarias (cambio de servicer) \= mayoría simple 50%, decisiones importantes (ajuste de covenants) \= mayoría calificada 66%, decisiones críticas (restructura de deuda) \= súper mayoría 75%, cambios fundamentales (modificación de prelación) \= unanimidad 100%  
* Diseñar enforcement automático mediante smart contracts: covenant breaches detectados automáticamente por smart contract monitoreando DSCR calculado por oracle, activación automática de cash sweep cuando DSCR \< threshold sin necesidad de votación, bloqueo automático de distribuciones a equity cuando reservas por debajo de target  
* Implementar sistema de oráculos para datos off-chain: oracle suministra CFADS realizado cada período desde sistema contable del proyecto, oracle suministra tasas de interés de referencia para floating rate tranches, múltiples oracles con mecanismo de mediación para evitar manipulación, penalizaciones para oracles que reportan datos incorrectos  
* Diseñar representación de seniority on-chain: diferentes clases de tokens representan diferentes tranches (SeniorToken, MezzToken, SubToken), smart contract enforza prelación en waterfall automáticamente transfiriendo primero a holders de SeniorToken, holders de tranches subordinados solo reciben distribución después que senior está completo  
* Implementar programabilidad de distribuciones: holders pueden configurar si reinvertir automáticamente distribuciones en más tokens, si transferir a wallet externa, si convertir a stablecoin mediante DEX automático, si usar para pagar fees de protocolo  
* Diseñar mecanismo de resolución de disputes: si hay desacuerdo sobre datos de oracle o ejecución de waterfall, token holders pueden proponer arbitraje on-chain, árbitros independientes (seleccionados mediante votación) revisan evidencia y emiten ruling, ruling ejecutado automáticamente por smart contract con distribución retroactiva si necesario  
* Implementar transparency y auditability: toda la información de CFADS, distribuciones, saldos y eventos está on-chain como eventos emitidos por smart contract, cualquiera puede verificar historial completo y reproducir cálculos, auditoría en tiempo real sin necesidad de disclosure periódico  
* Crear especificación técnica de interfaces de smart contracts: interfaz IERC20 extendida para tokens de deuda con metadatos adicionales (tranche, seniority, maturity), interfaz IWaterfall con métodos executeDistribution y checkCovenants, interfaz IGovernance con métodos propose, vote y execute  
* Documentar limitaciones y trade-offs: gobernanza on-chain es más transparente y automática pero menos flexible que tradicional, cambios requieren mayorías calificadas dificultando restructuras urgentes, dependencia de oracles introduce risk de manipulación o fallo, costos de gas de ejecutar lógica compleja on-chain pueden ser significativos  
* Comparar con gobernanza tradicional: en estructura bancaria agente puede tomar decisiones rápidas en nombre de acreedores mediante waiver, en estructura tokenizada cada cambio requiere proceso de votación que puede tomar semanas, analizar casos donde cada enfoque es superior  
* Diseñar governance minimization: decidir qué debe estar on-chain versus off-chain, cálculos complejos como Monte Carlo se ejecutan off-chain con resultados publicados on-chain mediante oracle, lógica simple como comparar DSCR contra threshold se ejecuta on-chain, balancear descentralización contra costo y complejidad  
* Generar diagrama de arquitectura de gobernanza: mostrar interacción entre smart contracts, oracles, token holders y sistemas externos, flujo de información desde proyecto hasta blockchain, mecanismos de votación y enforcement  
* Incluir referencias a protocolos DeFi existentes: analizar MakerDAO governance para inspiración sobre voting mechanisms, analizar Aave governance sobre propuestas y ejecución, analizar Compound timelock para seguridad de cambios críticos

## **WP-04: PRICING Y CURVAS**

### **T-007: Módulo valuación tramos**

**¿En qué consiste?**  
 Implementar el módulo core de pricing que valúa cada tramo de deuda usando metodología de Discounted Cash Flow (DCF) con factores de descuento derivados de curva spot calibrada.

**Relaciones con otras tareas:**

* **Depende de:** T-006 (waterfall genera flujos por tramo), T-014 (DebtStructure define tranches)  
* **Utilizado por:** T-008 (curva spot para descontar), T-009 (WACD usa prices), T-026 (pricing estocástico extiende)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase PricingEngine que centraliza toda la lógica de valuación de instrumentos de deuda  
* Método price\_tranche que tome un Tranche y WaterfallResult, extraiga flujos específicos que van a ese tranche (intereses \+ principal), descuente cada flujo usando tasa apropiada, sume valores presentes para obtener precio del tranche  
* Implementar extracción de flujos por tranche: dado WaterfallResult que contiene distribuciones totales por período, filtrar solo pagos que corresponden al tranche específico según prelación y seniority, construir serie temporal de cash flows esperados para ese tranche  
* Método calculate\_discount\_factors que tome curva spot como input y compute factores de descuento para cada horizonte temporal: DF(t) \= 1 / (1 \+ r(t))^t donde r(t) es tasa spot para maturity t, manejar convención de conteo de días (Actual/360 versus 30/360), ajustar por frecuencia de cupones  
* Implementar pricing usando ecuación fundamental: PV\_tranche \= Σ\[CF\_t × DF\_t\] sumando sobre todos los flujos esperados del tranche, donde CF\_t incluye cupones de interés y repagos de principal, DF\_t son factores de descuento apropiados  
* Calcular yield to maturity (YTM) del tranche: dado precio de mercado (o calculado mediante DCF), resolver iterativamente para la tasa que hace PV \= precio, usar algoritmo de Newton-Raphson o bisección, validar que converge a solución única  
* Implementar cálculo de spread sobre curva base: dado YTM del tranche y curva risk-free de referencia, calcular spread \= YTM \- curva\_libre\_riesgo(maturity), este spread refleja primas por riesgo de crédito, liquidez y complejidad  
* Método calculate\_tranche\_duration que compute Duración de Macaulay: suma ponderada de tiempos de flujos donde pesos \= PV de cada flujo / PV total, Duration \= Σ\[t × PV\_t / PV\_total\], mide sensibilidad del precio a cambios en tasa de interés  
* Implementar cálculo de Modified Duration: ModDur \= MacDur / (1 \+ y) donde y es yield, mide cambio porcentual en precio por cambio de 1 bp en yield: ΔP/P ≈ \-ModDur × Δy  
* Método calculate\_convexity que compute segunda derivada de precio respecto a yield: Convexity \= Σ\[t × (t+1) × PV\_t / PV\_total\] / (1 \+ y)², captura curvatura de relación precio-yield, mejora aproximación lineal de duration  
* Implementar ajuste de pricing por riesgo de crédito: incorporar PD y LGD de modelo Merton de T-005, calcular Expected Loss \= PD × LGD × Exposure, ajustar precio restando valor presente de pérdidas esperadas  
* Método calculate\_risk\_adjusted\_price: precio\_ajustado \= precio\_libre\_riesgo \- PV(Expected\_Loss), donde PV de pérdidas esperadas se calcula descontando EL en cada horizonte con tasa libre de riesgo  
* Implementar pricing de tranches con prepayment: si waterfall incluye cash sweep que acelera prepago de principal, modelar prepayment risk usando CPR (Conditional Prepayment Rate), ajustar flujos esperados incorporando probabilidad de prepago anticipado  
* Crear estructura PricingResult conteniendo: precio calculado (PV), yield to maturity, spread sobre curva base, duration, convexity, precio ajustado por riesgo, sensibilidades a parámetros clave  
* Método price\_entire\_structure que compute precio de todos los tranches simultáneamente: iterar sobre cada tranche de DebtStructure, calcular precio individual, sumar para obtener valor total de deuda, comparar contra par value para detectar over/under valuation  
* Implementar validación de pricing: verificar que precio está entre 0 y valor nominal ajustado, que yield es positivo, que duration es positivo y menor que maturity, que convexity es positivo  
* Método calculate\_pricing\_sensitivities que compute sensibilidad de precio a cambios en inputs clave: sensibilidad a CFADS (cuánto cambia precio si CFADS aumenta 10%), sensibilidad a tasa de descuento (cuánto cambia si curva sube 100 bps), sensibilidad a PD (cuánto cae si PD se duplica)  
* Generar tabla de pricing: mostrar para cada tranche su precio, YTM, spread, duration y métricas de riesgo en formato profesional con redondeo apropiado  
* Implementar visualización de curva de precio-yield: graficar relación entre precio del tranche y diferentes niveles de yield, mostrar curvatura (convexity) y tangente (duration), marcar punto actual de mercado  
* Documentar metodología de pricing: explicar supuestos (flujos descontados a YTM, ausencia de arbitraje, mercados líquidos), limitaciones (no considera riesgo de liquidez, asume cumplimiento de covenants), referencias a literatura de fixed income como Fabozzi "Bond Markets, Analysis and Strategies"

### **T-008: Curva zero-coupon**

**¿En qué consiste?**  
 Construir curva spot zero-coupon que sirva como referencia para descontar flujos de caja, calibrada a partir de instrumentos de mercado observables y extrapolada para horizontes largos del proyecto.

**Relaciones con otras tareas:**

* **Depende de:** T-007 (pricing necesita curva)  
* **Utilizado por:** T-007 (descuenta flujos), T-027 (duration usa curva), T-028 (calibración de spreads)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase SpotCurve que encapsula curva de tasas spot zero-coupon  
* Método build\_curve\_from\_market\_data que tome como input instrumentos observables de mercado: tasas de depósitos para tenores cortos (1M, 3M, 6M), tasas de swaps de tasa de interés para tenores medios (1Y, 2Y, 3Y, 5Y, 7Y), yields de bonos corporativos para tenores largos (10Y, 15Y), extraer tasas spot implícitas mediante bootstrapping  
* Implementar bootstrapping recursivo: para tenor más corto (ej. 6M), tasa spot \= tasa observada directamente de depósito, para tenores subsiguientes, usar precios de swaps o bonos con cupones para despejar tasa spot que hace precio teórico \= precio observado, resolver iterativamente construyendo curva de corto a largo  
* Implementar interpolación para tenores no observados: si tenemos tasas spot para 1Y y 2Y pero necesitamos 1.5Y, usar interpolación spline cúbica que garantiza suavidad de curva, verificar que curva interpolada no tiene arbitrajes (forward rates positivos)  
* Método get\_spot\_rate que retorne tasa spot para cualquier tenor solicitado: si tenor está en nodos de curva retornar directamente, si no interpolar usando spline, extraer hacia horizontes más largos usando extrapolación plana o con decay exponencial hacia long-term rate  
* Implementar extrapolación para proyectos con tenores \> 10Y: asumir que tasa spot converge a long-term rate estimado como tasa de crecimiento nominal de largo plazo de economía (ej. 4-5%), usar función de transición suave desde último punto observado hasta long-term rate en horizonte de 20-30 años  
* Método get\_forward\_rate que calcule tasa forward implícita entre dos fechas futuras: f(t1, t2) \= \[(1 \+ s(t2))^t2 / (1 \+ s(t1))^t1\]^(1/(t2-t1)) \- 1, donde s(t) son tasas spot, forwards útiles para proyectar tasas de refinanciamiento  
* Implementar ajuste por convexidad en derivación de forwards: ajustar por sesgo de convexidad cuando se usan instrumentos con optionalidad embedded  
* Método shift\_curve que aplique shock paralelo a toda la curva: sumar/restar bps uniformemente a todas las tasas, útil para stress testing sensibilidad de pricing a movimientos de tasas de interés  
* Implementar non-parallel shifts: twist (steepening/flattening donde short end sube menos que long end), butterfly (middle of curve sube más que extremos), simular diferentes scenarios de cambio en shape de curva  
* Método calculate\_discount\_factors que convierta toda la curva spot a factores de descuento: DF(t) \= 1 / (1 \+ s(t))^t para cada nodo de la curva, almacenar como array de numpy para operaciones vectorizadas eficientes  
* Crear estructura CurveResult conteniendo: array de tenores en años, array de tasas spot correspondientes, array de discount factors, método de interpolación usado, fecha de construcción de curva  
* Implementar validación de curva construida: verificar que tasas spot son estrictamente positivas, que curva es monotónicamente creciente o tiene forma razonable, que forward rates implícitos son positivos (no arbitrage condition)  
* Método plot\_curves que genere visualización de curva spot, curva de forwards y factores de descuento en mismo gráfico con múltiples ejes Y, mostrar nodos observados versus interpolados  
* Implementar comparación con curvas de mercado reales: importar curvas oficiales de Tesoro USA o Swaps de Bloomberg, comparar nuestra curva construida contra benchmark, calcular spreads  
* Documentar convenciones de mercado: especificar day count convention usado (Actual/360 para USD swaps, 30/360 para bonos corporativos), especificar business day convention para ajuste de fechas, documentar fuentes de datos de mercado  
* Incluir análisis de sensibilidad: cómo varía pricing de proyecto si curva sube 100 bps paralelo, si hay steepening de 50 bps, generar tornado chart de impactos  
* Referencias académicas: métodos de bootstrapping según literatura de fixed income, papers sobre interpolación de curvas como papers de BIS sobre construcción de curvas centrales

### **T-009: WACD**

**¿En qué consiste?**  
 Calcular el Weighted Average Cost of Debt (WACD) de la estructura completa considerando diferentes tasas y pesos de cada tramo, comparar WACD entre estructura tradicional y tokenizada.

**Relaciones con otras tareas:**

* **Depende de:** T-007 (pricing de tranches con yields), T-014 (DebtStructure con weights)  
* **Utilizado por:** T-016 (comparación de estructuras usa WACD), T-036 (optimización minimiza WACD)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase WACDCalculator que compute costo promedio ponderado de deuda  
* Método calculate\_wacd que tome DebtStructure con múltiples tranches, extraiga peso de cada tramo \= principal\_tramo / principal\_total, extraiga costo de cada tramo \= yield o tasa contractual, compute WACD \= Σ(weight\_i × cost\_i)  
* Implementar cálculo usando yields de mercado: si hay pricing disponible de T-007, usar yield to maturity de cada tranche como costo para reflejar precio de mercado actual, si no hay precio usar tasa contractual nominal  
* Implementar ajuste por fees y costos de transacción: incluir arrangement fees, commitment fees, legal costs amortizados sobre vida de deuda, calcular all-in WACD que refleja costo total efectivo para el proyecto  
* Método calculate\_wacd\_traditional que compute WACD de estructura tradicional bancaria con parámetros típicos: 70% senior secured a 6%, 30% mezz unsecured a 9%, WACD\_trad \= 0.7×6% \+ 0.3×9% \= 6.9%  
* Método calculate\_wacd\_tokenized que compute WACD de estructura tokenizada granular: 50% senior a 5.5%, 30% mezz a 8%, 20% sub a 12%, WACD\_token \= 0.5×5.5% \+ 0.3×8% \+ 0.2×12% \= 7.55%  
* Implementar análisis de diferencial: delta\_WACD \= WACD\_tokenized \- WACD\_traditional, interpretar si tokenización reduce o aumenta costo de capital, explicar drivers de diferencia (más granularidad implica más sub que es más caro, pero senior puede ser más barato por mayor transparencia)  
* Método calculate\_wacd\_after\_tax que ajuste por deductibilidad fiscal de intereses: WACD\_after\_tax \= WACD\_pretax × (1 \- tax\_rate), refleja ahorro fiscal por escudo tributario de deuda  
* Implementar cálculo de WACC (Weighted Average Cost of Capital) completo: incluir no solo deuda sino también costo de equity, WACC \= (E/V)×r\_equity \+ (D/V)×r\_debt×(1-tax) donde E=equity, D=debt, V=valor total, útil para comparar contra retorno del proyecto  
* Método compare\_wacd\_scenarios que compute WACD bajo diferentes supuestos de spreads: escenario optimista con spreads 50 bps menores, escenario pesimista con spreads 100 bps mayores, analizar sensibilidad de conclusión sobre tokenización  
* Crear estructura WACDResult conteniendo: WACD de estructura tradicional, WACD de estructura tokenizada, diferencial absoluto y porcentual, breakdown por tramo mostrando contribución de cada uno, WACD after-tax  
* Implementar análisis de valor creado: calcular NPV del proyecto usando WACC como tasa de descuento, comparar contra inversión inicial, calcular excess return \= IRR \- WACC como medida de creación de valor  
* Método plot\_wacd\_breakdown que genere gráfico de barras apiladas mostrando contribución de cada tramo al WACD total, comparar lado a lado estructura tradicional versus tokenizada  
* Generar tabla de sensibilidad: mostrar cómo varía WACD si spread de cada tramo cambia en ±50 bps, identificar cuál tramo tiene mayor impacto en WACD total (típicamente senior por tener mayor peso)  
* Documentar interpretación de WACD: WACD menor indica estructura de capital más eficiente, pero debe balancearse contra flexibilidad y riesgo, WACD no es único criterio de selección de estructura  
* Incluir benchmarking: comparar WACD calculado contra WACDs típicos de Project Finance en sector telecomunicaciones satelitales (rango 6-9% según grado de inversión del proyecto)  
* Referencias: papers sobre optimal capital structure en Project Finance, análisis de trade-off entre tax shield y costs of financial distress

### **T-018: Pricing multimoneda**

**¿En qué consiste?**  
 Extender el framework de pricing para manejar estructuras de deuda denominadas en múltiples monedas, incorporando riesgo cambiario y curvas de descuento específicas por moneda.

**Relaciones con otras tareas:**

* **Depende de:** T-008 (curva spot base que se extiende para cada moneda)  
* **Extiende:** T-007 (pricing con descuentos multimoneda)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase MultiCurrencyPricer que generaliza pricing para tranches en diferentes monedas  
* Implementar concepto de currency denomination: cada tranche puede estar denominado en USD, EUR, GBP u otra moneda, CFADS del proyecto típicamente en una moneda base (USD para proyecto satelital), requiere conversión de flujos  
* Método build\_currency\_curves que construya curva spot separada para cada moneda relevante: curva USD basada en SOFR swaps, curva EUR basada en EURIBOR swaps, curva GBP basada en SONIA swaps, calibrar cada curva independientemente usando instrumentos de esa moneda  
* Implementar pricing de tranche en moneda extranjera: convertir flujos proyectados de moneda base a moneda de denominación del tranche usando forward FX rates, descontar flujos convertidos usando curva apropiada para esa moneda, obtener precio en moneda del tranche  
* Calcular forward FX rates usando paridad de tasas de interés cubiertas (Covered Interest Rate Parity): F(t) \= S\_0 × (1 \+ r\_domestic)^t / (1 \+ r\_foreign)^t, donde S\_0 es spot FX rate, r son tasas libres de riesgo en cada moneda, F(t) es forward rate para delivery en t  
* Implementar modelo simple de riesgo cambiario: asumir que proyecto genera CFADS en USD pero tranche está denominado en EUR, entonces flujos en USD deben convertirse a EUR, exposición a variaciones en FX spot rate introduce volatilidad adicional al valor del tranche  
* Método calculate\_fx\_adjusted\_yield que compute yield del tranche incorporando costo implícito de FX hedging: si proyecto hace hedge mediante forwards FX, costo de hedge se refleja en diferencial de tasas forward versus spot  
* Implementar análisis de cobertura cambiaria: comparar costo de dejar exposición sin cubrir versus costo de hedge completo mediante forwards FX o cross-currency swaps, calcular breakeven de volatilidad FX donde hedging se vuelve óptimo  
* Método price\_with\_fx\_hedging que compute precio asumiendo que proyecto implementa hedge: flujos en moneda extranjera se fijan mediante forwards, elimina riesgo de FX pero introduce costo del hedge, precio más alto pero menos volátil  
* Método price\_without\_hedging que compute precio asumiendo exposición sin cubrir: flujos en moneda extranjera convertidos usando expectativa de spot FX rate futuro, agregar prima de riesgo de FX a tasa de descuento, precio más bajo pero mayor incertidumbre  
* Implementar cálculo de basis spreads entre monedas: observar spreads de cross-currency basis swaps en mercado, ajustar pricing por desviaciones de paridad de tasas de interés debido a fricciones de mercado, demanda/oferta de funding en diferentes monedas  
* Crear estructura MultiCurrencyPricingResult conteniendo: precio en moneda original del tranche, precio equivalente en USD usando spot FX actual, yield en moneda del tranche, yield equivalente en USD, sensibilidad a movimientos de FX  
* Implementar análisis de optimal currency mix: evaluar si mix de monedas en estructura de deuda puede reducir WACD aprovechando diferenciales de tasas entre países, considerar trade-off entre costo menor y riesgo de FX mayor  
* Método plot\_currency\_risk que genere gráfico mostrando impacto de diferentes escenarios de FX: apreciación/depreciación de 10%, 20%, 30% de moneda extranjera versus USD, cómo varía valor de tranche y distribuciones a equity  
* Documentar limitaciones: modelo asume mercados FX líquidos con acceso a hedging instruments, en práctica hedging de largo plazo (10 años) puede ser costoso o ilíquido, basis spreads pueden ser significativos en momentos de stress  
* Incluir caso de uso: analizar si tranche denominado en EUR para atraer inversores europeos reduce WACD suficiente para justificar asumir riesgo de FX o costo de hedging  
* Referencias: literatura de international finance sobre paridad de tasas de interés, papers sobre basis spreads en cross-currency swaps, análisis de corporate hedging strategies

### **T-019: Ajuste LGD colateral**

**¿En qué consiste?**  
 Refinar el cálculo de Loss Given Default (LGD) considerando el valor de colateral específico del proyecto (satélites, licencias, contratos) y su recuperabilidad en escenarios de default.

**Relaciones con otras tareas:**

* **Depende de:** T-010 (métricas de riesgo base con LGD), T-005 (modelo Merton usa LGD)  
* **Utilizado por:** T-007 (pricing ajusta por expected loss), T-033 (pérdida esperada por tramo)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase CollateralAnalyzer que evalúa valor recuperable de activos en escenario de default  
* Método classify\_collateral que categorice activos del proyecto por recuperabilidad: activos físicos (satélites en órbita, ground stations), activos intangibles (licencias de espectro, contratos con clientes), working capital (cuentas por cobrar, inventario), cash y reservas  
* Implementar valuación de satélites en distress: satélites en órbita operativa tienen valor de reventa limitado pues son assets-in-place específicos, estimar valor de liquidación como porcentaje del costo (típicamente 20-30% dado especificidad), satélites manufacturados pero no lanzados tienen mayor valor de reventa (50-60%)  
* Valuación de licencias de espectro: frecuencias radioeléctricas tienen valor significativo y son transferibles, estimar valor de mercado de licencias basado en transacciones comparables, típicamente 40-60% del costo original dependiendo de remaining life  
* Valuación de contratos con clientes: contratos de largo plazo con dispositivos IoT tienen valor de going concern, estimar como NPV de flujos futuros descontados a tasa apropiada, aplicar haircut por riesgo de churn en transición, típicamente 30-50% del valor teórico  
* Método calculate\_recovery\_value que sume valores de liquidación de todos los activos: Recovery \= Σ(valor\_liquidacion\_i), comparar contra deuda total outstanding en momento de default, calcular recovery rate \= Recovery / Debt\_outstanding  
* Implementar jerarquía de prelación en liquidación: senior secured tiene claim sobre activos específicos pignoreados, senior unsecured comparte pro-rata en assets residuales, mezz subordinado solo recupera después de senior, sub absorbe primeras pérdidas  
* Calcular LGD por tramo considerando prelación: LGD\_senior \= 1 \- (min(Recovery, Debt\_senior) / Debt\_senior), si recovery completa excede deuda senior entonces LGD\_senior \= 0, remainder disponible para tranches subordinados  
* Método simulate\_default\_scenarios que modele diferentes moments de default: default en año 2 cuando proyecto inmaduro y colateral tiene menos valor, default en año 5 cuando proyecto está operando y contratos tienen valor going concern, default en año 8 cerca de maturity  
* Implementar factor de tiempo en valuación de colateral: activos se deprecian con el tiempo reduciendo recovery value, satélites tienen degradación física y tecnológica, licencias pierden valor cerca de expiración, generar curva de recovery value en función de time to default  
* Método calculate\_lgd\_with\_priority que implemente waterfall de liquidación: realizar activos obteniendo cash proceeds, pagar costos de bankruptcy y liquidación (típicamente 5-10% de proceeds), distribuir remainder según absolute priority rule empezando por senior secured  
* Implementar análisis de recovery rate scenarios: optimista con recovery de 70% reflejando going concern sale, base case con recovery de 50% mediante piece-meal liquidation, pesimista con recovery de 30% en fire sale durante market downturn  
* Crear estructura CollateralResult conteniendo: valor total de colateral, breakdown por categoría de activo, recovery rate esperado, LGD por tramo considerando prelación, sensibilidad de LGD a valor de colateral  
* Método plot\_lgd\_waterfall que visualice cómo recovery value se distribuye entre tranches: gráfico de cascada mostrando recovery total en tope, sustracción de costs, distribución a senior hasta satisfacer claim, remainder a mezz, etc.  
* Implementar análisis de covenant de collateral: verificar si valor de colateral se mantiene por encima de threshold mínimo definido en loan agreement, típicamente LTV (Loan to Value) \< 80%, trigger de covenant breach si valor de activos cae por debajo  
* Documentar supuestos: valuación de colateral asume que hay compradores dispuestos en momento de default, en práctica liquidation puede tomar tiempo extendido con costos de carrying, mercados de activos específicos pueden ser ilíquidos  
* Incluir benchmarking: comparar recovery rates calculados contra estadísticas históricas de defaults en Project Finance, según Moody's recovery medio en infraestructura es 60-70% para senior secured, 30-40% para mezz  
* Referencias: literatura sobre bankruptcy y liquidation values, papers sobre asset specificity y recovery rates, guías de Banco Mundial sobre valuation de colateral en Project Finance

## **WP-05: RIESGO CREDITICIO**

### **T-010: Módulo EL/VaR/CVaR**

**¿En qué consiste?**  
 Implementar el módulo central de métricas de riesgo crediticio calculando Expected Loss (EL), Value at Risk (VaR) y Conditional Value at Risk (CVaR) para cada tramo de deuda.

**Relaciones con otras tareas:**

* **Depende de:** T-006 (waterfall con eventos de default), T-005 (Merton para PD/LGD)  
* **Utilizado por:** T-033 (pérdida esperada agregada), T-034 (métricas de cola), T-038 (stress testing)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase RiskMetricsCalculator que centraliza cálculo de todas las métricas de riesgo de crédito  
* Método calculate\_expected\_loss que compute pérdida esperada por tramo: EL\_tramo \= PD × LGD × EAD, donde PD es probabilidad de default de T-005, LGD es loss given default de T-019, EAD (Exposure At Default) es saldo outstanding esperado en momento de default  
* Implementar cálculo de EAD term structure: EAD varía en el tiempo conforme deuda se amortiza, construir curva de EAD\_t \= saldo\_outstanding\_t para cada período futuro, calcular EL\_t \= PD\_t × LGD\_t × EAD\_t para cada horizonte, sumar ELs descontados para obtener pérdida esperada total  
* Método calculate\_var que compute Value at Risk al nivel de confianza especificado: ordenar distribución de pérdidas de menor a mayor (del Monte Carlo o modelo Merton), encontrar percentil correspondiente a nivel de confianza, VaR(α) \= pérdida en percentil (1-α), ej. VaR(95%) es pérdida que se excede solo en 5% peor de escenarios  
* Implementar VaR para diferentes horizontes temporales: VaR a 1 año típico para gestión de riesgo anual, VaR a maturity para evaluar riesgo acumulado durante vida completa del proyecto, escalar VaR usando regla de raíz cuadrada del tiempo si se asume i.i.d.  
* Método calculate\_cvar que compute Conditional Value at Risk (Expected Shortfall): CVaR(α) \= E\[Pérdida | Pérdida \> VaR(α)\], promedio de pérdidas en el α% peor de escenarios, más conservador que VaR pues captura severidad de tail events  
* Implementar diferencia entre VaR y CVaR: VaR solo indica threshold de pérdida máxima al nivel de confianza pero no informa magnitud de pérdidas peores, CVaR captura tail risk completo, útil para escenarios de crisis donde pérdidas extremas importan  
* Método calculate\_marginal\_risk que compute contribución de cada tramo al riesgo total de portafolio: marginal EL de tramo i \= ∂EL\_total/∂weight\_i, identifica qué tranches aportan más riesgo y podrían reducirse para mejorar perfil  
* Implementar cálculo de component VaR: descomponer VaR total en contribuciones de cada tramo considerando correlaciones, suma de component VaRs \= VaR total por propiedades de coherencia de CVaR  
* Método calculate\_diversification\_benefit que cuantifique beneficio de diversificación en estructura con múltiples tranches: compare riesgo de portafolio agregado versus suma de riesgos standalone de cada tramo, benefit \= Σ(Risk\_i) \- Risk\_portfolio, positivo si hay correlación imperfecta  
* Crear estructura RiskMetricsResult conteniendo: EL por tramo y total, VaR al 95% y 99%, CVaR al 95% y 99%, component risk por tramo, diversification benefit  
* Implementar stress testing de métricas de riesgo: cómo varía EL si PD se duplica, cómo varía VaR si volatilidad aumenta 50%, generar tornado chart mostrando sensibilidades de métricas de riesgo a inputs clave  
* Método calculate\_risk\_adjusted\_returns que compute retornos ajustados por riesgo: RAROC (Risk Adjusted Return on Capital) \= (Expected Return \- EL) / Economic Capital, donde Economic Capital \= VaR o CVaR al nivel de confianza deseado  
* Implementar cálculo de capital económico regulatorio: estimar capital que institución financiera debería reservar para cubrir pérdidas inesperadas según Basilea III, Regulatory Capital \= K × EAD donde K es factor derivado de PD y LGD usando IRB approach  
* Método plot\_loss\_distribution que grafique distribución completa de pérdidas: histograma de pérdidas simuladas, marcar EL con línea vertical, marcar VaR y CVaR con líneas de diferente color, sombrear tail region más allá de VaR  
* Generar reporte de riesgo por tramo: tabla con métricas key de cada tranche (EL, VaR, CVaR, RAROC), ranking de tranches por riskiness, identificar red flags donde métricas exceden thresholds  
* Documentar interpretación de métricas: EL es costo esperado del riesgo que debe incorporarse en pricing, VaR/CVaR son medidas de worst-case útiles para stress testing y capital allocation, CVaR preferido por reguladores por ser coherent risk measure  
* Incluir benchmarking: comparar métricas calculadas contra estándares de industria, según estudios de Project Finance EL típico para senior es 0.5-1%, para mezz 2-3%, para sub 5-7%  
* Referencias: papers sobre credit risk modeling de Altman, Saunders et al, documentos de Basilea III sobre regulatory capital, literatura sobre coherent risk measures de Artzner et al

### **T-033: Cálculo pérdida esperada**

**¿En qué consiste?**  
 Calcular la pérdida esperada agregada del portafolio de deuda considerando la estructura completa de tranches y sus interdependencias, útil para análisis de diversificación y allocation de capital.

**Relaciones con otras tareas:**

* **Depende de:** T-030 (probabilidades de breach de Monte Carlo), T-010 (EL por tramo base)  
* **Utilizado por:** T-034 (métricas de cola), T-041 (resultados de stress con pérdidas)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase AggregateRiskCalculator que compute riesgo crediticio a nivel de portafolio completo  
* Método calculate\_portfolio\_el que agregue pérdidas esperadas de todos los tranches: EL\_portfolio \= Σ(EL\_i) donde i indexa tranches, pero considerando interdependencias pues default de proyecto afecta a todos los tranches simultáneamente  
* Implementar modelo de default conjunto: reconocer que si proyecto entra en default todos los tranches se ven impactados aunque con diferentes LGDs según prelación, modelar default como evento común que activa pérdidas correlacionadas  
* Método calculate\_joint\_pd que estime probabilidad de que múltiples tranches experimenten pérdidas simultáneamente: usar copulas para modelar dependencia entre eventos de default, si default del proyecto es único evento entonces PD\_joint \= PD\_proyecto para todos los tranches  
* Implementar waterfall de pérdidas en escenario de default: dado recovery value de T-019, distribuir pérdidas empezando por tranche más subordinado: sub absorbe primeras pérdidas hasta su nominal, excess loss va a mezz, solo si pérdidas exceden mezz+sub entonces impacta senior  
* Método calculate\_loss\_allocation que determine cuánto pierde cada tranche en escenario de default: Loss\_sub \= min(Total\_Loss, Principal\_sub), Loss\_mezz \= min(max(0, Total\_Loss \- Principal\_sub), Principal\_mezz), Loss\_senior \= max(0, Total\_Loss \- Principal\_sub \- Principal\_mezz)  
* Crear distribución empírica de pérdidas por tramo usando simulaciones Monte Carlo: para cada trayectoria de MC, determinar si hay default, calcular pérdida total en ese escenario, aplicar waterfall de pérdidas, obtener pérdida específica por tramo, repetir para todas las trayectorias  
* Método calculate\_correlation\_of\_losses que estime correlación entre pérdidas de diferentes tranches: en práctica senior y sub tienen correlación alta pues ambos dependen de default del proyecto, calcular matriz de correlación entre pérdidas de tranches  
* Implementar análisis de tranching efficiency: evaluar si estructura de tranches efectivamente diversifica riesgo entre inversores con diferentes apetitos, calcular ratio de pérdida esperada senior/total versus ratio de principal senior/total, si ratio de pérdida es menor entonces tranching es efectivo  
* Método calculate\_diversification\_effect que cuantifique beneficio de tener múltiples tranches: compare EL de portafolio agregado versus EL de estructura sin tranching (toda deuda es pari passu), positivo si tranching reduce EL total mediante mejor risk allocation  
* Crear estructura AggregateRiskResult conteniendo: EL total del portafolio, breakdown de EL por tramo, correlación de pérdidas entre tranches, métricas de efficiency del tranching  
* Implementar análisis de seniority impact: cómo cambia EL de senior si se aumenta proportion de sub que actúa como cushion, encontrar optimal tranching que minimiza EL de senior subject a constraint de WACD total  
* Método plot\_loss\_waterfall que visualice distribución de pérdidas por tranche en escenario de default: stacked bar chart mostrando principal de cada tramo, overlay de pérdidas esperadas, highlighting que sub absorbe mayoría de EL  
* Generar tabla de contribución al riesgo: mostrar para cada tranche su contribution a portfolio EL como porcentaje, identificar si hay concentración de riesgo en algún tramo o si está bien diversificado  
* Documentar implicaciones para pricing: tranches con mayor EL deben tener spreads mayores para compensar risk, verificar que spreads calibrados son consistentes con ELs calculados, señalar incoherencias  
* Incluir análisis de capital allocation: cómo debería banco o inversor institucional allocar capital económico entre tranches, usar component risk de T-010 para determinar allocation proporcional  
* Referencias: literatura sobre structured finance y tranching como papers de Gorton & Pennacchi sobre asset securitization, análisis de CDOs (Collateralized Debt Obligations) que usan tranching similar

### **T-034: Métricas de cola VaR/CVaR**

**¿En qué consiste?**  
 Refinar el cálculo de métricas de riesgo de cola (VaR y CVaR) usando distribución empírica de Monte Carlo, evaluar tail risk para diferentes niveles de confianza y horizones temporales.

**Relaciones con otras tareas:**

* **Depende de:** T-033 (pérdidas agregadas), T-021 (Monte Carlo genera distribución)  
* **Utilizado por:** T-035 (frontera eficiente), T-041 (resultados de stress)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase TailRiskAnalyzer que especializa en análisis de riesgo de cola extrema  
* Método calculate\_empirical\_var usando distribución completa de Monte Carlo: ordenar pérdidas de N trayectorias, encontrar índice correspondiente a percentil (1-α), VaR\_empírico(α) \= pérdida en ese índice, ej. para α=95% y N=10,000 usar pérdida ranked 9,500  
* Implementar cálculo de VaR para múltiples niveles de confianza: calcular VaR(90%), VaR(95%), VaR(99%), VaR(99.9%) para capturar tail risk creciente, mostrar cómo pérdida máxima aumenta con nivel de confianza  
* Método calculate\_empirical\_cvar usando tails empíricos: seleccionar todas las trayectorias donde pérdida \> VaR(α), promediar esas pérdidas para obtener CVaR(α), CVaR siempre ≥ VaR por construcción  
* Implementar cálculo de Expected Shortfall completo: ES(α) \= CVaR(α) × α \+ VaR(α) × (1-α), representa pérdida esperada total considerando toda la distribución ponderada por probabilidad  
* Método calculate\_tail\_risk\_by\_horizon que compute VaR y CVaR para diferentes horizontes: VaR(1Y), VaR(3Y), VaR(5Y), VaR(maturity), mostrar cómo tail risk se acumula con tiempo, longer horizons tienen mayor VaR por cumulative probability de default  
* Implementar análisis de tail dependence: evaluar si pérdidas extremas de diferentes tranches están correlacionadas, calcular coeficiente de tail dependence entre senior y sub, alto tail dependence indica que en crisis todos sufren simultáneamente  
* Método fit\_extreme\_value\_distribution a cola de distribución empírica: usar Generalized Pareto Distribution (GPD) o Generalized Extreme Value (GEV) para modelar tail behavior más allá de datos observados, extrapolar VaR para niveles de confianza muy altos como 99.99%  
* Implementar estimación de parámetros EVD mediante Maximum Likelihood: ajustar shape parameter ξ y scale parameter σ de GPD a excesos sobre threshold, usar para estimar VaR de eventos súper raros  
* Método calculate\_var\_backtesting que evalúe calidad de estimaciones de VaR: si VaR(95%) es correcto entonces violaciones (pérdidas \> VaR) deben ocurrir en \~5% de casos, test de Kupiec para verificar cobertura, test de Christoffersen para verificar independencia de violaciones  
* Crear estructura TailRiskResult conteniendo: VaR y CVaR para múltiples niveles de confianza, tail dependence entre tranches, parámetros de EVD ajustados, resultados de backtesting  
* Implementar stress testing de tail risk: cómo varía VaR si volatilidad de inputs aumenta 50%, cómo varía si hay más fat tails en distribución (mayor kurtosis), sensitivity analysis de métricas de cola  
* Método plot\_tail\_comparison que visualice tails de distribuciones de pérdidas para diferentes tranches: overlay de histogramas en región de cola, mostrar que sub tiene tail más gordo que mezz que a su vez es más gordo que senior  
* Generar gráfico de Quantile-Quantile (QQ plot) comparando tail empírico versus distribución normal: verificar si tail es fat tailed (desviación positiva de normal en extremos), justificar uso de EVD si hay evidencia de fat tails  
* Documentar diferencias entre VaR y CVaR: VaR puede ser non-coherent risk measure (no es subadditive), CVaR es coherent y preferido por Basel III, explicar por qué CVaR es más apropiado para portfolios  
* Implementar análisis de tail scenarios: identificar qué combinación de shocks produce pérdidas en el tail, ej. pérdidas extremas resultan de simultánea caída de demanda \+ incremento de OPEX \+ fallas técnicas, útil para diseñar stress scenarios de T-038  
* Incluir benchmarking de tail risk: comparar VaR/CVaR calculados contra niveles típicos en Project Finance, según estándares internos de bancos target es CVaR(99%) \< 20% de exposición  
* Referencias: literatura sobre extreme value theory de Embrechts et al "Modelling Extremal Events", papers sobre coherent risk measures, documentos de Basel III sobre market risk capital y use of Expected Shortfall

### **T-035: Frontera eficiente**

**¿En qué consiste?**  
 Analizar trade-off riesgo-retorno de diferentes configuraciones de estructura de deuda construyendo frontera eficiente en espacio (riesgo, rendimiento).

**Relaciones con otras tareas:**

* **Depende de:** T-034 (métricas de riesgo completadas), T-028 (spreads calibrados)  
* **Relacionado con:** T-036 (optimización que busca punto óptimo)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase EfficientFrontierAnalysis en archivo pftoken/analysis/efficient\_frontier.py  
* Método generate\_portfolio\_configurations que genere conjunto de estructuras de deuda con diferentes mezclas de tranches: variar peso\_senior de 40% a 80% en incrementos de 5%, variar peso\_mezz y peso\_sub proporcionalmente manteniendo suma \= 100%, generar grid de \~50-100 configuraciones posibles  
* Para cada configuración calcular: expected\_return \= WACD (costo para equity holders es retorno para debtholders), risk \= CVaR\_95 del portfolio como medida de downside risk, alternativamente usar volatilidad de CFADS o EL como medida de riesgo  
* Método calculate\_sharpe\_ratio que compute (Return \- Rf) / Risk para cada configuración: configuraciones con Sharpe ratio alto son superiores, identificar configuración con máximo Sharpe ratio \= tangency portfolio  
* Método plot\_efficient\_frontier que grafique en espacio (Risk, Return): eje X \= CVaR o volatilidad, eje Y \= WACD, plotear cada configuración como punto, conectar puntos en boundary superior formando frontera eficiente, configuraciones por debajo de frontera son dominadas  
* Identificar configuraciones notables: minimum variance portfolio (menor riesgo), maximum Sharpe portfolio (mejor risk-adjusted return), current structure (baseline para comparación)  
* Implementar análisis de dominancia: estructura A domina B si tiene menor riesgo y mayor return, marcar puntos dominados en gris, resaltar frontera eficiente en color  
* Método find\_optimal\_allocation que dado preferencia de risk aversion del inversor, encuentre punto óptimo en frontera: maximizar Utility \= Return \- λ × Risk donde λ es coeficiente de risk aversion, λ alto implica preferencia por bajo riesgo, λ bajo implica agresividad  
* Implementar análisis de corner portfolios: identificar puntos donde composición de frontera cambia cualitativamente, útil para entender transition de strategies conservativas a agresivas  
* Método compare\_structures\_on\_frontier que plotee estructura Traditional y Tokenized en mismo gráfico de frontera: evaluar si tokenización mueve estructura hacia frontera o mejora su posición, cuantificar improvement en Sharpe ratio o reduction en CVaR para mismo return  
* Implementar constraints en optimización: peso mínimo de senior \= 40% por requerimientos de lenders, peso máximo de sub \= 25% por appetite de market, WACD máximo aceptable \= 10% por viabilidad de proyecto, incorporar constraints en búsqueda de frontera  
* Crear sensitivity analysis: cómo se mueve frontera si aumenta volatilidad de CFADS, si cambian correlaciones entre tranches, si se modifican recovery rates, mostrar robustez de recomendaciones  
* Documentar interpretación: explicar que puntos en frontera son Pareto-efficient (no se puede mejorar return sin aumentar risk), decisión final depende de risk appetite del equity sponsor, presentar range de opciones viables  
* Visualización interactiva: si es posible, crear plot interactivo donde al hacer hover sobre punto muestre composición exacta de tranches y métricas de riesgo/retorno

---

### **T-037: Índice Herfindahl**

**¿En qué consiste?**  
 Calcular el Índice de Herfindahl-Hirschman (HHI) de concentración de riesgo entre tranches para evaluar si estructura diversifica riesgo efectivamente o lo concentra.

**Relaciones con otras tareas:**

* **Depende de:** T-034 (distribución de riesgo por tramo conocida)  
* **Utilizado en:** T-016 (comparación de estructuras), T-048 (análisis final)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase RiskConcentrationAnalysis en archivo pftoken/analysis/concentration.py  
* Método calculate\_herfindahl\_index que compute HHI de concentración de riesgo: HHI \= Σ\[w\_i²\] donde w\_i es fracción del riesgo total asumida por tranche i, calcular w\_i \= EL\_i / EL\_total usando Expected Loss como medida de riesgo  
* Interpretar HHI: valor entre 0 y 1, HHI cercano a 1 indica alta concentración (un tranche asume casi todo el riesgo), HHI cercano a 1/N indica diversificación perfecta entre N tranches, típicamente HHI \= 0.4-0.6 es realista en structured finance  
* Ejemplo: si EL\_senior \= $3M, EL\_mezz \= $5M, EL\_sub \= $2M entonces w\_senior \= 3/10, w\_mezz \= 5/10, w\_sub \= 2/10, HHI \= (0.3)² \+ (0.5)² \+ (0.2)² \= 0.09 \+ 0.25 \+ 0.04 \= 0.38  
* Método calculate\_participation\_by\_tranche que compute porcentaje de riesgo total por tranche: tabla mostrando para cada tranche su share of total risk, útil para identificar tranches que concentran riesgo  
* Implementar comparación de HHI entre estructuras: HHI\_traditional típicamente más alto (2 tranches \= senior/mezz concentran riesgo), HHI\_tokenized más bajo (3 tranches \= senior/mezz/sub diversifican), cuantificar reduction en HHI como beneficio de tokenización  
* Método calculate\_equivalent\_n que compute número equivalente de tranches homogéneos: N\_equiv \= 1 / HHI, si HHI \= 0.38 entonces N\_equiv \= 2.6 significa que nivel de diversificación equivale a 2.6 tranches idénticos, útil para interpretación intuitiva  
* Implementar análisis dinámico de HHI: calcular HHI en cada período del proyecto, típicamente HHI decrease durante ramping a medida que proyecto se estabiliza, puede increase cerca de maturity cuando senior ya amortizó y solo quedan tranches junior  
* Método decompose\_concentration\_sources que identifique por qué hay concentración: es por diferencia en tamaños de tranches o por diferencia en riesgo per dollar, separar efecto de allocation (pesos) vs efecto de risk intensity (pérdidas por peso)  
* Implementar threshold analysis: si HHI \> 0.6 emitir warning de excessive concentration, si HHI \> 0.8 emitir alert de dangerous concentration, recomendar restructuring para reducir concentración  
* Crear visualización de concentración: pie chart mostrando share de cada tranche en riesgo total, bar chart comparando HHI\_traditional vs HHI\_tokenized, time series de evolución de HHI durante vida de proyecto  
* Implementar análisis de contagion risk: alta concentración implica que default de un tranche grande puede desestabilizar estructura completa, baja concentración distribuye pérdidas, cuantificar systemic risk usando network analysis  
* Método calculate\_systemic\_importance que identifique tranches que son systemically important: tranche es systemic si su default causa cascade defaults en otros tranches, medir mediante correlation de defaults y share of total debt  
* Documentar interpretación de HHI: explicar que bajo HHI es deseable desde perspectiva de diversificación pero puede complicar governance, relacionar con literatura de systemic risk en structured finance  
* Referencias: usar literatura de securitization donde HHI es métrica estándar de calidad de tranching, comparar con HHI observados en CDOs, CLOs, MBS

---

## **WP-06: STRESS TESTING (AMPLIADO)**

### **T-038: Diseño escenarios estrés**

**¿En qué consiste?**  
 Diseñar conjunto comprehensivo de escenarios de estrés que representen eventos adversos plausibles para el proyecto de constelación LEO IoT, que serán usados para stress testing.

**Relaciones con otras tareas:**

* **Depende de:** T-002 (requerimientos definen riesgos clave)  
* **Utilizado por:** T-040 (motor de estrés ejecuta estos escenarios), T-041 (resultados de estrés)  
* **Se extiende con:** T-038B (escenario S6 CAPEX Failure), T-039 (escenarios combinados)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase StressScenarioLibrary en archivo pftoken/stress/scenarios.py que centraliza definición de escenarios  
* Clase base StressScenario con atributos: name (identificador único), description (narrativa del escenario), shock\_parameters (dict con ajustes a parámetros), severity (mild/moderate/severe), probability (likelihood estimado), rationale (justificación académica)  
* **Escenario S1 \- Demand Shock:** contracción severa en demanda de IoT por recesión económica global, shocks: revenue\_growth \= \-20% respecto a base, churn\_rate \= \+50% (más clientes cancelan servicio), ARPU \= \-15% por presión competitiva, duración \= 2 años antes de recovery gradual, rationale: crisis como COVID-19 redujo inversión corporativa en IoT  
* **Escenario S2 \- Interest Rate Shock:** aumento abrupto de tasas de interés por política monetaria restrictiva de Fed, shocks: base\_rate \= \+200bps (de 5% a 7%), spread\_mezz \= \+100bps adicionales, spread\_sub \= \+150bps adicionales por flight to quality, aplicar instantáneamente en año 2, duración permanente (tasas no revierten), rationale: ciclo de normalización post-QE puede elevar tasas estructuralmente  
* **Escenario S3 \- Launch Failure:** falla catastrófica en lanzamiento destruyendo fracción de satélites, shocks: capacidad\_inicial \= \-15% (pérdida de satélites), CAPEX\_recovery \= \+$10M para lanzamiento de reemplazo, delay \= 12 meses en inicio de operaciones comerciales, ingresos \= 0 durante delay, rationale: histórico de fallas de lanzamiento en 3-5% de misiones  
* **Escenario S4 \- Operational Degradation:** degradación acelerada de satélites reduciendo vida útil, shocks: lifetime \= \-2 años (de 7 a 5 años), RCAPEX adelantado \= comenzar reemplazo en año 4 en lugar de año 6, OPEX \= \+20% por mantenimiento correctivo incrementado, rationale: ambiente espacial más hostil que esperado (radiación, debris)  
* **Escenario S5 \- Regulatory Change:** cambio regulatorio aumentando costos de compliance, shocks: regulatory\_fees \= \+$3M anuales por nuevas licencias, insurance\_rate \= \+50% por nuevos requerimientos, delay\_approval \= 6 meses en obtener permisos para expansión, rationale: tendencia hacia mayor regulación de megaconstelaciones por Space Sustainability  
* Método define\_shock\_profile que especifique timing y magnitude de shocks: algunos shocks son instantáneos (interest rate jump), otros son graduales (demand decline over 2 years), algunos son permanentes (new baseline), otros son transitorios (recovery after shock)  
* Implementar mecanismo de recovery paths: después de shock, parámetros pueden revertir parcialmente a baseline (V-shaped recovery), permanecer en nivel deprimido (L-shaped), o tener bounce-back seguido de nueva normalidad (U-shaped)  
* Método combine\_scenarios que permita combinar múltiples shocks simultáneos para escenarios más severos: S1+S2 \= demanda cae Y tasas suben simultáneamente (double whammy), calibrar correlación entre eventos (demand shocks y rate hikes a menudo ocurren juntos en crisis)  
* Crear library de escenarios parametrizados: poder generar variantes como S1\_mild (-10% demand), S1\_moderate (-20% demand), S1\_severe (-30% demand) para análisis de sensibilidad  
* Documentar precedentes históricos: para cada escenario citar eventos reales del pasado donde ocurrieron shocks similares, ej: crisis satelital de Iridium en 2000, crisis financiera 2008 para rate shock, SpaceX failures para launch risks  
* Implementar stress test de inverso: reverse stress testing identifica qué combinación de shocks causaría default inevitable, útil para identificar vulnerabilidades extremas  
* Calibrar probabilidades subjetivas: asignar probabilidad anual a cada escenario basado en análisis histórico y juicio experto, ej: launch failure \= 5% anual, severe demand shock \= 10% en 5 años, rate shock 200bps \= 20% en 10 años

---

### **T-038B: Escenario S6 CAPEX Failure**

**¿En qué consiste?**  
 Agregar escenario de estrés específico modelando falla crítica de CAPEX donde MRA es insuficiente para cubrir RCAPEX necesario, forzando refinanciamiento de emergencia o degradación acelerada.

**Relaciones con otras tareas:**

* **Depende de:** T-040 (motor de estrés debe estar funcional)  
* **Extiende:** T-038 (librería de escenarios)  
* **Duración:** 2 días según Gantt (tarea NUEVA en versión actualizada)

**Qué se debe implementar:**

* Crear StressScenario S6\_CAPEX\_Failure con narrativa: "Reemplazo masivo inesperado de satélites por falla sistémica de componente crítico requiere RCAPEX de emergencia que excede MRA disponible"  
* Especificar shocks: RCAPEX\_unexpected \= $25M en año 5 (vs $10M planeado), MRA\_available \= solo $12M acumulado (shortfall de $13M), consecuencias: degradación de servicio si no se reemplaza, potential default técnico si se viola covenants por usar CFADS para CAPEX en lugar de deuda service  
* Implementar lógica de decisión en waterfall: si RCAPEX\_required \> MRA\_available entonces opciones: A) diferir CAPEX y aceptar degradación de servicio reduciendo capacidad y afectando revenues futuro, B) desviar CFADS prioritariamente a CAPEX violando waterfall y causando payment default, C) buscar refinanciamiento de emergencia con términos punitivos  
* Modelar opción A \- diferir CAPEX: si diferimos reemplazo, capacidad operativa decline \= \-10% por año sin satelites reemplazados, revenues afectados proporcionalmente, espiral negativa donde menores revenues hacen más difícil acumular MRA futuro  
* Modelar opción B \- violación de waterfall: desviar CFADS a CAPEX emergency \= immediate default técnico en pagos de deuda, activar cross-default clauses, potencial aceleración de toda la deuda, lenders toman control del proyecto  
* Modelar opción C \- refinanciamiento de emergencia: conseguir bridge loan de $13M con términos caros: rate \= 15% (vs 6-12% de estructura base), upfront fee \= 3%, tenor \= 3 años, agregar este nuevo tramo al waterfall con super-senior priority, incremento permanente de WACD  
* Implementar análisis de trade-offs: comparar NPV de equity bajo cada opción, opción A puede ser mejor si degradación es temporal y recuperable, opción C mejor si permite mantener operación pero erode returns, opción B lleva a liquidation  
* Calcular probability of MRA insufficiency: desde simulaciones Monte Carlo, contar escenarios donde RCAPEX realizado \> MRA acumulado, estimar probabilidad \= \~5-10% en proyectos típicos, cuantificar expected shortfall conditional on insuficiencia  
* Implementar estrategias de mitigación preventivas: aumentar target de MRA de 50% a 75% de RCAPEX esperado, hacer fondeo acelerado de MRA en años buenos, contratar insurance para CAPEX overruns (aunque caro)  
* Crear visualización de trayectorias: plot mostrando evolución de MRA saldo vs RCAPEX requerido en diferentes escenarios, identificar momentos de crisis donde shortfall ocurre, mostrar impact en DSCR  
* Documentar justificación del escenario: citar caso de OneWeb bankruptcy parcialmente atribuido a underestimation de CAPEX requirements, argumentar que es riesgo material en proyectos satelitales con tecnología unproven

---

### **T-039: Escenarios combinados**

**¿En qué consiste?**  
 Diseñar escenarios de estrés combinados donde múltiples shocks ocurren simultáneamente o en secuencia, representando crisis sistémicas más realistas que shocks aislados.

**Relaciones con otras tareas:**

* **Depende de:** T-038 (escenarios individuales definidos)  
* **Utilizado por:** T-040 (motor ejecuta combinaciones), T-042 (reverse stress testing)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Extender StressScenarioLibrary con factory method create\_combined\_scenario  
* **Combo C1 \- Perfect Storm:** combinar S1 Demand \+ S2 Interest Rate \+ S4 Degradation simultáneamente, narrativa: "Crisis económica global deprime demanda de IoT justo cuando Fed sube tasas y problemas técnicos aumentan OPEX", efecto compounding: menores revenues dificultan pagar mayores intereses mientras costos aumentan, triple presión sobre CFADS  
* **Combo C2 \- Launch Failure \+ Refinancing Crisis:** combinar S3 Launch Failure (año 1\) seguido por S2 Rate Shock (año 3), narrativa: "Falla de lanzamiento retrasa proyecto y depleta capital, justo cuando proyecto busca refinanciamiento las tasas han subido dramáticamente", timing adverso maximiza impacto: proyecto debilitado enfrenta mercado hostil  
* **Combo C3 \- Operational Cascade:** combinar S4 Degradation \+ S6 CAPEX Failure \+ S5 Regulatory, narrativa: "Degradación acelerada requiere RCAPEX imprevisto en momento donde nuevas regulaciones aumentan costos, MRA insuficiente", efecto domino: un problema operativo trigger crisis financiera  
* Implementar lógica de correlación temporal: modelar que algunos shocks aumentan probabilidad de otros, ej: demand shock puede llevar a que proyecto corte mantenimiento preventivo causando operational degradation posterior, rate shock puede ocurrir como respuesta a demand shock (Fed tightening)  
* Método sample\_correlated\_shocks que genere pares de shocks con correlación realista: usar copulas para modelar dependencia en tails, demand shocks y rate shocks tienen correlación negativa de \-0.3, operational problems y capex overruns tienen correlación positiva de 0.6  
* Implementar escalamiento temporal de crisis: combo scenario comienza con shock moderate que deteriora métricas, luego second shock hit when project es vulnerable, efecto amplificado vs suma de shocks individuales  
* Método calculate\_compounding\_factor que mida sinergias negativas: si shock A causa pérdida de $5M y shock B causa $7M individualmente, combo A+B puede causar $15M por efectos no-lineales, compounding \= (Loss\_combo \- Loss\_A \- Loss\_B) / (Loss\_A \+ Loss\_B)  
* Crear matriz de interacciones: tabla mostrando para cada par de escenarios cuál es effect size de combinación vs suma de efectos individuales, identificar pares con mayor synergy negativa  
* Implementar historical precedent mapping: identificar crisis reales donde ocurrieron combos similares, ej: Iridium 1999-2000 tuvo tech problems \+ demand underestimation \+ refinancing crisis simultáneamente  
* Método generate\_stress\_narrative que cree storyline convincente explicando cómo se desarrolla crisis combinada: inicio con evento trigger, propagación a través de sistema, puntos de inflexión, posibles recovery paths  
* Calibrar severity levels de combos: C1 Perfect Storm es severity \= extreme (\> 3 sigma event), C2 es severe (2-3 sigma), C3 es moderate (1-2 sigma), asignar probabilidades conjuntas usando joint probability  
* Implementar análisis de vulnerabilidad period-specific: identificar ventanas temporales donde proyecto es más vulnerable a combos, típicamente años 2-4 durante ramping cuando DSCR aún bajo y reservas no completamente fondadas  
* Crear visualización de combo scenarios: timeline diagram mostrando timing de cada shock component, cómo se propagan efectos, peaks de stress en DSCR, momento de potential default  
* Documentar lessons para design de estructura: qué covenants o buffers serían necesarios para sobrevivir combos severos, cómo mejorar resilience mediante diversificación de revenue streams o hedging instruments

---

### **T-040: Motor de estrés**

**¿En qué consiste?**  
 Implementar engine que ejecute escenarios de estrés aplicando shocks a parámetros del modelo, re-ejecutando CFADS \+ Waterfall \+ Pricing, y comparando resultados vs caso base.

**Relaciones con otras tareas:**

* **Crítico: Depende de:** T-031 (pipeline Monte Carlo), T-038 (escenarios definidos)  
* **Genera inputs para:** T-041 (resultados), T-042 (reverse testing), T-043 (stress híbridas)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase StressTestEngine en archivo pftoken/stress/stress\_engine.py  
* Método apply\_stress\_scenario que reciba StressScenario y ProjectParams base, aplique shocks especificados creando ProjectParams\_stressed, shocks pueden ser multiplicative (×1.2), additive (+$5M), o replacement (new value)  
* Implementar lógica de aplicación temporal de shocks: algunos shocks aplican desde cierto período en adelante, otros tienen profile temporal específico, mantener timeline de cuando cada shock se activa y desactiva  
* Método run\_stressed\_simulation que ejecute pipeline completo con parámetros estresados: calcular CFADS\_stressed usando T-003, ejecutar Waterfall\_stressed usando T-006, calcular ratios\_stressed usando T-004, calcular pricing\_stressed usando T-007, recolectar todos los outputs en StressResult object  
* Implementar comparison engine: dado baseline\_result y stressed\_result, calcular deltas y ratios: delta\_CFADS \= CFADS\_stressed \- CFADS\_base, delta\_DSCR, delta\_prices, identify\_breaches (qué covenants se violan bajo stress que no se violan en base)  
* Método calculate\_stress\_metrics que compute indicadores de resilience: time\_to\_default \= número de períodos hasta primer covenant breach bajo stress (infinito si nunca breach), severity\_of\_breach \= máxima magnitud de DSCR undershoot, recovery\_time \= períodos desde shock hasta recuperación de DSCR \> covenant  
* Implementar batch stress testing: ejecutar múltiples escenarios en loop, comparar resultados side-by-side, rank escenarios por severity (cuál causa mayor daño), identify most vulnerable period del proyecto  
* Método generate\_stress\_dashboard que cree tabla comprehensiva: filas \= escenarios, columnas \= métricas clave (min DSCR, EL, default flag, recovery time), formato condicional resaltando failures en rojo  
* Implementar probabilistic stress testing: en lugar de deterministic shock, shock parameters son random variables con distribución, ejecutar Monte Carlo dentro de stress test, obtener distribución de outcomes bajo stress scenario  
* Método calculate\_stress\_var que compute VaR conditional on stress scenario: P(Loss | Stress S1), distribución de pérdidas dado que ocurre S1 es diferente de distribución incondicional, útil para risk planning  
* Crear módulo de stress propagation: rastrear cómo shock inicial se propaga a través del modelo, ej: demand shock → menores revenues → menor CFADS → menor DSCR → breach covenant → trigger reserve funding → menor disponible para dividendos, visualizar cascade of effects  
* Implementar comparative stress testing: ejecutar mismo stress en estructura Traditional vs Tokenized, identificar cuál estructura es más resilient, argumentar sobre design features que mejoran robustness  
* Método simulate\_management\_actions que modele respuestas endógenas al stress: si DSCR \< covenant, management puede cortar OPEX discrecional para preservar solvency, incorporar estas countermeasures en simulación para realismo  
* Implementar break-even analysis: para cada escenario, identificar qué magnitude de shock causaría break-even donde DSCR \= covenant exactly, ej: demand puede caer hasta 18% antes de breach, útil para determinar safety margin  
* Crear visualización de stress waterfall: gráfico comparativo mostrando waterfall normal vs waterfall bajo stress, destacar qué pagos se sacrifican, dónde aparecen shortfalls  
* Documentar metodología de stress testing: citar Basel Committee guidelines sobre stress testing de capital structure, explicar diferencia entre sensitivity analysis (small perturbations) vs stress testing (plausible but extreme shocks)

---

### **T-041: Resultados stress**

**¿En qué consiste?**  
 Compilar, analizar e interpretar resultados de stress testing generando reportes comprehensivos con visualizaciones y conclusiones sobre resilience de cada estructura.

**Relaciones con otras tareas:**

* **Depende de:** T-038B (todos los escenarios ejecutados), T-040 (motor produjo resultados)  
* **Utilizado en:** T-048 (notebook final), T-049 (informe académico)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase StressResultsAnalyzer en archivo pftoken/stress/results\_analyzer.py  
* Método aggregate\_stress\_results que consolide outputs de múltiples escenarios: crear DataFrame comprehensivo con fila por escenario y columnas para cada métrica relevante, incluir baseline\_case como primera fila para comparación  
* Implementar métricas de resiliencia por estructura: count número de escenarios donde estructura sobrevive sin default, average DSCR under stress, worst-case DSCR observed, fraction of scenarios triggering covenant breach, tiempo promedio hasta recovery después de shock  
* Método rank\_scenarios\_by\_severity que ordene escenarios desde más a menos dañinos: usar score compuesto combinando impact en DSCR, EL, default probability, NPV destruction, identificar "killer scenarios" donde proyecto fails irrecuperablemente  
* Implementar análisis de break points: identificar umbrales críticos donde proyecto transition de stressed pero viable a default, ej: proyecto sobrevive demand shock hasta \-25% pero \-30% causa cascade failure  
* Método compare\_structure\_resilience que evalúe Traditional vs Tokenized bajo estrés: count scenarios where Tokenized survives but Traditional fails (or vice versa), compute relative performance \= (DSCR\_tokenized \- DSCR\_traditional) / DSCR\_traditional under each stress, argue cuál estructura es more robust  
* Crear tabla de resiliencia comparativa: filas \= escenarios, columna "Traditional" con DSCR mínimo bajo ese escenario, columna "Tokenized" con DSCR mínimo, columna "Advantage" mostrando cuál es mejor, formato condicional resaltando winner  
* Implementar vulnerability heatmap: matriz con períodos en eje X, escenarios en eje Y, celdas coloreadas por magnitude de DSCR breach, identificar visualmente "danger zones" donde proyecto es vulnerable  
* Método calculate\_expected\_recovery que compute tiempo y costo de recovery post-shock: si covenant breach ocurre, cuántos períodos hasta DSCR vuelve \> threshold, cuánto CFADS acumulado se pierde durante recovery, estimar NPV destruction del shock  
* Crear distribución de time-to-default: histograma mostrando en qué período ocurre primer default bajo cada escenario, moda indica período más vulnerable, útil para timing de hedges o refinanciamiento preventivo  
* Implementar análisis de near-misses: identificar escenarios donde proyecto casi hace default pero sobrevive por narrow margin, ej: DSCR llega a 1.26x (apenas above 1.25 covenant), estos near-misses indican fragilidad  
* Método generate\_executive\_summary que produzca reporte en lenguaje no-técnico: explicar cuáles son mayores amenazas al proyecto, bajo qué circunstancias proyecto podría fallar, qué mitigaciones se recomiendan, presentar en formato de slides  
* Crear visualizaciones comprehensivas: radar chart comparando resilience de structures en múltiples dimensiones (severity of breach, recovery time, default probability, EL increase), tornado chart mostrando sensibilidad de DSCR a diferentes shocks, spaghetti plot de trayectorias de DSCR bajo cada escenario  
* Implementar confidence intervals en resultados: dado que algunos stress tests usan MC interno, reportar no solo mean outcome sino también percentiles 10/90, reconocer incertidumbre incluso dentro de stress scenario  
* Documentar conclusiones académicas: argumentar qué features de estructura contribuyen a resilience (ej: mayor DSRA, menor leverage inicial, diversificación de tranches), relacionar findings con literatura de project finance sobre failure determinants

---

### **T-042: Reverse stress testing**

**¿En qué consiste?**  
 Implementar reverse stress testing que en lugar de partir de escenarios predefinidos, identifica qué combinación de shocks causaría default inevitable del proyecto.

**Relaciones con otras tareas:**

* **Depende de:** T-041 (entender resultados de stress forward)  
* **Complementa:** T-040 (motor de estrés usado en modo inverso)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase ReverseStressTester en archivo pftoken/stress/reverse\_stress.py  
* Método find\_breaking\_point que dado parámetro específico (ej: revenue\_growth), busque valor que causa DSCR \= covenant threshold exactly, usar bisection o Newton method para converger eficientemente, ej: encontrar que revenue\_growth \= \-24.3% causa DSCR \= 1.25 exactly  
* Implementar búsqueda multidimensional: encontrar combinación de (demand\_shock, rate\_shock, opex\_increase) que causa default, problema de optimización: minimize magnitude of shocks subject to DSCR \< 1.25, usar optimizer como scipy.optimize.minimize con constraint  
* Método identify\_minimal\_fatal\_combo que encuentre "smallest" combinación de shocks que mata proyecto: definir size como weighted sum of shock magnitudes normalized, solve para combo que minimiza size while causing default  
* Implementar monte carlo search para breaking points: sample random combinations de shocks, ejecutar stress test para cada combo, identify cuáles causan default, cluster combos letales y buscar patrones  
* Método map\_failure\_surface que discretize espacio de shocks en grid, evaluar outcome en cada punto del grid, crear surface plot mostrando región de parameter space donde proyecto survives vs region donde defaults, boundary es critical frontier  
* Crear visualización 2D de safe/unsafe regions: plot con demand\_shock en X-axis, rate\_shock en Y-axis, región verde donde proyecto viable, región roja donde proyecto fails, boundary curve entre regiones es breaking line  
* Implementar análisis de distance-to-failure: dado parámetros base, calcular minimum distance en parameter space hasta failure boundary, larger distance indica mayor robustness margin, útil para quantificar safety buffer  
* Método simulate\_gradual\_deterioration que modele decline gradual en lugar de shock único: empezar desde base case, incrementar stress magnitude step-by-step, identificar tipping point donde sistema colapsa abruptamente vs deterioro gradual  
* Implementar análisis de puntos de inflexión no-lineales: en algunos casos pequeño shock adicional causa disproportionate damage (threshold effects), identificar estos non-linearities que son peligrosos  
* Método generate\_vulnerability\_map que categorice proyecto en zones: safe zone (múltiples shocks requeridos para default), caution zone (single severe shock puede causar distress), danger zone (sistema es frágil y pequeñas perturbaciones fatal)  
* Crear narrative de cada breaking scenario: explicar storyline plausible que llevaría a esa combinación de shocks, ej: "Trade war reduce demanda global de IoT en 20% mientras simultáneamente Fed sube tasas 250bps para combatir inflación importada", evaluar plausibility vs extremity  
* Implementar probability weighting: asignar probabilidades a diferentes breaking scenarios basado en historical precedent, integrate para calcular probability of project failure \= P(entering failure region), useful para risk reporting  
* Documentar insights estratégicos: identificar cuáles parámetros cuando shocking causan mayor vulnerabilidad (ej: proyecto más sensible a demand que a costs), informar sobre qué variables hedging o covenants deberían focus

---

### **T-043: Stress híbridas**

**¿En qué consiste?**  
 Implementar híbridos entre stress testing determinístico y simulación Monte Carlo estocástica, permitiendo evaluar riesgo bajo condiciones específicas de stress.

**Relaciones con otras tareas:**

* **Depende de:** T-041 (stress results) \+ T-031 (MC pipeline)  
* **Sintetiza:** Stress determinístico \+ MC estocástico  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase HybridStressTester en archivo pftoken/stress/hybrid\_stress.py que combine ambos enfoques  
* Método stress\_conditional\_mc que ejecute Monte Carlo conditional en escenario de stress: fijar algunos parámetros en valores estresados (ej: base\_rate \= 7% instead of 5%), mientras otros parámetros permanecen estocásticos con sus distribuciones (ej: demand growth \~ N(μ, σ)), ejecutar MC completo bajo esta condición  
* Ejemplo: "Dado que tasas suben 200bps (deterministic), cuál es distribución de outcomes considerando incertidumbre normal en demanda y costos (stochastic)", produce distribución de DSCR conditional on rate stress  
* Implementar conditional VaR: calcular VaR\_95 bajo diferentes stress conditions, comparar VaR\_baseline vs VaR\_given\_rate\_shock vs VaR\_given\_demand\_shock, identificar cuál stress amplifica tail risk más  
* Método progressive\_stress\_mc que modele stress escalating over time: empezar con mild stress en año 2, increase severity gradualmente hasta año 5, overlay esto sobre trayectorias estocásticas de MC, capturar interaction entre stress trend y noise estocástico  
* Implementar path-dependent stress: magnitud de stress en período t depende de outcomes en período t-1, ej: si DSCR\_t-1 \< 1.5 entonces demand\_stress\_t incrementa por feedback negativo (clients lose confidence), modelar spirals downward  
* Método adaptive\_stress\_scenario que ajuste severity of stress basado en resilience observed: si proyecto surviving well bajo moderate stress, escalate to severe, continuar hasta encontrar stress level que causa distress, útil para calibrar robustness  
* Crear familia de stress-conditional distributions: para cada escenario S1-S6, generar histograma completo de outcomes considerando variabilidad estocástica además del shock determinístico, comparar dispersión de outcomes bajo cada stress  
* Implementar análisis de probability of default under stress: PD\_unconditional vs PD\_conditional\_on\_S1, quantify cuánto aumenta PD ante cada escenario, useful para stress testing of risk metrics  
* Método combine\_historical\_stress\_with\_stochastic: usar shocks históricos observados (ej: COVID demand drop de 2020\) como central tendency, agregar noise estocástico around eso, produce realistic "could have been worse" scenarios  
* Crear visualización de stress+uncertainty: fan chart mostrando percentiles de outcomes bajo stress scenario, wider fan indica mayor incertidumbre, overlap entre fans de different stresses indica regions donde outcomes are ambiguous  
* Implementar variance decomposition: dado outcome bajo hybrid stress, descomponer variance en component debido a deterministic shock vs component debido a stochastic noise, identificar si stress dominate o noise dominate  
* Documentar casos de uso: hybrid stress útil para stress testing donde queremos evaluar specific risk (deterministic shock) mientras reconociendo que other risks remains uncertain (stochastic), más realista que pure deterministic stress testing

---

## **WP-07: SIMULACIÓN MONTE CARLO**

### **T-021: Motor MC estocástico**

**¿En qué consiste?**  
 Implementar el motor central de simulación Monte Carlo que genera trayectorias estocásticas de parámetros del proyecto, ejecuta CFADS+Waterfall en cada trayectoria, y recolecta distribución completa de outcomes.

**Relaciones con otras tareas:**

* **Crítico: Depende de:** T-004 (ratios), T-005B (Merton validado)  
* **Utilizado por:** T-026 (pricing estocástico), T-033 (pérdida esperada), T-038 (stress testing)  
* **Se extiende con:** T-022 (variables aleatorias), T-023 (correlaciones), T-024 (Merton integrado)  
* **Duración:** 5 días según Gantt (tarea core)

**Qué se debe implementar:**

* Clase MonteCarloEngine en archivo pftoken/simulation/monte\_carlo.py que orquesta simulación completa  
* Método run\_simulation que ejecute N simulaciones configurables: típicamente N \= 10,000 para balance entre precisión y runtime, cada simulación \= un escenario futuro posible  
* Implementar seeding para reproducibilidad: permitir fijar random seed en SimulationParams, mismo seed produce mismos resultados, crítico para debugging y comparaciones  
* Implementar arquitectura vectorizada para performance: usar NumPy broadcasting para generar múltiples trayectorias simultáneamente, evitar loops Python explícitos cuando posible, meta \= ejecutar 10k simulaciones en \< 5 minutos  
* Método generate\_scenario que sample un conjunto de parámetros estocásticos: revenue\_growth\_realizado, OPEX\_realizado, base\_rate\_realizado, etc., usando distribuciones definidas en T-022  
* Para cada scenario generado, ejecutar pipeline completo: calcular CFADS\_scenario usando T-003B, ejecutar Waterfall\_scenario usando T-006, calcular ratios\_scenario usando T-004, detectar defaults si DSCR \< covenant, calcular losses si default ocurre  
* Implementar estructura de datos para almacenar resultados: SimulationResult conteniendo arrays de N elementos: CFADS\_t para cada período t y escenario, DSCR\_t, default\_flags, losses\_senior, losses\_mezz, losses\_sub, prices\_por\_tramo  
* Método aggregate\_results que compute estadísticas sobre distribución: mean, median, std dev, percentiles (5th, 25th, 75th, 95th), histogram bins, todo esto para cada métrica de interés  
* Implementar convergence checking: verificar que estadísticas se estabilizan a medida que N aumenta, plotear mean y variance como función de N, detectar si N es suficiente o se requieren más simulaciones  
* Método calculate\_confidence\_intervals que compute intervals using bootstrap: resample simulaciones con replacement, recalculate statistics en cada bootstrap sample, percentiles de bootstrap distribution dan confidence intervals  
* Implementar parallel execution: si computadora tiene múltiples cores, distribuir simulaciones across cores usando multiprocessing, reducir runtime proporcionalmente a número de cores disponibles  
* Crear progress tracking: mostrar progress bar durante simulación indicando porcentaje completo y ETA, útil para simulaciones largas  
* Implementar checkpointing: guardar resultados parciales cada 1000 simulaciones, permite resumir simulación si es interrumpida, evita perder progreso en caso de crash  
* Método export\_results que exporte resultados completos a CSV y/o HDF5 para análisis posterior, incluir metadata como parámetros usados, timestamp, version del código  
* Implementar validation checks post-simulation: verificar que distribución de outcomes es razonable (no todos los escenarios default, no todos son perfectos), detectar anomalías que podrían indicar bugs  
* Crear visualización de trayectorias: spaghetti plot mostrando CFADS\_t de múltiples scenarios superpuestos, transparencia para ver densidad, resaltar percentiles clave como bandas  
* Documentar design decisions: por qué usar distribuciones particulares, cómo se calibraron parámetros, qué correlaciones se asumieron, limitaciones del modelo

---

### **T-022: Variables aleatorias**

**¿En qué consiste?**  
 Especificar distribuciones estadísticas para cada variable estocástica del modelo y implementar sampling eficiente de estas distribuciones.

**Relaciones con otras tareas:**

* **Depende de:** T-021 (motor MC necesita distributions)  
* **Informado por:** T-047 (calibración de parámetros estocásticos)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase StochasticVariables en archivo pftoken/simulation/distributions.py  
* Para revenue growth: usar distribución lognormal con parámetros μ y σ calibrados en T-047, lognormal asegura growth rate positivo, capture right-skew típico de uncertainty económica  
* Implementar sampling: growth\_rate\_sample \= np.random.lognormal(mean=μ, sigma=σ, size=N) para N simulaciones  
* Para ARPU (Average Revenue Per User): usar normal truncada bounded entre \[ARPU\_min, ARPU\_max\], evita valores negativos o absurdamente altos, reflejar competencia mantiene ARPU en rango  
* Para churn rate: usar beta distribution bounded en \[0,1\] apropiado para rates/probabilities, shape parameters α y β calibrados para match mean y variance observados  
* Para OPEX: modelar como función de CFADS con noise aditivo, OPEX \= α × CFADS \+ N(μ, σ), captura que costos tienden a escalar con actividad pero tienen component fijo  
* Para base interest rate: usar proceso de mean reversion (Ornstein-Uhlenbeck), r\_t \= r\_t-1 \+ κ(θ \- r\_t-1)dt \+ σdW, tasas tienden a revertir hacia long-run mean θ con speed κ  
* Implementar Geometric Brownian Motion para variables de precio: dS/S \= μdt \+ σdW, usado para simular valor de activos en modelo Merton de T-024  
* Para eventos discretos como launch failure: usar Bernoulli distribution con probabilidad p calibrada desde histórico, sample \= np.random.binomial(n=1, p=p\_failure)  
* Implementar mixture distributions para capturar regime changes: en 95% de casos distribution A (normal times), en 5% distribution B (crisis), sample primero el regime y luego condicional en regime sample value  
* Método validate\_distributions que verifique samples generados tienen propiedades correctas: mean empírico ≈ mean teórico, variance empírica ≈ variance teórica, no outliers absurdos  
* Crear visualización de distribuciones: histograma de samples generados vs curva de PDF teórica superpuesta, Q-Q plot para verificar goodness of fit  
* Implementar antithetic variates technique: para reducir variance de estimadores MC, generar pares de samples (X, \-X) simétricos, reduce variance sin aumentar número de simulaciones  
* Documentar elección de distribuciones: justificar por qué lognormal para growth (prevent negative rates), por qué beta para proportions, por qué mean reversion para tasas (reflect monetary policy)

---

### **T-023: Matriz correlación**

**¿En qué consiste?**  
 Especificar matriz de correlación entre variables estocásticas y implementar generación de muestras correlacionadas usando Cholesky decomposition.

**Relaciones con otras tareas:**

* **Depende de:** T-022 (variables aleatorias definidas)  
* **Calibrada en:** T-047 (estimación de correlaciones)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase CorrelationMatrix en archivo pftoken/simulation/correlation.py  
* Definir matriz de correlación ρ de dimensión (n\_vars × n\_vars) donde n\_vars \= número de variables estocásticas  
* Ejemplo de correlaciones importantes: ρ(revenue\_growth, OPEX) \= 0.4 positiva (más actividad → más costos), ρ(revenue\_growth, base\_rate) \= \-0.2 negativa (baja actividad → Fed baja tasas), ρ(OPEX, degradation) \= 0.5 positiva (mayor degradación → mayor mantenimiento)  
* Implementar validación de matriz: verificar que ρ es simétrica (ρ\_ij \= ρ\_ji), diagonal \= 1, eigenvalues todos positivos (positive definite condition), si no es positive definite hacer ajuste para ensure it  
* Método generate\_correlated\_samples usando Cholesky decomposition: descomponer ρ \= L L^T donde L es lower triangular, generar samples independientes Z \~ N(0,1) de dimensión n\_vars, transformar X \= L Z para obtener samples correlacionados con matriz de correlación ρ  
* Implementar para caso multivariado: generar matriz de N×n\_vars donde N \= número de simulaciones, aplicar Cholesky, cada fila es un escenario con variables correlacionadas  
* Método transform\_to\_target\_distributions: samples X están en espacio normal estándar, transformar cada variable a su distribution target usando quantile transformation, ej: para lognormal usar X\_log \= F\_lognormal^(-1)(Φ(X\_normal))  
* Implementar copula approach como alternativa: Gaussian copula separa estructura de correlación (copula) de distribuciones marginales, más flexible que asumir todo es Gaussian  
* Validar samples generados: calcular correlation matrix empírica de samples, comparar con ρ target, verificar que match es close (tolerancia \~0.05)  
* Implementar sensibilidad a correlación: correr simulaciones con diferentes assumptions de ρ, mostrar cómo resultados (VaR, DSCR, etc) cambian con correlación, típicamente higher correlation → higher tail risk  
* Crear visualización de correlaciones: heatmap de matriz ρ con color intensity indicando strength, scatter plots pairwise de variables mostrando correlación visualmente  
* Documentar fuentes de calibración: cómo se estimaron correlaciones, si desde datos históricos o juicio experto, incertidumbre en estimates, impacto de correlation errors en resultados

### **T-024: Merton en MC**

**¿En qué consiste?**  
 Integrar modelo de Merton de T-005 dentro del loop de Monte Carlo para calcular PD y LGD endógenamente en cada trayectoria simulada.

**Relaciones con otras tareas:**

* **Depende de:** T-021 (MC engine), T-005 (modelo Merton)  
* **Genera:** PD dinámica por trayectoria  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Extender MonteCarloEngine para incluir cálculo de Merton en cada scenario  
* En cada iteración de MC: simular trayectoria de valor de activos V(t) usando GBM desde T-022, simular trayectoria de saldo de deuda D(t) que decrece por amortization según waterfall  
* En cada período t de la simulación: calcular distance to default: DD\_t \= \[ln(V\_t / D\_t) \+ (μ \- σ²/2)τ\] / (σ√τ) donde τ es time to maturity desde t  
* Calcular PD\_t \= Φ(-DD\_t) que es probability of default en horizonte τ starting from t  
* Si V\_t \< D\_t en algún momento → immediate default triggered, marcar default\_flag \= True, calcular recovery \= V\_t / D\_t, LGD \= 1 \- recovery  
* Implementar lógica de prelación en recovery: si default ocurre y V\_default disponible, senior recupera primero hasta su claim, mezz recupera de residuo, sub obtiene último, calcular recovery\_senior, recovery\_mezz, recovery\_sub por separado  
* Método calculate\_dynamic\_pd que retorne time series de PD\_t durante trayectoria de simulación: muestra cómo PD evoluciona a medida que V y D cambian, típicamente PD increase cuando leverage aumenta o performance se deteriora  
* Método aggregate\_pd\_across\_simulations que compute PD promedio en cada período agregando sobre N simulaciones: PD\_aggregated\_t \= mean(PD\_scenario\_t) over all scenarios  
* Implementar term structure de PD: extraer PD para diferentes horizontes (1y, 3y, 5y, 10y) desde simulaciones, mostrar que PD increasing con horizon reflejando cumulative risk  
* Calcular EL endógena: EL\_scenario \= PD\_scenario × LGD\_scenario × EAD\_scenario, agregar EL over scenarios para obtener expected loss total  
* Comparar EL endógena de Merton con EL exógena fija de T-005: verificar si modelar PD dinámicamente cambia significativamente resultados vs usar PD constante  
* Crear visualización de trayectorias V vs D: plot mostrando evolución de valor de activos y valor de deuda en múltiples scenarios, resaltar scenarios donde V cruza por debajo de D (default events), mostrar distribución de timing de defaults  
* Implementar feedback loop entre defaults y correlación: si un tranche defaults, puede aumentar correlación de otros tranches por contagion, modelar este systemic effect  
* Documentar ventajas de approach endógeno: captura naturaleza path-dependent del riesgo de crédito, refleja que PD no es estática sino evoluciona con fundamentals del proyecto, más realista que fixed PD approach

### **T-025: Flags de default**

**¿En qué consiste?**  
 Implementar sistema robusto de detección y clasificación de eventos de default durante simulaciones, diferenciando tipos de default y severidad.

**Relaciones con otras tareas:**

* **Depende de:** T-024 (Merton detecta algunos defaults)  
* **Utilizado por:** T-030 (probabilidades de breach), T-033 (cálculo de pérdidas)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase DefaultDetector en archivo pftoken/simulation/default\_detection.py  
* Enum DefaultType definiendo categorías: TECHNICAL\_DEFAULT (breach de covenant sin pérdida económica inmediata), PAYMENT\_DEFAULT (no pago de intereses o principal programado), CROSS\_DEFAULT (default triggered por breach en otra deuda), BANKRUPTCY (insolvencia total con liquidación)  
* Método detect\_default\_events que escanee cada período de simulación verificando múltiples condiciones  
* **Default Tipo 1 \- Covenant Breach:** verificar si DSCR \< covenant\_threshold por X períodos consecutivos (típicamente 2), si detectado marcar technical\_default \= True, severity \= moderate si DSCR entre 1.0-1.25, severity \= severe si DSCR \< 1.0  
* **Default Tipo 2 \- Payment Default:** verificar si en waterfall algún tranche no recibió pago completo de intereses, si senior\_interest\_paid \< senior\_interest\_due entonces payment\_default\_senior \= True con severity \= critical, mezz y sub defaults son menos críticos  
* **Default Tipo 3 \- Insolvency:** verificar condición Merton V \< D indicando activos insuficientes para cubrir deuda, bankruptcy \= True, severity \= terminal, activar proceso de liquidación  
* **Default Tipo 4 \- Reserve Depletion:** si DSRA\_balance \= 0 AND CFADS insuficiente para servicio entonces liquidity\_crisis \= True, puede ser temporary si CFADS recovers pronto  
* Implementar cure periods: algunos defaults pueden ser "curados" si condición se revierte rápidamente, ej: DSCR breach en 1 período seguido por recovery en próximo período \= warning no default, solo marcar default si condition persists  
* Método calculate\_default\_probability que compute frecuencia de cada tipo de default: P(covenant\_breach) \= count(scenarios con breach) / total\_scenarios, P(payment\_default) \= count(scenarios con payment miss) / total, calcular para cada tranche por separado  
* Implementar time-to-default tracking: para scenarios con default, registrar período exacto cuando ocurre primer default, crear distribución de time-to-default útil para pricing y risk management  
* Método classify\_default\_severity usando score: score \= weighted\_sum(DSCR\_breach\_magnitude, payment\_miss\_amount, recovery\_rate\_shortfall), classify como mild/moderate/severe/catastrophic basado en score  
* Crear matriz de co-occurrence: calcular cuán frecuentemente diferentes tipos de default ocurren juntos, ej: payment default de mezz casi siempre accompanied by covenant breach, pero covenant breach no siempre lleva a payment default  
* Implementar contagion detection: marcar scenarios donde default de un tranche trigger cascade de defaults en otros tranches, útil para identificar systemic risk  
* Método generate\_default\_timeline que para cada scenario con default cree narrativa temporal: "Período 18: DSCR breach (1.22x), Período 19: DSCR persists (1.18x) → technical default declared, Período 20: Payment miss en mezz, Período 22: Bankruptcy declared"  
* Crear visualización de default patterns: heatmap mostrando período de default en eje X, tipo de default en eje Y, intensidad de color indica frecuencia, identify vulnerable periods visualmente  
* Implementar recovery tracking post-default: si default no es terminal, rastrear si proyecto logra cure el default y recover, calculate recovery\_rate y recovery\_time statistics  
* Documentar taxonomía de defaults: explicar diferencias entre tipos, severity implications para investors, typical remedies por tipo según Project Finance standards

### **T-029: DSCR/LLCR por trayectoria**

**¿En qué consiste?**  
 Calcular ratios de cobertura de deuda (DSCR, LLCR) para cada trayectoria individual de Monte Carlo, generando distribuciones completas de estos ratios clave.

**Relaciones con otras tareas:**

* **Depende de:** T-021 (MC genera trayectorias), T-004 (cálculo de ratios establecido)  
* **Alimenta:** T-030 (probabilidades de breach), T-034 (métricas de cola)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Extender MonteCarloEngine para calcular ratios en cada scenario  
* Implementar cálculo vectorizado de DSCR: dado arrays de CFADS\[scenario, period\] y DebtService\[scenario, period\], calcular DSCR\[scenario, period\] \= CFADS / DebtService element-wise, manejar división por cero si DebtService \= 0 en grace period  
* Método calculate\_dscr\_distribution que para cada período t agregue sobre scenarios: compute mean\_DSCR\_t, median\_DSCR\_t, std\_DSCR\_t, percentiles (10th, 25th, 75th, 90th, 95th, 99th), histogram de DSCR\_t mostrando shape de distribución  
* Implementar tracking de DSCR mínimo: para cada scenario identificar min\_DSCR \= minimum ratio observado durante toda la vida del proyecto, agregar min\_DSCR across scenarios para obtener distribución de "worst moment" DSCR  
* Método calculate\_llcr\_per\_trajectory que compute LLCR en cada período de cada scenario: requiere calcular NPV de flujos futuros desde t hasta maturity dentro de cada trayectoria, descontar usando tasa apropiada por tranche, dividir por saldo de deuda en t  
* Implementar cálculo eficiente de LLCR: pre-calcular discount factors, usar cumulative sum reversa para compute NPV rápidamente, evitar loops anidados para performance  
* Crear estructura RatioDistributions como dataclass conteniendo: DSCR\_by\_period con estadísticas, LLCR\_by\_period con estadísticas, PLCR\_distribution, min\_DSCR\_distribution, max\_DSCR\_distribution, time\_series\_percentiles  
* Método identify\_breach\_scenarios que filtre scenarios donde DSCR cae por debajo de covenant en algún momento: compute breach\_rate \= count(scenarios con breach) / total\_scenarios, identificar características comunes de breach scenarios (típicamente baja demanda \+ altos costos)  
* Implementar análisis de persistence: dado breach en período t, cuál es probabilidad de breach en t+1, calcular auto-correlation de breach events, mide si breaches son transitorios o persistentes  
* Método calculate\_coverage\_headroom que compute margen de seguridad: headroom\_t \= (DSCR\_t \- covenant\_threshold) / covenant\_threshold, positivo \= OK, negativo \= breach, analizar distribución de headroom en different períodos  
* Crear visualización de fan charts: plot mostrando percentiles de DSCR en el tiempo, líneas para 10th, 25th, 50th, 75th, 90th percentiles creando "fan" que muestra uncertainty increasing con horizonte, línea horizontal en covenant threshold para reference  
* Implementar comparación vs benchmark: overlaying DSCR distribution del proyecto con distribuciones típicas de Project Finance comparables, evaluar si proyecto es más o menos riskier que peers  
* Método generate\_stress\_overlay que superponga distribución base vs distribución bajo stress scenarios: mostrar cómo stress shift distribution downward y increase tail risk  
* Documentar interpretación de distribuciones: explicar que median DSCR indica central tendency, percentiles bajos indican tail risk, volatilidad de DSCR indica stability del proyecto, persistent low DSCR indica structural problems

### **T-030: Probabilidades breach**

**¿En qué consiste?**  
 Calcular probabilidades de breach de covenants en diferentes períodos y bajo diferentes condiciones, usando resultados de Monte Carlo.

**Relaciones con otras tareas:**

* **Depende de:** T-029 (distribuciones de DSCR/LLCR)  
* **Utilizado por:** T-033 (pérdida esperada requiere PD), T-034 (tail risk analysis)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase BreachProbabilityAnalyzer en archivo pftoken/analysis/breach\_probability.py  
* Método calculate\_period\_breach\_probability que para cada período t compute: P(DSCR\_t \< threshold) \= count(scenarios donde DSCR\_t \< 1.25) / total\_scenarios, produce time series de probabilidades mostrando cómo riesgo evoluciona  
* Implementar cálculo de cumulative breach probability: P(breach antes de período T) \= P(breach en algún momento hasta T), compute usando counting o usando survival analysis framework  
* Método calculate\_conditional\_breach\_probability: P(breach en t | no breach hasta t-1), mide probabilidad marginal de breach dado survival hasta ahora, captura increasing hazard rate si proyecto se deteriora  
* Implementar breach probability por covenant type: P(DSCR breach), P(LLCR breach), P(DSRA depletion), algunos covenants más fáciles de violar que otros, ranking por severity  
* Método analyze\_breach\_correlations: calcular correlation entre breach events de diferentes covenants, típicamente DSCR breach correlaciona con LLCR breach pero no perfectamente, identify independent vs correlated risks  
* Implementar survival analysis: usar Kaplan-Meier estimator para compute survival function S(t) \= P(no breach hasta t), plot survival curve mostrando declining survival probability, hazard rate h(t) \= instantaneous risk de breach en t  
* Método calculate\_expected\_time\_to\_breach: integrar sobre distribución de time-to-default, produce metric como "proyecto esperado a breach covenant en año 4.2 en promedio"  
* Implementar segmentation por características: compute breach probability conditional en initial conditions, ej: P(breach | high\_initial\_leverage) vs P(breach | low\_initial\_leverage), identify risk factors  
* Método compare\_breach\_risk\_structures: calcular breach probabilities para Traditional vs Tokenized structures, argumentar cuál tiene lower breach risk, quantify difference in basis points  
* Crear tabla de breach probabilities: filas \= períodos, columnas \= percentiles de distribución (10th, 50th, 90th), celdas \= probabilidad de breach, formato condicional resaltando high-risk periods  
* Implementar confidence intervals sobre probabilidades: usar bootstrap resampling de simulaciones para compute uncertainty en probability estimates, reportar probabilities como point estimate ± margin of error  
* Método generate\_breach\_heatmap: matriz con período en X, covenant type en Y, color intensity \= breach probability, visually identify danger zones  
* Documentar interpretación: explicar que 10% breach probability es material risk requiring attention, 50% probability indica high likelihood de stress, \> 90% suggests structure is undersized

### **T-031: Pipeline end-to-end MC**

**¿En qué consiste?**  
 Integrar todos los componentes de Monte Carlo en un pipeline cohesivo end-to-end que ejecute simulación completa desde parámetros hasta outputs finales con una sola llamada.

**Relaciones con otras tareas:**

* **Depende de:** T-026 (pricing estocástico), T-029 (ratios por trayectoria), T-030 (probabilidades)  
* **Culminación de:** WP-07 Simulación Monte Carlo completo  
* **Utilizado por:** T-040 (stress testing usa este pipeline), T-048 (notebook final)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase MonteCarloPipeline en archivo pftoken/simulation/pipeline.py que orquesta flujo completo  
* Método run\_complete\_analysis que reciba solo ProjectParams y SimulationParams, ejecute toda la cadena, retorne ComprehensiveResults  
* **Step 1 \- Initialization:** validar parámetros de entrada, setup random seeds, initialize result containers, log configuration  
* **Step 2 \- Generate Scenarios:** llamar T-022 para sample variables aleatorias, aplicar T-023 para correlations, generar matriz completa de scenarios \[N\_scenarios × N\_periods × N\_variables\]  
* **Step 3 \- Execute Trajectories:** para cada scenario calcular CFADS usando T-003B, ejecutar Waterfall usando T-006, calcular ratios usando T-004, detectar defaults usando T-025, calcular Merton PD/LGD usando T-024, almacenar todos los resultados  
* **Step 4 \- Price Tranches:** para cada scenario valorar cada tranche usando T-007 y T-026, generar distribución de precios por tranche, calcular expected prices y price volatility  
* **Step 5 \- Calculate Risk Metrics:** agregar resultados para compute EL usando T-033, VaR/CVaR usando T-034, breach probabilities usando T-030, HHI usando T-037  
* **Step 6 \- Generate Analytics:** compute all derived metrics, perform comparisons, identify patterns, generate insights  
* **Step 7 \- Export Results:** save to CSV/HDF5, generate summary statistics, create visualizations, compile final report  
* Implementar progress tracking comprehensivo: mostrar progress en cada step principal, estimate remaining time, log warnings y errors  
* Implementar error handling robusto: try-catch en cada step, si un scenario falla no crash entire simulation, log failed scenarios para investigación, continue con scenarios restantes  
* Método validate\_results que ejecute sanity checks: verificar que distribuciones son razonables (no todos escenarios default, no todos perfectos), verificar conservation laws (suma de flujos en waterfall), identificar anomalías estadísticas  
* Implementar caching inteligente: si re-running simulation con algunos parámetros cambiados, reusar cálculos que no cambiaron, detectar qué steps necesitan re-ejecución  
* Crear comprehensive logging: log todas las decisiones importantes, timing de cada step, memory usage, warnings about potential issues, facilitar debugging de simulaciones complejas  
* Método generate\_executive\_summary que produzca one-page summary: key metrics (mean DSCR, VaR\_95, default probability, WACD), comparison Traditional vs Tokenized, traffic-light indicators (green/yellow/red) para key risks, executive recommendation  
* Implementar comparator mode: run simulation para múltiples estructuras simultáneamente, produce side-by-side comparison, highlight differences, facilitate decision-making  
* Crear configuración por templates: definir templates predefinidos como "conservative", "balanced", "aggressive", cada template con parámetros calibrados, usuarios pueden select template o customize  
* Implementar sensitivity analyzer integrado: vary key parameters one-at-a-time, re-run pipeline para cada variation, produce tornado chart mostrando sensitivity de NPV, DSCR, VaR a each parameter  
* Documentar workflow completo: crear diagrama de flujo mostrando todos los steps del pipeline, dependencies entre steps, decisiones en cada punto, facilitar entendimiento del modelo completo

## **WP-08: PRICING ESTOCÁSTICO**

### **T-026: Valuación estocástica**

**¿En qué consiste?**  
 Extender pricing determinístico de T-007 para incorporar incertidumbre estocástica de flujos futuros usando resultados de Monte Carlo, generando distribuciones de precios de tranches.

**Relaciones con otras tareas:**

* **Depende de:** T-021 (MC genera distribución de flujos), T-007 (pricing base determinístico)  
* **Continúa en:** T-027 (duration/convexity), T-028 (calibración de spreads)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase StochasticPricing en archivo pftoken/pricing/stochastic\_pricing.py  
* Método price\_tranche\_distribution que reciba distribución completa de cashflows por tranche desde MC: para cada scenario calcular PV del tranche descontando sus flujos con tasa apropiada, generar distribución de N precios (uno por scenario)  
* Implementar ajuste de tasa de descuento por riesgo: en cada scenario usar tasa \= risk\_free\_rate \+ spread donde spread puede variar con condiciones del scenario, scenarios con higher default risk requieren higher spread  
* Método calculate\_expected\_price que compute E\[Price\] \= mean de distribución de precios, este es valor justo del tranche considerando toda la incertidumbre, comparar con precio par para determinar si emisión debe ser over/under par  
* Implementar cálculo de price volatility: σ\_price \= std dev de distribución de precios, alta volatilidad indica mayor riesgo de marking-to-market, inversores requieren mayor compensation  
* Método calculate\_price\_percentiles que extraiga percentiles clave: P10, P25, P50 (median), P75, P90 de distribución de precios, P10 representa downside scenario para inversores, P90 representa upside  
* Implementar análisis de probability of loss: P(Price \< Par) \= probabilidad de que precio caiga por debajo de 100, mide riesgo de principal loss para investors, complementa VaR analysis  
* Método decompose\_price\_uncertainty que atribuya variance de precio a diferentes fuentes: variance debido a revenue uncertainty, variance debido a cost uncertainty, variance debido a rate uncertainty, usar ANOVA o regression-based decomposition  
* Crear visualización de distribuciones de precio: histogram para cada tranche mostrando shape de distribución, Senior típicamente tight distribution (low risk), Sub tiene fat tails (high risk), overlay distributions para comparar tranches  
* Implementar pricing con early redemption options: si tranche tiene call provision permitiendo prepayment, modelar decision endógena de ejercer call, price \= E\[min(PV\_hold, PV\_call)\], incorpora option value  
* Método calculate\_yield\_distribution usando iteración: para cada precio simulado, resolver para YTM que hace NPV \= ese precio, generar distribución de yields, compute expected yield, yield volatility  
* Implementar spread\_distribution analysis: calcular spread sobre benchmark para cada scenario, genera distribución de spreads, mean spread refleja riesgo promedio, tail of spread distribution refleja tail risk  
* Método compare\_deterministic\_vs\_stochastic: plot precio determinístico (usando expected cashflows) vs expected precio estocástico (E\[PV(CF)\]), Jensen's inequality implica que pueden diferir si utility es nonlinear, discutir cuándo difieren materialmente  
* Crear price-yield scatter: plot con yield en X-axis, price en Y-axis, uno por scenario, muestra relación inversa yield-price y dispersión due to credit risk differences  
* Implementar risk-neutral pricing: ajustar probabilidades de scenarios para reflejar risk aversion, usar stochastic discount factor, compute risk-neutral expected price \= E^Q\[PV\], comparar con physical expected price \= E^P\[PV\]  
* Documentar diferencias con pricing determinístico: explicar que usar expected cashflows subestima riesgo vs pricing cada scenario por separado, convexity effects pueden causar material differences

### **T-027: Duration y convexity**

**¿En qué consiste?**  
 Calcular duration efectiva y convexidad efectiva de cada tranche como medidas de sensibilidad de precio a cambios en tasas de interés.

**Relaciones con otras tareas:**

* **Depende de:** T-008 (curva spot), T-026 (pricing estocástico)  
* **Complementa:** T-044 (sensibilidad a tasas), T-045 (pricing de hedges)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Extender StochasticPricing con métodos de duration/convexity  
* Método calculate\_effective\_duration usando bump-and-revalue: shift curva de tasas \+25bps, reprice tranche → Price\_up, shift curva \-25bps, reprice → Price\_down, duration \= (Price\_down \- Price\_up) / (2 × Price\_base × 0.0025)  
* Implementar para cada tranche por separado: Senior típicamente tiene duration \~5-7 años (depende de amortization), Mezz duration ligeramente mayor, Sub puede tener duration distinta si tiene different maturity  
* Método calculate\_macaulay\_duration analíticamente: Duration\_Macaulay \= Σ\[t × PV(CF\_t)\] / Price donde t es tiempo, peso cada período por su contribución a PV, mide weighted average time to receive cashflows  
* Calcular modified duration: Duration\_modified \= Duration\_Macaulay / (1 \+ yield), esta es la sensibilidad de precio a pequeños cambios en yield, ΔP/P ≈ \-Duration\_modified × Δy  
* Método calculate\_effective\_convexity: Convexity \= (Price\_up \+ Price\_down \- 2×Price\_base) / (Price\_base × Δy²) donde Δy \= 0.0025, mide curvature de relación precio-yield, positiva para bonds normales  
* Implementar interpretación de convexity: positive convexity es deseable, significa que losses de rate increases son menos que gains de rate decreases (asymmetric payoff favorable), negative convexity (ej: prepayment risk) es unfavorable  
* Método calculate\_key\_rate\_durations: en lugar de shift paralelo de toda la curva, shift individual key rates (2y, 5y, 10y, etc) uno a la vez, compute sensibilidad a cada, suma de key rate durations \= effective duration, permite hedging granular  
* Crear tabla de risk metrics por tranche: columnas \= Duration, Convexity, DV01, rows \= Senior/Mezz/Sub, facilita comparación de risk profiles  
* Implementar análisis de duration gap: comparar duration de activos (proyecto CFADS) vs duration de pasivos (deuda), positive gap indica asset-liability mismatch risk, negative gap también risky, objetivo es matching  
* Método simulate\_rate\_scenarios para validar duration: generar \+100bps, \+200bps, \-50bps, \-100bps scenarios, compute actual price changes, verificar que duration aproximation is accurate for small changes pero breaks down para large shifts  
* Crear visualización de price-yield curve: plot mostrando precio del tranche como función de yield level, tangent line en current yield \= duration, curvature \= convexity, ilustra second-order effects  
* Implementar duration hedging recommendation: dado duration de tranche, calcular notional de interest rate swap necesario para hedge, duration of swap × notional\_swap \= duration of tranche × notional\_tranche  
* Documentar diferencias entre duration types: Macaulay (time measure), Modified (yield sensitivity), Effective (rate curve sensitivity), explicar cuándo usar cada uno

### **T-028: Calibración spreads**

**¿En qué consiste?**  
 Calibrar spreads de crédito de cada tranche sobre curva base usando modelo risk-based que relaciona spread con PD, LGD y otras métricas de riesgo calculadas.

**Relaciones con otras tareas:**

* **Depende de:** T-026 (pricing), T-010 (métricas de riesgo EL/PD/LGD), T-008 (curva base)  
* **Utilizado por:** T-036 (optimización de WACD requiere spreads calibrados)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase SpreadCalibrator en archivo pftoken/pricing/spread\_calibration.py  
* Método calibrate\_credit\_spread usando modelo reducido: spread\_tranche \= α × PD \+ β × LGD \+ γ × illiquidity\_premium \+ δ donde α, β, γ, δ son parámetros a calibrar  
* Implementar estimación de parámetros: si hay datos de mercado de spreads observados para comparables, correr regresión de spreads vs (PD, LGD, illiquidity) para estimar α, β, γ, si no hay data usar benchmark values de literatura  
* Método calculate\_default\_adjusted\_spread: spread que iguala expected return de bond riesgoso a bond libre de riesgo considerando probability de default, spread \= \-ln(1 \- PD × LGD) / duration, aproximation lineal \= PD × LGD para small PD  
* Implementar illiquidity premium calculation: tranche tokenizado puede tener menor illiquidity vs loan tradicional, cuantificar usando bid-ask spreads de mercados secundarios, típicamente 10-50bps dependiendo de market depth  
* Método calibrate\_to\_ratings: si tranches tienen ratings (AAA, A, BBB), usar historical default rates por rating desde Moody's/S\&P, mapear PD → rating → typical spread para ese rating  
* Implementar ajuste por seniority: Senior spread baseline, Mezz spread \= Senior \+ seniority\_premium (típicamente 200-400bps), Sub spread \= Mezz \+ additional premium (400-600bps), reflejar structural subordination  
* Método calibrate\_structural\_model usando Merton: relacionar spread con distance-to-default del modelo Merton, spread increase exponentially cuando DD decrease, implementar función spread(DD) \= a × exp(-b × DD) donde a,b calibrados  
* Crear curva de term structure de spreads: spreads típicamente increase con maturity reflejando cumulative default risk, implementar curva spread(tenor) usando interpolación entre tenors observados  
* Implementar credit migration modeling: si rating puede cambiar en futuro (upgrade/downgrade), modelar probabilidades de migración, ajustar spread por expected rating changes, incorporar en pricing  
* Método validate\_spread\_calibration: verificar que spreads calibrados están en rango razonable vs benchmarks de mercado, ej: Senior spread 100-200bps, Mezz 300-500bps, Sub 600-1000bps para infrastructure projects, flag si fuera de rango  
* Implementar sensibilidad de spreads: cómo cambiarían spreads si PD aumenta 50%, si LGD se deteriora, generar table mostrando elasticidades, útil para stress testing de pricing  
* Método compare\_implied\_vs\_model\_spreads: si hay precios de mercado observados, extraer implied spreads, comparar con spreads predichos por modelo, compute pricing errors, refinar modelo si errors son grandes  
* Crear visualización de spread composition: stacked bar chart mostrando breakdown de spread en components: base spread por PD, add-on por LGD, add-on por illiquidity, total spread, facilita understanding de drivers  
* Documentar metodología de calibración: citar referencias académicas sobre credit spread modeling, discutir limitaciones como ignoring spread volatility o recovery risk, acknowledge uncertainty en estimates

### **T-044: Sensibilidad tasas**

**¿En qué consiste?**  
 Analizar exhaustivamente cómo cambios en curva de tasas de interés afectan valoración de tranches, DSCR, y viabilidad del proyecto.

**Relaciones con otras tareas:**

* **Depende de:** T-027 (duration calculada), T-008 (curva spot)  
* **Prepara para:** T-045 (hedging con caps requiere entender sensibilidad)  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase InterestRateSensitivity en archivo pftoken/analysis/rate\_sensitivity.py  
* Método analyze\_parallel\_shift que shift curva completa por Δr \= {-100, \-50, 0, \+50, \+100, \+200}bps, para cada shift recalcular: precio de cada tranche, DSCR de proyecto, WACD de estructura, compare resultados across shifts  
* Implementar cálculo de elasticidad: ε\_price \= (ΔP/P) / (Δr/r), mide sensibilidad porcentual, típicamente senior tiene |ε| mayor que sub porque duration mayor (paradójicamente menos risky bond más sensible a rates)  
* Método analyze\_non\_parallel\_shifts: generar scenarios de steepening (short rates stable, long rates up), flattening (short rates up, long rates stable), inversion (short \> long), cada shape tiene different impact on project con different maturity structure  
* Implementar simulation de trayectorias de tasas: usando mean reversion model de T-022, simular paths posibles de tasas futuras, para cada path recalcular DSCR stream, identificar paths que causan stress  
* Método calculate\_rate\_var que compute "Valor en Riesgo por Tasa": cuánto puede caer valor del tranche con 95% confidence debido a movimientos adversos de tasas en próximo año, separa rate risk de credit risk  
* Crear tornado chart de sensibilidades: bars mostrando impacto en NPV de proyecto ante \+1% change en diferentes rates (Fed funds, 5y Treasury, 10y Treasury, etc), identifica cuál rate tiene mayor impacto  
* Implementar análisis de cash flow timing impact: proyecto con early high CFADs es menos sensible a late rate increases vs proyecto con backend-loaded CFADs, cuantificar usando cash flow duration  
* Método decompose\_total\_sensitivity: separar efecto de tasa en: (1) costo de deuda increase reduce CFADS disponible, (2) discount rate increase reduce PV de flujos, identificar cuál efecto domina  
* Crear scenario matrix: tabla con nivel de tasa en filas (3%, 5%, 7%, 9%), tranche en columnas, celdas \= valor del tranche, formato condicional mostrando green/red según ganancia/pérdida  
* Implementar análisis de break-even rate: encontrar nivel de tasa que hace DSCR \= covenant threshold exactly, ej: proyecto viable si tasas \< 8.5% pero breach covenant si tasas \> 8.5%, crucial para risk assessment  
* Método simulate\_fed\_policy\_scenarios: modelar scenarios de Fed policy como "hawkish" (fast rate increases), "dovish" (stable/decreasing rates), "volatile" (frequent changes), evaluar project performance bajo cada regime  
* Documentar implicaciones estratégicas: explicar que alta sensibilidad a tasas indica necesidad de hedging mediante swaps o caps, cuantificar beneficio potencial de hedging vs costo

## **WP-09: VISUALIZACIONES**

### **T-032: Dashboard resultados**

**¿En qué consiste?**  
 Crear dashboard interactivo comprehensivo que presente todos los resultados del análisis de manera visual e intuitiva para stakeholders no-técnicos.

**Relaciones con otras tareas:**

* **Depende de:** T-031 (pipeline MC completo), T-041 (resultados stress), T-043 (stress híbridas), TAMM11 (resultados AMM)  
* **Culminación de:** Todos los módulos analíticos, integración final  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Crear notebook Jupyter interactivo dashboard.ipynb en carpeta notebooks/ que sirva como dashboard principal  
* **Panel 1 \- Executive Summary:** KPIs principales en formato "card": DSCR promedio con indicador verde/amarillo/rojo, probabilidad de default con gauge chart, WACD con benchmark comparison, NPV del proyecto, IRR vs hurdle rate  
* Implementar traffic light indicators: verde si métrica cumple target (DSCR \> 1.35), amarillo si close to threshold (1.25-1.35), rojo si breach (\< 1.25)  
* **Panel 2 \- Cash Flow Waterfall:** gráfico de cascada mostrando cómo fluye CFADS típico a través de waterfall, barras para OPEX, intereses de cada tranche, fondeo de reservas, principal, dividendos, usar colores distintivos por categoría  
* **Panel 3 \- Ratio Evolution:** líneas temporales mostrando DSCR, LLCR en el tiempo, fan chart con percentiles 10-90 mostrando uncertainty band, línea horizontal marcando covenant threshold, sombrear períodos con breach risk  
* **Panel 4 \- Risk Metrics:** tabla con métricas de riesgo por tranche (EL, VaR\_95, CVaR\_95, PD, LGD), formato condicional resaltando tranches con mayor riesgo, gráfico de barras comparando EL por tranche  
* **Panel 5 \- Monte Carlo Distributions:** histogramas de distribuciones clave (DSCR mínimo, NPV, default time), overlay normal fit para comparar, marcar percentiles importantes, mostrar skewness y kurtosis  
* **Panel 6 \- Stress Testing:** heatmap mostrando impacto de cada escenario de estrés en métricas clave, ejes \= escenario × métrica, color intensity \= magnitude de impacto, tabla de resilience comparison Traditional vs Tokenized  
* **Panel 7 \- Structure Comparison:** gráficos side-by-side comparando Traditional vs Tokenized en multiple dimensions (costo, riesgo, liquidez, flexibilidad), radar chart agregado, recommendation summary  
* **Panel 8 \- Pricing Analysis:** distribuciones de precios por tranche con box plots, tabla de yields y spreads, duration/convexity metrics, sensibilidad a rate changes con tornado chart  
* **Panel 9 \- AMM Liquidity:** resultados de análisis de mercado secundario (de WP-14), gráficos de convergencia DCF vs market price, impacto de panic sells, profundidad de liquidez por pool  
* Implementar interactividad usando widgets: sliders para ajustar parámetros key y ver impacto en real-time, dropdowns para seleccionar scenarios diferentes, checkboxes para toggle visibility de elementos  
* Crear visualizaciones con Plotly para interactividad: hover tooltips mostrando valores exactos, zoom y pan para explorar detalles, click legends para show/hide series, export a PNG para reportes  
* Implementar tabla dinámica explorable: usuarios pueden drill-down en métricas, sort por diferentes columnas, filter por ranges, útil para análisis ad-hoc  
* Método generate\_static\_report que exporte dashboard a HTML estático o PDF para sharing con stakeholders sin Python, preservar interactividad en HTML, layout profesional en PDF  
* Documentar cada visualización con markdown cells: explicar qué muestra el gráfico, cómo interpretarlo, qué insights se derivan, referencias a secciones relevantes del informe académico  
* Implementar narrative flow: organizar visualizaciones en orden lógico que cuenta historia del proyecto, empezar con overview, profundizar en detalles, concluir con recomendaciones

## **WP-10: OPTIMIZACIÓN**

### **T-036: Búsqueda WACD mínimo**

**¿En qué consiste?**  
 Implementar optimización de estructura de capital buscando combinación óptima de pesos de tranches que minimiza WACD considerando feedback loop entre estructura, riesgo y spreads.

**Relaciones con otras tareas:**

* **Depende de:** T-028 (spreads calibrados), T-009 (WACD calculation)  
* **Relacionado con:** T-035 (frontera eficiente provee context)  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase CapitalStructureOptimizer en archivo pftoken/optimization/capital\_optimizer.py  
* Definir problema de optimización: minimize WACD(w\_senior, w\_mezz, w\_sub) sujeto a: w\_senior \+ w\_mezz \+ w\_sub \= 1, w\_senior \>= 0.40 (minimum por requerimiento lenders), w\_mezz \>= 0.15, w\_sub \>= 0 (can be zero), w\_i ∈ \[0,1\]  
* Implementar feedback loop crítico: spreads NO son constantes, dependen de leverage y riesgo que a su vez dependen de pesos, ej: más Senior (menor leverage) → menor PD → menor spread\_senior, pero también menos tax shield y weight shifts  
* Método calculate\_implied\_spreads que dado vector de pesos (w), calcule leverage ratio, ejecute MC simulation con esa estructura, obtenga PD/LGD por tranche, calibre spreads usando T-028, retorne spread\_vector \= \[s\_senior, s\_mezz, s\_sub\]  
* Implementar WACD calculation endógena: WACD(w) \= Σ\[w\_i × (base\_rate \+ spread\_i(w))\] donde spread\_i depende de w vía feedback loop, esto hace optimization no-trivial  
* Método optimize\_using\_sequential\_quadratic que use scipy.optimize.minimize con method='SLSQP': maneja constraints nonlinear y bounds, converge bien para problems smooth, especificar bounds, constraints, initial guess  
* Implementar iterative refinement: empezar con grid search grueso para identificar región prometedora, refinar usando gradient-based optimizer, validar convergencia verificando que gradient → 0  
* Método validate\_optimum verificando que solución satisface KKT conditions: gradient of objective \= linear combination of gradients of constraints en óptimo, constraints están binding o slack correctamente  
* Implementar sensibilidad del óptimo: perturbar parámetros (ej: base\_rate, PD multiplier) ligeramente, re-optimize, measure cuánto cambia óptimo, robusto si óptimo se mueve poco ante perturbaciones  
* Crear visualización 3D de superficie de WACD: ejes X,Y \= (w\_senior, w\_mezz), eje Z \= WACD, plot surface mostrando landscape, marcar óptimo con punto rojo, mostrar contour lines en projection  
* Método compare\_optimal\_vs\_current: compute WACD de estructura actual (baseline), compute WACD de estructura óptima, calculate savings \= WACD\_current \- WACD\_optimal, translate a NPV savings \= PV(interest\_savings)  
* Implementar análisis de trade-offs en óptimo: cuánto cambiaría WACD si agregamos constraint adicional (ej: minimum 20% sub for diversification), useful para entender cost of constraints  
* Método generate\_optimization\_report: narrative explicando estructura óptima encontrada, comparación vs baseline, justificación de por qué es óptima, sensibilidad a assumptions, recommendations para implementación  
* Documentar limitaciones: optimización asume que todos los pesos son continuously adjustable, en realidad market preferences pueden limitar, regulaciones pueden imponer constraints no modelados, model risk en spread calibration afecta óptimo

## **WP-11: DERIVADOS**

### **T-045: Modelo Interest Rate Cap**

**¿En qué consiste?**  
 Modelar y analizar uso de un Interest Rate Cap como instrumento de cobertura para mitigar riesgo de aumento de tasas de interés identificado en análisis de sensibilidad.

**Relaciones con otras tareas:**

* **Depende de:** T-044 (sensibilidad a tasas cuantificada)  
* **Referencia:** T-008 (curva para pricing), T-027 (duration para hedging)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase InterestRateCap en archivo pftoken/derivatives/interest\_rate\_cap.py  
* Definir estructura de cap: cap es portafolio de caplets, cada caplet es call option en tasa de interés, if rate\_observed \> strike entonces payoff \= notional × (rate \- strike) × period\_fraction, else payoff \= 0  
* Método price\_caplet usando Black's formula: caplet\_value \= notional × period × \[F × N(d1) \- K × N(d2)\] × DF donde F \= forward rate, K \= strike, N \= normal CDF, d1 y d2 dependen de volatility  
* Implementar pricing de cap completo: cap\_value \= Σ caplet\_values sumando sobre todos los períodos de reset, típicamente cap tiene tenors de 3m o 6m alineados con pagos de deuda  
* Método calibrate\_volatility: necesitamos volatilidad de tasas para pricing, extraer implied volatilities desde market quotes de caps comparables, si no hay market data usar historical volatility de tasas  
* Implementar selección de strike óptimo: strike bajo \= cobertura amplia pero premium alto, strike alto \= cobertura limitada pero premium bajo, analizar trade-off mediante cost-benefit analysis  
* Método calculate\_hedge\_effectiveness: simular scenarios con rate increases, compare outcomes con vs sin cap, measure variance reduction, típicamente cap elimina 60-80% de tail risk de rates pero costo ongoing  
* Implementar análisis de carry cost: cap premium es upfront cost que reduce CFADS inicial, amortizar costo over life de cap, calcular impact en DSCR, verificar que cap no causa liquidity problems  
* Método design\_hedging\_strategy: dado duration de deuda y exposure a rate risk, determinar notional óptimo de cap, típicamente hedge 50-100% de exposición dependiendo de risk appetite  
* Crear scenario analysis con hedge: re-run stress scenarios de T-038 pero con cap en place, mostrar que outcomes severos (high rate scenarios) están mitigados, quantify benefit en terms de reducción de VaR  
* Implementar comparación cap vs swap: cap es one-sided protection (paga solo cuando rates suben), swap es two-sided (fixed for floating), comparar costo y efectividad, típicamente cap preferido para Project Finance porque preserva upside de rate decreases  
* Método calculate\_break\_even\_rate: determinar nivel de rate increase necesario para que benefit de cap exceda su costo, if rates increase less que break-even entonces cap is money lost, if more entonces beneficial  
* Crear visualización de payoff profile: plot mostrando payoff de cap como función de rate level, non-linear kinked profile (flat cuando rate \< strike, linear cuando rate \> strike), compare con linear profile de swap  
* Documentar recomendaciones: recomendar si proyecto debe comprar cap based en análisis, qué strike y notional son óptimos, cuándo ejecutar hedge (upfront o esperar), monitoreo ongoing necesario

## **WP-14: AMM SIMPLIFICADO (REDEFINIDO)**

### **T-053: Diseño arquitectura AMM**

**¿En qué consiste?**  
 Diseñar la arquitectura conceptual del módulo AMM (Automated Market Maker) que simulará mercado secundario de tokens de deuda usando modelos DeFi, sin implementación blockchain real.

**Relaciones con otras tareas:**

* **Depende de:** T-041 (stress testing completo para poder aplicar shocks a AMM)  
* **Habilita:** TAMM01-TAMM11 (todas las tareas AMM subsiguientes)  
* **Duración:** 2 días según Gantt (tarea NUEVA en versión actualizada)

**Qué se debe implementar:**

* Crear módulo pftoken/amm/ con subpaquetes para pools/, pricing/, simulation/  
* Documento de diseño especificando objetivos del módulo AMM: (1) demostrar pricing dinámico de mercado vs pricing fundamental DCF, (2) cuantificar liquidez disponible para diferentes tamaños de orden, (3) simular panic sells y stress de liquidez, (4) evaluar viabilidad económica para liquidity providers  
* Definir scope explícito: modelo es TEÓRICO y ACADÉMICO, no requiere deployment en blockchain real, no maneja transactions reales, no involucra wallets o gas fees reales, objetivo es explorar CONCEPTOS cuantitativos de market dynamics  
* Especificar dos arquitecturas de pool a modelar: Pool V2 (Constant Product x×y=k estilo Uniswap V2), Pool V3 (Concentrated Liquidity con rangos estilo Uniswap V3), comparar trade-offs entre ambos designs  
* Definir flujo de datos: DCF pricing de T-007 provee "precio fundamental" de cada token, Pool inicializado a ese precio como baseline, Swaps simulados mueven precio de mercado, Arbitraje traer precio de vuelta hacia DCF  
* Documento de limitaciones y asunciones: ignora MEV y front-running, asume gas costs \= 0 (simplificación académica), asume oracle perfecto para DCF price, asume liquidez no fragmentada en múltiples DEXs, asume arbitrajistas respond instantáneamente  
* Especificar parámetros configurables: liquidez inicial en cada pool (ej: $1M USDC), fee tier (ej: 30 bps), rango de liquidez para V3 (ej: \[P\_DCF × 0.98, P\_DCF × 1.02\]), estos serán inputs de simulación  
* Crear diagrama de arquitectura mostrando: módulo DCF pricing → inicializa pools → traders ejecutan swaps → precio de mercado diverge → arbitrajistas cierran brecha → loop continúa, overlayed con stress scenarios que trigger volume spikes  
* Implementar clase base Pool abstracta con métodos: get\_price(), execute\_swap(amount\_in, token\_in), add\_liquidity(amount0, amount1), remove\_liquidity(shares), calculate\_fees\_earned(), subclases implementan specifics  
* Documentar casos de uso principales del módulo: Caso 1 \= stress test de liquidez (100 vendedores simultáneos), Caso 2 \= diseño óptimo de rango de liquidez, Caso 3 \= análisis de breakeven para LPs, Caso 4 \= impacto de eventos crediticios  
* Definir métricas de output esperadas: precio de mercado vs DCF spread (bps), slippage por orden size, tiempo de convergencia post-shock, impermanent loss acumulado, fees earned por LPs, todas estas métricas facilitan comparación de designs

### **TAMM01: Pool V2 Constant Product**

**¿En qué consiste?**  
 Implementar pool AMM tipo Uniswap V2 usando fórmula constant product x×y=k para simular mercado secundario básico de tokens.

**Relaciones con otras tareas:**

* **Depende de:** T-053 (arquitectura definida)  
* **Baseline para:** TAMM02 (V3 concentrated liquidity como extensión)  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase ConstantProductPool en archivo pftoken/amm/pools/constant\_product.py heredando de Pool  
* Atributos del pool: reserve\_token (cantidad de tokens de deuda en pool), reserve\_usdc (cantidad de USDC en pool), k\_constant \= reserve\_token × reserve\_usdc (invariante), total\_shares (liquidity provider shares), fee\_rate (ej: 0.003 para 30bps)  
* Método initialize\_pool que dado precio\_DCF y liquidez\_total cree pool balanceado: calcular reserve\_token y reserve\_usdc tal que price \= reserve\_usdc / reserve\_token \= precio\_DCF, y reserve\_token × price\_DCF \= liquidez\_total / 2  
* Método get\_spot\_price que retorne precio actual: price \= reserve\_usdc / reserve\_token, este es precio marginal para swap infinitesimal  
* Método calculate\_swap\_output usando fórmula constant product: dado amount\_in de token\_in, calcular amount\_out de token\_out preservando k \= (reserve\_in \+ amount\_in × (1-fee)) × (reserve\_out \- amount\_out), solve para amount\_out  
* Implementar execute\_swap que actualice reservas: reserve\_in \+= amount\_in, reserve\_out \-= amount\_out, verificar que k se preserva (o aumenta ligeramente por fees), actualizar precio implícito  
* Método calculate\_price\_impact que compute slippage: price\_impact \= (execution\_price \- spot\_price) / spot\_price, para órdenes grandes impacto puede ser significativo (varios %), útil para evaluar profundidad de mercado  
* Implementar add\_liquidity permitiendo LP depositar ambos tokens proporcionalmente: shares\_minted \= (liquidity\_added / total\_liquidity) × total\_shares, LP recibe shares representing su fracción del pool  
* Método remove\_liquidity permitiendo LP retirar: recibe proporción de ambas reservas igual a su share fraction, burn shares correspondientes, útil para calcular retornos de LP  
* Implementar tracking de fees acumulados: cada swap contribuye fee \= amount\_in × fee\_rate, fees se acumulan en pool aumentando reserves, LPs capturan fees proporcionalmente cuando withdraw  
* Método calculate\_impermanent\_loss que compare valor actual de LP position vs hodling: IL \= (value\_LP \- value\_hodl) / value\_hodl, típicamente IL ocurre cuando price diverge significativamente de precio inicial, puede ser offset por fees earned  
* Crear simulación de swap sequence: generar serie de trades simulando actividad normal, apply a pool, track evolución de precio, reserves, IL over time  
* Implementar visualización de bonding curve: plot mostrando relación entre reserves (x×y=k hyperbola), price como pendiente de tangente, trade como movimiento along curve  
* Validar implementación: verificar que swaps en ambas direcciones reversan el estado, que k aumenta monotónicamente por fees, que arbitraje opportunity desaparece cuando price converge

### **TAMM02: Pool V3 Concentrated Liq**

**¿En qué consiste?**  
 Implementar pool AMM tipo Uniswap V3 con concentrated liquidity permitiendo LPs especificar rango de precios donde proveen liquidez, más capital-efficient que V2.

**Relaciones con otras tareas:**

* **Depende de:** TAMM01 (baseline V2 para comparar)  
* **Más sofisticado que:** V2, require cálculos adicionales  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Clase ConcentratedLiquidityPool en archivo pftoken/amm/pools/concentrated\_liquidity.py  
* Modelo matemático: liquidity L activa solo en rango \[P\_lower, P\_upper\], fórmula: x \= L × (√P\_upper \- √P) / (√P\_upper × √P), y \= L × (√P \- √P\_lower), donde x \= token reserves, y \= USDC reserves, P \= price  
* Atributos: tick\_spacing (granularidad de precios, ej: 60 ticks \= \~0.6% steps), liquidity\_positions \= lista de (P\_lower, P\_upper, L\_amount) para cada LP, active\_liquidity \= suma de L para posiciones activas en precio actual  
* Método initialize\_position permitiendo LP crear position con rango específico: LP escoge \[P\_a, P\_b\], deposita tokens según fórmula arriba, recibe position\_id, posición es activa solo cuando P ∈ \[P\_a, P\_b\]  
* Implementar tick mathematics: precio se representa como tick \= log\_base(price), conversión P \= 1.0001^tick permite arithmetic eficiente, liquidity transitions at ticks  
* Método execute\_swap\_v3 que calcule output considerando concentrated liquidity: si swap crosses multiple ranges con different liquidity, integrate piecewise, más complejo que V2 pero más eficiente si well-concentrated  
* Implementar capital efficiency calculation: compare V3 con liquidez concentrada vs V2 con liquidez dispersa, para mismo notional V3 puede proveer Nx más liquidez en rango relevante, típicamente N \= 3-10x  
* Método calculate\_fee\_apr que compute retorno anualizado para LP: fees earned dependen de fracción de tiempo que position está in-range y de volumen de trades, APR \= (fees\_24h × 365\) / capital\_deployed  
* Implementar IL calculation para V3: IL depende de cuánto precio se movió fuera del rango, si price exits range entonces LP se queda solo con un token (peor IL que V2), trade-off entre efficiency y robustness  
* Método optimize\_range\_width: dado volatilidad esperada y fee rate, encontrar rango óptimo que maximiza (fees earned \- expected IL), tight range \= más fees pero más IL risk, wide range \= menos fees pero menos IL  
* Crear comparación V2 vs V3: para mismo stress scenario (ej: panic sell), simular impacto en precio en ambos pools, V3 con narrow range puede tener peor price impact pero V2 desperdicia capital, cuantificar trade-off  
* Implementar just-in-time liquidity: modelar LP que agregan liquidez justo antes de grandes swaps y remueven después, capturan fees sin mucha IL exposure, controversial pero posible en V3  
* Visualizar posiciones V3: plot con precio en X-axis, liquidez en Y-axis, mostrar distribution de liquidity across price range, resaltar current price, mostrar gaps donde no hay liquidez  
* Documentar conclusiones sobre design: V3 superior para stable assets con poco price volatility, V2 mejor para volatile assets donde predecir range es difícil, recomendar based en proyecto

### **TAMM05: Market Price Calculator**

**¿En qué consiste?**  
 Implementar calculadora que extraiga pricing de mercado desde pools AMM y compare con pricing fundamental DCF para detectar discrepancias y oportunidades de arbitraje.

**Relaciones con otras tareas:**

* **Depende de:** TAMM02 (pools implementados), T-007 (DCF pricing como benchmark)  
* **Core de:** análisis de convergencia precio mercado vs fundamental  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase MarketPriceAnalyzer en archivo pftoken/amm/pricing/market\_price.py  
* Método get\_spot\_price que extraiga precio instantáneo de pool: para V2 es simple ratio de reserves, para V3 es más complejo requiriendo active liquidity en tick actual, normalizar a mismo numeraire (USDC por token)  
* Implementar TWAP calculation (Time-Weighted Average Price): mantener histórico de precios con timestamps, compute promedio ponderado por duración en cada precio, TWAP smooths volatility y resiste manipulation  
* Método calculate\_execution\_price que para orden de tamaño dado compute precio promedio efectivo: simulate el swap, compare price\_average \= total\_usdc\_out / total\_tokens\_in con spot price, diferencia es slippage  
* Implementar profundidad de mercado analysis: para grid de order sizes \[100, 500, 1k, 5k, 10k tokens\], calcular execution price y slippage cada uno, plot slippage vs size mostrando liquidity curve  
* Método compare\_to\_dcf que reciba precio fundamental del módulo DCF y compare: spread \= (price\_market \- price\_DCF) / price\_DCF en basis points, clasificar magnitude: \< 50bps \= tight, 50-200bps \= normal, \> 200bps \= wide/arbitrable  
* Implementar tracking histórico: almacenar time series de (timestamp, price\_market, price\_DCF, spread), útil para análisis de convergencia temporal, persistencia de mispricing, efectividad de arbitraje  
* Método detect\_arbitrage\_opportunity que identifique cuando spread excede threshold (ej: 100bps): si price\_market \> price\_DCF \+ threshold entonces tokens overpriced → sell en mercado buy at fundamental, if price\_market \< price\_DCF \- threshold entonces underpriced → buy en mercado sell at fundamental  
* Implementar cálculo de arbitrage profit potencial: profit \= |price\_market \- price\_DCF| × size \- transaction\_costs, para simplificación académica asumir transaction\_costs \= pool\_fee únicamente, real world tendría gas \+ slippage  
* Método calculate\_convergence\_metrics: tiempo promedio para que spread revierte a \< 50bps post-shock, volatilidad del spread, maximum divergence observado, half-life de mean reversion  
* Crear visualización dual-axis: línea azul \= price\_market evolving over time, línea roja \= price\_DCF (más estable), área sombreada entre ellas \= spread, resaltar períodos de wide spreads  
* Implementar análisis de eficiencia de mercado: si spread persiste despite arbitrage opportunities entonces mercado inefficient, podría deberse a capital constraints de arbitrajistas, friction costs, información asimétrica  
* Documentar casos donde divergencia es justificada: si hay event risk no reflejado en DCF model (ej: rumores de technical issues), price\_market puede incorporate info faster, spread no es pure arbitrage

### **TAMM06: DCF Integration Convergence**

**¿En qué consiste?**  
 Implementar mecanismo de arbitraje que simula cómo traders cierran brecha entre precio de mercado y precio fundamental DCF, analizando dinámica de convergencia.

**Relaciones con otras tareas:**

* **Depende de:** TAMM05 (detección de mispricing), T-007 (DCF como anchor)  
* **Core conceptual:** del módulo AMM, demuestra convergencia teoría-práctica  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase ArbitrageEngine en archivo pftoken/amm/arbitrage/arbitrage\_engine.py  
* Método execute\_arbitrage\_trade que detecte y ejecute arbitrage: si price\_market \> price\_DCF entonces sell tokens en pool comprando USDC, si price\_market \< price\_DCF entonces buy tokens en pool vendiendo USDC, size de trade proporcional a magnitude de mispricing  
* Implementar sizing heuristic: trade\_size \= α × liquidity × |spread| donde α es aggressiveness parameter (0-1), larger spreads justify larger trades, limited by available liquidity en pool  
* Método simulate\_arbitrage\_dynamics con loop iterativo: (1) medir spread actual, (2) si spread \> threshold ejecutar arbitrage trade, (3) actualizar precio de pool, (4) repetir hasta spread \< threshold o max iterations  
* Implementar realism via capital constraints: arbitrajistas tienen budget limitado, track capital\_available que decrece con cada trade, replenish over time simulando fundraising  
* Método calculate\_convergence\_speed: medir cuántos periods (o trades) requiere para que spread reduzca a \< 10bps, faster convergence indica mercado más eficiente, slower indica friction  
* Implementar variantes de arbitrage strategy: aggressive (large trades closing spread rápidamente), conservative (small trades gradualmente), adaptive (adjust size based on volatility), comparar effectiveness  
* Método analyze\_profit\_from\_arbitrage: sumar profits de todas las trades ejecutadas, subtract transaction costs (fees), compute ROI \= net\_profit / capital\_deployed, determinar si arbitrage is economically viable  
* Crear escenario de shock exógeno: DCF precio suddenly drops por 10% (credit event simulation), observe cómo rápido market price converges down, alternately DCF precio increases (positive news), observe convergence up  
* Implementar partial arbitrage: en realidad arbitrajistas no pueden close 100% de spread instantáneamente por capital y risk constraints, modelar fractional closing: spread\_new \= spread\_old × (1 \- α) donde α \< 1  
* Método propagate\_scenarios\_to\_amm que tome stress scenarios de T-038 y aplique a AMM: ej: Demand Shock \-20% → CFADS reduce → DCF price reduce → spread widens → arbitrage activity intensifies, full propagation loop  
* Crear visualización de convergence dynamics: plot temporal mostrando price\_market (volátil) converging toward price\_DCF (estable), trade points marcados, área de spread disminuyendo over time  
* Implementar análisis de equilibrium: identificar precio de equilibrio donde buy pressure \= sell pressure, verificar que equilibrio está cerca de DCF price (valida modelo), desviaciones persistentes indican market inefficiency o model error  
* Documentar hallazgos sobre speed of convergence: cuantificar half-life típica de mispricing (ej: 50% de spread cierra en 2 períodos), relacionar con literatura de market microstructure sobre price discovery

### **TAMM09: Impermanent Loss Calculator**

**¿En qué consiste?**  
 Calcular Impermanent Loss (pérdida impermanente) sufrida por liquidity providers cuando precio de token diverge de precio inicial, crucial para evaluar viabilidad económica de proveer liquidez.

**Relaciones con otras tareas:**

* **Depende de:** TAMM06 (dinámica de precios establecida), TAMM01/02 (cálculo de LP positions)  
* **Crítico para:** Análisis de viabilidad de LPs, diseño de incentivos  
* **Duración:** 2 días según Gantt

**Qué se debe implementar:**

* Clase ImpermanentLossCalculator en archivo pftoken/amm/analytics/impermanent\_loss.py  
* Método calculate\_il\_v2 para constant product pools: dado price\_initial y price\_final, IL \= 2×√(price\_ratio) / (1 \+ price\_ratio) \- 1 donde price\_ratio \= price\_final / price\_initial, resultado negativo indica loss  
* Ejemplo: si precio doubles (price\_ratio \= 2), IL \= 2×√2 / 3 \- 1 ≈ \-5.7%, si precio 4x entonces IL ≈ \-20%, IL is convex function de price change  
* Método calculate\_il\_v3 para concentrated liquidity: IL depends si price stays in-range o exits, if in-range IL similar a V2 pero amplificado por concentration, if out-of-range entonces LP se queda con single asset y IL es máximo  
* Implementar fórmula para V3 in-range: IL\_v3 \= IL\_v2 × concentration\_factor donde concentration\_factor \= 1 / (range\_width\_percentage), narrow ranges \= mayor IL risk per unit price change  
* Método calculate\_fees\_earned que offset IL: fees \= Σ(volume\_i × fee\_rate), LPs capturan fees proporcionalmente a su liquidity share, fees acumulan over time, pueden compensar IL si volume es suficiente  
* Implementar cálculo de break-even volume: volumen necesario tal que fees \= IL, breakeven\_volume \= IL\_absolute / fee\_rate, si actual volume \> breakeven entonces LP es profitable despite IL  
* Método calculate\_total\_return\_lp que combine IL y fees: return \= (value\_final\_LP \- value\_initial) / value\_initial donde value\_final incluye both withdrawn assets \+ accrued fees, compare vs hodl return  
* Crear simulación de diferentes price paths: (1) price stable \= no IL pero low fees, (2) price volatile but mean-reverting \= moderate IL moderate fees, (3) price trending \= high IL but potentially high fees, identify cuál profile mejor para LPs  
* Implementar análisis de sensibilidad de IL: cómo IL varía con range width (V3), con volatilidad de precio, con fee tier, generar surface plots mostrando IL como función de (price\_change, range\_width)  
* Método recommend\_lp\_strategy: dado características del token (volatilidad esperada, volumen esperado), recomendar si LP should use V2 o V3, qué range elegir si V3, qué fee tier óptimo  
* Crear visualización clásica de IL curve: plot con price ratio en X-axis (0.5x, 1x, 2x, 4x), IL percentage en Y-axis, curva mostrando symmetric IL loss en ambas direcciones away from initial price  
* Implementar comparación IL entre tranches: Senior tokens más estables → menor IL, Sub tokens más volátiles → mayor IL, recomendar que LPs provean liquidez para Senior si risk-averse  
* Documentar conclusión sobre LPs: proveer liquidez es profitable si fees \> IL, requiere volumen consistente de trades, riesgo principal es price trending fuertemente en una dirección, diversificación across múltiples pools reduce risk

### **TAMM11: Liquidity Stress Testing**

**¿En qué consiste?**  
 Simular panic sells y eventos de liquidez extremos para evaluar robustez de pools AMM bajo stress, culminación del análisis de mercado secundario.

**Relaciones con otras tareas:**

* **Depende de:** TAMM09 (IL calculado), T-038 (escenarios de stress como input), TAMM06 (arbitrage dynamics)  
* **Culminación de:** WP-14 AMM module completo  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Clase LiquidityStressTester en archivo pftoken/amm/stress/liquidity\_stress.py  
* **Escenario 1 \- Coordinated Panic Sell:** simular 100 small holders vendiendo simultáneamente tokens por fear, cada uno vende $10k, total \= $1M selling pressure, ejecutar todas las ventas sequentially en pool, observar price impact  
* Método simulate\_panic\_sell que ejecute batch de sell orders: para cada order calcular slippage incremental, aggregate total slippage, measure final price vs initial, time to recovery post-panic  
* Implementar cálculo de cascading effects: large price drop puede trigger stop-losses de otros holders, modelar secondary wave de selling amplifying initial shock, feedback loop potencialmente causing market crash  
* **Escenario 2 \- Liquidity Withdrawal:** simular LPs retirando liquidez during crisis, reducing pool depth right when needed most, model withdrawal\_rate \= función de IL y fear, self-reinforcing spiral  
* Método simulate\_liquidity\_drain: start con pool de $2M liquidez, LPs withdraw 50% seeing high IL, re-simulate panic sell con menor liquidez, price impact es mucho peor, demonstrate fragility  
* Implementar cálculo de critical liquidity threshold: identificar mínima liquidez requerida para que pool sobreviva panic sell sin price falling \> 50%, below threshold \= death spiral likely  
* **Escenario 3 \- Flash Crash Recovery:** simular sharp drop seguido por arbitrage recovery, measure resilience \= cuán rápido price rebounds to fundamental, compare V2 vs V3 recovery speed  
* Método analyze\_recovery\_dynamics: después de stress, track (1) time to 50% recovery, (2) time to 90% recovery, (3) overshoot si hay, (4) final stabilization level, faster recovery \= more resilient design  
* Implementar cálculo de max drawdown durante crisis: max\_DD \= (peak\_price \- trough\_price) / peak\_price, measure worst-case loss para LP que entered at peak, compare across pool designs  
* **Escenario 4 \- Asymmetric Stress:** stress uno de los tranches (ej: Mezz downgraded) while Senior stays stable, observe contagion effects, does stress en Mezz pool afecta Senior pool via correlated selling  
* Método propagate\_credit\_event\_to\_pools: dado credit downgrade de un tranche (from T-038 stress scenarios), model selling pressure en ese tranche's pool, spillover effects a otros pools vía risk-off sentiment  
* Crear dashboard de stress results: tabla mostrando para cada scenario (stress type × pool design), métricas: max price impact, recovery time, LP losses, arbitrajeur profits, system stability score  
* Implementar circuit breaker analysis: evaluar si trading pauses ayudarían durante extreme stress, model scenario donde trading se pausa when price drops \> 20% en 1 período, permite time for arbitrage capital to arrive  
* Método recommend\_pool\_parameters: basado en stress testing results, recomendar óptimo (liquidity amount, range width if V3, fee tier), trade-off between capital efficiency y robustness  
* Documentar conclusiones finales sobre AMM viability: bajo qué condiciones mercado secundario tokenizado es viable, cuándo liquidity es insuficiente y estructura tradicional preferible, requisitos mínimos de volumen y liquidez para sustainable market

## **WP-12: ENTREGABLES**

### **T-048: Notebook final integrado**

**¿En qué consiste?**  
 Crear notebook Jupyter ejecutivo que integra todos los análisis en narrativa cohesiva, sirve como documento principal de presentación del trabajo.

**Relaciones con otras tareas:**

* **Depende de:** T-032 (dashboard), T-043 (stress híbridas completo), TAMM11 (AMM completo)  
* **Culminación:** De todo el proyecto, integración final  
* **Duración:** 5 días según Gantt

**Qué se debe implementar:**

* Crear notebook TP\_Quant\_Final.ipynb en carpeta notebooks/ con estructura académica profesional  
* **Sección 1 \- Executive Summary:** resumen de una página con objetivos del TP, metodología general, hallazgos principales, recomendación final sobre tokenización, métricas clave en tabla  
* **Sección 2 \- Introducción y Motivación:** contexto del proyecto LEO IoT, justificación de caso de uso, relevancia de tokenización en Project Finance, objetivos cuantitativos específicos, estructura del documento  
* **Sección 3 \- Metodología:** descripción detallada de arquitectura del modelo, módulos implementados (CFADS, Waterfall, MC, Pricing, Risk, Stress, AMM), parámetros calibrados, supuestos clave con justificaciones académicas  
* **Sección 4 \- Análisis Base Case:** resultados determinísticos usando parámetros esperados, CFADS proyectados con visualizaciones, Waterfall típico execution, ratios DSCR/LLCR, pricing de tranches, WACD de cada estructura  
* **Sección 5 \- Simulación Monte Carlo:** descripción de setup estocástico con distribuciones y correlaciones, resultados agregados (distribuciones de DSCR, NPV, precios), análisis de sensibilidad a parámetros clave  
* **Sección 6 \- Métricas de Riesgo:** EL/VaR/CVaR por tranche, análisis de distribución de pérdidas, concentración de riesgo (HHI), probabilidades de breach, comparación Traditional vs Tokenized en riesgo  
* **Sección 7 \- Stress Testing:** descripción de escenarios de estrés diseñados, resultados de cada escenario, análisis de resilience, reverse stress testing findings, conclusiones sobre robustez  
* **Sección 8 \- Optimización de Estructura:** análisis de frontera eficiente, estructura óptima encontrada, comparación con estructuras base, sensibilidad del óptimo, recomendaciones  
* **Sección 9 \- Análisis de Mercado Secundario (AMM):** conceptual framework de AMM para tokens, resultados de simulación de liquidez, convergencia DCF vs market price, viability de LPs, limitaciones del análisis  
* **Sección 10 \- Comparación Final:** tabla comprehensiva Traditional vs Tokenized en todas dimensiones (costo, riesgo, liquidez, flexibilidad, complejidad), scoring ponderado, recomendación final con justificación  
* **Sección 11 \- Conclusiones y Trabajo Futuro:** síntesis de hallazgos principales, limitaciones del modelo, extensiones propuestas, implicaciones para práctica de Project Finance  
* **Sección 12 \- Referencias:** bibliografía completa en formato APA, citar Gatti, Yescombe, Esty, Allen et al, BIS, OECD, papers relevantes de structured finance  
* Implementar ejecución end-to-end: notebook debe ser ejecutable de principio a fin sin errores, carga datos, ejecuta análisis, genera visualizaciones, produce outputs  
* Usar markdown cells extensively: explicar cada paso del análisis, interpretar resultados, conectar con teoría, proveer insights, mantener narrativa fluida  
* Implementar estilo académico profesional: usar LaTeX para ecuaciones, citar apropiadamente, mantener objetividad, reconocer limitaciones, evitar afirmaciones no soportadas  
* Crear TOC (table of contents) al inicio con hyperlinks a secciones, facilitar navegación  
* Implementar sección de reproducibilidad: especificar versiones de software, proveer instrucciones de setup, listar dependencias, asegurar que resultados son replicables  
* Optimizar para presentación: usar figuras de alta resolución, tablas bien formateadas, colores consistentes, layout limpio, evitar clutter  
* Generar versión exportada a HTML con interactividad preservada para sharing fácil sin requerir Python

### **T-049: Informe PDF**

**¿En qué consiste?**  
 Generar informe académico formal en PDF de 10-15 páginas que documenta trabajo práctico siguiendo estándares académicos, complementa notebook con formalidad.

**Relaciones con otras tareas:**

* **Depende de:** T-048 (notebook es fuente de contenido)  
* **Entregable académico:** Para evaluación formal del TP  
* **Duración:** 4 días según Gantt

**Qué se debe implementar:**

* Crear documento LaTeX o Word TP\_Quant\_Informe.tex/.docx en carpeta docs/  
* **Portada:** título completo del trabajo, subtítulo indicando caso de estudio, nombres de autores, afiliación institucional, fecha, logo institucional si aplica  
* **Resumen Ejecutivo (Abstract):** máximo 250 palabras, síntesis del problema, metodología, hallazgos principales, conclusión, keywords  
* **Tabla de Contenidos:** numerada con páginas  
* **Capítulo 1 \- Introducción:** contexto de Project Finance para infraestructura satelital, tendencia hacia tokenización en finanzas, gap que este trabajo busca llenar, objetivos específicos y alcance, organización del documento  
* **Capítulo 2 \- Marco Teórico:** revisión de literatura sobre Project Finance (Gatti, Yescombe), tokenización de activos (OECD, BIS), market making y AMMs (Uniswap whitepapers), credit risk modeling (Merton 1973, 1974), establecer fundamentos teóricos del análisis  
* **Capítulo 3 \- Metodología:** descripción formal del modelo cuantitativo, ecuaciones principales (CFADS, waterfall, pricing DCF, Merton PD), algoritmo de Monte Carlo, stress testing framework, AMM design, parámetros calibrados con fuentes, diagrama de arquitectura del sistema  
* **Capítulo 4 \- Resultados:** presentación estructurada de hallazgos, subsecciones para cada tipo de análisis (base case, MC, risk metrics, stress, AMM), tablas y gráficos selectos más relevantes (no incluir todo, ser selectivo), interpretación de cada resultado clave  
* **Capítulo 5 \- Discusión:** análisis crítico de implicaciones, comparación Traditional vs Tokenized con argumento balanceado, trade-offs identificados, contexto de resultados en literatura existente, limitaciones del modelo reconocidas explícitamente  
* **Capítulo 6 \- Conclusiones:** síntesis final de si tokenización es ventajosa para este caso, condiciones bajo las cuales recomendación aplica, contribuciones del trabajo, trabajo futuro sugerido  
* **Referencias Bibliográficas:** formato APA consistente, mínimo 15-20 referencias incluyendo papers académicos, libros de texto, reportes de instituciones, websites con dates de acceso  
* **Apéndices:** (A) tabla de parámetros completa, (B) detalles técnicos de implementación, (C) código selecto si aplica, (D) outputs adicionales no incluidos en cuerpo principal  
* Implementar figuras profesionales: todas las figuras con captions descriptivos, numeradas secuencialmente, referenciadas en texto, alta resolución, ejes labeled claramente, leyendas incluidas  
* Implementar tablas formales: formato académico con headers, unidades especificadas, fuentes citadas en notas al pie, formato numérico consistente (decimales, separadores)  
* Usar referencias cruzadas: referir a "Figura 3.2", "Tabla 4.1", "Sección 2.3", facilitar navegación, mantener consistencia  
* Implementar estilo académico formal: tercera persona, voz pasiva cuando apropiado, lenguaje técnico preciso, evitar coloquialismos, mantener objetividad  
* Generar PDF final: si LaTeX usar pdflatex con referencias y bibliografía correctamente compiladas, si Word exportar a PDF preservando formato, verificar que todos los links funcionan  
* Implementar revisión de calidad: spell check, grammar check, verificar consistencia de terminología, revisar flujo lógico entre secciones, asegurar que argumentos están claramente articulados

---

### **T-050: README y docs**

**¿En qué consiste?**  
 Actualizar y finalizar toda la documentación del proyecto para que sea completa, clara y profesional, incluyendo README principal, guías de usuario y documentación técnica.

**Relaciones con otras tareas:**

* **Actualiza:** T-002 (documentación inicial)  
* **Depende de:** T-048 (notebook), T-049 (informe), proyecto completo finalizado  
* **Cierre:** Documentación final del proyecto

**Qué se debe implementar:**

* Actualizar README.md principal en raíz del repositorio con contenido comprehensivo  
* **Sección \- Descripción del Proyecto:** párrafo ejecutivo explicando qué es, para qué sirve, qué problema resuelve, audiencia target  
* **Sección \- Características Principales:** lista bullet de capacidades clave del modelo (Monte Carlo con 10k scenarios, pricing estocástico, stress testing con 6 escenarios, AMM simulation, optimización de estructura, etc)  
* **Sección \- Instalación:** instrucciones paso a paso para setup, requirements system (Python 3.10+), clonar repositorio, crear virtual environment, instalar dependencias desde requirements.txt, verificar instalación ejecutando tests  
* **Sección \- Quick Start:** ejemplo mínimo de uso mostrando cómo ejecutar análisis básico, cargar parámetros default, run simulation, visualizar resultados, 5-10 líneas de código suficientes  
* **Sección \- Estructura del Repositorio:** árbol de directorios con descripción de cada carpeta y su propósito (pftoken/ \= source code, tests/ \= test suite, notebooks/ \= análisis, data/ \= inputs, docs/ \= documentación)  
* **Sección \- Documentación Adicional:** links a notebook final, informe PDF, guía de usuario detallada, documentación de API  
* **Sección \- Casos de Uso:** ejemplos concretos de cómo usar el modelo para diferentes propósitos (evaluar estructura tradicional, comparar con tokenizada, optimizar pesos, stress test personalizado)  
* **Sección \- Requisitos y Dependencias:** lista de todas las librerías necesarias con versiones específicas, justificación de por qué cada una es necesaria  
* **Sección \- Testing:** cómo ejecutar test suite, coverage esperado, cómo agregar nuevos tests  
* **Sección \- Contribución:** guidelines si otros quieren contribuir, estándares de código, proceso de pull request, no obligatorio para TP pero profesional incluirlo  
* **Sección \- Licencia:** especificar licencia del proyecto (MIT, GPL, propietaria), términos de uso  
* **Sección \- Autores y Contacto:** nombres de autores, afiliación, emails de contacto  
* **Sección \- Agradecimientos:** reconocer profesores, fuentes de datos, papers que inspiraron trabajo  
* **Sección \- Changelog:** versiones del proyecto con cambios principales en cada versión  
* Crear archivo CONTRIBUTING.md con guías detalladas: código style (PEP 8), convenciones de naming, estructura de commits, process de testing antes de commit  
* Crear archivo API.md documentando funciones públicas principales: para cada función proveer signature, descripción, parámetros con tipos y descripciones, valor de retorno, ejemplos de uso, excepciones que puede lanzar  
* Crear archivo USER\_GUIDE.md con tutorial paso a paso: cómo modificar parámetros del proyecto, cómo agregar nuevos escenarios de stress, cómo customizar visualizaciones, cómo interpretar outputs, troubleshooting de problemas comunes  
* Agregar badges al README: build status (if CI/CD), test coverage percentage, license type, Python version, makes proyecto look professional  
* Verificar que todos los links funcionan: links internos entre docs, links externos a papers y websites, fix broken links  
* Implementar consistency check: verificar que terminología es consistente across todos los documentos, que versiones mencionadas coinciden, que ejemplos funcionan

## **WP-13: TESTING Y QA**

### **T-051: Suite completa de tests**

**¿En qué consiste?**  
 Consolidar y expandir todos los tests del proyecto asegurando cobertura comprehensiva de funcionalidad crítica.

**Relaciones con otras tareas:**

* **Depende de:** T-031 (pipeline MC como major functionality a testear)  
* **Continuo:** Testing debe ocurrir durante todo el desarrollo  
* **Duración:** 5 días según Gantt

**Qué se debe implementar:**

* Crear suite de tests organizada en carpeta tests/ con estructura paralela a pftoken/  
* **tests/test\_cfads.py:** unit tests para módulo CFADS, test\_calculate\_revenues con inputs conocidos verifica output correcto, test\_grace\_period verifica que durante grace solo intereses se pagan, test\_ramping verifica función phi correcta, test\_edge\_cases como CFADS negativo  
* **tests/test\_waterfall.py:** test\_priority\_of\_payments verifica orden correcto (OPEX \> intereses \> reservas \> principal), test\_default\_detection verifica que flags se activan correctamente, test\_covenant\_breach simula DSCR \< threshold y verifica remedies, test\_mra\_funding verifica lógica MRA  
* **tests/test\_pricing.py:** test\_dcf\_pricing con bond simple verifica pricing matches fórmula analítica, test\_yield\_calculation verifica que resolver para YTM funciona, test\_curve\_interpolation verifica smoothness  
* **tests/test\_monte\_carlo.py:** test\_distribution\_properties verifica que samples generados tienen mean/variance correctos, test\_correlation\_matrix verifica que correlaciones se preservan, test\_convergence verifica que resultados stable al aumentar N  
* **tests/test\_merton.py:** test\_distance\_to\_default con valores conocidos, test\_pd\_calculation verifica que PD increase cuando DD decrease, test\_recovery\_waterfall verifica prelación  
* **tests/test\_stress.py:** test\_apply\_shocks verifica que shocks modifican parámetros correctamente, test\_stress\_execution verifica que stress scenarios ejecutan sin crash  
* **tests/test\_amm.py:** test\_constant\_product verifica que k se preserva en swaps, test\_price\_impact calculation correcta, test\_liquidity\_provision verifica que shares se calculan bien  
* **tests/test\_integration.py:** integration tests que ejecutan pipeline completo end-to-end con dataset pequeño, verifican que no hay crashes, outputs están en rangos razonables, tiempo de ejecución aceptable  
* Implementar fixtures usando pytest: crear @pytest.fixture para ProjectParams default, DebtStructure típica, evitar duplicación de setup code  
* Implementar parametrized tests: @pytest.mark.parametrize para correr mismo test con múltiples inputs, ej: test pricing con diferentes tenors, tasas, estructuras  
* Usar mocking para tests rápidos: mock módulos lentos como MC simulation durante unit tests, permite testear lógica sin ejecutar 10k simulaciones  
* Implementar assertions comprehensivas: no solo assert result \== expected, también assert type(result) correcto, assert no NaN/inf en outputs, assert conservación de cantidades (suma de flujos en waterfall)  
* Crear tests de regression: guardar outputs de versión estable, verificar que cambios futuros no rompen funcionalidad existente, alert si métricas clave cambian \> threshold  
* Implementar test coverage measurement usando pytest-cov: ejecutar pytest \--cov=pftoken \--cov-report=html, generar reporte mostrando qué líneas están covered, objetivo \> 80% coverage para code crítico  
* Crear tests de performance: marcar tests lentos con @pytest.mark.slow, medir tiempo de ejecución de funciones críticas, alert si tiempo aumenta significativamente (regression de performance)  
* Implementar continuous testing en CI/CD: configurar GitHub Actions o similar para ejecutar tests automáticamente en cada push, bloquear merge si tests fail, mantener calidad  
* Documentar cada test: docstring explicando qué se testea, por qué es importante, qué edge cases cubre, facilita mantenimiento futuro

---

### **T-052: Code review refactor**

**¿En qué consiste?**  
 Realizar revisión final comprehensiva del código, refactorizar para mejorar calidad, eliminar code smells, optimizar performance, asegurar adherencia a best practices.

**Relaciones con otras tareas:**

* **Depende de:** T-051 (tests pasan antes de refactor)  
* **Final:** Limpieza y polish antes de entrega  
* **Duración:** 3 días según Gantt

**Qué se debe implementar:**

* Ejecutar linters automáticos: pylint, flake8, mypy sobre todo el codebase, corregir warnings y errors, configurar para enforcing PEP 8 style, type hints correctos  
* Implementar revisión de complejidad: usar herramienta como radon para medir complejidad ciclomática, funciones con complejidad \> 10 son candidatas a refactoring, split en sub-funciones más simples  
* Identificar y eliminar código duplicado: buscar bloques de código repetidos, extract a funciones reusables, aplicar DRY principle (Don't Repeat Yourself)  
* Refactorizar funciones largas: funciones \> 50 líneas probablemente hacen demasiado, split en componentes más pequeños con single responsibility, mejorar legibilidad  
* Mejorar naming: variables con nombres no descriptivos (ej: x, tmp, data) renombrar a nombres significativos (ej: tranche\_cashflows, temp\_price, simulation\_results), funciones deben tener nombres verbosos explicando qué hacen  
* Optimizar imports: eliminar imports no usados, organizar en orden (standard library, third-party, local), usar imports absolutos cuando posible  
* Implementar lazy evaluation: calcular valores solo cuando necesarios, avoid computations que luego no se usan, especialmente en loops  
* Optimizar loops críticos: identificar loops que ejecutan muchas veces (ej: dentro de MC), vectorizar usando NumPy, eliminar Python loops cuando posible, puede mejorar performance 10-100x  
* Implementar caching de resultados costosos: usar @lru\_cache para funciones puras que se llaman repetidamente con mismos inputs (ej: cálculo de discount factors)  
* Refactorizar clases grandes: clases con muchos métodos (\> 20\) posiblemente violan single responsibility, considerar split en clases más cohesivas  
* Mejorar error handling: reemplazar bare except: con excepciones específicas, agregar mensajes de error descriptivos, raise excepciones custom en lugar de genéricas  
* Implementar logging strategically: agregar logging.info en puntos clave del flujo, logging.debug para detalles útiles en debugging, logging.warning para situaciones anormales, configurar nivel apropiadamente  
* Documentar funciones públicas: todas las funciones públicas deben tener docstrings en formato NumPy/Google style, describir parámetros, retorno, raises, examples  
* Eliminar código comentado: código obsoleto en comentarios debe ser eliminado, mantiene repo limpio, confusión innecesaria  
* Implementar consistencia de estilo: verificar que todo el código sigue mismo style guide, formatear usando black o autopep8 para consistencia automática  
* Optimizar uso de memoria: identificar objetos grandes que se mantienen en memoria innecesariamente, usar generators en lugar de listas cuando posible, del variables cuando ya no se necesitan  
* Refactorizar basado en feedback de tests: áreas del código donde tests fallaron frecuentemente probablemente tienen design issues, refactor para hacer más testeable  
* Crear checklist de quality gates: código debe pasar tests, linters, no memory leaks, performance aceptable, documentation completa, antes de considerar done  
* Documentar decisiones de refactoring: mantener log de cambios mayores, razón del cambio, impacto en performance/legibilidad, facilita entendimiento futuro

---

**FIN DE LA GUÍA DE IMPLEMENTACIÓN \- 62 TAREAS TOTALES**

* 

