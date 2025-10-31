import pandas as pd
import requests

from ..config import settings

KEY = "D.USD.EUR.SP00.A"  # daily USD per EUR reference rate

def fetch_eur_usd(start: str, end: str, http_timeout: int = None) -> pd.DataFrame:
    base = settings.ecb_base.rstrip("/")
    url = (
        f"{base}/data/EXR/{KEY}"
        f"?startPeriod={start}&endPeriod={end}"
        f"&detail=dataonly&format=jsondata"
    )
    r = requests.get(url, timeout=http_timeout or settings.http_timeout)
    r.raise_for_status()
    data = r.json()

    time_vals = data["structure"]["dimensions"]["observation"][0]["values"]
    series_dict = data["dataSets"][0]["series"]
    rows = []
    for serie in series_dict.values():
        for idx_str, arr in serie.get("observations", {}).items():
            t = time_vals[int(idx_str)]["id"]
            v = arr[0]
            rows.append({"date": pd.to_datetime(t), "eurusd": float(v)})
    fx = pd.DataFrame(rows).sort_values("date")
    if fx.empty:
        return pd.DataFrame(columns=["date", "eurusd", "usdeur", "source"])
    fx["usdeur"] = 1.0 / fx["eurusd"]
    fx["source"] = "ecb:data-api"
    fx.reset_index(drop=True, inplace=True)
    return fx
