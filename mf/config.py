
from dataclasses import dataclass, field
from typing import Dict
import os

@dataclass
class Settings:
    http_timeout: int = field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT", 30)))
    ecb_base: str = field(default_factory=lambda: os.getenv("ECB_API_BASE", "https://data-api.ecb.europa.eu/service"))
    tickers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.tickers.update({
            "brent": os.getenv("YF_TICK_BRNT", "BZ=F"),
            "stoxx": os.getenv("YF_TICK_STOXX", "^STOXX50E"),
            "ibex":  os.getenv("YF_TICK_IBEX", "^IBEX"),
            "cac":   os.getenv("YF_TICK_CAC", "^FCHI"),
            "psi20": os.getenv("YF_TICK_PSI", "^PSI20"),
        })
        self.tickers = {k.lower(): v for k, v in self.tickers.items() if v}

    def get_ticker(self, key: str) -> str:
        k = key.lower()
        if k not in self.tickers or not self.tickers[k]:
            raise KeyError(f"Missing ticker for '{key}'. Set YF_TICK_* env var.")
        return self.tickers[k]

settings = Settings()