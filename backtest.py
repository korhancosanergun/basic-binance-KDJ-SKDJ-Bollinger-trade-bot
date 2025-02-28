import ccxt
import pandas as pd
import numpy as np
import time
import logging
import os
import json
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class DataHandler:
    def __init__(self, api_key=None, secret=None):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

    def get_ohlcv(self, symbol, timeframe='4h', limit=1000):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            logging.info(f"{len(df)} data points fetched for: {symbol} {timeframe}")
            return df
        except Exception as e:
            logging.error(f"{symbol} data fetching error: {e}")
            return pd.DataFrame()

class IndicatorCalculator:
    def calculate_kdj(self, df, period=14, smoothing=3):
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        df['%K'] = (df['close'] - low_min) / (high_max - low_min) * 100
        df['%D'] = df['%K'].rolling(window=smoothing).mean()
        df['%J'] = 3 * df['%K'] - 2 * df['%D']
        return df

    def calculate_skdj(self, df, sk_period=7, sd_period=3):
        df['%SK'] = df['%K'].rolling(window=sk_period).mean()
        df['%SD'] = df['%SK'].rolling(window=sd_period).mean()
        return df

    def calculate_bollinger_bands(self, df, period=20, std_multiplier=2):
        df['SMA'] = df['close'].rolling(window=period).mean()
        df['std'] = df['close'].rolling(window=period).std()
        df['UB'] = df['SMA'] + std_multiplier * df['std']
        df['LB'] = df['SMA'] - std_multiplier * df['std']
        return df

    def calculate_rsi(self, df, period=14):
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

class SignalGenerator:
    def generate_signals(self, df):
        # Generate individual signals for KDJ and SKDJ
        df['KDJ_signal'] = 'HOLD'
        df['SKDJ_signal'] = 'HOLD'
        for i in range(1, len(df)):
            # KDJ signal: if previous bar's %K < %D and current bar's %K > %D and %J > %D, then BUY; vice versa for SELL.
            if (df.loc[df.index[i-1], '%K'] < df.loc[df.index[i-1], '%D'] and
                df.loc[df.index[i], '%K'] > df.loc[df.index[i], '%D'] and
                df.loc[df.index[i], '%J'] > df.loc[df.index[i], '%D']):
                df.at[df.index[i], 'KDJ_signal'] = 'BUY'
            elif (df.loc[df.index[i-1], '%K'] > df.loc[df.index[i-1], '%D'] and
                  df.loc[df.index[i], '%K'] < df.loc[df.index[i], '%D'] and
                  df.loc[df.index[i], '%J'] < df.loc[df.index[i], '%D']):
                df.at[df.index[i], 'KDJ_signal'] = 'SELL'
            # SKDJ signal
            if (df.loc[df.index[i-1], '%SK'] < df.loc[df.index[i-1], '%SD'] and
                df.loc[df.index[i], '%SK'] > df.loc[df.index[i], '%SD']):
                df.at[df.index[i], 'SKDJ_signal'] = 'BUY'
            elif (df.loc[df.index[i-1], '%SK'] > df.loc[df.index[i], '%SD'] and
                  df.loc[df.index[i], '%SK'] < df.loc[df.index[i], '%SD']):
                df.at[df.index[i], 'SKDJ_signal'] = 'SELL'
        # Combined signal: Count conditions – require at least two for a BUY or SELL.
        df['Combined_signal'] = 'HOLD'
        for i in range(len(df)):
            buy_count = 0
            sell_count = 0
            if df.loc[df.index[i], 'KDJ_signal'] == 'BUY':
                buy_count += 1
            if df.loc[df.index[i], 'SKDJ_signal'] == 'BUY':
                buy_count += 1
            if df.loc[df.index[i], 'close'] > df.loc[df.index[i], 'UB']:
                buy_count += 1

            if df.loc[df.index[i], 'KDJ_signal'] == 'SELL':
                sell_count += 1
            if df.loc[df.index[i], 'SKDJ_signal'] == 'SELL':
                sell_count += 1
            if df.loc[df.index[i], 'close'] < df.loc[df.index[i], 'LB']:
                sell_count += 1

            # RSI filter: For BUY, RSI must be below 40; for SELL, above 60.
            rsi = df.loc[df.index[i], 'RSI']
            if buy_count >= 2 and rsi < 40:
                df.at[df.index[i], 'Combined_signal'] = 'BUY'
            elif sell_count >= 2 and rsi > 60:
                df.at[df.index[i], 'Combined_signal'] = 'SELL'
            else:
                df.at[df.index[i], 'Combined_signal'] = 'HOLD'
        return df

class Backtester:
    def __init__(self, df, initial_balance=10000):
        self.df = df
        self.balance = initial_balance
        self.position = None
        self.entry_price = None
        self.entry_datetime = None
        self.entry_row = None
        self.trade_history = []
        self.loss_trades = []

    def run_backtest(self):
        for index, row in self.df.iterrows():
            signal = row['Combined_signal']
            price = row['close']
            current_datetime = row['datetime']
            if signal == 'BUY' and self.position is None:
                self.position = 'LONG'
                self.entry_price = price
                self.entry_datetime = current_datetime
                self.entry_row = row.copy()
                logging.info(f"Position opened at {price} | Time: {self.entry_datetime}")
            elif signal == 'SELL' and self.position == 'LONG':
                profit = price - self.entry_price
                self.balance += profit
                close_datetime = current_datetime
                duration = close_datetime - self.entry_datetime
                trade_data = {
                    'entry': self.entry_price,
                    'exit': price,
                    'profit': profit,
                    'open_datetime': self.entry_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    'close_datetime': close_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    'duration': str(duration),
                    'open_KDJ': {
                        '%K': self.entry_row.get('%K'),
                        '%D': self.entry_row.get('%D'),
                        '%J': self.entry_row.get('%J')
                    },
                    'open_SKDJ': {
                        '%SK': self.entry_row.get('%SK'),
                        '%SD': self.entry_row.get('%SD')
                    },
                    'open_Bollinger': {
                        'SMA': self.entry_row.get('SMA'),
                        'UB': self.entry_row.get('UB'),
                        'LB': self.entry_row.get('LB')
                    },
                    'exit_KDJ': {
                        '%K': row.get('%K'),
                        '%D': row.get('%D'),
                        '%J': row.get('%J')
                    },
                    'exit_SKDJ': {
                        '%SK': row.get('%SK'),
                        '%SD': row.get('%SD')
                    },
                    'exit_Bollinger': {
                        'SMA': row.get('SMA'),
                        'UB': row.get('UB'),
                        'LB': row.get('LB')
                    },
                    'exit_RSI': row.get('RSI')
                }
                self.trade_history.append(trade_data)
                logging.info(f"Position closed at {price}, Profit/Loss: {profit} | Duration: {duration}")
                if profit < 0:
                    self.loss_trades.append(trade_data)
                self.position = None
                self.entry_price = None
                self.entry_datetime = None
                self.entry_row = None
        logging.info(f"Backtest complete. Final balance: {self.balance}")
        if self.loss_trades:
            with open("loss_trades.json", "w") as f:
                json.dump(self.loss_trades, f, indent=4)
            logging.info("Loss trades saved to loss_trades.json.")
        return self.trade_history

def main():
    trading_pair = input("Enter trading pair (e.g., BTC/USDT): ").strip()
    if not trading_pair:
        print("No trading pair provided, exiting.")
        return

    data_handler = DataHandler()
    df = data_handler.get_ohlcv(symbol=trading_pair, timeframe='4h', limit=1000)
    if df.empty:
        logging.error("No data fetched, exiting.")
        return

    indicator_calc = IndicatorCalculator()
    df = indicator_calc.calculate_kdj(df, period=14, smoothing=3)
    df = indicator_calc.calculate_skdj(df, sk_period=7, sd_period=3)
    df = indicator_calc.calculate_bollinger_bands(df, period=20, std_multiplier=2)
    df = indicator_calc.calculate_rsi(df, period=14)

    signal_gen = SignalGenerator()
    df = signal_gen.generate_signals(df)

    backtester = Backtester(df, initial_balance=10000)
    trades = backtester.run_backtest()

    logging.info("Trade History:")
    for trade in trades:
        logging.info(trade)

if __name__ == '__main__':
    main()
