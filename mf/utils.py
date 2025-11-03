from __future__ import annotations

import pandas as pd


def normalize_dtindex_to_naive_midnight_utc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure df.index is a tz-naive DatetimeIndex aligned to midnight (UTC-normalized day).
    - If index is tz-aware: convert to UTC, drop tz.
    - Floor to day via .normalize().

    Returns the same DataFrame instance with its index adjusted.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        return df
    # If tz-aware, convert to UTC first
    if df.index.tz is not None:
        df = df.tz_convert("UTC")
    # Drop tz and align to midnight
    df.index = df.index.tz_localize(None).normalize()
    return df
