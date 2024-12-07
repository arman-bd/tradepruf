from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from ..core.asset import Asset
from ..utils.logger import get_logger
from .cache import DataCache

logger = get_logger(__name__)


class DataFetcher:
    """Fetches and manages market data."""

    def __init__(self, use_cache: bool = True):
        self.cache = DataCache() if use_cache else None

    def get_data(
        self,
        asset: Asset,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch market data for given asset and time range."""
        if self.cache:
            cached_data = self._try_cache(asset, start_date, end_date, interval)
            if cached_data is not None:
                return cached_data

        try:
            data = self._fetch_from_yahoo(asset, start_date, end_date, interval)

            if self.cache:
                self._save_to_cache(data, asset, start_date, end_date, interval)

            return data

        except Exception as e:
            logger.error(f"Error fetching data for {asset.symbol}: {str(e)}")
            raise

    def _try_cache(
        self, asset: Asset, start_date: datetime, end_date: datetime, interval: str
    ) -> pd.DataFrame | None:
        """Try to get data from cache."""
        if not self.cache:
            return None

        cache_key = self._get_cache_key(asset, start_date, end_date, interval)
        return self.cache.get(cache_key)

    def _save_to_cache(
        self,
        data: pd.DataFrame,
        asset: Asset,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ):
        """Save data to cache."""
        if not self.cache:
            return

        cache_key = self._get_cache_key(asset, start_date, end_date, interval)
        self.cache.set(cache_key, data)

    def _get_cache_key(
        self, asset: Asset, start_date: datetime, end_date: datetime, interval: str
    ) -> str:
        """Generate cache key for data."""
        return f"{asset.symbol}_{start_date.date()}_{end_date.date()}_{interval}"

    def _fetch_from_yahoo(
        self, asset: Asset, start_date: datetime, end_date: datetime, interval: str
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
        ticker = yf.Ticker(asset.yahoo_symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)

        if data.empty:
            raise ValueError(f"No data available for {asset.symbol}")

        return self._process_data(data)

    def _process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Process and validate market data."""
        required_columns = ["Open", "High", "Low", "Close", "Volume"]

        if not all(col in data.columns for col in required_columns):
            raise ValueError("Missing required columns in data")

        # Add useful technical columns
        data["Returns"] = data["Close"].pct_change()
        data["LogReturns"] = np.log(data["Close"] / data["Close"].shift(1))
        data["TrueRange"] = pd.DataFrame(
            {
                "hl": data["High"] - data["Low"],
                "hc": abs(data["High"] - data["Close"].shift(1)),
                "lc": abs(data["Low"] - data["Close"].shift(1)),
            }
        ).max(axis=1)

        return data
