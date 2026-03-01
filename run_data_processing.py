from __future__ import annotations

from pathlib import Path

from src.settings import DATA_DIR, config, logger
from src.data.process_daily import process_daily_to_monthly_features


def main() -> None:
    in_csv = Path(DATA_DIR) / "processed" / config["data"]["daily_csv"]
    out_csv = Path(DATA_DIR) / "processed" / config["data"]["monthly_features_csv"]

    logger.info("Processing daily -> monthly features")
    logger.info("Input:  %s", in_csv)
    logger.info("Output: %s", out_csv)

    process_daily_to_monthly_features(
        in_csv=in_csv,
        out_csv=out_csv,
        mom_months=int(config["features"]["mom_months"]),
        vol_days=int(config["features"]["vol_days"]),
    )


if __name__ == "__main__":
    main()
