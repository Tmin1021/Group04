# Group04

## Abstract


## Introduction


## Trading (Algorithm) Hypotheses


## Data
Currently, we collect daily data of VN30F1M in one month based on the database from Assignment 2:
```bash
data_collection:
  start: "2023-01-01"
  end: "2023-02-01"
  tickers: ["HPG", "VIC", "VNM"]
```
## Implementation
### Environment Setup
1. Set up python virtual environment
```bash
python -m venv .venv
source .venv/Scripts/activate # for Window Git Bash
```
2. Install the required packages
```bash
pip install -r requirements.txt
```

### Data Collection
- For testing the implementation, run:
```bash
python -m src.data.export_daily --help
```

- Download the database.json file from assignment 2 and put it in the project.

- To start collecting daily data, run:
```bash
python run_data_collection.py
```

### Data processing


### In-sample Backtesting


### Optimization


### Out-of-sample Backtesting


### Configurations


## In-sample Backtesting
### Stock Selection

### Rebalancing and Risk Management


### Evaluation Metrics

### Parameters


### In-sample Backtesting Result


### Optimization Result


## Out-of-sample Backtesting


### Out-of-sample Backtesting Result





