# Tokenized Spread Decomposition

Este documento describe cómo se derivan los spreads tokenizados de cada componente
(crédito, liquidez, originación, servicing e infraestructura) y cómo se alimenta
el delta que utiliza `WACDCalculator`. Todos los datos provienen de módulos
versionables (Tinlake, Etherscan/Chainlink, literatura PF) para evitar supuestos
arbitrarios.

## Arquitectura

| Módulo | Archivo | Fuente principal |
| --- | --- | --- |
| `CreditSpreadComponent` | `pftoken/pricing/spreads/credit.py` | Merton PD/LGD + delta de transparencia (Allen et al. 2022, Zetzsche et al. 2020) |
| `LiquiditySpreadComponent` | `pftoken/pricing/spreads/liquidity.py` | Datos Tinlake (TVL, volumen, ticket) vía DeFiLlama + supuestos OECD |
| `OriginationServicingComponent` | `pftoken/pricing/spreads/costs.py` | Gatti (2018), World Bank (2024), MSLP/Florida/Leon HFAs |
| `BlockchainInfrastructureTracker` | `pftoken/pricing/spreads/infrastructure.py` | Gas/oracle (Etherscan multi-chain, Chainlink), monitoreo interno |
| `TokenizedSpreadModel` | `pftoken/pricing/spreads/tokenized.py` | Coordina todas las piezas y produce la descomposición delta |

## Fórmulas clave

### Crédito

```
credit_trad = ((PD * LGD / duración) / (1 - PD)) * λ
credit_token = max(credit_trad + Δ_transparencia, 0)
```

- `PD`, `LGD` del `MertonModel`.
- Duración = `TranchePricingMetrics.macaulay_duration` (fallback tenor).
- `λ` default 0.10 (`TokenizedSpreadConfig`).
- `Δ_transparencia` proviene de estudios DeFi (Allen et al., Zetzsche et al.)
  y representa la reducción por menor asimetría informativa (por defecto −30 bps).

### Liquidez

1. **Prima tradicional**: depende del tamaño del tramo (`impact_coeff`) y sirve
   como proxy (75 bps ≈ baseline PF).
2. **Datos Tinlake** (`https://api.llama.fi/protocol/centrifuge`):
   - `TVL ≈ 1.45 B`, `avg_daily_volume ≈ 2.4 M`, `avg_ticket ≈ 15.5 M`.
   - Turnover observado = `(avg_daily_volume × 365) / TVL`.
3. **Factor de microestructura**:

```
turnover_ratio = max(turnover_observado / turnover_tradfi, 0.1)
turnover_factor = 1 / max(sqrt(turnover_ratio), 1)
base_factor = (ticket_multiplier) / (depth_multiplier × volume_multiplier)
factor_total = max(base_factor × turnover_factor, min_liquidity_factor)
```

4. **Prima tokenizada** = `prima_tradicional × factor_total × (1 - α)`.

> **Operación Tinlake:** el snapshot vivo se guarda en
> `data/derived/liquidity/tinlake_metrics.json` y se acompaña con metadatos en
> `data/derived/liquidity/tinlake_metadata.json`. Si la API no responde y no hay
> cache, se emplea un fallback conservador (TVL≈500 M, volumen≈0.75 M,
> ticket≈15 M). Use `PYTHONPATH=. python scripts/manage_tinlake_snapshot.py --status`
> para revisar la edad; si supera 7 días, el comando mostrará un warning con la
> instrucción exacta para forzar el refresh.

### Origination

- Fee upfront (100-300 bps) → se toma 150 bps y se amortiza en
  `origination_fee_amortization_years` (10 años por defecto).
- Ahorro = `amortizado × β` (β=0.5 ⇒ automatización del 50 % del flujo de trabajo).

### Servicing

- Baseline = `paying_agent_bps + compliance_audit_bps` (≈25 bps confirmados por MSLP, Florida Housing, Leon County, World Bank).
- Ahorro = `baseline × γ` (γ=1.0 por defecto) pero se mantiene un residual
  (`servicing_residual_bps`, default 5 bps) para cubrir governance/oracles.
- Con los valores actuales (`15 + 7.5 = 22.5 bps`), el delta efectivo es
  −17.5 bps (22.5 trad vs. 5 tokenizado). Si se quisiera replicar los −20/−25 bps
  de los briefs anteriores, habría que incrementar el baseline regulatorio a
  25 bps o eliminar el residual.

### Infraestructura

- `gas_cost_bps = (annual_tx × gas_per_tx × gas_price × token_price) / principal × 10,000`.
- Oracles (Chainlink) y monitoreo se suman en bps.
- Defaults ajustados a un flujo realista (≈200 tx/año). Los datos en vivo se
  extraen de Etherscan V2 (multi-chain) con fallback a endpoints legacy o RPC.
- Prima de riesgo: `max(0, (5 - score_pesado)) × 4 bps`, donde
  `score_pesado = 0.4·security + 0.3·liquidity + 0.2·regulation + 0.1·ux`.
  Esta fórmula se documenta en el CSV exportado junto con las fuentes utilizadas
  (Chainlink para oráculos y los gas trackers públicos).

## Delta tokenizado derivado

La convención de signos es `Δ = tokenized − tradicional`. Valores negativos
representan ahorros para la versión tokenizada. Con la curva USD
`usd_combined_curve_2025-11-07.csv`, `β=0.5`, `γ=1.0` y la calibración Tinlake
vigente, `TokenizedSpreadModel.compute_delta_decomposition()` produce:

| Componente | Trad (bps ponderado) | Tok (bps ponderado) | Δ (bps) |
| --- | --- | --- | --- |
| Crédito | 2.43 | 0.00 | −2.43 |
| Liquidez | 55.63 | 5.56 | −50.06 |
| Origination | 15.00 | 7.50 | −7.50 |
| Servicing | 22.50 | 5.00 | −17.50 |
| Infraestructura | 0.00 | 11.66 | +11.66 |
| **Total ponderado** | 95.58 | 29.72 | **−65.83** |

El modelo recalcula automáticamente esta tabla cuando cambian los insumos y el
resultado ponderado se refleja en `wacd.compare_traditional_vs_tokenized()`. Si
se desea forzar los supuestos originales (−75 / −25 bps), basta con fijar
`PricingContext.use_computed_deltas=False` y establecer los overrides deseados.
> Estos valores son dinámicos: varían con el snapshot Tinlake, `β`, la red
> blockchain seleccionada y cualquier override. Para auditoría, consulte los CSV
> exportados en `data/derived/delta_decomposition/` y las sensibilidades en
> `data/derived/sensitivities/`, donde cada corrida queda sellada con timestamp
> y hash de configuración.

## Sensitivity Analysis

`TokenizedSpreadModel.simulate_delta_scenarios()` aplica un modelo de escalado
lineal sobre la descomposición consolidada:

- `liquidity_scale`: multiplica `weighted_delta_liquidity_bps`.
- `beta_override`: recalcula el ahorro de originación escalando por
  `beta_override / config.origination_beta`.
- `infra_tx_multiplier`: multiplica `weighted_delta_infrastructure_bps` (positivo
  si la infraestructura tokenizada suma costo adicional).
- Crédito y servicing permanecen constantes (se omite riesgo dual para mantener
  la traza simple en WP-04).

Los 7 escenarios base (QF-1) son:

| Escenario | liquidity_scale | beta_override | infra_tx_multiplier |
| --- | --- | --- | --- |
| Base | 1.0 | — | 1.0 |
| Tinlake TVL -50 % | 0.5 | — | 1.0 |
| Tinlake TVL +50 % | 1.5 | — | 1.0 |
| Beta = 0.3 | 1.0 | 0.3 | 1.0 |
| Beta = 0.7 | 1.0 | 0.7 | 1.0 |
| Infra × 2 | 1.0 | — | 2.0 |
| Stressed | 0.5 | 0.3 | 2.0 |

Cada corrida produce una tabla (`SensitivityScenario`) con los deltas por
componente, el total en bps **y el WACD tokenizado resultante** (columnas
`tokenized_wacd` y `wacd_delta_bps`), exportada automáticamente a
`data/derived/sensitivities/wacd_delta_sensitivity_<timestamp>.csv`. En paralelo,
`WACDCalculator.compare_traditional_vs_tokenized()` exporta la matriz
consolidada a `data/derived/delta_decomposition/wacd_delta_breakdown_<timestamp>.csv`
(con metadatos JSON) para mantener la trazabilidad histórica.

## Configuración

```python
from pftoken.pricing.spreads import TokenizedSpreadConfig
config = TokenizedSpreadConfig(
    credit_transparency_delta_bps=-30,
    traditional_liquidity_premium_bps=75,
    tradfi_turnover_ratio=0.05,
    origination_beta=0.5,
    origination_fee_amortization_years=10,
    servicing_gamma=1.0,
    servicing_residual_bps=5,
    blockchain_network="Ethereum",
)
```

## Reporting & Export

- `TokenizedSpreadModel.reporting_payload()` devuelve los spreads tradicionales
  y tokenizados por componente.
- `TokenizedSpreadModel.compute_delta_decomposition()` agrega por tramo y
  permite exportar la matriz a CSV/JSON mediante
  `WACDCalculator.export_delta_decomposition()`.

## Fuentes

- **Crédito**: Oxford Sustainable Finance (2024); IEA (2020) para primas PF;
  Allen et al. (2022), Zetzsche et al. (2020) para transparencia DeFi.
- **Liquidez**: OECD (2024), Allen et al. (2022) para reducción de fricción;
  datos Tinlake (DeFiLlama) para TVL/volumen/ticket.
- **Origination/Servicing**: Gatti (2018), Esty & Sesia (2011), World Bank (2024),
  MSLP (2022), Florida Housing (2022), Leon County HFA (2024).
- **Infraestructura**: Etherscan V2 (gas oracle), Chainlink documentation, costos
  internos de monitoreo.
- **Space finance / LGD**: Jakhu et al. (2017), Sarret (2021), Sorge (2004) —
  usados en otros apartados del proyecto para contextualizar spreads y LGD.
