# Análisis WP-04 Actualizado (2025-11-22)

## 1. CURVA ZERO CUPÓN (Actualizada)
**Fuente:** [usd_combined_curve_2025-11-20.csv](/app/data/derived/market_curves/usd_combined_curve_2025-11-20.csv) — FRED DGS

### Spot Rates (%)

| Tenor | 1Y | 2Y | 3Y | 5Y | 7Y | 10Y | 15Y | 20Y | 30Y |
|---|---|---|---|---|---|---|---|---|---|
| **Rate** | 3.65% | 3.55% | 3.56% | 3.68% | 3.87% | 4.10% | 4.39% | 4.68% | 4.73% |

## 2. ESTRUCTURA DE TRAMOS
**Fuente:** [data/input/leo_iot/tranches.csv](data/input/leo_iot/tranches.csv)

| Tramo | Principal | Cupón | Peso | Gracia | Tenor | Amortización |
|-------|-----------|-------|------|--------|-------|--------------|
| **Senior** | $43,200,000.00 | 6.0% | 60% | 4 años | 15 años | Sculpted |
| **Mezzanine** | $18,000,000.00 | 8.5% | 25% | 4 años | 15 años | Amortizing |
| **Subordinated** | $10,800,000.00 | 11.0% | 15% | 4 años | 15 años | Bullet |
| **Total** | $72,000,000.00 | - | 100% | - | - | - |

## 3. PRICING POR TRAMO (Con Curva de Mercado)
**Haircut:** 25% — **Time to Liquidation:** 1.5 años

| Tramo | Price/Par | Present Value | YTM | Duración | LGD |
|-------|-----------|---------------|-----|----------|-----|
| **Senior** | 1.14115 | $49,297,729.83 | 3.9219% | 6.7347 | 0.000 |
| **Mezzanine** | 1.32727 | $23,890,925.70 | 3.9474% | 6.7949 | 0.555 |
| **Subordinated** | 1.55772 | $16,823,382.64 | 3.9963% | 7.1812 | 1.000 |

## 4. SPREADS POR TRAMO (bps)

| Tramo | Tradicional | Tokenizado | Delta |
|-------|-------------|------------|-------|
| **Senior** | 117.50 bps | 30.68 bps | -86.82 bps |
| **Mezzanine** | 73.75 bps | 24.76 bps | -48.99 bps |
| **Subordinated** | 65.93 bps | 23.07 bps | -42.86 bps |

## 5. DELTA DECOMPOSITION PONDERADA

| Componente | Delta (bps) | Fuente |
|------------|-------------|--------|
| **Crédito** | -5.70 bps | Floor 5.0 bps + transparencia -30.0 bps |
| **Liquidez** | -48.10 bps | Tinlake TVL calibration (DeFiLlama) |
| **Originación** | -7.50 bps | β = 0.5 (50% automation) |
| **Servicing** | -17.50 bps | γ = 1.0 + residual 5.0 bps |
| **Infraestructura** | 8.03 bps | Ethereum gas/oracle/monitoring |
| **TOTAL** | **-70.77 bps** | Before-tax weighted |

## 6. WACD FINAL
**Tax Rate:** 25%

| Métrica | Valor |
|---------|-------|
| **WACD Tradicional (after-tax)** | 6.2725% |
| **WACD Tokenizado (after-tax)** | 5.7417% |
| **Delta After-Tax** | -0.5308% (-53.08 bps) |
| **Delta Before-Tax** | -70.77 bps |

**Verificación:** Delta after-tax = -70.77 × (1 - 0.25) = -53.08 bps

## 7. DATOS TINLAKE (DeFiLlama)

| Métrica | Valor |
|---------|-------|
| TVL | $1,447,607,220.00 |
| Daily Volume | $186,114.67 |
| Avg Pool Ticket | $15,673,931.80 |
| Source | api |
| Timestamp | 2025-11-22T22:24:44.831935+00:00 |

## 8. COSTOS INFRAESTRUCTURA BLOCKCHAIN

| Network | TX/año | Gas/TX | Gas Price | Oracle | Monitoring | Total |
|---------|--------|--------|-----------|--------|------------|-------|
| Ethereum | 200 | 110,000 | 25.0 gwei | 3.0 bps | 2.0 bps | **7.97 bps** |
| Arbitrum | 200 | 35,000 | 1.5 gwei | 4.0 bps | 2.5 bps | **13.50 bps** |
| Polygon | 200 | 45,000 | 0.9 gwei | 4.0 bps | 2.5 bps | **13.58 bps** |
| Optimism | 200 | 40,000 | 1.2 gwei | 4.5 bps | 2.5 bps | **14.44 bps** |
| Base | 200 | 28,000 | 1.0 gwei | 4.0 bps | 2.2 bps | **14.08 bps** |
