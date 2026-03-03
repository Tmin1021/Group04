"""src.data.process_daily

Step 3 (Data Processing):
Convert daily data (price + volume) into *monthly* features for the Momentum Strategy.

Inputs:
- data/processed/daily_data.csv  (from export_daily)

Outputs:
- data/processed/monthly_features.csv

The output is designed for monthly-rebalanced backtests:
Each row is a ticker at a month-end trading date with features computed using ONLY past data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.settings import DATA_DIR, config, logger


REQUIRED_COLS = {"datetime", "tickersymbol", "price", "quantity"}


def _standardize_daily(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(
            f"daily CSV missing columns {sorted(missing)}. Got: {sorted(df.columns)}"
        )

    out = df.copy()
    out["datetime"] = pd.to_datetime(out["datetime"])
    out = out.rename(
        columns={
            "tickersymbol": "ticker",
            "price": "close",
            "quantity": "volume",
        }
    )
    out = out[["datetime", "ticker", "close", "volume"]]
    out = out.sort_values(["ticker", "datetime"]).reset_index(drop=True)

    # basic cleaning
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce")
    out = out.dropna(subset=["close"]).copy()
    out["volume"] = out["volume"].fillna(0.0)
    return out


def process_daily_to_monthly_features(
    in_csv: str | Path,
    out_csv: str | Path,
    mom_months: int,
    vol_days: int,
) -> pd.DataFrame:
    """Create monthly momentum/vol/liquidity features.

    Momentum definition (classic, no look-ahead):
    - For month-end date t, momentum uses prices from (t-1) back to (t-1-mom_months).
      i.e., mom(t) = close(t-1) / close(t-1-mom_months) - 1.

    Volatility definition:
    - Rolling std of daily returns over the last `vol_days` trading days, sampled at month-end.

    Also provides forward 1M return (for backtesting):
    - fwd_ret_1m(t) = close(t+1) / close(t) - 1.
    """

    in_csv = Path(in_csv)
    out_csv = Path(out_csv)

    df_raw = pd.read_csv(in_csv)
    df = _standardize_daily(df_raw)

    # daily returns
    df["daily_ret"] = df.groupby("ticker")["close"].pct_change()

    # daily rolling volatility
    df["vol_daily"] = (
        df.groupby("ticker")["daily_ret"]
        .rolling(window=vol_days, min_periods=max(10, vol_days // 3))
        .std()
        .reset_index(level=0, drop=True)
    )

    # identify each row's month bucket
    df["month"] = df["datetime"].dt.to_period("M")

    # month-end per ticker: last trading day in that month
    idx = df.groupby(["ticker", "month"])["datetime"].idxmax()
    month_end_daily = df.loc[idx, ["ticker", "month", "datetime", "close", "vol_daily"]].copy()
    month_end_daily = month_end_daily.rename(columns={"datetime": "date", "close": "month_end_close"})

    # monthly mean daily volume (liquidity proxy)
    vol_month = (
        df.groupby(["ticker", "month"])["volume"].mean().rename("avg_daily_volume")
    )

    # build monthly series
    month_close = (
        month_end_daily.set_index(["ticker", "month"])["month_end_close"].sort_index()
    )

    # monthly returns (t-1 -> t)
    monthly_ret = month_close.groupby(level=0).pct_change().rename("ret_1m")

    # forward 1M returns for backtest (t -> t+1)
    fwd_ret_1m = monthly_ret.groupby(level=0).shift(-1).rename("fwd_ret_1m")

    # momentum as described above
    mom = (
        month_close.groupby(level=0).shift(1) / month_close.groupby(level=0).shift(1 + mom_months) - 1.0
    ).rename(f"mom_{mom_months}m")

    # volatility sampled at month-end
    vol_m = month_end_daily.set_index(["ticker", "month"])["vol_daily"].rename(f"vol_{vol_days}d")

    features = (
        pd.concat([month_close, vol_month, monthly_ret, fwd_ret_1m, mom, vol_m], axis=1)
        .reset_index()
        .merge(
            month_end_daily[["ticker", "month", "date"]],
            on=["ticker", "month"],
            how="left",
        )
    )

    # Final columns
    features = features.rename(columns={"month_end_close": "price"})
    features = features[
        [
            "date",
            "ticker",
            "price",
            "avg_daily_volume",
            "ret_1m",
            "fwd_ret_1m",
            f"mom_{mom_months}m",
            f"vol_{vol_days}d",
        ]
    ]

    features = features.sort_values(["date", "ticker"]).reset_index(drop=True)

    # replace infinite
    features = features.replace([np.inf, -np.inf], np.nan)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(out_csv, index=False)
    logger.info(
        "Processed %s daily rows -> %s monthly feature rows at %s",
        len(df),
        len(features),
        out_csv,
    )

    return features


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--in_csv",
        default=str(DATA_DIR / "processed" / config["data"]["daily_csv"]),
        help="Daily CSV path",
    )
    p.add_argument(
        "--out_csv",
        default=str(DATA_DIR / "processed" / config["data"]["monthly_features_csv"]),
        help="Output monthly features CSV path",
    )
    p.add_argument("--mom_months", type=int, default=int(config["features"]["mom_months"]))
    p.add_argument("--vol_days", type=int, default=int(config["features"]["vol_days"]))
    args = p.parse_args()

    process_daily_to_monthly_features(
        in_csv=args.in_csv,
        out_csv=args.out_csv,
        mom_months=args.mom_months,
        vol_days=args.vol_days,
    )


if __name__ == "__main__":
    main()
