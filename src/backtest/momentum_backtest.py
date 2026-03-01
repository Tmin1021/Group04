"""src.backtest.momentum_backtest

Step 4 & 6: In-sample and out-of-sample backtesting for the Momentum Strategy.

This backtest is monthly rebalanced:
- At each month-end date t, select top-N tickers by momentum.
- Hold them for 1 month (t -> t+1) and realize the forward return.
- Apply transaction cost proportional to turnover.

It consumes the output from Step 3: monthly_features.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.settings import DATA_DIR, config, logger


@dataclass(frozen=True)
class BacktestParams:
    mom_months: int
    vol_days: int
    top_n: int
    weight_scheme: str  # "equal" or "inv_vol"
    max_weight: float
    min_avg_daily_volume: float
    min_price: float
    commission: float


def _compute_metrics(returns: pd.Series) -> Dict[str, float]:
    r = returns.dropna().astype(float)
    if len(r) == 0:
        return {
            "months": 0,
            "cagr": np.nan,
            "vol": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
        }

    equity = (1.0 + r).cumprod()
    n_months = len(r)

    cagr = equity.iloc[-1] ** (12.0 / n_months) - 1.0
    vol = r.std(ddof=1) * np.sqrt(12.0)
    sharpe = (r.mean() / r.std(ddof=1)) * np.sqrt(12.0) if r.std(ddof=1) > 0 else np.nan

    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    max_dd = float(drawdown.min())

    return {
        "months": float(n_months),
        "cagr": float(cagr),
        "vol": float(vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
    }


def _turnover(prev_w: Dict[str, float], new_w: Dict[str, float]) -> float:
    tickers = set(prev_w) | set(new_w)
    tv = 0.0
    for t in tickers:
        tv += abs(new_w.get(t, 0.0) - prev_w.get(t, 0.0))
    return 0.5 * tv


def run_momentum_backtest(
    features_csv: str | Path,
    start: str,
    end: str,
    params: BacktestParams,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """Run backtest and return (returns_df, weights_df, metrics)."""

    features_csv = Path(features_csv)
    df = pd.read_csv(features_csv)
    df["date"] = pd.to_datetime(df["date"])

    mom_col = f"mom_{params.mom_months}m"
    vol_col = f"vol_{params.vol_days}d"

    required = {"date", "ticker", "price", "avg_daily_volume", "fwd_ret_1m", mom_col, vol_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"monthly features missing columns {sorted(missing)}")

    # Filter backtest window on decision dates (month-ends)
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)

    df = df[(df["date"] >= start_dt) & (df["date"] <= end_dt)].copy()

    dates = sorted(df["date"].unique())
    if not dates:
        raise ValueError("No feature rows in the requested date range")

    results = []
    weights_rows = []

    prev_weights: Dict[str, float] = {}

    for d in dates:
        snap = df[df["date"] == d].copy()

        # Need next-month returns to evaluate; if missing, skip (usually last available date)
        snap = snap.dropna(subset=["fwd_ret_1m", mom_col])

        # Universe filters
        snap = snap[snap["price"] >= params.min_price]
        snap = snap[snap["avg_daily_volume"] >= params.min_avg_daily_volume]

        if params.weight_scheme == "inv_vol":
            snap = snap.dropna(subset=[vol_col])
            snap = snap[snap[vol_col] > 0]

        if len(snap) == 0:
            # stay in cash (0 return) but still pay no cost
            results.append(
                {
                    "date": d,
                    "gross_ret": 0.0,
                    "turnover": 0.0,
                    "cost": 0.0,
                    "net_ret": 0.0,
                    "n_positions": 0,
                }
            )
            prev_weights = {}
            continue

        # Select top N momentum
        snap = snap.sort_values(mom_col, ascending=False)
        picks = snap.head(params.top_n).copy()

        # Build weights
        if params.weight_scheme == "equal":
            w = np.ones(len(picks), dtype=float)
        elif params.weight_scheme == "inv_vol":
            w = 1.0 / picks[vol_col].to_numpy(dtype=float)
        else:
            raise ValueError("weight_scheme must be 'equal' or 'inv_vol'")

        # Normalize
        w = w / w.sum() if w.sum() > 0 else np.ones_like(w) / len(w)

        # Cap max weight and renormalize
        if params.max_weight is not None and params.max_weight > 0:
            w = np.minimum(w, params.max_weight)
            w = w / w.sum() if w.sum() > 0 else np.ones_like(w) / len(w)

        new_weights = dict(zip(picks["ticker"].tolist(), w.tolist()))

        # Returns + costs
        gross_ret = float(np.dot(w, picks["fwd_ret_1m"].to_numpy(dtype=float)))
        tv = _turnover(prev_weights, new_weights)
        cost = float(params.commission * tv)
        net_ret = gross_ret - cost

        results.append(
            {
                "date": d,
                "gross_ret": gross_ret,
                "turnover": tv,
                "cost": cost,
                "net_ret": net_ret,
                "n_positions": int(len(picks)),
            }
        )

        for tkr, wi in new_weights.items():
            weights_rows.append({"date": d, "ticker": tkr, "weight": wi})

        prev_weights = new_weights

    returns_df = pd.DataFrame(results).sort_values("date").reset_index(drop=True)
    returns_df["equity"] = (1.0 + returns_df["net_ret"]).cumprod()

    weights_df = pd.DataFrame(weights_rows).sort_values(["date", "ticker"]).reset_index(drop=True)

    metrics = _compute_metrics(returns_df.set_index("date")["net_ret"])
    metrics["avg_turnover"] = float(returns_df["turnover"].mean()) if len(returns_df) else np.nan

    return returns_df, weights_df, metrics


def _params_from_config(cfg: dict) -> BacktestParams:
    return BacktestParams(
        mom_months=int(cfg["features"]["mom_months"]),
        vol_days=int(cfg["features"]["vol_days"]),
        top_n=int(cfg["portfolio"]["top_n"]),
        weight_scheme=str(cfg["portfolio"]["weight_scheme"]),
        max_weight=float(cfg["portfolio"].get("max_weight", 1.0)),
        min_avg_daily_volume=float(cfg["universe"]["min_avg_daily_volume"]),
        min_price=float(cfg["universe"].get("min_price", 0.0)),
        commission=float(cfg["costs"].get("commission", 0.0)),
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--features_csv",
        default=str(DATA_DIR / "processed" / config["data"]["monthly_features_csv"]),
    )
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--top_n", type=int, default=int(config["portfolio"]["top_n"]))
    p.add_argument("--mom_months", type=int, default=int(config["features"]["mom_months"]))
    p.add_argument("--vol_days", type=int, default=int(config["features"]["vol_days"]))
    p.add_argument("--weight_scheme", default=str(config["portfolio"]["weight_scheme"]))
    p.add_argument("--max_weight", type=float, default=float(config["portfolio"].get("max_weight", 1.0)))
    p.add_argument("--min_avg_daily_volume", type=float, default=float(config["universe"]["min_avg_daily_volume"]))
    p.add_argument("--min_price", type=float, default=float(config["universe"].get("min_price", 0.0)))
    p.add_argument("--commission", type=float, default=float(config["costs"].get("commission", 0.0)))

    p.add_argument(
        "--out_dir",
        default=str(DATA_DIR / "processed"),
        help="Where to save backtest outputs",
    )
    p.add_argument("--tag", default="backtest")

    args = p.parse_args()

    params = BacktestParams(
        mom_months=args.mom_months,
        vol_days=args.vol_days,
        top_n=args.top_n,
        weight_scheme=args.weight_scheme,
        max_weight=args.max_weight,
        min_avg_daily_volume=args.min_avg_daily_volume,
        min_price=args.min_price,
        commission=args.commission,
    )

    returns_df, weights_df, metrics = run_momentum_backtest(
        features_csv=args.features_csv,
        start=args.start,
        end=args.end,
        params=params,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ret_path = out_dir / f"{args.tag}_returns.csv"
    w_path = out_dir / f"{args.tag}_weights.csv"

    returns_df.to_csv(ret_path, index=False)
    weights_df.to_csv(w_path, index=False)

    logger.info("Saved returns -> %s", ret_path)
    logger.info("Saved weights -> %s", w_path)
    logger.info("Metrics: %s", metrics)


if __name__ == "__main__":
    main()
