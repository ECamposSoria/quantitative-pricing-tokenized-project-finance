# 10-Minute Thesis Presentation Structure
## "Quantitative Pricing of Tokenized Project Finance: AMM-Based Liquidity Engineering"

**4 Speakers × 2.5 minutes each = 10 minutes total**
**6 Slides Total**

---

## 📊 SLIDE ALLOCATION BY SPEAKER

| Speaker | Slides | Duration | Topics |
|---------|--------|----------|--------|
| **Speaker 1** | Slide 1 | 2.5 min | Problem Statement & Innovation |
| **Speaker 2** | Slides 2-3 | 2.5 min | Zero Curve + Monte Carlo Risk |
| **Speaker 3** | Slide 4 | 2.5 min | AMM V2 vs V3 Analysis |
| **Speaker 4** | Slides 5-6 | 2.5 min | WACD Synthesis + Conclusion |

---

## 🎤 SPEAKER 1: Problem Statement & Technical Innovation (2.5 min)

### **SLIDE 1: The Tokenized Project Finance Problem**

#### **Top Half: Problem Setup (1 min)**

**LEO IoT Satellite Constellation - Case Study**
- **Project**: Low Earth Orbit IoT constellation
- **Economics**: $100M total CAPEX ($50M debt + $50M equity), 15-year horizon
- **Traditional Challenge**: Illiquid project finance debt → **75 bps liquidity premium**

**Traditional Project Finance Limitations**:
1. Illiquid secondary markets (6-month settlement lags)
2. High transaction costs (origination, servicing, admin)
3. Limited price discovery
4. Capital inefficient (sponsor LP requirements)

---

#### **Bottom Half: Our Innovation (1.5 min)**

**Research Question**:
> *Can blockchain tokenization + AMM microstructure reduce the cost of debt capital while maintaining institutional-grade risk management?*

**Technical Innovation - Triple Integration**:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Project Finance │  →   │ Structural Credit│  →   │ DeFi AMM        │
│                 │      │ Risk Models      │      │ Microstructure  │
├─────────────────┤      ├──────────────────┤      ├─────────────────┤
│ • DCF/CFADS     │      │ • Merton model   │      │ • Uniswap V3    │
│ • Waterfall     │      │ • Monte Carlo    │      │ • Concentrated  │
│ • Covenant      │      │ • 10k scenarios  │      │   liquidity     │
│   tracking      │      │ • Correlated     │      │ • Slippage →    │
│                 │      │   shocks         │      │   spread model  │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

**Key Methodological Contribution**:
- **First quantitative framework** linking AMM slippage to traditional liquidity spreads
- Amihud-style calibration: `Liquidity_Premium = 75 × (1 - depth_score^0.8)`
- Validated against real DeFi data (Centrifuge/Tinlake, $1.45B TVL)

**Bottom Line Result** (teaser):
- **86 bps cost reduction** vs traditional finance
- **83% lower slippage** with V3 concentrated liquidity
- **NPV savings: $4.2M** on $50M debt

---

**VISUALS FOR SLIDE 1**:
- Top: Satellite constellation image + project economics box
- Middle: Architecture diagram (3-box flow above)
- Bottom: Key numbers in colored boxes (86 bps, 83%, $4.2M)

---

## 🎤 SPEAKER 2: Zero Curve & Monte Carlo Risk Framework (2.5 min)

### **SLIDE 2: Zero Curve Construction & Discounting**

#### **Content (1.25 min)**:

**Purpose**: Discount tranche cashflows to present value over 15-year project horizon

**Simplified Flat Yield Approach** (NOT bootstrapping):

1. **Base Reference**: SOFR (Secured Overnight Financing Rate) @ 4.5%
   - Source: `project_params.csv` → `base_rate_reference = 0.045`

2. **Flat Zero Curve Assumption**:
   - **Same 4.5% rate applied to ALL maturities** (1Y to 15Y)
   - Simplification justified by:
     - Academic project scope (not trading desk)
     - Stable long-term infrastructure financing
     - Focus on tokenization innovation, not term structure modeling

3. **Discount Factor Formula**:
   ```
   DF(t) = (1 + r)^(-t) = (1.045)^(-t)

   Examples:
   DF(5Y)  = 0.8025  →  $1M in 5 years = $802.5K today
   DF(10Y) = 0.6439  →  $1M in 10 years = $643.9K today
   DF(15Y) = 0.5167  →  $1M in 15 years = $516.7K today
   ```

**Implementation** (matching main code):
```python
from pftoken.pricing.zero_curve import ZeroCurve, CurvePoint

def build_zero_curve_from_base_rate(base_rate: float, tenor_years: int):
    points = [
        CurvePoint(maturity_years=1.0, zero_rate=base_rate),
        CurvePoint(maturity_years=float(tenor_years), zero_rate=base_rate)
    ]
    return ZeroCurve(points=points, currency="USD")

curve = build_zero_curve_from_base_rate(0.045, 15)
```

**Sensitivity Analysis**:
- Parallel shock scenarios: ±50 bps, ±100 bps
- Tests robustness of NPV calculations to interest rate changes

**Note**: Full bootstrapping methodology (using swaps/deposits) is **available in the codebase** but **not used** for this project's simplified approach

---

**VISUALS FOR SLIDE 2**:
- **Chart**: Zero curve (0-15 years) with:
  - Main curve line (blue)
  - Bootstrapping nodes marked (red dots at 1Y, 5Y, 15Y)
  - Shaded bands for ±50 bps shocks
  - Y-axis: 4.0%-6.0% zero rates
  - Annotations showing methodology (deposits → swaps)

---

### **SLIDE 3: Monte Carlo Risk Framework & Results**

#### **Content (1.25 min)**:

**CFADS Model** (Quick overview):
```
CFADS_t = Revenue_t - OPEX_t - Taxes_t - RCAPEX_t - ΔReserves_t

Present Value = Σ[CFADS_t × DF(t)]  ← Using bootstrapped zero curve
```

**Monte Carlo Simulation**:
- **10,000 scenarios** with correlated shocks:
  - Revenue volatility: σ = 15%
  - OPEX volatility: σ = 10%
  - Interest rate paths: Vasicek model (mean reversion to 4.5%)
- **Antithetic variates** for variance reduction
- **Merton structural default**: Default if `Asset_Value_t < Debt_Threshold_t`

**Risk Metrics by Tranche**:

| Tranche | Weight | Coupon | PD | LGD | Expected Loss (EL) |
|---------|--------|--------|----|----|-------------------|
| **Senior** | 60% | 3.5% | 2.0% | 40% | **0.80%** |
| **Mezzanine** | 25% | 5.0% | 5.0% | 60% | **3.00%** |
| **Subordinated** | 15% | 7.0% | 10.0% | 80% | **8.00%** |

**Structure Optimization Results**:

| Metric | Traditional (60/25/15) | Optimized (55/34/11) | Improvement |
|--------|------------------------|---------------------|-------------|
| **Breach Probability** | 23.0% | 18.4% | **-22%** |
| **DSCR p50** | 2.59x | 2.59x | Same |
| **DSCR p5 (tail)** | 1.11x | 1.25x | **At covenant** |
| **Equity IRR** | 10.56% | 10.56% | Same |

**Key Insight**: Shift 9% from Senior → Mezz reduces tail risk without sacrificing returns

---

**VISUALS FOR SLIDE 3**:
- **Primary**: DSCR fan chart (Monte Carlo) showing p5/p25/p50/p75/p95 bands across 15 years
  - Covenant line at 1.25x (red dashed)
  - Highlight breach zones
- **Inset table**: Risk metrics comparison (Traditional vs Optimized)

---

## 🎤 SPEAKER 3: AMM Innovation - V2 vs V3 (2.5 min)

### **SLIDE 4: Liquidity Engineering - Concentrated Liquidity Breakthrough**

#### **Top Section: The Challenge (45 sec)**

**Problem**: Tokenized debt needs liquid secondary markets
- Traditional project finance: 6-month settlement lag → **75 bps liquidity premium**
- DeFi opportunity: Instant settlement, but which AMM model?

**Experimental Setup**:
- Pool depth: $5M per side (10% of $50M debt)
- Trade sizes: 5%, 10%, 25% of pool reserves
- Measure: Slippage as proxy for market depth quality

---

#### **Middle Section: V2 vs V3 Comparison (1 min)**

**Uniswap V2 (Constant Product)**:
- Formula: `x × y = k` (uniform liquidity)
- Capital: $5M per side
- 10% trade → **17.3% slippage**

**Uniswap V3 (Concentrated Liquidity)**:
- Liquidity concentrated in **±5% range** around par (ticks -500 to +500)
- **Same $5M capital** → **5x density** in active range
- 10% trade → **3.9% slippage**

**Slippage Comparison Table**:

| Trade Size | V2 Slippage | V3 Slippage | Improvement |
|-----------|------------|------------|-------------|
| **5% of pool** | 9.27% | 1.96% | **79%** ↓ |
| **10% of pool** | 17.31% | 3.87% | **78%** ↓ |
| **25% of pool** | 35.92% | 4.88% | **86%** ↓ |
| **Average** | 20.83% | 3.57% | **83%** ↓ |

**Capital Efficiency**: V3 achieves same depth with **20% of V2 capital** ($1M vs $5M)

---

#### **Bottom Section: Slippage → Spread Calibration (45 sec)**

**Theoretical Framework** (Amihud 2002 illiquidity measure):

```
depth_score = 1 / (1 + slippage_10pct × 2.5)

Liquidity_Premium_bps = 75 × (1 - depth_score^0.8)
```

**Results**:
- **V2 model**: 56.3 bps reduction (validated against Tinlake: 54.2 bps ✓)
- **V3 model**: **69.7 bps reduction** (+13 bps vs V2)

**Why V3 Wins for Debt Tokens**:
1. Debt trades near par (stable asset, not volatile crypto)
2. ±5% range captures >99% of trading activity
3. Out-of-range risk negligible
4. Unlocks 80% of LP capital for other uses

---

**VISUALS FOR SLIDE 4**:
- **Left**: Side-by-side slippage curves
  - X-axis: Trade size (% of pool)
  - Y-axis: Slippage (%)
  - V2 curve (steep red line)
  - V3 curve (flat blue line)
  - Dramatic visual gap
- **Right Top**: Capital efficiency diagram
  - V2: Full circle ($5M)
  - V3: 20% slice ($1M) achieving same result
  - "5x efficiency" label
- **Right Bottom**: Validation scatter plot (Model vs Tinlake benchmark)

---

## 🎤 SPEAKER 4: WACD Synthesis & Conclusion (2.5 min)

### **SLIDE 5: All-In WACD Decomposition**

#### **Content (1.25 min)**:

**Component Breakdown - The 86 bps Story**:

```
Traditional WACD:  450 bps (4.50%)

Tokenization Benefits:
  ├─ Liquidity (V3 AMM):       -69.7 bps  ← Core innovation (slide 4)
  ├─ Operational savings:       -3.5 bps  (No SPV admin, automation)
  ├─ Transparency premium:     -20.0 bps  (On-chain audit trail)
  └─ Regulatory risk:           +7.5 bps  (Security token ban tail risk)
                                ─────────
  Net Tokenization Impact:     -85.7 bps

Tokenized WACD:  364.3 bps (3.64%)

After-Tax Savings (35% corp tax):
  Traditional effective: 292.5 bps
  Tokenized effective:   236.8 bps
  Savings: 55.7 bps after-tax
```

**NPV Impact** (on $50M debt, 15 years):
- Annual savings: **$428,500** (86 bps × $50M)
- Discounted @ 4.5%: **NPV ≈ $4.2M**
- As % of debt: **8.4%**

**WACD Scenarios**:

| Scenario | Structure | WACD (bps) | Savings |
|----------|-----------|-----------|---------|
| **Traditional** | 60/25/15 | 450 | Baseline |
| **Tokenized (same)** | 60/25/15 | 364 | **-86 bps** |
| **+ Optimal structure** | 55/34/11 | 364 | -86 bps (same cost, lower risk) |
| **+ Interest rate cap** | 55/34/11 | 388 | **-62 bps** (net, after hedge) |

---

**VISUALS FOR SLIDE 5**:
- **Waterfall chart**: Showing 450 → 364 bps breakdown
  - Start bar: 450 (dark red)
  - Liquidity down: -70 (blue)
  - Operational down: -3.5 (light blue)
  - Transparency down: -20 (green)
  - Regulatory up: +7.5 (orange)
  - End bar: 364 (dark green)
- **Inset**: NPV savings callout box ($4.2M in bold)

---

### **SLIDE 6: Thesis Contributions & Implementation**

#### **Top Half: Academic Contributions (1 min)**

**Novel Contributions to Literature**:

1. **Methodological Innovation**:
   - First quantitative framework linking AMM microstructure to project finance liquidity spreads
   - Bridges DeFi (slippage curves) ↔ TradFi (basis point premiums)
   - Empirically calibrated against $1.45B TVL protocol (Centrifuge)

2. **Empirical Finding**:
   - V3 concentrated liquidity delivers **83% slippage reduction** vs V2
   - **5x capital efficiency** enables viable markets with minimal LP requirements
   - Debt-specific advantage: stability allows tight ranges (±5%)

3. **Practical Impact**:
   - **86 bps all-in cost reduction** (19% cheaper than traditional)
   - **22% breach probability reduction** via structure optimization
   - **$4.2M NPV savings** on $50M project

---

#### **Bottom Half: Implementation & Conclusion (1.25 min)**

**Thesis Finding**:
> *"Uniswap V3 concentrated liquidity enables viable secondary markets for tokenized project finance debt with 20% of traditional LP capital requirements, reducing all-in financing costs by 86 basis points while maintaining institutional-grade risk management through Monte Carlo validation and Merton structural default models."*

**Implementation Roadmap**:

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Tokenization** | Centrifuge/Tinlake | $1.45B TVL, SEC Reg D/S compliant |
| **Liquidity** | Uniswap V3 pools | 30 bps fee tier, ±5% range |
| **Governance** | CFG token incentives | External LP bootstrapping |
| **Compliance** | Smart contract audits | Institutional-grade security |

**Timeline**: Tokenization at financial close → LP bootstrapping (months 1-3) → full liquidity (month 6)

**Future Research Directions**:
1. Dynamic LP rebalancing strategies (active range management)
2. Cross-chain liquidity aggregation (Ethereum ↔ L2s)
3. Regulatory framework analysis (MiCA, SEC security token rules)
4. Credit rating methodology for tokenized tranches

---

**VISUALS FOR SLIDE 6**:
- **Top**: Summary metrics table (3x3 grid)
  - Cost Reduction: 86 bps
  - Risk Reduction: 22% lower breaches
  - NPV Savings: $4.2M
  - V3 Slippage: 83% improvement
  - Capital Efficiency: 5x multiplier
  - Equity IRR: 10.56%
- **Bottom**: Implementation timeline (Gantt-style)
  - Month 0: Tokenization
  - Months 1-3: LP bootstrapping
  - Month 6: Full liquidity
- **Footer**: Key academic references (Hull, Amihud, Reisin, Merton)

---

## 📋 COMPLETE PRESENTATION SUMMARY

### **Slide Distribution**:
1. ✅ **Slide 1**: Problem + Innovation (Speaker 1)
2. ✅ **Slide 2**: Zero Curve Methodology (Speaker 2)
3. ✅ **Slide 3**: Monte Carlo Risk (Speaker 2)
4. ✅ **Slide 4**: AMM V2 vs V3 (Speaker 3)
5. ✅ **Slide 5**: WACD Synthesis (Speaker 4)
6. ✅ **Slide 6**: Contributions + Conclusion (Speaker 4)

### **Timing Breakdown**:
- Speaker 1: 2.5 min (Slide 1)
- Speaker 2: 2.5 min (Slides 2-3, ~1.25 min each)
- Speaker 3: 2.5 min (Slide 4)
- Speaker 4: 2.5 min (Slides 5-6, ~1.25 min each)
- **Total: 10 minutes**

---

## 📊 CRITICAL VISUALIZATIONS NEEDED

### **From Notebook** (screenshot these):
1. ✅ **Slide 3**: `PANELS['dscr_fan_chart']` - Monte Carlo DSCR trajectories
2. ✅ **Slide 4**: `PANELS['amm_comparison']` - V2 vs V3 slippage curves
3. ✅ **Slide 5**: `PANELS['wacd_synthesis']` - Waterfall component breakdown

### **Generate Manually**:
1. ✅ **Slide 1**: Architecture diagram (3-box flow: PF → Credit Risk → AMM)
2. ✅ **Slide 2**: Zero curve plot (need to create - see script below)
3. ✅ **Slide 6**: Summary metrics table + timeline

---

## 🔬 KEY EQUATIONS TO DISPLAY

### **Slide 2 (Zero Curve)**:
```latex
% Deposit discount factor
DF(t) = (1 + r)^{-t}

% Swap NPV = 0 (bootstrapping)
\sum_{i=1}^{n-1} c \cdot DF(t_i) + (1 + c) \cdot DF(T) = 1

% Zero rate extraction
r_{\text{zero}}(T) = DF(T)^{-1/T} - 1
```

### **Slide 3 (Monte Carlo)**:
```latex
% CFADS formula
\text{CFADS}_t = \text{Revenue}_t - \text{OPEX}_t - \text{Taxes}_t - \text{RCAPEX}_t - \Delta\text{Reserves}_t

% DSCR covenant
\text{DSCR}_t = \frac{\text{CFADS}_t}{\text{Debt Service}_t} \geq 1.25

% Merton default condition
\text{Default}_t \iff V_{\text{asset},t} < D_t
```

### **Slide 4 (AMM)**:
```latex
% V2 constant product
x \times y = k, \quad \text{Price} = \frac{y}{x}

% V3 liquidity depth
\text{depth\_score} = \frac{1}{1 + \text{slippage} \times 2.5}

% Liquidity premium
\text{Premium}_{\text{bps}} = 75 \times (1 - \text{depth\_score}^{0.8})
```

### **Slide 5 (WACD)**:
```latex
% WACD formula
\text{WACD} = \sum_{i} w_i \times (r_i + s_i + \delta_{\text{token}}) \times (1 - \tau)

\text{where } \tau = 0.35 \text{ (corporate tax rate)}
```

---

## 🎯 BACKUP SLIDES (For Q&A)

Prepare 2-3 additional slides for anticipated questions:

1. **Backup A**: Detailed Merton model math (asset value dynamics, PD calculation)
2. **Backup B**: Sensitivity analysis (tornado chart showing robustness to assumptions)
3. **Backup C**: Collateral analysis (haircuts, liquidation timelines, LGD adjustment)
