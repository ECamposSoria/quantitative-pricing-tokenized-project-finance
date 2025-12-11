# Quantitative Pricing of Tokenized Project Finance

**Tesis de Maestría en Finanzas Cuantitativas**

Framework cuantitativo para el pricing de deuda tokenizada en project finance, aplicado a una constelación satelital LEO IoT. El modelo integra riesgo crediticio estructural, simulación Monte Carlo, liquidez AMM y mecanismos contingentes habilitados por smart contracts.

> **Para análisis detallado, visualizaciones y resultados completos, ver el notebook [`notebooks/TP_Quant_Final.ipynb`](notebooks/TP_Quant_Final.ipynb)**

---

## Reproducción de Resultados

### Requisitos
- Docker 20.x+
- 4GB RAM mínimo

### 1. Construir imagen Docker

```bash
docker build -t qptf-quant_token_app:latest .
```

### 2. Generar resultados (JSON)

```bash
docker run --rm \
  -v "$(pwd)":/app -w /app \
  qptf-quant_token_app:latest \
  python scripts/demo_risk_metrics.py --sims 10000 --include-collar
```

Genera `outputs/leo_iot_results.json` con:
- Simulación Monte Carlo (10,000 paths)
- Métricas de riesgo por tranche (PD, LGD, EL, VaR, CVaR)
- Stress testing (16 escenarios)
- Comparación AMM V2 vs V3
- Análisis de hedging (Cap vs Collar)
- Síntesis WACD
- Comparación estructura tradicional vs tokenizada

### 3. Ejecutar notebook

```bash
docker run --rm \
  -v "$(pwd)":/app -w /app \
  qptf-quant_token_app:latest \
  jupyter nbconvert --to notebook --execute --inplace notebooks/TP_Quant_Final.ipynb
```

### 4. Exportar a HTML (opcional)

```bash
docker run --rm \
  -v "$(pwd)":/app -w /app \
  qptf-quant_token_app:latest \
  jupyter nbconvert --to html notebooks/TP_Quant_Final.ipynb --output-dir=outputs/
```

### 5. Ejecutar tests

```bash
docker run --rm \
  -v "$(pwd)":/app -w /app \
  qptf-quant_token_app:latest \
  pytest tests/ -v
```

---

## Marco Teórico Implementado

### 1. Modelo de Riesgo Crediticio: Merton Extendido

**Fundamento:** El modelo estructural de Merton (1974) trata el equity como una opción call sobre los activos de la empresa con strike igual a la deuda.

**Implementación:** `pftoken/models/merton.py`

**Distancia a Default:**
$$DD = \frac{\ln(V_A/D) + (\mu - 0.5\sigma^2)T}{\sigma\sqrt{T}}$$

**Probabilidad de Default:**
$$PD = \Phi(-DD)$$

Donde:
- $V_A$: Valor de activos (NPV de CFADS)
- $D$: Valor facial de deuda por tranche
- $\mu$: Drift del proceso de activos
- $\sigma$: Volatilidad de activos (calibrada por tranche)
- $T$: Tiempo a madurez

**Extensiones implementadas:**

1. **Path-Dependent (First-Passage Barrier)** - Black & Cox (1976):
   $$\tau = \inf\{t : V_t < B_t\}$$
   El default ocurre en el primer cruce de la barrera, no solo al vencimiento.

2. **Regime-Switching (Markov 2-estados)** - Hamilton (1989):
   $$P = \begin{pmatrix} 0.95 & 0.05 \\ 0.20 & 0.80 \end{pmatrix}$$

   | Régimen | Drift (μ) | Volatilidad (σ) | Prob. Estacionaria |
   |---------|-----------|-----------------|-------------------|
   | Normal  | 8%        | 25%             | 80%               |
   | Stress  | 2%        | 40%             | 20%               |

---

### 2. Simulación Monte Carlo

**Fundamento:** Propagación de incertidumbre mediante muestreo estocástico de variables de entrada para generar distribución de outcomes.

**Implementación:** `pftoken/simulation/monte_carlo.py`

**Variables estocásticas:**
- Revenue: Lognormal (μ=5%, σ=15%)
- OPEX: Lognormal (μ=3%, σ=10%)
- Tasas de interés: Vasicek con reversión a media

**Técnicas de reducción de varianza:**
- Antithetic variates: para cada path con shocks ε, se genera path con -ε
- Correlación via Cholesky: matriz de correlación entre variables

**Outputs:**
- Fan chart de DSCR (P5, P25, P50, P75, P95)
- Probabilidad de breach acumulativa
- Distribución de valor de activos

---

### 3. Valoración de Renta Fija: Bootstrapping

**Fundamento:** Construcción de curva zero mediante inversión secuencial de precios de instrumentos de mercado (Hull, 2018).

**Implementación:** `pftoken/pricing/zero_curve.py`

**Ecuación de valoración de bonos:**
$$P = \sum_{t=1}^{T} C_t \cdot DF(t) + Principal \cdot DF(T)$$

**Bootstrapping (asumiendo P=100):**
$$DF(T) = \frac{100 - \sum_{t=1}^{T-1} C_t \cdot DF(t)}{C_T + Principal}$$

**Conversión a tasa zero:**
$$z_T = (DF(T))^{-1/T} - 1$$

**Datos:** Curva SOFR de FRED (Federal Reserve Economic Data), series DGS.

---

### 4. Derivados de Tasa de Interés: Black-76

**Fundamento:** Modelo Black (1976) para valoración de opciones sobre forwards/futuros.

**Implementación:** `pftoken/derivatives/`

**Valoración de Caplet:**
$$\text{Caplet} = DF(T) \cdot [F \cdot N(d_1) - K \cdot N(d_2)]$$

Donde:
$$d_1 = \frac{\ln(F/K) + 0.5\sigma^2 T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}$$

- $F$: Forward rate
- $K$: Strike del cap
- $\sigma$: Volatilidad implícita (20% flat)
- $DF(T)$: Factor de descuento

**Instrumentos implementados:**
- Interest Rate Cap (`interest_rate_cap.py`)
- Interest Rate Floor (`interest_rate_floor.py`)
- Interest Rate Collar (`collar.py`)
- Zero-cost collar finder

---

### 5. Modelo AMM: Uniswap V2/V3

**Fundamento:** Automated Market Makers para provisión de liquidez descentralizada.

**Implementación:** `pftoken/amm/core/`

**Uniswap V2 - Constant Product (Buterin et al., 2018):**
$$x \cdot y = k$$

**Uniswap V3 - Concentrated Liquidity (Adams et al., 2021):**
$$L = \frac{\Delta y}{\sqrt{P_{upper}} - \sqrt{P_{lower}}}$$

Donde:
- $L$: Liquidez concentrada en el rango
- $P_{upper}, P_{lower}$: Límites del rango de precio

**Ventaja para RWA:** Tokens de deuda operan near-par (±5%), permitiendo concentrar liquidez y lograr 5x eficiencia de capital vs V2.

---

### 6. Spread de Liquidez: Bao-Pan-Wang

**Fundamento:** Cuantificación de la prima de iliquidez en spreads de bonos corporativos.

**Referencia:** Bao, Pan & Wang (2011), "The Illiquidity of Corporate Bonds"

**Modelo:**
$$\text{Spread}_{liquidez} = \lambda \cdot \gamma$$

Donde:
- $\lambda$: Carga de iliquidez (factor de mercado, típicamente 0.5)
- $\gamma$: Bid-ask spread del instrumento

**Aplicación:**
| Mercado | Bid-Ask (γ) | Spread Liquidez |
|---------|-------------|-----------------|
| Tradicional (sindicado) | 150 bps | 75 bps |
| Tokenizado V3 | 10 bps | 5 bps |

---

### 7. Optimización Multi-Objetivo: Frontera de Pareto

**Fundamento:** Optimización con múltiples objetivos en conflicto donde no existe un único óptimo.

**Implementación:** `pftoken/risk/efficient_frontier.py`

**Objetivos:**
1. Minimizar Riesgo (CVaR 95%)
2. Maximizar Retorno Esperado
3. Minimizar WACD

**Dominancia de Pareto:**
Un portfolio A domina a B si:
- A es mejor o igual en TODAS las dimensiones
- A es estrictamente mejor en AL MENOS una dimensión

Los portfolios no dominados forman la **Frontera de Pareto**.

---

### 8. Decomposición de Spreads Tokenizados

**Implementación:** `pftoken/pricing/spreads/`

$$\text{Spread}_{total} = \text{Credit} + \text{Liquidity} + \text{Origination} + \text{Servicing} + \text{Infrastructure}$$

**Componentes del delta tokenizado:**

| Componente | Δ (bps) | Fuente |
|------------|---------|--------|
| Liquidez | -70 | AMM V3 vs mercado sindicado |
| Operacional | -3.5 | Automatización smart contracts |
| Transparencia | -20 | Reducción asimetría información |
| Infraestructura | +12 | Costos blockchain/oracle |
| Regulatorio | +7.5 | Prima por incertidumbre legal |

---

## Bibliografía

### Riesgo Crediticio y Modelos Estructurales

- **Merton, R.C. (1974)**. On the pricing of corporate debt: The risk structure of interest rates. *Journal of Finance*, 29(2), 449-470. https://doi.org/10.1111/j.1540-6261.1974.tb03058.x

- **Black, F., & Cox, J.C. (1976)**. Valuing corporate securities: Some effects of bond indenture provisions. *Journal of Finance*, 31(2), 351-367. https://doi.org/10.1111/j.1540-6261.1976.tb01891.x

- **Hamilton, J.D. (1989)**. A new approach to the economic analysis of nonstationary time series and the business cycle. *Econometrica*, 57(2), 357-384. https://doi.org/10.2307/1912559

### Project Finance

- **Yescombe, E.R. (2013)**. *Principles of Project Finance* (2nd ed.). Academic Press.

- **Gatti, S. (2018)**. *Project Finance in Theory and Practice* (3rd ed.). Academic Press.

### Liquidez y Spreads

- **Bao, J., Pan, J., & Wang, J. (2011)**. The illiquidity of corporate bonds. *Journal of Finance*, 66(3), 911-946. https://doi.org/10.1111/j.1540-6261.2011.01655.x

- **Amihud, Y. (2002)**. Illiquidity and stock returns: Cross-section and time-series effects. *Journal of Financial Markets*, 5(1), 31-56.

### Derivados y Valoración

- **Black, F. (1976)**. The pricing of commodity contracts. *Journal of Financial Economics*, 3(1-2), 167-179. https://doi.org/10.1016/0304-405X(76)90024-6

- **Hull, J.C. (2018)**. *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

### DeFi y Tokenización

- **Adams, H., Zinsmeister, N., Salem, M., Keefer, R., & Robinson, D. (2021)**. *Uniswap v3 Core* [Whitepaper]. Uniswap Labs. https://uniswap.org/whitepaper-v3.pdf

- **Buterin, V., et al. (2018)**. *Uniswap v2 Core* [Whitepaper]. https://uniswap.org/whitepaper.pdf

### Datos de Mercado

- **Federal Reserve Economic Data (FRED)**. Treasury yield curves, DGS series. https://fred.stlouisfed.org/

- **DefiLlama**. Centrifuge/Tinlake protocol data. https://defillama.com/protocol/centrifuge

---

## Estructura del Repositorio

```
quantitative-pricing-tokenized-project-finance/
├── pftoken/                    # Paquete Python principal
│   ├── models/                 # CFADS, Merton, ratios financieros
│   ├── simulation/             # Monte Carlo, regime-switching
│   ├── pricing/                # Curva zero, WACD, spreads
│   ├── derivatives/            # Cap, Floor, Collar (Black-76)
│   ├── amm/                    # Uniswap V2/V3, slippage, IL
│   ├── waterfall/              # Cascade de pagos, contingente
│   ├── risk/                   # PD, LGD, VaR, CVaR, Pareto
│   ├── stress/                 # Stress testing, reverse stress
│   └── viz/                    # Plotly dashboards
├── notebooks/
│   └── TP_Quant_Final.ipynb    # Notebook principal con análisis completo
├── scripts/
│   └── demo_risk_metrics.py    # Script de generación de resultados
├── data/input/leo_iot/         # Datos del caso de estudio
├── outputs/
│   └── leo_iot_results.json    # Resultados consolidados
├── tests/                      # 77 archivos de tests
└── docs/                       # Documentación técnica adicional
```

---

## Resultados Principales

| Métrica | Tradicional | Tokenizado | Tokenizado + Collar | Δ Total |
|---------|-------------|------------|---------------------|---------|
| **WACD** | 738 bps | 652 bps | 678 bps | **-60 bps** |
| **Prob. Breach** | 46.7% | 6.6% | 2.3% | **-95%** |
| **IRR Equity** | ~8.5% | 10.56% | 10.56% | **+2.1 pp** |
| **Payback** | Año 11 | Año 9 | Año 9 | **-2 años** |

> Ver notebook para análisis detallado, visualizaciones interactivas y derivación completa de resultados.

---

## Licencia

MIT License - Ver archivo LICENSE para detalles.
