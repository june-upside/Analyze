"""
Binance API client for fetching cryptocurrency prices in USD
"""
import requests
import pandas as pd
import time
import os
from datetime import datetime
from typing import List, Dict

from config import (
    BINANCE_API_BASE,
    COINS,
    RATE_LIMIT_DELAY,
    DATA_DIR,
    START_DATE,
    END_DATE
)


class BinancePriceCollector:
    """Collects price data from Binance exchange"""
    
    def __init__(self):
        self.base_url = BINANCE_API_BASE
        
    def fetch_klines(self, symbol: str, start_time: int, end_time: int, 
                     limit: int = 1000) -> List[List]:
        """
        Fetch klines (candlestick data) from Binance
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of candles to fetch (max 1000)
            
        Returns:
            List of kline data
        """
        url = f"{self.base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Binance klines for {symbol}: {e}")
            return []
    
    def collect_symbol_data(self, symbol: str, start_date: datetime, 
                           end_date: datetime) -> pd.DataFrame:
        """
        Collect all hourly data for a symbol within date range
        
        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with hourly price data
        """
        all_klines = []
        
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        current_start = start_ms
        
        print(f"Fetching Binance data for {symbol}...")
        
        # Binance allows max 1000 candles per request
        # For hourly data, 1000 hours = ~41 days
        one_thousand_hours_ms = 1000 * 60 * 60 * 1000
        
        while current_start < end_ms:
            current_end = min(current_start + one_thousand_hours_ms, end_ms)
            
            klines = self.fetch_klines(symbol, current_start, current_end, limit=1000)
            
            if not klines:
                break
            
            all_klines.extend(klines)
            print(f"  Fetched {len(all_klines)} klines")
            
            # Move to next batch
            if len(klines) < 1000:
                break
            
            # Use the last kline's close time + 1ms as the new start
            current_start = klines[-1][6] + 1
            
            time.sleep(RATE_LIMIT_DELAY)
        
        # Process into DataFrame
        df = self.process_klines(all_klines)
        
        print(f"Total klines for {symbol}: {len(df)}")
        return df
    
    def process_klines(self, klines: List[List]) -> pd.DataFrame:
        """
        Process raw kline data into DataFrame
        
        Binance kline format:
        [
          Open time,
          Open,
          High,
          Low,
          Close,
          Volume,
          Close time,
          Quote asset volume,
          Number of trades,
          Taker buy base asset volume,
          Taker buy quote asset volume,
          Ignore
        ]
        
        Args:
            klines: List of kline arrays
            
        Returns:
            Processed DataFrame
        """
        processed = []
        
        for kline in klines:
            timestamp = datetime.fromtimestamp(kline[0] / 1000)
            
            processed.append({
                "timestamp": timestamp,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5])
            })
        
        df = pd.DataFrame(processed)
        if not df.empty:
            df = df.sort_values("timestamp").reset_index(drop=True)
            df = df.drop_duplicates(subset=["timestamp"])
        
        return df
    
    def collect_all_coins(self) -> Dict[str, pd.DataFrame]:
        """
        Collect price data for all configured coins (that have Binance symbols)
        
        Returns:
            Dictionary mapping coin symbols to DataFrames
        """
        results = {}
        
        for coin, config in COINS.items():
            symbol = config["binance_symbol"]
            
            # Skip USDT as it doesn't have a Binance pair (it's the base currency)
            if symbol is None:
                continue
            
            df = self.collect_symbol_data(symbol, START_DATE, END_DATE)
            
            if not df.empty:
                # Save to CSV
                output_file = os.path.join(DATA_DIR, f"binance_{coin.lower()}_hourly.csv")
                df.to_csv(output_file, index=False)
                print(f"Saved {coin} data to {output_file}")
                
                results[coin] = df
            else:
                print(f"Warning: No data collected for {coin}")
        
        return results


if __name__ == "__main__":
    collector = BinancePriceCollector()
    data = collector.collect_all_coins()
    
    print("\nSummary:")
    for coin, df in data.items():
        print(f"{coin}: {len(df)} hours, {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

