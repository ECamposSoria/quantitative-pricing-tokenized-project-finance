# Stochastic Parameter Calibration Sources

## Revenue & Market Variables
| Parameter | Source | Reference |
|-----------|--------|-----------|
| revenue_growth μ=0.065 | Iridium 10-K (2019-2023) CAGR | SEC EDGAR |
| churn_rate β(2,18) | Globalstar subscriber metrics | Annual reports |
| competitive_pressure lognormal μ=-0.02 σ=0.10 | Comparable LEO entrants | Industry reports |

## Operational Variables
| Parameter | Source | Reference |
|-----------|--------|-----------|
| launch_failure p=0.07 | SpaceX Falcon 9 reliability | spacex.com/reliability |
| satellite_degradation β(2,20) | LEO constellation lifecycle studies | IEEE Aerospace 2021 |
| ground_segment_cost lognormal μ=0.02 σ=0.06 | Ground infra OPEX benchmarks | Vendor surveys |
| opex_inflation lognormal μ=0.03 σ=0.07 | OECD telecom cost trends | OECD data |

## Tokenization Variables
| Parameter | Source | Reference |
|-----------|--------|-----------|
| secondary_market_depth β(4,2) | DeFi liquidity studies (Uniswap/Aave) | DeFi Pulse, Dune Analytics |
| smart_contract_risk p=0.005 | Historical exploit frequency | rekt.news |

## Correlation Matrix
Expert judgment based on:
- Moody's Project Finance Default Study 2022
-, S&P Infrastructure Risk Correlation Report
-, DeFi market co-movements (liquidity vs. smart contract risk)
