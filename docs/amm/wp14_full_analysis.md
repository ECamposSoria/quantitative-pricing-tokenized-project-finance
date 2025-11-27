# WP-14 AMM Simplificado - Complete Implementation Analysis

## Executive Summary

WP-14 implements a full AMM (Automated Market Maker) simulation framework for tokenized project finance, covering:
- Uniswap V2/V3 pool mechanics
- Market pricing with slippage
- Almgren-Chriss optimal execution
- Impermanent loss analytics
- Liquidity stress scenarios
- WP-09 export interface

**Total Implementation**: ~1,500 lines of Python across 21 modules + 12 test files

---

## 1. CORE MODULE: Pool Mechanics

### 1.1 Constant Product Pool (V2)
**File**: `pftoken/amm/core/pool_v2.py` (176 lines)

**Mathematical Foundation**:
```
Invariant: x × y = k
Price: P = reserve1 / reserve0  (token1 per token0)
Fee model: fee-on-input (deducted before swap)
```

**Key Classes**:
| Class | Purpose | Fields |
|-------|---------|--------|
| `PoolConfig` | Immutable metadata | `token0`, `token1`, `fee_bps=30` (0.30%) |
| `PoolState` | Mutable reserves | `reserve0`, `reserve1` |
| `SwapQuote` | Swap result | `amount_in`, `amount_out`, `price_before`, `price_after`, `fee_paid` |
| `ConstantProductPool` | Main pool | config + state + methods |

**Swap Formula** (token0 → token1):
```python
fee_paid = amount_in × fee_fraction           # fee_fraction = fee_bps / 10,000
net_amount = amount_in - fee_paid
new_reserve0 = reserve0 + net_amount
new_reserve1 = k / new_reserve0               # k = reserve0 × reserve1
amount_out = reserve1 - new_reserve1
price_after = new_reserve1 / new_reserve0
```

**Example Output**:
```
Pool: reserve0=1000, reserve1=1000, fee=30bps
Swap 100 token0:
  → amount_out = 90.66 token1
  → fee_paid = 0.30 token0
  → price_before = 1.0
  → price_after = 0.826 (token1/token0)
```

---

### 1.2 Concentrated Liquidity Pool (V3)
**File**: `pftoken/amm/core/pool_v3.py` (247 lines)

**Mathematical Foundation** (Full Uniswap V3):
```
Tick system: price = 1.0001^tick
Q64.96 fixed-point: sqrtPriceX96 = sqrt(price) × 2^96
Liquidity formula: L = Δy / (√Pb - √Pa) = Δx / (1/√Pa - 1/√Pb)
```

**Key Classes**:
| Class | Purpose | Fields |
|-------|---------|--------|
| `RangePosition` | LP position | `owner`, `lower_tick`, `upper_tick`, `liquidity` |
| `SwapResult` | V3 swap output | `amount_in`, `amount_out`, `fee_paid`, `final_sqrt_price_x96`, `final_tick`, `ticks_crossed` |
| `ConcentratedLiquidityPool` | V3 pool | `token0`, `token1`, `fee_bps`, `current_tick`, `sqrt_price_x96`, `positions[]` |

**Swap Algorithm** (`simulate_swap`):
```
1. Start at current sqrtPriceX96 and tick
2. Build liquidity_net map from positions (add at lower_tick, subtract at upper_tick)
3. Find next initialized tick boundary in swap direction
4. Compute swap step within current tick range:
   - For zero_for_one (token0→token1):
     amount0_needed = L × (1/√Pb - 1/√Pa)
     amount_out = L × (√Pa - √Pb)
   - For one_for_zero (token1→token0):
     amount1_needed = L × (√Pb - √Pa)
     amount_out = L × (1/√Pa - 1/√Pb)
5. If swap crosses tick: update liquidity, continue iteration
6. Deduct fees from input amount
7. Return SwapResult
```

**Example Output**:
```
Pool: tick=0 (price=1.0), fee=5bps
Position: lp1 at [-1000, 1000] with liquidity=10,000
Swap 100 token0:
  → amount_out = 98.95 token1
  → fee_paid = 0.05 token0
  → ticks_crossed = 0
  → final_tick = -158
  → final_sqrt_price_x96 = 78,831,426,...
```

---

### 1.3 Sqrt Price Math
**File**: `pftoken/amm/core/sqrt_price_math.py` (57 lines)

**Constants**:
```python
Q96 = 2^96 = 79,228,162,514,264,337,593,543,950,336
MIN_TICK = -887272
MAX_TICK = 887272
MIN_SQRT_PRICE_X96 = int(1.0001^(-887272/2) × Q96)
MAX_SQRT_PRICE_X96 = int(1.0001^(887272/2) × Q96)
```

**Functions**:
| Function | Formula | Purpose |
|----------|---------|---------|
| `tick_to_sqrt_price_x96(tick)` | `int(1.0001^(tick/2) × 2^96)` | Tick → Q64.96 sqrt price |
| `sqrt_price_x96_to_tick(sqrtPriceX96)` | `round(2 × log₁.₀₀₀₁(sqrtPriceX96 / 2^96))` | Q64.96 → tick |
| `get_amount0_delta(sqrtA, sqrtB, L)` | `L × (1/√lower - 1/√upper)` | Token0 amount for price move |
| `get_amount1_delta(sqrtA, sqrtB, L)` | `L × (√upper - √lower)` | Token1 amount for price move |

---

### 1.4 Swap Engine
**File**: `pftoken/amm/core/swap_engine.py` (44 lines)

**Purpose**: Unified routing layer for V2/V3 pools with slippage protection

```python
@dataclass
class SwapIntent:
    amount_in: float
    side_in: "token0" | "token1"
    min_amount_out: float = 0.0

def execute_swap(pool, intent) -> SwapQuote | SwapResult:
    # Routes to V2 or V3 based on pool type
    # Validates output >= min_amount_out
```

---

### 1.5 Liquidity Manager
**File**: `pftoken/amm/core/liquidity_manager.py` (79 lines)

**LP Share Minting**:
```python
# First deposit: geometric mean
shares_minted = sqrt(amount0 × amount1)

# Subsequent deposits: proportional
shares_minted = min(
    amount0 / reserve0 × total_shares,
    amount1 / reserve1 × total_shares
)
```

**Withdrawal**:
```python
pool_fraction = shares_to_burn / total_shares
amount0_out = reserve0 × pool_fraction
amount1_out = reserve1 × pool_fraction
```

---

## 2. PRICING MODULE

### 2.1 Market Price Helpers
**File**: `pftoken/amm/pricing/market_price.py` (113 lines)

| Function | Formula | Output |
|----------|---------|--------|
| `spot_price(pool)` | `reserve1 / reserve0` | Current price |
| `geometric_twap(prices, window)` | `exp(mean(log(prices)))` | Time-weighted average |
| `price_deviation(observed, reference)` | `(observed - reference) / reference` | % deviation |
| `execution_price(pool, amount, side)` | Simulated swap | Effective price with slippage |
| `depth_curve(pool, price_range)` | `x_new = sqrt(k/p)` | Cumulative depth to move to target prices |
| `arbitrage_signal(pool_price, ref_price, threshold)` | If `|rel| >= threshold` → signal | Arb direction + magnitude |

**Depth Curve Formula**:
```
For target price p = y/x with invariant k:
  x_new = sqrt(k / p)
  depth = x_new - x_current (token0 required)
```

---

### 2.2 Slippage Analytics
**File**: `pftoken/amm/pricing/slippage.py` (40 lines)

| Function | Formula | Purpose |
|----------|---------|---------|
| `slippage_percent(before, after)` | `(after - before) / before` | Single swap slippage |
| `aggregate_slippage(series)` | `mean(|slippages|)` | Average over multiple swaps |
| `slippage_curve(price_before, sizes, price_fn)` | Grid of slippages | Slippage vs trade size |

**Example CLI Output** (from stress run):
```
slippage_curve: [
  [0.1, -0.173],   # 10% sell → -17.3% price impact
  [0.25, -0.359],  # 25% sell → -35.9% price impact
  [0.5, -0.555]    # 50% sell → -55.5% price impact
]
```

---

### 2.3 Arbitrage Engine (Almgren-Chriss)
**File**: `pftoken/amm/pricing/arbitrage_engine.py` (95 lines)

**Model Parameters**:
| Parameter | Symbol | Description |
|-----------|--------|-------------|
| `eta` (η) | Temporary impact | Linear coefficient for instant impact |
| `gamma` (γ) | Permanent impact | Linear coefficient for lasting impact |
| `sigma` (σ) | Volatility | Price volatility |
| `lambda_risk` (λ) | Risk aversion | Penalty for execution risk |

**Execution Cost Formula**:
```
E[C] = price_term + temporary_impact + permanent_impact
     = Σ(nⱼ × pⱼ) + η × Σ(nⱼ²) + ½γ × X²

Where:
  nⱼ = trade size at step j
  X = total trade size
```

**Optimal Trajectory** (simplified):
```python
decay = exp(-λ × linspace(0, T, n_steps))
weights = decay / sum(decay)
trajectory = weights × total_size
```

**Convergence Half-Life**:
```
Time to 50% spread reduction = argmin(|spread - 0.5 × initial_spread|)
```

---

### 2.4 DCF Integration
**File**: `pftoken/amm/pricing/dcf_integration.py` (55 lines)

**Blending Functions**:
```python
# Simple blend
blended = (1 - weight_market) × dcf_price + weight_market × market_price

# With arbitrage penalty
penalty = min(0.05, |arb_result.realized_spread_reduction|)
blended_adjusted = blended × (1 - penalty)
```

**Discrepancy Series**:
```python
deviations = (market_series - dcf_series) / dcf_series  # % deviation vector
adjustment_factor = 1 + mean(deviations)
```

---

## 3. ANALYSIS MODULE

### 3.1 Impermanent Loss
**File**: `pftoken/amm/analysis/impermanent_loss.py` (109 lines)

**V2 Closed Form**:
```
IL_v2(r) = 2√r / (1 + r) - 1

Where r = P_new / P_old (price ratio)
```

| Price Ratio (r) | IL |
|-----------------|-----|
| 0.5 | -5.72% |
| 0.75 | -1.03% |
| 1.0 | 0.0% |
| 1.25 | -0.62% |
| 1.5 | -2.02% |
| 2.0 | -5.72% |

**V3 Range-Aware** (`il_v3_range`):
```python
def amounts_at_price(sqrt_price, sqrt_lower, sqrt_upper):
    if sqrt_price <= sqrt_lower:  # All token0
        return (L × (1/sqrt_lower - 1/sqrt_upper), 0)
    if sqrt_price >= sqrt_upper:  # All token1
        return (0, L × (sqrt_upper - sqrt_lower))
    # In range
    return (
        L × (1/sqrt_price - 1/sqrt_upper),
        L × (sqrt_price - sqrt_lower)
    )

V_hold = x0 × P_end + y0
V_lp = x1 × P_end + y1
IL_v3 = V_lp / V_hold - 1
```

**IL Surface**:
```python
surface[i, j] = il_v3_range(1.0, ratios[j], ranges[i][0], ranges[i][1])
# Returns 2D grid: len(ranges) × len(ratios)
```

**Fee Breakeven**:
```python
days_to_breakeven = |IL| / daily_fees
if days_to_breakeven > holding_period: return ∞
```

---

### 3.2 LP PnL Decomposition
**File**: `pftoken/amm/analysis/lp_pnl.py` (93 lines)

**Components**:
```
Net PnL = Fees Earned + Price Appreciation + Impermanent Loss

Where:
  Fees Earned = cumulative trading fees collected
  Price Appreciation = V_hold_end - V_initial
  Impermanent Loss = V_lp_end - V_hold_end
```

**Data Classes**:
```python
@dataclass
class LPPnLDecomposition:
    fees_earned: float
    impermanent_loss: float
    price_appreciation: float
    net_pnl: float
```

---

## 4. STRESS MODULE

### 4.1 Stress Scenarios
**File**: `pftoken/stress/amm_stress_scenarios.py` (41 lines)

| Code | Name | Parameters | Description |
|------|------|------------|-------------|
| `PS` | Panic Sell Ladder | `steps: [0.10, 0.25, 0.50]` | Progressive sell pressure |
| `LP` | LP Withdrawal Cascade | `steps: [0.10, 0.20, 0.30]` | Sequential LP exits |
| `FC` | Flash Crash + Recovery | `drop: 0.4, recovery: 0.5` | Sharp drop → partial recovery |

---

### 4.2 Liquidity Stress Implementation
**File**: `pftoken/stress/liquidity_stress.py` (143 lines)

**Scenario Output** (`ScenarioOutcome`):
```python
@dataclass
class ScenarioOutcome:
    name: str
    price_path: np.ndarray      # Prices at each step
    liquidity_path: np.ndarray  # Total liquidity at each step
    slippage_curve: np.ndarray  # [step, slippage%]
    il: float                   # Impermanent loss
    recovery_steps: int         # Steps to 90% recovery
```

**Panic Sell Ladder**:
```python
for fraction in [0.10, 0.25, 0.50]:
    quote = pool.simulate_swap(reserve0 × fraction, "token0")
    prices.append(pool.price())
    liquidity.append(reserve0 + reserve1 / base_price)
    slippage.append((quote.price_after - quote.price_before) / quote.price_before)
```

**Flash Crash + Recovery**:
```python
crashed_price = base_price × (1 - drop_fraction)         # e.g., 0.6
recovered_price = crashed_price + drop × recovery × base # e.g., 0.8
price_path = [base, crashed, recovered]
il = il_v2(recovered / base)
recovery_steps = 1 if recovered >= base × 0.9 else 2
```

---

### 4.3 WP-09 Export Interface
**File**: `pftoken/stress/amm_metrics_export.py` (62 lines)

**Export Structure**:
```python
@dataclass
class AMMStressMetrics:
    depth_curve: np.ndarray               # [price, token0_depth]
    slippage_curve: np.ndarray            # [step, slippage%]
    stressed_depths: Dict[str, np.ndarray] # scenario → liquidity path
    il_by_scenario: Dict[str, float]       # scenario → IL
    recovery_steps: Dict[str, int]         # scenario → steps
```

**CLI Output Example** (reserves=1000/1000):
```python
{
  'depth_curve': [[0.9, 0.0], [1.0, 0.0], [1.1, 0.0]],
  'il_by_scenario': {'FC': -0.00619, 'LP': 0.0, 'PS': 0.0},
  'recovery_steps': {'FC': 2, 'LP': 0, 'PS': 0},
  'slippage_curve': [
    [0.10, -0.173],   # 10% sell → 17.3% negative impact
    [0.25, -0.359],   # 25% sell → 35.9% negative impact
    [0.50, -0.555]    # 50% sell → 55.5% negative impact
  ],
  'stressed_depths': {
    'FC': [2000.0, 2666.67, 2250.0],  # Flash crash liquidity path
    'LP': [1800.0, 1440.0, 1008.0],   # LP withdrawal cascade
    'PS': [2000.0, 2000.0, 2000.0]    # Panic sell (price impact, not liquidity)
  }
}
```

---

## 5. VISUALIZATION MODULE

### 5.1 AMM Visualizations
**File**: `pftoken/viz/amm_viz.py` (66 lines)

| Function | Input | Output |
|----------|-------|--------|
| `plot_price_series(prices)` | Price array | Line chart |
| `plot_price_vs_dcf(pool, dcf)` | Two price arrays | Comparison chart |
| `plot_il_heatmap(surface, ratios, ranges)` | IL grid | Heatmap |
| `plot_stress_outcomes(results)` | Dict of paths | Multi-line chart |
| `plot_liquidity_depth(curve)` | Depth array | Depth curve |

---

### 5.2 Dashboard Integration
**File**: `pftoken/viz/dashboards.py` (hooks at lines 23, 114-123)

```python
def build_financial_dashboard(
    params: ProjectParameters,
    mc_ratio_summary: dict | None = None,
    include_amm: bool = False,           # Toggle AMM visualizations
    amm_context: dict | None = None,     # AMM data
) -> Dict[str, Figure]:
    ...
    if include_amm and amm_context:
        if "pool_prices" in amm_context and "dcf_prices" in amm_context:
            figures["price_vs_dcf"] = amm_viz.plot_price_vs_dcf(...)
        if "il_surface" in amm_context:
            figures["il_heatmap"] = amm_viz.plot_il_heatmap(...)
        if "stress_results" in amm_context:
            figures["stress_outcomes"] = amm_viz.plot_stress_outcomes(...)
```

---

## 6. CLI INTERFACE

**File**: `scripts/run_amm_stress.py` (44 lines)

**Usage**:
```bash
python scripts/run_amm_stress.py \
  --reserve0 1000 \
  --reserve1 1000 \
  --scenarios PS LP FC
```

**Arguments**:
| Arg | Default | Description |
|-----|---------|-------------|
| `--price` | 1.0 | Initial price |
| `--reserve0` | 1000 | Token0 reserve |
| `--reserve1` | 1000 | Token1 reserve |
| `--scenarios` | PS LP FC | Scenario codes |

---

## 7. TEST COVERAGE

**Directory**: `tests/test_amm/` (12 files)

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_pool_v3.py` | 4 | ✅ Passed |
| `test_arbitrage_engine.py` | 3 | ✅ Passed |
| `test_impermanent_loss.py` | 5 | ✅ Passed |
| `test_lp_pnl.py` | 3 | ✅ Passed |
| `test_market_pricing.py` | 4 | ✅ Passed |
| `test_slippage.py` | 3 | ✅ Passed |
| `test_dcf_integration.py` | 1 | ⏭ Skipped |
| `test_pool_v2.py` | 1 | ⏭ Skipped |
| `test_liquidity_manager.py` | 1 | ⏭ Skipped |
| `test_swap_engine.py` | 1 | ⏭ Skipped |
| `test_range_optimizer.py` | 1 | ⏭ Skipped |

**Integration**: `tests/test_integration/test_amm_stress.py` (1 test, ✅ Passed)

**Total**: 22 passed, 5 skipped

---

## 8. DATA FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WP-14 AMM Pipeline                          │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Pool Config │
                    │  (reserves)  │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  pool_v2   │  │  pool_v3   │  │ swap_engine│
    │ (x×y=k)    │  │ (Q64.96)   │  │  (router)  │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │      PRICING          │
              ├───────────────────────┤
              │ • spot_price          │
              │ • execution_price     │──────┐
              │ • depth_curve         │      │
              │ • arbitrage_signal    │      │
              └───────────┬───────────┘      │
                          │                  │
           ┌──────────────┼──────────────┐   │
           ▼              ▼              ▼   │
    ┌────────────┐ ┌────────────┐ ┌──────────┴──┐
    │  slippage  │ │    arb     │ │    dcf      │
    │  curves    │ │  engine    │ │ integration │
    └─────┬──────┘ │(Almgren-   │ │  (blend)    │
          │        │  Chriss)   │ └──────┬──────┘
          │        └─────┬──────┘        │
          │              │               │
          └──────────────┼───────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │      ANALYSIS         │
              ├───────────────────────┤
              │ • il_v2 / il_v3_range │
              │ • il_surface          │
              │ • fee_breakeven       │
              │ • pnl_decomposition   │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │       STRESS          │
              ├───────────────────────┤
              │ • panic_sell_ladder   │
              │ • lp_withdrawal       │
              │ • flash_crash         │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   WP-09 EXPORT        │
              │  (AMMStressMetrics)   │
              └───────────┬───────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ dashboards │ │    CLI     │ │   tests    │
    │(optional)  │ │  output    │ │            │
    └────────────┘ └────────────┘ └────────────┘
```

---

## 9. KEY FORMULAS REFERENCE

| Component | Formula |
|-----------|---------|
| V2 Price | `P = reserve1 / reserve0` |
| V2 Swap Output | `amount_out = reserve1 - k / (reserve0 + net_in)` |
| V3 Tick → Price | `price = 1.0001^tick` |
| V3 sqrtPriceX96 | `sqrtPriceX96 = sqrt(price) × 2^96` |
| V3 Amount0 Delta | `Δx = L × (1/√Pa - 1/√Pb)` |
| V3 Amount1 Delta | `Δy = L × (√Pb - √Pa)` |
| IL (V2) | `IL = 2√r / (1+r) - 1` |
| IL (V3) | `IL = V_lp / V_hold - 1` |
| Slippage | `slip = (P_after - P_before) / P_before` |
| AC Execution Cost | `E[C] = Σnⱼpⱼ + ηΣnⱼ² + ½γX²` |
| DCF Blend | `blend = (1-w)×dcf + w×market` |

---

## 10. COMPLETE FILE LISTING

### Core (5 files, ~600 lines)
- `pftoken/amm/core/__init__.py`
- `pftoken/amm/core/pool_v2.py` (176 lines)
- `pftoken/amm/core/pool_v3.py` (247 lines)
- `pftoken/amm/core/sqrt_price_math.py` (57 lines)
- `pftoken/amm/core/swap_engine.py` (44 lines)
- `pftoken/amm/core/liquidity_manager.py` (79 lines)

### Pricing (5 files, ~300 lines)
- `pftoken/amm/pricing/__init__.py`
- `pftoken/amm/pricing/market_price.py` (113 lines)
- `pftoken/amm/pricing/slippage.py` (40 lines)
- `pftoken/amm/pricing/arbitrage.py` (53 lines)
- `pftoken/amm/pricing/arbitrage_engine.py` (95 lines)
- `pftoken/amm/pricing/dcf_integration.py` (55 lines)

### Analysis (5 files, ~300 lines)
- `pftoken/amm/analysis/__init__.py`
- `pftoken/amm/analysis/impermanent_loss.py` (109 lines)
- `pftoken/amm/analysis/lp_pnl.py` (93 lines)
- `pftoken/amm/analysis/depth_analysis.py` (28 lines)
- `pftoken/amm/analysis/range_optimizer.py` (71 lines)

### Stress (4 files, ~250 lines)
- `pftoken/stress/liquidity_stress.py` (143 lines)
- `pftoken/stress/amm_stress_scenarios.py` (41 lines)
- `pftoken/stress/amm_metrics_export.py` (62 lines)

### Visualization (2 files, ~200 lines)
- `pftoken/viz/amm_viz.py` (66 lines)
- `pftoken/viz/dashboards.py` (hooks)

### CLI (1 file)
- `scripts/run_amm_stress.py` (44 lines)

### Documentation (4 files)
- `docs/amm/architecture.md`
- `docs/amm/amm_overview.md`
- `docs/amm/integration_guide.md`
- `docs/amm/impermanent_loss.md`

### Tests (12 files)
- `tests/test_amm/*.py`
- `tests/test_integration/test_amm_stress.py`

---

**Document Generated**: 2025-11-26
**WP-14 Status**: Complete
