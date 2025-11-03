from __future__ import annotations

import pandas as pd

from mf.extract import yahoo


class _FakeTicker:
    """In-memory stand-in for yfinance.Ticker, returns deterministic frames."""

    def __init__(self, symbol: str):
        self.symbol = symbol

    def history(self, start: str, end: str, auto_adjust: bool = False) -> pd.DataFrame:
        # Simulate an empty series for a specific symbol
        if self.symbol == "EMPTY":
            return pd.DataFrame()

        # Build a small tz-aware frame (America/New_York) to test normalization
        idx = pd.date_range(
            "2025-10-01 16:00", periods=3, freq="D", tz="America/New_York"
        )
        df = pd.DataFrame(
            {
                "Open": [1.0, 2.0, 3.0],
                "High": [1.0, 2.0, 3.0],
                "Low": [1.0, 2.0, 3.0],
                "Close": [10.0, 11.0, 12.0],
                "Volume": [100, 200, 300],
            },
            index=idx,
        )
        return df


def test_fetch_yahoo_two_series_normalizes_and_labels(monkeypatch):
    # Patch yfinance.Ticker in the module under test
    monkeypatch.setattr(yahoo, "yf", type("yfmod", (), {"Ticker": _FakeTicker}))

    # Return a concrete symbol (doesn't matter which) for each key
    def _fake_get_ticker(key: str) -> str:
        return "FAKE"

    monkeypatch.setattr(yahoo.settings, "get_ticker", _fake_get_ticker)

    # Call: list[str] mode (uses default series names for keys)
    df = yahoo.fetch_yahoo(
        start="2025-10-01",
        end="2025-10-10",
        requests_=["brent", "stoxx"],
    )

    # Shape: 3 days * 2 series = 6 rows
    assert len(df) == 6
    assert set(df.columns) == {"date", "series", "value", "source"}

    # Dates: tz-naive & normalized to midnight
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["date"].dt.tz is None
    assert (df["date"].dt.hour == 0).all() and (df["date"].dt.minute == 0).all()

    # Series labels are correct (defaults)
    assert set(df["series"].unique()) == {"brent_usd_bbl", "stoxx50e_index"}

    # Source is stamped with yahoo:<symbol>
    assert df["source"].nunique() == 1
    assert df["source"].iloc[0] == "yahoo:FAKE"

    # Values preserved from Close (sanity check)
    # Expect 10.0,11.0,12.0 per series (order sorted by date)
    vals_by_series = {
        s: list(df.loc[df["series"] == s, "value"]) for s in df["series"].unique()
    }
    for series_vals in vals_by_series.values():
        assert series_vals == [10.0, 11.0, 12.0]


def test_fetch_yahoo_handles_empty_series_without_crashing(monkeypatch):
    # Patch yfinance.Ticker again
    monkeypatch.setattr(yahoo, "yf", type("yfmod", (), {"Ticker": _FakeTicker}))

    # Return different symbols per key to simulate one empty series
    def _fake_get_ticker(key: str) -> str:
        return {"brent": "FAKE", "stoxx": "EMPTY"}[key]

    monkeypatch.setattr(yahoo.settings, "get_ticker", _fake_get_ticker)

    df = yahoo.fetch_yahoo(
        start="2025-10-01",
        end="2025-10-10",
        requests_={"brent": "brent_usd_bbl", "stoxx": "stoxx50e_index"},
    )

    # Only brent returns data: 3 rows total
    assert len(df) == 3
    assert set(df["series"].unique()) == {"brent_usd_bbl"}
    assert (df["source"] == "yahoo:FAKE").all()
