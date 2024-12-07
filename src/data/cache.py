import pickle
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataCache:
    """Manages caching of market data."""

    def __init__(self, cache_dir: str = ".cache", expiry_days: int = 7):
        self.cache_dir = Path(cache_dir)
        self.expiry_days = expiry_days
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> pd.DataFrame | None:
        """Retrieve data from cache."""
        cache_file = self.cache_dir / f"{key}.pkl"

        if not cache_file.exists():
            return None

        # Check if cache has expired
        if self._is_expired(cache_file):
            logger.debug(f"Cache expired for {key}")
            cache_file.unlink()
            return None

        try:
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error reading cache for {key}: {str(e)}")
            return None

    def set(self, key: str, data: pd.DataFrame):
        """Save data to cache."""
        cache_file = self.cache_dir / f"{key}.pkl"

        try:
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Error writing cache for {key}: {str(e)}")

    def _is_expired(self, cache_file: Path) -> bool:
        """Check if cache file has expired."""
        modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return datetime.now() - modified_time > timedelta(days=self.expiry_days)

    def clear(self, older_than_days: int | None = None):
        """Clear cache files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            if older_than_days is None or self._is_expired(cache_file):
                cache_file.unlink()
