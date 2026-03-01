"""src.optimize.optimize_momentum

Step 5 (Optimization):
Grid search simple hyperparameters for the Momentum Strategy using the in-sample period.

What it optimizes (optional):
- momentum lookback months
- volatility lookback days (only if using inv_vol)
- top_n
- weight_scheme

Outputs:
- data/processed/optimization_results.csv
- data/processed/best_params.yaml

Notes:
- This is intentionally simple and transparent.
- If you don't provide an `optimization:` section in config, it will just evaluate the single config setting.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from src.settings import DATA_DIR, config, logger
from src.data.process_daily import process_daily_to_monthly_features
from src.backtest.momentum_backtest import BacktestParams, run_momentum_backtest


def _as_list(x: Any) -> List[Any]:
    if isinstance(x, list):
        return x
    return [x]


def optimize_momentum(cfg: Dict[str, Any]) -> Dict[str, Any]:
    proc_dir = Path(DATA_DIR) / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    daily_csv = proc_dir / cfg["data"]["daily_csv"]
    if not daily_csv.exists():
        raise FileNotFoundError(
            f"Missing daily CSV at {daily_csv}. Run: python run_data_collection.py (or put your CSV there)."
        )

    in_sample = cfg["periods"]["in_sample"]

    opt = cfg.get("optimization", {})

    mom_months_list = _as_list(opt.get("mom_months", cfg["features"]["mom_months"]))
    vol_days_list = _as_list(opt.get("vol_days", cfg["features"]["vol_days"]))
    top_n_list = _as_list(opt.get("top_n", cfg["portfolio"]["top_n"]))
    weight_scheme_list = _as_list(opt.get("weight_scheme", cfg["portfolio"]["weight_scheme"]))

    results = []

    best = None
    best_key = None

    for mom_m, vol_d, top_n, scheme in itertools.product(
        mom_months_list, vol_days_list, top_n_list, weight_scheme_list
    ):
        mom_m = int(mom_m)
        vol_d = int(vol_d)
        top_n = int(top_n)
        scheme = str(scheme)

        # Build / reuse features for this combo
        feat_path = proc_dir / f"monthly_features_mom{mom_m}m_vol{vol_d}d.csv"
        if not feat_path.exists():
            process_daily_to_monthly_features(
                in_csv=daily_csv,
                out_csv=feat_path,
                mom_months=mom_m,
                vol_days=vol_d,
            )

        params = BacktestParams(
            mom_months=mom_m,
            vol_days=vol_d,
            top_n=top_n,
            weight_scheme=scheme,
            max_weight=float(cfg["portfolio"].get("max_weight", 1.0)),
            min_avg_daily_volume=float(cfg["universe"]["min_avg_daily_volume"]),
            min_price=float(cfg["universe"].get("min_price", 0.0)),
            commission=float(cfg["costs"].get("commission", 0.0)),
        )

        returns_df, _, metrics = run_momentum_backtest(
            features_csv=feat_path,
            start=in_sample["start"],
            end=in_sample["end"],
            params=params,
        )

        row = {
            "mom_months": mom_m,
            "vol_days": vol_d,
            "top_n": top_n,
            "weight_scheme": scheme,
            **metrics,
        }
        results.append(row)

        # Select best by Sharpe; tie-break by CAGR
        key = (metrics.get("sharpe", float("-inf")), metrics.get("cagr", float("-inf")))
        if best_key is None or key > best_key:
            best_key = key
            best = row

        logger.info(
            "Tested mom=%s vol=%s top_n=%s scheme=%s | sharpe=%.3f cagr=%.3f",
            mom_m,
            vol_d,
            top_n,
            scheme,
            row.get("sharpe", float("nan")),
            row.get("cagr", float("nan")),
        )

    # Save results
    import pandas as pd

    res_df = pd.DataFrame(results)
    res_path = proc_dir / "optimization_results.csv"
    res_df.sort_values(["sharpe", "cagr"], ascending=False).to_csv(res_path, index=False)
    logger.info("Saved optimization results -> %s", res_path)

    if best is None:
        raise RuntimeError("Optimization produced no results")

    # Save best params for re-use
    best_params = {
        "features": {"mom_months": int(best["mom_months"]), "vol_days": int(best["vol_days"])},
        "portfolio": {"top_n": int(best["top_n"]), "weight_scheme": str(best["weight_scheme"])},
    }
    best_path = proc_dir / "best_params.yaml"
    best_path.write_text(yaml.safe_dump(best_params, sort_keys=False), encoding="utf-8")
    logger.info("Saved best params -> %s", best_path)

    return {"best": best, "best_params": best_params, "results_csv": str(res_path)}
