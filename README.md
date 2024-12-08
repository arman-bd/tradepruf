# TradePruf - Simple Python based Trading Strategy Backtester

## 🚨 Disclaimer
This project was developed in a very short period with heavy use of AI assistance. While the code is functional and well-structured, it should be used for educational and research purposes only. Trading financial instruments involves substantial risk of loss. Past performance is not indicative of future results.

## 🚀 Overview
TradePruf is a flexible and extensible backtesting framework that allows you to test trading strategies across multiple asset classes including stocks, cryptocurrencies, and ETFs. It provides detailed performance metrics, portfolio management capabilities, and interactive visualizations.

## ✨ Features
- Multiple asset classes support (Stocks, Crypto, ETFs)
- Built-in trading strategies:
  - Simple Moving Average (SMA) Crossover
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
  - Moving Average Convergence Divergence (MACD)
  - Bollinger Bands
  - ATR Trailing Stop
- Portfolio backtesting with custom allocation
- Detailed performance metrics:
  - Total/Annual Returns
  - Sharpe Ratio
  - Maximum Drawdown
  - Win Rate
  - Trade Statistics
- Interactive visualizations:
  - Equity curves
  - Drawdown analysis
  - Monthly returns heatmap
  - Asset allocation
- Flexible data granularity (1m to 1wk)
- Position sizing and risk management
- Extensible strategy framework

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/arman-bd/tradepruf.git
cd tradepruf
```

2. Create and activate a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -e ".[dev]"
```

## 📊 Quick Start

### Single Asset Backtest
```bash
# Basic backtest
tradepruf backtest --symbol BTC-USD --asset-type crypto --strategy sma

# With visualization
tradepruf backtest \
    --symbol AAPL \
    --asset-type stock \
    --strategy macd \
    --start-date 2023-01-01 \
    --end-date 2024-01-01 \
    --charts interactive
```

### Portfolio Backtest
1. Create a portfolio configuration file:
```json
{
    "initial_capital": 100000,
    "position_size": 0.1,
    "max_positions": 5,
    "start_date": "2023-01-01",
    "end_date": "2024-01-31",
    "interval": "1d",
    "assets": [
        {
            "symbol": "BTC-USD",
            "type": "crypto",
            "strategy": "sma",
            "params": {
                "short_window": 20,
                "long_window": 50
            }
        },
        {
            "symbol": "ETH-USD",
            "type": "crypto",
            "strategy": "rsi"
        },
        {
            "symbol": "AAPL",
            "type": "stock",
            "strategy": "macd"
        }
    ]
}
```

2. Run the backtest:
```bash
tradepruf backtest-portfolio --portfolio portfolios/my_portfolio.json --charts html
```

## 📈 Custom Strategies
Create your own strategy by extending the base Strategy class:

```python
from strategies.base import Strategy, SignalType

class MyCustomStrategy(Strategy):
    def __init__(self, param1: int = 10, param2: float = 2.0):
        super().__init__("My Custom Strategy")
        self.param1 = param1
        self.param2 = param2
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = pd.Series(SignalType.HOLD, index=data.index)
        # Your strategy logic here
        return signals
```

## 📊 Visualization Options
- `interactive`: Display charts in browser
- `html`: Save interactive charts as HTML files
- `png`: Save static chart images
- `none`: No visualization (default)

## 🔍 Performance Metrics
- Total Return
- Annual Return
- Sharpe Ratio
- Maximum Drawdown
- Win Rate
- Average Win/Loss
- Total Trades
- Volatility
- Per-asset Performance

## 🛠 Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy src
```

## 📝 Todo
- [ ] Add more technical indicators
- [ ] Implement portfolio optimization
- [ ] Add transaction costs and slippage
- [ ] Real-time trading capabilities
- [ ] Enhanced risk management features
- [ ] Machine learning strategy support
- [ ] More visualization options
- [ ] Performance optimization for large datasets

## ⚠️ Limitations
- Limited to yfinance data
- No support for options or futures
- Basic position sizing
- No margin trading simulation
- Historical data limitations

## 📜 License
MIT License - see [LICENSE](LICENSE) for details

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments
- YFinance for market data
- Plotly and Matplotlib for visualizations
- Click for CLI interface
- Rich for terminal formatting
- All the AI tools that helped in development

## ⚠️ Risk Warning
This software is for educational purposes only. Trading financial instruments carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade, you should carefully consider your investment objectives, level of experience, and risk appetite.

---
*Note: This project was developed with the assistance of AI tools. While efforts have been made to ensure accuracy and reliability, users should conduct their own testing and validation before using in any real-world applications.*
```