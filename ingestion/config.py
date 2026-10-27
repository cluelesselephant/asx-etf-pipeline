"""Settings for the ETF price pipeline."""

# Broad-market benchmarks plus Global X funds, covering three asset classes
TICKERS = [
    # broad market (Vanguard, iShares, BetaShares)
    "VAS", "IOZ", "A200", "VGS",
    # Global X: equity, equity, commodity, fixed income
    "FANG", "SEMI", "GOLD", "USTB",
]
HISTORY_PERIOD = "2y"
