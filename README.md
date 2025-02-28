# basic-binance-KDJ-SKDJ-Bollinger-trade-bot

# Binance Trading Bot

This repository contains two versions of a trading bot for Binance using a technical strategy based on KDJ, SKDJ, Bollinger Bands, and RSI.

## Versions

- **Backtest Version (`backtest.py`)**  
  Simulates historical trades using 4-hour timeframe data. It calculates the technical indicators, generates trade signals, and logs detailed trade information (including indicator values at trade open and close). Loss-making trades are saved to a JSON file (`loss_trades.json`).

- **Live Trading Version (`live_trader.py`)**  
  Executes live trades on Binance for the BTC/USDT pair using 15-minute timeframe data. It uses 75% of your USDT balance for each trade and automatically closes a position if it incurs a loss of 15% (stop loss).

## Requirements

- Python 3.7+
- [ccxt](https://github.com/ccxt/ccxt)
- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (required for the live trading version)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/korhancosanergun/basic-binance-KDJ-SKDJ-Bollinger-trade-bot.git
   cd <repository_directory>

Install the required packages:
```bash
pip install ccxt pandas numpy python-dotenv
```
## Usage

Backtest Version
Run the backtest script:

```bash
python backtest.py
```

Input the trading pair:

When prompted, enter a trading pair (e.g., BTC/USDT).

Review the output:
The script will fetch historical 4-hour data, calculate indicators, generate trade signals, and simulate trades. Detailed trade history will be logged, and any loss-making trades will be saved to loss_trades.json.

Live Trading Version
Create a .env file in the repository directory and add your Binance API keys:
```bash
BINANCE_API_KEY='your_api_key_here'
BINANCE_API_SECRET='your_api_secret_here'
```
Run the live trading script:

```bash
python live_trader.py
```

Monitor live trades:
The bot will continuously fetch 15-minute data, calculate indicators, generate trading signals, and execute trades using 75% of your USDT balance. A stop loss is triggered if the price falls to 85% of the entry price.

## Disclaimer
# WARNING: This trading bot is provided for educational and reference purposes only. Live trading involves significant risk. Thoroughly test and understand any strategy before using real funds. Use at your own risk.

License
This project is licensed under the MIT License.

```bash
---

With these files you have:

- **backtest.py:** For backtesting the strategy on historical 4h data.
- **live_trader.py:** For live trading on Binance using 15m data.
- **README.md:** Instructions on installation and usage.

Feel free to modify the code or README as needed. Good luck and happy coding!
```
