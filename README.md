# GROUP04 - Momentum Strategy

## Abstract
This project implements a **Price Momentum** trading strategy using a simplified 6-step workflow for developing a trading algorithm:
1) Form Algorithm Hypothesis  
2) Data Collection  
3) Data Processing / Feature Engineering  
4) In-sample Backtesting  
5) Optimization  
6) Out-of-sample Backtesting  

We use daily market data to construct **monthly momentum & volatility features**, then run a **monthly rebalanced** backtest: at each month-end we select the **top-N tickers by momentum**, allocate weights (equal-weight or inverse-volatility), apply transaction costs based on turnover, and evaluate performance via metrics like **CAGR, volatility, Sharpe ratio, and max drawdown**.


## Strategy Overview (Momentum)
**Hypothesis:** assets that performed well over the recent past tend to keep performing well over a short horizon.

**Monthly rebalancing logic:**
- On each month-end date **t**:
  - compute momentum over a lookback window (e.g., `mom_months = 3`)
  - rank tickers by momentum
  - pick **top_n**
  - assign weights:
    - `equal` (equal weights), or
    - `inv_vol` (inverse-vol weights using a daily-volatility lookback)
  - hold from **t → t+1**, realizing the next-month forward return (`fwd_ret_1m`)
  - subtract transaction cost proportional to **turnover**


## Installation
### 1) Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```


## Configuration
Edit `config/config.yaml` to control:
- **data source / tickers** (`data_collection`)
- **in-sample / out-of-sample periods** (`periods`)
- **features** (e.g., `mom_months`, `vol_days`)
- **portfolio rules** (`top_n`, `weight_scheme`, `max_weight`)
- **costs** (`commission`)
- **universe filters** (`min_avg_daily_volume`, `min_price`)


## Data
### Data Collection
This step pulls daily data from the database and saves it to:
`data/processed/daily_data.csv`

Run:
```bash
python run_data_collection.py
```

Output:
- `data/processed/daily_data.csv`


### Data Processing
This step converts daily data into a monthly feature table used by the strategy backtest:
- momentum column: `mom_{mom_months}m`
- volatility column: `vol_{vol_days}d`
- forward return column: `fwd_ret_1m`
- liquidity column: `avg_daily_volume`

Run:
```bash
python run_data_processing.py
```

Output:
- `data/processed/monthly_features.csv`


## Backtesting
### In-sample Backtest
Runs the baseline configuration defined in `config/config.yaml` and saves:
- returns time series
- monthly weights
- prints metrics to console (CAGR, vol, Sharpe, max drawdown, avg turnover, etc.)

Run:
```bash
python run_backtest.py
```

Outputs (baseline):
- `data/processed/result_in_sample/baseline_returns.csv`
- `data/processed/result_in_sample/baseline_weights.csv`
- `data/processed/result_out_sample/baseline_returns.csv`
- `data/processed/result_out_sample/baseline_weights.csv`


## Optimization
### Hyperparameter Search
A simple grid search over parameters:
- `mom_months`
- `vol_days`
- `top_n`
- `weight_scheme`

Run:
```bash
python run_optimization.py
```

Outputs:
- `data/processed/optimization_results.csv`
- `data/processed/best_params.yaml`


## Out-of-sample Backtest
### Evaluate Best Params on Out-of-sample
After optimization, `run_backtest.py` will automatically detect `best_params.yaml` and run a second backtest tagged as **best**.

Run:
```bash
python run_backtest.py
```

Outputs (best, if `best_params.yaml` exists):
- `data/processed/result_in_sample/best_returns.csv`
- `data/processed/result_in_sample/best_weights.csv`
- `data/processed/result_out_sample/best_returns.csv`
- `data/processed/result_out_sample/best_weights.csv`


## Notes / Troubleshooting
- If you see `Missing daily CSV...`, run **data collection** first:
  ```bash
  python run_data_collection.py
  ```
- If you changed `mom_months` or `vol_days`, re-run:
  ```bash
  python run_data_processing.py
  ```
- If `weight_scheme = inv_vol`, make sure volatility lookback is valid and your feature file contains `vol_{vol_days}d`.
- Universe filters (`min_avg_daily_volume`, `min_price`) can reduce the tradable set; if you get many “cash months”, loosen these thresholds.


## What to Submit / Show (typical)
- Config used (`config/config.yaml`)
- In-sample results (baseline vs best)
- Out-of-sample results (baseline vs best)
- Optimization table (`optimization_results.csv`)
- Short explanation of:
  - hypothesis,
  - feature definitions,
  - backtest methodology (monthly rebalance + costs),
  - key metrics and interpretation.
