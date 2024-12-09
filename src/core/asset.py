from enum import Enum


class AssetType(Enum):
    """Enumeration of different asset types."""

    STOCK = "stock"
    ETF = "etf"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    INDEX = "index"
    FUTURE = "future"


class Asset:
    """Represents a tradable asset."""

    COMMODITY_MAPPINGS = {
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "OIL": "CL=F",
        "COPPER": "HG=F",
    }

    INDEX_MAPPINGS = {
        "SPX": "^GSPC",
        "DOW": "^DJI",
        "NASDAQ": "^IXIC",
        "VIX": "^VIX",
    }

    def __init__(self, symbol: str, asset_type: AssetType):
        """Initialize an Asset instance.

        :param symbol: The symbol of the asset.
        :param asset_type: The type of the asset, as an AssetType enum.
        """
        self.symbol = symbol
        self.asset_type = asset_type
        self.yahoo_symbol = self._get_yahoo_symbol()

    def _get_yahoo_symbol(self) -> str:
        if self.asset_type == AssetType.COMMODITY:
            return self.COMMODITY_MAPPINGS.get(self.symbol, self.symbol)
        if self.asset_type == AssetType.INDEX:
            return self.INDEX_MAPPINGS.get(self.symbol, self.symbol)
        return self.symbol
