# mf/extract/yahoo.py
from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Union

import pandas as pd
import yfinance as yf

from ..config import settings
from ..utils import normalize_dtindex_to_naive_midnight_utc

# Default mapping from logical keys -> output series names
DEFAULT_SERIES_MAP: Dict[str, str] = {
    "brent": "brent_usd_bbl",
    "stoxx": "stoxx50e_index",
    "ibex": "ibex_index",
    "cac": "cac40_index",
    "psi20": "psi20_index",
}


def _fetch_close(symbol: str, start: str, end: str) -> pd.DataFrame:
    """
    Low-level Yahoo fetcher: returns (date, value, source) with tz-normalized dates.
    """
    y = yf.Ticker(symbol)
    df = y.history(start=start, end=end, auto_adjust=False)

    if df.empty:
        return pd.DataFrame(columns=["date", "value", "source"])

    # Normalize to tz-naive midnight and ensure the index is named 'date'
    df = normalize_dtindex_to_naive_midnight_utc(df)
    df = df.rename_axis("date")

    # Build long frame without assuming yfinance's index name
    out = df.reset_index()[["date", "Close"]].rename(columns={"Close": "value"})
    out["source"] = f"yahoo:{symbol}"
    return out[["date", "value", "source"]]


RequestsArg = Union[
    Iterable[str],  # e.g. ["brent", "stoxx"]
    Mapping[str, str],  # e.g. {"brent": "brent_usd_bbl"}
    None,  # -> use all DEFAULT_SERIES_MAP keys
]


def fetch_yahoo(
    start: str,
    end: str,
    requests_: RequestsArg = None,
    *,
    series_map: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """
    Unified Yahoo extractor.

    Parameters
    ----------
    start, end : str
        Date bounds (YYYY-MM-DD). Passed to yfinance.
    requests_ :
        - None -> fetch ALL known keys (DEFAULT_SERIES_MAP).
        - Iterable[str] -> fetch those keys using default series names.
        - Mapping[str, str] -> custom {key -> series_name}.
    series_map :
        Optional override/extension of default {key -> series_name}. Only
        used when `requests_` is None or an Iterable[str].

    Returns
    -------
    pd.DataFrame
        Long format with columns: date, series, value, source.
        Empty-safe.
    """
    # Resolve what to fetch
    if requests_ is None:
        # All defaults
        eff_map = dict(DEFAULT_SERIES_MAP)
        if series_map:
            eff_map.update(series_map)
    elif isinstance(requests_, Mapping):
        # Caller provided explicit key->series_name mapping
        eff_map = {k.lower(): v for k, v in requests_.items()}
    else:
        # Iterable[str] of keys
        keys = [k.lower() for k in requests_]
        eff_map = dict(DEFAULT_SERIES_MAP)
        if series_map:
            eff_map.update(series_map)
        # keep only requested keys (and validate)
        missing = [k for k in keys if k not in eff_map]
        if missing:
            raise KeyError(f"Unknown Yahoo keys {missing}. Known: {sorted(eff_map)}")
        eff_map = {k: eff_map[k] for k in keys}

    # Pull each key
    frames: List[pd.DataFrame] = []
    for key, series_name in eff_map.items():
        try:
            symbol = settings.get_ticker(key)
            df = _fetch_close(symbol, start, end)
            if df.empty:
                frames.append(
                    pd.DataFrame(columns=["date", "series", "value", "source"])
                )
                continue
            df = df.copy()
            df["series"] = series_name
            frames.append(df[["date", "series", "value", "source"]])
        except Exception:
            # Be resilient: return an explicit empty slice for this key
            frames.append(pd.DataFrame(columns=["date", "series", "value", "source"]))

    if not frames:
        return pd.DataFrame(columns=["date", "series", "value", "source"])

    non_empty = [f for f in frames if not f.empty]
    if not non_empty:
        return pd.DataFrame(columns=["date", "series", "value", "source"])

    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["date", "series"]).reset_index(drop=True)
