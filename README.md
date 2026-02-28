# Group04

## Abstract


## Introduction


## Trading (Algorithm) Hypotheses


## Data

 
### Data collection
#### VCBF open-end fund financial portfolio


#### Daily price, quantity of Vietnamese stocks

#### Stocks financial portfolio data

### Data Processing
#### Extract VCBF open-end fund financial portfolio


#### Monthly scores preprocessing


## Implementation
### Environment Setup

### Data Collection


### Data processing


### In-sample Backtesting


### Optimization


### Out-of-sample Backtesting


### Configurations


## In-sample Backtesting
### Stock Selection

### Rebalancing and Risk Management


### Evaluation Metrics
- Backtesting results are stored in the `<DATA_PATH>/backtest/` folder. 
- Used metrics to compare with VNINDEX are: 
  - Return on Investment (ROI)
  - Maximum drawdown (MDD)
  - Sharpe ratio (SR)
  - Sortino ratio (SoR)
  - Calmar ratio (CR)
  - Votality (Vol)
  - Max Time to Recover from a drawdown (MTR) in days
- Other metrics:
  - Cumulative annual growth rate (CAGR)
  - Win rate: the percentage of winning trades over total trades.

### Parameters


### In-sample Backtesting Result


### Optimization Result


## Out-of-sample Backtesting


### Out-of-sample Backtesting Result





