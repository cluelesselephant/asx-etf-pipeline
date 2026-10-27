"""Fetch daily ASX ETF prices from Yahoo Finance, validate them and MERGE into Snowflake."""
import logging
import sys
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from config import HISTORY_PERIOD, TICKERS
from snowflake_client import get_connection, log_run, stage_dataframe
from validate import validate_prices

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fetch_prices")

RENAME = {"Date": "PRICE_DATE", "Open": "OPEN", "High": "HIGH", "Low": "LOW",
          "Close": "CLOSE", "Adj Close": "ADJ_CLOSE", "Volume": "VOLUME"}

MERGE_SQL = """
MERGE INTO ETF_PRICES t
USING ETF_PRICES_STAGE s
  ON t.TICKER = s.TICKER AND t.PRICE_DATE = s.PRICE_DATE::DATE
WHEN MATCHED THEN UPDATE SET
  OPEN = s.OPEN, HIGH = s.HIGH, LOW = s.LOW, CLOSE = s.CLOSE,
  ADJ_CLOSE = s.ADJ_CLOSE, VOLUME = s.VOLUME, LOADED_AT = s.LOADED_AT::TIMESTAMP_NTZ
WHEN NOT MATCHED THEN INSERT
  (TICKER, PRICE_DATE, OPEN, HIGH, LOW, CLOSE, ADJ_CLOSE, VOLUME, SOURCE, LOADED_AT)
VALUES
  (s.TICKER, s.PRICE_DATE::DATE, s.OPEN, s.HIGH, s.LOW, s.CLOSE, s.ADJ_CLOSE,
   s.VOLUME, s.SOURCE, s.LOADED_AT::TIMESTAMP_NTZ)
"""


def extract(tickers: list[str], period: str) -> pd.DataFrame:
    """Download each ticker one at a time and combine them into one DataFrame."""
    frames = []
    for ticker in tickers:
        df = yf.download(f"{ticker}.AX", period=period, interval="1d",
                         auto_adjust=False, progress=False)
        if df.empty:
            log.warning("No data returned for %s", ticker)
            continue
        if isinstance(df.columns, pd.MultiIndex):  # newer yfinance returns (field, ticker)
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index().rename(columns=RENAME)
        df["TICKER"] = ticker
        frames.append(df[["TICKER", *RENAME.values()]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Format dates as text and add lineage columns before staging."""
    df = df.copy()
    df["PRICE_DATE"] = pd.to_datetime(df["PRICE_DATE"]).dt.strftime("%Y-%m-%d")
    df["SOURCE"] = "yfinance"
    df["LOADED_AT"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return df


def main() -> None:
    conn = get_connection()
    try:
        df = extract(TICKERS, HISTORY_PERIOD)
        problems = validate_prices(df)
        if problems:
            log_run(conn, "yfinance", 0, "FAILED", "; ".join(problems))
            log.error("Validation failed: %s", problems)
            sys.exit(1)  # fail loudly so CI and schedulers notice
        stage_dataframe(conn, prepare(df), "ETF_PRICES_STAGE")
        conn.cursor().execute(MERGE_SQL)
        log_run(conn, "yfinance", len(df), "SUCCESS")
        log.info("Loaded %s rows for %s tickers",
                 len(df), df["TICKER"].nunique())
    except Exception as exc:
        log_run(conn, "yfinance", 0, "FAILED", str(exc))
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
