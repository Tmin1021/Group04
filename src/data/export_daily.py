"""
Example exporter for daily data from tick table(s).

Adjust SQL to match your database schema (your notebooks show tables under "quote").
If you already have `data/daily_data.csv`, you can ignore this module.
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.data.db import DBInfo, connect
from src.settings import logger, DATA_DIR, config

def export_daily_data(database_json: str, out_csv: str, start: str, end: str, tickers: list[str]) -> None:
    if not tickers:
        raise ValueError("tickers must be non-empty")

    placeholders = ",".join(["%s"] * len(tickers))
    sql = f"""
        SELECT date(m.datetime) as datetime, m.tickersymbol, 
               (array_agg(m.price ORDER BY m.datetime DESC))[1] as price,
               sum(coalesce(v.quantity,0)) as quantity
        FROM "quote"."matched" m
        LEFT JOIN "quote"."total" v
          ON m.tickersymbol = v.tickersymbol AND m.datetime = v.datetime
        WHERE m.datetime >= %s AND m.datetime < %s
          AND m.tickersymbol IN ({placeholders})
        GROUP BY 1,2
        ORDER BY 1,2;
    """
    params = [start, end] + tickers

    db = DBInfo.from_json(database_json)
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [d.name for d in cur.description]

    df = pd.DataFrame(rows, columns=cols)
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logger.info("Saved %s rows to %s", len(df), out_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database_json", default="database.json")
    p.add_argument("--out", default=str(DATA_DIR / config["data"]["daily_csv"]))
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--tickers", nargs="+", required=True)
    args = p.parse_args()
    export_daily_data(args.database_json, args.out, args.start, args.end, args.tickers)

if __name__ == "__main__":
    main()
