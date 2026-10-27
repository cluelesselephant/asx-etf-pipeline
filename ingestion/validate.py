"""Data quality checks that run before anything is loaded into Snowflake."""
import pandas as pd

PRICE_COLUMNS = ["TICKER", "PRICE_DATE", "OPEN",
                 "HIGH", "LOW", "CLOSE", "ADJ_CLOSE", "VOLUME"]


def validate_prices(df: pd.DataFrame) -> list[str]:
    """Return a list of problems. An empty list means the batch is safe to load."""
    missing = set(PRICE_COLUMNS) - set(df.columns)
    if missing:
        return [f"missing columns: {sorted(missing)}"]
    problems = []
    if df.empty:
        problems.append("no rows returned")
    if df.duplicated(["TICKER", "PRICE_DATE"]).any():
        problems.append("duplicate ticker/date rows")
    if df["CLOSE"].isna().any():
        problems.append("null close prices")
    if (df["CLOSE"] <= 0).any():
        problems.append("non-positive close prices")
    if (df["HIGH"] < df["LOW"]).any():
        problems.append("high below low")
    return problems
