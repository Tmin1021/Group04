# run_data_collection.py
from __future__ import annotations

from pathlib import Path
from src.settings import config, DATA_DIR, logger
from src.data.export_daily import export_daily_data

def main():
    # Defaults from config/config.yaml
    database_json = config.get("database_json", "database.json")

    start = config["data_collection"]["start"]
    end = config["data_collection"]["end"]
    tickers = config["data_collection"]["tickers"]

    out_csv = str(DATA_DIR / "processed" / config["data"]["daily_csv"])
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Exporting daily data: %s -> %s", start, end)
    logger.info("Tickers: %s", tickers)
    export_daily_data(database_json, out_csv, start, end, tickers)

if __name__ == "__main__":
    main()