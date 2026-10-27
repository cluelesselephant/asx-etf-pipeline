import pandas as pd

from validate import validate_prices


def good_batch() -> pd.DataFrame:
    return pd.DataFrame({
        "TICKER": ["VAS", "VAS"], "PRICE_DATE": ["2026-10-26", "2026-10-27"],
        "OPEN": [108.0, 108.5], "HIGH": [109.0, 109.5], "LOW": [107.5, 108.0],
        "CLOSE": [108.8, 109.3], "ADJ_CLOSE": [108.8, 109.3], "VOLUME": [1000, 1200],
    })


def test_good_batch_passes():
    assert validate_prices(good_batch()) == []


def test_duplicates_fail():
    df = pd.concat([good_batch(), good_batch().head(1)])
    assert "duplicate ticker/date rows" in validate_prices(df)


def test_non_positive_price_fails():
    df = good_batch()
    df.loc[0, "CLOSE"] = -1
    assert "non-positive close prices" in validate_prices(df)


def test_missing_column_fails():
    df = good_batch().drop(columns=["VOLUME"])
    assert validate_prices(df) == ["missing columns: ['VOLUME']"]
