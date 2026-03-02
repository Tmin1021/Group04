# Abstract

---

This project implements and evaluates a **Price Momentum** strategy on a Vietnam stock universe (example tickers: `HPG`, `VIC`, `VNM`). We follow a simplified **6-step** workflow (subset of the 9-step Algotrade framework): **Hypothesis → Data Collection → Data Processing → In-sample Backtest → Optimization → Out-of-sample Backtest**.

Using daily market data, we build **monthly features** (momentum, volatility, liquidity, forward 1-month return). The backtest is **monthly rebalanced**: at each month-end date *t*, we select the **top-N tickers by momentum**, assign weights (equal-weight or inverse-volatility with a max-weight cap), hold for one month (*t → t+1*), and subtract **transaction cost proportional to turnover**. Performance is measured by metrics such as **CAGR, volatility, Sharpe ratio, max drawdown, and average turnover**.

# Introduction

---

This project tests whether **past relative performance** of stocks (momentum) can be used to form a systematic, rule-based portfolio that produces positive risk-adjusted returns in a simple monthly-rebalanced setting.

**Feature**

- [x] Export daily data from database into CSV
- [x] Process daily data into monthly features (momentum, volatility, forward return, liquidity)
- [x] In-sample and out-of-sample backtesting (monthly rebalanced)
- [x] Optimize hyperparameters via grid search (in-sample)
- [x] Save outputs (returns/weights/metrics) for reporting
- [ ] Add benchmark comparison (optional, if VNINDEX series is provided)
- [ ] Paper trade / live trading

**Installation**

- Requirement: pip
- Create and source new virtual environment in the current working directory with command
```
python -m venv .venv
source .venv/Scripts/activate
```
- Install dependencies by:
```
pip install -r requirements.txt
```

# Related Work
Momentum has been widely studied in academic finance. This project is motivated by classic cross-sectional momentum evidence (buy recent winners / sell recent losers) and related momentum research in equities and other asset classes.

# Trading (Algorithm) Hypotheses
Stocks that have performed well over the recent past (e.g., last **3 months**) tend to continue outperforming over the next month, so selecting the **top-N momentum** stocks and rebalancing monthly can produce positive risk-adjusted returns (after costs) over a test period.

# Data
We export daily data from the provided database (derived from tick tables) and use it to compute monthly features for a momentum backtest.

Default configuration (edit in `config/config.yaml`):

- **Data export window** (`data_collection`):
  - start: `2022-01-01`
  - end: `2024-01-01`
  - tickers: `["HPG", "VIC", "VNM"]`

- **Backtest periods** (`periods`):
  - In-sample: `2021-01-01` → `2022-12-31`
  - Out-of-sample: `2023-01-01` → `2023-12-31`

> Note: Make sure your `data_collection` window covers the dates you want to backtest (both in-sample and out-of-sample).

## Data Collection
- Put your `database.json` (credentials/config) in the project root (or update `database_json` in `config/config.yaml`).
- Configure the data collection range and tickers in `config/config.yaml`, e.g.
```
data_collection:
  start: "2022-01-01"
  end: "2024-01-01"
  tickers: ["HPG", "VIC", "VNM"]
```
- Run:
```
python run_data_collection.py
```
- Output:
  - `data/processed/daily_data.csv`

## Data Processing
Daily data is transformed into a monthly feature table used by the strategy:
- `mom_{mom_months}m`: momentum over a month-end lookback window (default `mom_months = 3`)
- `vol_{vol_days}d`: volatility over a daily-return lookback (default `vol_days = 60`)
- `avg_daily_volume`: liquidity proxy (monthly mean daily volume)
- `fwd_ret_1m`: next-month forward return (used for evaluation)

Run:
```
python run_data_processing.py
```
Output:
- `data/processed/monthly_features.csv`

# Implementation
- **Data exporter**: `src/data/export_daily.py`
  - Aggregates tick tables into daily close price and daily volume per ticker.
- **Feature engineering**: `src/data/process_daily.py`
  - Converts daily data into monthly snapshots + features.
- **Backtest engine**: `src/backtest/momentum_backtest.py`
  - Monthly rebalance:
    - select top-N tickers by `mom_{mom_months}m`
    - weight scheme: `equal` or `inv_vol`
    - enforce `max_weight`
    - apply transaction cost: `cost = commission * turnover`
- **Optimization**: `src/optimize/optimize_momentum.py`
  - Grid search on (optional): `mom_months`, `vol_days`, `top_n`, `weight_scheme`
  - Select best by Sharpe (tie-break by CAGR)

# In-sample Backtesting
Run the backtest driver:
```
python run_backtest.py
```

This will:
- ensure the required feature CSV exists (it will generate it if missing)
- run **baseline** backtest for both in-sample and out-of-sample periods
- print metrics to console

## In-sample Backtesting Result
Outputs (baseline):
- `data/processed/result_in_sample/baseline_returns.csv`
- `data/processed/result_in_sample/baseline_weights.csv`

Metrics are printed to the console logs (CAGR, vol, Sharpe, max drawdown, avg turnover, etc.).

Example result table (fill after running):
| Strategy (baseline) | Sharpe Ratio | Maximum Drawdown | CAGR |
|---------------------|--------------|------------------|------|
| Momentum            | TBD          | TBD              | TBD  |

# Optimization
Run in-sample optimization (grid search):
```
python run_optimization.py
```

Outputs:
- `data/processed/optimization_results.csv`
- `data/processed/best_params.yaml`

To re-run backtest using the optimized parameters:
```
python run_backtest.py
```

If `best_params.yaml` exists, `run_backtest.py` will automatically run an additional backtest tag named `best`.

## Optimization Result
- Inspect `data/processed/optimization_results.csv` to compare parameter sets.
- The best parameters are saved to `data/processed/best_params.yaml` and used automatically by `run_backtest.py`.

Typical columns in the optimization CSV include:
- parameters: `mom_months`, `vol_days`, `top_n`, `weight_scheme`
- metrics: `months`, `cagr`, `vol`, `sharpe`, `max_drawdown`, `avg_turnover`

# Out-of-sample Backtesting
After optimization, run:
```
python run_backtest.py
```

This will produce both baseline and best (if available) out-of-sample outputs.

## Out-of-sample Backtesting Reuslt
Outputs (baseline):
- `data/processed/result_out_sample/baseline_returns.csv`
- `data/processed/result_out_sample/baseline_weights.csv`

Outputs (best, if `best_params.yaml` exists):
- `data/processed/result_out_sample/best_returns.csv`
- `data/processed/result_out_sample/best_weights.csv`

Example result table (fill after running):
| Strategy | Sharpe Ratio | Maximum Drawdown | CAGR |
|----------|--------------|------------------|------|
| Baseline | TBD          | TBD              | TBD  |
| Best     | TBD          | TBD              | TBD  |

# Conclusion
This repository provides a transparent end-to-end implementation of a monthly-rebalanced **Momentum Strategy**: data export → feature engineering → backtesting → optimization → out-of-sample evaluation. The final results depend on the chosen universe, time period, transaction costs, and the optimized hyperparameters.

# Reference
[1] Jegadeesh, N., & Titman, S. (1993). *Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency.*

[2] Moskowitz, T. J., Ooi, Y. H., & Pedersen, L. H. (2012). *Time Series Momentum.*
