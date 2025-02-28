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
   git clone <repository_url>
   cd <repository_directory>
