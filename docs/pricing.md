# WP-04 – Pricing & Curves

WP-04 extiende el pipeline determinístico (WP-02/03) con módulos de
valuación por tramo, construcción de curvas y comparaciones tokenizadas.
Todo el flujo mantiene la tolerancia de `0.01%` frente a benchmarks/Excel.

## Componentes

| Módulo | Descripción |
| --- | --- |
| `pftoken.pricing.zero_curve.ZeroCurve` | Bootstrapping de curvas spot/zero (depósitos + swaps), interpolación log-lineal, cálculo de forwards y shocks paralelos/no paralelos. |
| `pftoken.pricing.base_pricing.PricingEngine` | Extrae los cash flows por tramo desde `WaterfallResult`, descuenta con la `ZeroCurve` y reporta precio limpio, YTM (scipy `brentq`), duración de Macaulay/Modificada y convexidad. Incluye utilidades Matplotlib para visualizar cascadas y la curva. |
| `pftoken.pricing.wacd.WACDCalculator` | Calcula el costo promedio ponderado de la deuda (after-tax) y compara escenarios tradicional vs. tokenizado usando los deltas configurados en `pftoken.pricing.constants`. |
| `pftoken.pricing.collateral_adjust.CollateralAnalyzer` | Aplica haircuts y descuentos por tiempo de liquidación al pool de colateral y propaga recoveries/LGD por seniority. |
| `pftoken.pricing.curve_loader.load_zero_curve_from_csv` | Construye la curva a partir de un CSV versionado (ej. `data/derived/market_curves/us_treasury_par_yield_*.csv`, `usd_swap_rates_*.csv` o curvas combinadas). |
| `pftoken.pricing.constants` | Centraliza tolerancias, tasas impositivas, haircuts y parámetros tokenizados (`PricingContext`). |
| `pftoken.pricing.spreads.TokenizedSpreadModel` | Descompone los spreads por tramo (crédito, liquidez, originación, servicing e infraestructura) y alimenta el WACD. Ver `docs/tokenized_spread_decomposition.md` para fórmulas y calibración. |

Todos los módulos exportan sus clases principales desde `pftoken.pricing`.

## Flujo típico

```python
from pathlib import Path
from pftoken.pipeline import FinancialPipeline
from pftoken.pricing import (
    CollateralAnalyzer,
    PricingEngine,
    ZeroCurve,
    CurveInstrument,
)

# 1) Cargar el dataset canónico
pipeline = FinancialPipeline(data_dir=Path("data/input/leo_iot"))
outputs = pipeline.run()

# 2) Bootstrapping rápido (depósitos anuales planos al 5.5 %)
curve = ZeroCurve.bootstrap(
    [CurveInstrument(maturity_years=year, rate=0.055) for year in range(1, 16)],
    currency="USD",
)

# 3) Analizar colateral y descontar flujos por tramo
collateral = CollateralAnalyzer(pipeline.debt_structure, curve)
engine = PricingEngine(curve, collateral_analyzer=collateral)
pricing = engine.price_from_waterfall(outputs["waterfall"], pipeline.debt_structure)
# Payload listo para JSON/CSV (incluye ytm_label y curve_rate)
pricing_payload = engine.price_from_waterfall(
    outputs["waterfall"],
    pipeline.debt_structure,
    as_dict=True,
)
print(pricing_payload["senior"]["ytm_label"])  # "risk-free YTM"

# 4) Comparar WACD tradicional vs tokenizado
from pftoken.pricing import WACDCalculator
wacd = WACDCalculator(pipeline.debt_structure)
print(wacd.compare_traditional_vs_tokenized())
```

### Curvas versionadas (FRED)

`data/derived/market_curves/` almacena snapshots descargados de FRED:

- `us_treasury_par_yield_<fecha>.csv`: nodos Par Yield (tratados como depósitos).
- `usd_swap_rates_<fecha>.csv`: nodos swap (DSWP*, `instrument_type=swap`).
- `usd_combined_curve_<fecha>.csv`: mezcla ambos (depósitos cortos + swaps largos).

Todos comparten el formato `maturity_years`, `rate` (decimal) y, opcionalmente,
`instrument_type`/`payment_frequency`. El loader es:

```python
from pathlib import Path
from pftoken.pricing import load_zero_curve_from_csv

curve = load_zero_curve_from_csv(
    Path("data/derived/market_curves/usd_combined_curve_2016-10-28.csv"),
    currency="USD",
)
```

Si el CSV incluye nodos swap sin toda la información necesaria para bootstrap,
el loader cae automáticamente a tratarlos como tasas cero, garantizando que la
curva siempre se pueda construir. Actualizar la curva = regenerar el CSV y
reemplazar el archivo versionado.

### Visualizaciones

- `PricingEngine.plot_tranche_cashflows(...)` devuelve un `matplotlib.figure.Figure`
  con barras apiladas (interés vs. principal).
- `PricingEngine.plot_discount_curve()` muestra la curva subyacente.

Los tests solo validan metadatos (cantidad de ejes), evitando snapshots PNG.

## Configuración

- Las tolerancias y parámetros por defecto viven en `pftoken.pricing.constants`.
- Cualquier override puede hacerse vía `PricingContext` o argumentos explícitos
  (ej.: `CollateralAnalyzer(..., custom_haircuts={"senior": 0.2})`).
- No se añadieron nuevos archivos JSON; los datasets inmutables siguen bajo
  `data/input/leo_iot/`.
- Los spreads tokenizados usan `TokenizedSpreadConfig` para exponer λ/α/β/γ y los
  benchmarks de fees/infraestructura. Los CSV reproducibles se generan en
  `data/derived/tokenized_infra_costs.csv` y se pueden refrescar con
  `python scripts/update_blockchain_infra.py`, que consume APIs públicas
  (Etherscan API V2 multi-chain + CoinGecko; si V2 no expone el módulo para una
  red, el script cae automáticamente en los endpoints “legacy”, gas stations o
  RPCs y deja el mensaje exacto en el CSV) para mantener trazabilidad de
  gas/oracle/monitoring.
  Además, la sección de liquidez se auto-calibra con datos “live” de Tinlake
 (DeFiLlama `https://api.llama.fi/protocol/centrifuge`) y guarda snapshots en
  `data/derived/liquidity/tinlake_metrics.json`, razón por la cual ya no es
  necesario ajustar manualmente los multiplicadores salvo que quieras forzar
  valores custom (`auto_calibrate_liquidity=False`).
- El delta tokenizado del WACD se deriva automáticamente de los componentes
  (liquidez, origination, servicing, infraestructura). Si
  `PricingContext.use_computed_deltas=True`, el `WACDCalculator` usa ese delta
  derivado y expone la descomposición completa (incluyendo export a CSV/JSON);
  siempre queda disponible un modo override para reproducir el supuesto manual.

## Tests

```
pytest tests/test_pricing tests/test_integration/test_pricing_pipeline.py
```

Los tests cubren:

- Bootstrapping, interpolación y shocks (`test_zero_curve.py`).
- PricingEngine (precio/YTM/duración + plots) (`test_pricing_engine.py`).
- WACD y Collateral (`test_wacd.py`, `test_collateral_analyzer.py`).
- Integración completa: FinancialPipeline → PricingEngine/WACD con la data canónica
  (`tests/test_integration/test_pricing_pipeline.py`).

Cada aserción relevante usa `rel=1e-4` para respetar el umbral de 0.01 %.

## Nota sobre YTM

Los YTM que reporta `PricingEngine` provienen de descontar los cash flows contra
la curva libre de riesgo del snapshot (`usd_combined_curve_2025-11-07.csv`).
Como los cupones de los tramos (6‑11 %) superan ampliamente esa curva, los
precios limpiezan sobre par y los yields resultantes son menores al cupón. Los
spreads crediticios y de liquidez se incorporan en el delta tokenizado (vía
`TokenizedSpreadModel`/`WACDCalculator`), no en el solver de YTM.

### YTM vs. Credit Spread

`TranchePricingMetrics` ahora incluye metadata explícita:

- `ytm_label`: identifica que el valor reportado es `risk-free YTM`.
- `risk_free_curve_rate`: tasa spot de la curva usada para descontar (tenor del tramo).
- `spread_over_curve`: brecha `curve_rate - ytm`, útil para comparar con el spread crediticio calculado en `TokenizedSpreadModel`.
- `explanatory_note`: recordatorio textual de que el solver opera con la curva libre de riesgo y que el spread crediticio vive fuera del YTM.

El solver `_calculate_ytm` usa `scipy.optimize.brentq` para resolver
`sum(cf_t / (1+r)^t) = price_clean` y únicamente se alimenta de la curva libre
de riesgo (no del spread tokenizado).

Para exportar la metadata se puede invocar `price_from_waterfall(..., as_dict=True)` o
`metrics.to_dict()`, lo que serializa todos los campos (incluyendo cashflows) y deja
el label “risk-free YTM” explícito en el archivo JSON/CSV resultante.

### Tinlake Snapshot Management

El componente de liquidez se calibra con el snapshot
`data/derived/liquidity/tinlake_metrics.json`. Para refrescarlo/manualizarlo:

```bash
# Refrescar desde DeFiLlama (JSON a stdout, resumen en stderr)
PYTHONPATH=. python scripts/manage_tinlake_snapshot.py --force-refresh

# Consultar el snapshot existente sin tocar la red
PYTHONPATH=. python scripts/manage_tinlake_snapshot.py --offline

# Ver estado/edad actual (warning si > 7 días)
PYTHONPATH=. python scripts/manage_tinlake_snapshot.py --status
```

El script persiste `data/derived/liquidity/tinlake_metrics.json` y un companion
`data/derived/liquidity/tinlake_metadata.json` con el `api_endpoint`, la edad y
el estatus (`fresh`, `stale`, `missing`). Cuando la red no está disponible se
usa el snapshot previo; si tampoco existe, WP-04 inyecta un fallback
conservador documentado en la metadata. Cualquier snapshot con más de 7 días
dispara un warning explícito con la instrucción para forzar el refresh.
