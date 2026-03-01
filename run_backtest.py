from __future__ import annotations

from pathlib import Path
import yaml

from src.settings import DATA_DIR, config, logger
from src.data.process_daily import process_daily_to_monthly_features
from src.backtest.momentum_backtest import BacktestParams, run_momentum_backtest


def _ensure_features(mom_months: int, vol_days: int) -> Path:
    proc_dir = Path(DATA_DIR) / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    daily_csv = proc_dir / config["data"]["daily_csv"]
    if not daily_csv.exists():
        raise FileNotFoundError(
            f"Missing {daily_csv}. Run python run_data_collection.py (or place your CSV there)."
        )

    # If using the base config (same mom/vol), write to canonical name
    base_mom = int(config["features"]["mom_months"])
    base_vol = int(config["features"]["vol_days"])

    if mom_months == base_mom and vol_days == base_vol:
        out_csv = proc_dir / config["data"]["monthly_features_csv"]
    else:
        out_csv = proc_dir / f"monthly_features_mom{mom_months}m_vol{vol_days}d.csv"

    if not out_csv.exists():
        process_daily_to_monthly_features(
            in_csv=daily_csv,
            out_csv=out_csv,
            mom_months=mom_months,
            vol_days=vol_days,
        )

    return out_csv


def _run_one(tag: str, mom_months: int, vol_days: int, top_n: int, weight_scheme: str) -> None:
    feat_csv = _ensure_features(mom_months, vol_days)

    params = BacktestParams(
        mom_months=mom_months,
        vol_days=vol_days,
        top_n=top_n,
        weight_scheme=weight_scheme,
        max_weight=float(config["portfolio"].get("max_weight", 1.0)),
        min_avg_daily_volume=float(config["universe"]["min_avg_daily_volume"]),
        min_price=float(config["universe"].get("min_price", 0.0)),
        commission=float(config["costs"].get("commission", 0.0)),
    )

    proc_dir = Path(DATA_DIR) / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    ins_dir = proc_dir / "result_in_sample"
    oos_dir = proc_dir / "result_out_sample"
    ins_dir.mkdir(parents=True, exist_ok=True)
    oos_dir.mkdir(parents=True, exist_ok=True)

    # In-sample
    ins = config["periods"]["in_sample"]
    ins_ret, ins_w, ins_metrics = run_momentum_backtest(
        features_csv=feat_csv,
        start=ins["start"],
        end=ins["end"],
        params=params,
    )
    ins_ret.to_csv(ins_dir / f"{tag}_returns.csv", index=False)
    ins_w.to_csv(ins_dir / f"{tag}_weights.csv", index=False)

    # Out-of-sample
    oos = config["periods"]["out_sample"]
    oos_ret, oos_w, oos_metrics = run_momentum_backtest(
        features_csv=feat_csv,
        start=oos["start"],
        end=oos["end"],
        params=params,
    )
    oos_ret.to_csv(oos_dir / f"{tag}_returns.csv", index=False)
    oos_w.to_csv(oos_dir / f"{tag}_weights.csv", index=False)

    logger.info("%s | In-sample metrics: %s", tag, ins_metrics)
    logger.info("%s | Out-sample metrics: %s", tag, oos_metrics)


def main() -> None:
    # Always run baseline config
    _run_one(
        tag="baseline",
        mom_months=int(config["features"]["mom_months"]),
        vol_days=int(config["features"]["vol_days"]),
        top_n=int(config["portfolio"]["top_n"]),
        weight_scheme=str(config["portfolio"]["weight_scheme"]),
    )

    # If best_params.yaml exists, run those too
    best_path = Path(DATA_DIR) / "processed" / "best_params.yaml"
    if best_path.exists():
        best = yaml.safe_load(best_path.read_text(encoding="utf-8"))
        _run_one(
            tag="best",
            mom_months=int(best.get("features", {}).get("mom_months", config["features"]["mom_months"])),
            vol_days=int(best.get("features", {}).get("vol_days", config["features"]["vol_days"])),
            top_n=int(best.get("portfolio", {}).get("top_n", config["portfolio"]["top_n"])),
            weight_scheme=str(best.get("portfolio", {}).get("weight_scheme", config["portfolio"]["weight_scheme"])),
        )


if __name__ == "__main__":
    main()