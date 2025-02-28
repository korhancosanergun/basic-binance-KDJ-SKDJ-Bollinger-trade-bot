from dotenv import load_dotenv
import os
import ccxt
import pandas as pd
import time
import logging
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class LiveTrader:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.symbol = 'BTC/USDT'
        self.timeframe = '15m'
        self.position = None  # Stores open position details

    def fetch_data(self):
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe=self.timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df):
        # Calculate KDJ (14,3)
        period = 14
        smoothing = 3
        low_min = df['low'].rolling(window=period).min()
        high_max = df['high'].rolling(window=period).max()
        df['%K'] = (df['close'] - low_min) / (high_max - low_min) * 100
        df['%D'] = df['%K'].rolling(window=smoothing).mean()
        df['%J'] = 3 * df['%K'] - 2 * df['%D']
        # Calculate SKDJ (7,3)
        df['%SK'] = df['%K'].rolling(window=7).mean()
        df['%SD'] = df['%SK'].rolling(window=3).mean()
        # Bollinger Bands (20,2)
        df['SMA'] = df['close'].rolling(window=20).mean()
        df['std'] = df['close'].rolling(window=20).std()
        df['UB'] = df['SMA'] + 2 * df['std']
        df['LB'] = df['SMA'] - 2 * df['std']
        return df

    def generate_signal(self, df):
        last = df.iloc[-1]
        buy_count = 0
        sell_count = 0

        if last['%K'] > last['%D'] and last['%J'] > last['%D']:
            buy_count += 1
        if last['%K'] < last['%D'] and last['%J'] < last['%D']:
            sell_count += 1
        if last['%SK'] > last['%SD']:
            buy_count += 1
        if last['%SK'] < last['%SD']:
            sell_count += 1
        if last['close'] > last['UB']:
            buy_count += 1
        if last['close'] < last['LB']:
            sell_count += 1

        if buy_count >= 2:
            return 'BUY', last
        elif sell_count >= 2:
            return 'SELL', last
        else:
            return 'HOLD', last

    def get_usdt_balance(self):
        try:
            balance = self.exchange.fetch_balance()
            return balance['free']['USDT']
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
            return 0

    def place_order(self, side, amount):
        try:
            order = self.exchange.create_market_order(self.symbol, side, amount)
            logging.info(f"Market {side} order placed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing {side} order: {e}")
            return None

    def run(self):
        logging.info("Live trading bot started...")
        while True:
            df = self.fetch_data()
            if df.empty:
                logging.error("No data fetched, waiting...")
                time.sleep(60)
                continue

            df = self.calculate_indicators(df)
            signal, last_candle = self.generate_signal(df)
            current_price = last_candle['close']
            current_time = last_candle['datetime']
            logging.info(f"Signal: {signal} | Price: {current_price} | Time: {current_time}")

            if self.position is None and signal == 'BUY':
                usdt_balance = self.get_usdt_balance()
                if usdt_balance <= 0:
                    logging.error("Insufficient USDT balance!")
                else:
                    order_size_usdt = usdt_balance * 0.75
                    quantity = order_size_usdt / current_price
                    order = self.place_order('buy', quantity)
                    if order is not None:
                        self.position = {
                            'entry_price': current_price,
                            'quantity': quantity,
                            'entry_time': datetime.utcnow()
                        }
                        logging.info(f"Position opened: {self.position}")
            elif self.position is not None:
                entry_price = self.position['entry_price']
                if current_price <= entry_price * 0.85:
                    order = self.place_order('sell', self.position['quantity'])
                    if order is not None:
                        logging.info(f"Stop loss triggered. Position closed at {current_price} (Entry: {entry_price})")
                        self.position = None
                elif signal == 'SELL':
                    order = self.place_order('sell', self.position['quantity'])
                    if order is not None:
                        logging.info(f"Sell signal received. Position closed at {current_price} (Entry: {entry_price})")
                        self.position = None
            time.sleep(60)

if __name__ == '__main__':
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")
    if not API_KEY or not API_SECRET:
        logging.error("API keys not found. Please set them in the .env file.")
        exit()
    trader = LiveTrader(API_KEY, API_SECRET)
    trader.run()
