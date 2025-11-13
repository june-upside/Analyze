"""
Upbit API client for fetching cryptocurrency prices in KRW
"""
import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict

from config import (
    UPBIT_API_BASE,
    COINS,
    RATE_LIMIT_DELAY,
    DATA_DIR,
    START_DATE,
    END_DATE
)


class UpbitPriceCollector:
    """Collects price data from Upbit exchange"""
    
    def __init__(self):
        self.base_url = UPBIT_API_BASE
        
    def fetch_candles(self, market: str, to_time: datetime, count: int = 200) -> List[Dict]:
        """
        Fetch hourly candles from Upbit
        
        Args:
            market: Market code (e.g., "KRW-BTC")
            to_time: End time for the query
            count: Number of candles to fetch (max 200)
            
        Returns:
            List of candle data
        """
        url = f"{self.base_url}/candles/minutes/60"
        params = {
            "market": market,
            "to": to_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "count": count
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Upbit candles for {market}: {e}")
            return []
    
    def collect_market_data(self, market: str, start_date: datetime, 
                           end_date: datetime) -> pd.DataFrame:
        """
        Collect all hourly data for a market within date range
        
        Args:
            market: Market code
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with hourly price data
        """
        all_candles = []
        current_time = end_date
        
        print(f"Fetching Upbit data for {market}...")
        
        while current_time > start_date:
            candles = self.fetch_candles(market, current_time, count=200)
            
            if not candles:
                break
            
            all_candles.extend(candles)
            
            # Get the earliest timestamp from this batch
            earliest = min(candles, key=lambda x: x["candle_date_time_kst"])
            current_time = datetime.fromisoformat(earliest["candle_date_time_kst"].replace("Z", "+00:00"))
            
            print(f"  Fetched {len(all_candles)} candles, earliest: {current_time}")
            
            # Stop if we've gone past the start date
            if current_time <= start_date:
                break
            
            time.sleep(RATE_LIMIT_DELAY)
        
        # Process into DataFrame
        df = self.process_candles(all_candles)
        
        # Filter to exact date range
        if not df.empty:
            df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]
        
        print(f"Total candles for {market}: {len(df)}")
        return df
    
    def process_candles(self, candles: List[Dict]) -> pd.DataFrame:
        """
        Process raw candle data into DataFrame
        
        Args:
            candles: List of candle dictionaries
            
        Returns:
            Processed DataFrame
        """
        processed = []
        
        for candle in candles:
            timestamp = datetime.fromisoformat(candle["candle_date_time_kst"].replace("Z", "+00:00"))
            
            processed.append({
                "timestamp": timestamp,
                "open": candle["opening_price"],
                "high": candle["high_price"],
                "low": candle["low_price"],
                "close": candle["trade_price"],
                "volume": candle["candle_acc_trade_volume"]
            })
        
        df = pd.DataFrame(processed)
        if not df.empty:
            df = df.sort_values("timestamp").reset_index(drop=True)
            df = df.drop_duplicates(subset=["timestamp"])
        
        return df
    
    def collect_all_coins(self) -> Dict[str, pd.DataFrame]:
        """
        Collect price data for all configured coins
        
        Returns:
            Dictionary mapping coin symbols to DataFrames
        """
        results = {}
        
        for coin, config in COINS.items():
            market = config["upbit_market"]
            df = self.collect_market_data(market, START_DATE, END_DATE)
            
            if not df.empty:
                # Save to CSV
                output_file = os.path.join(DATA_DIR, f"upbit_{coin.lower()}_hourly.csv")
                df.to_csv(output_file, index=False)
                print(f"Saved {coin} data to {output_file}")
                
                results[coin] = df
            else:
                print(f"Warning: No data collected for {coin}")
        
        return results


if __name__ == "__main__":
    collector = UpbitPriceCollector()
    data = collector.collect_all_coins()
    
    print("\nSummary:")
    for coin, df in data.items():
        print(f"{coin}: {len(df)} hours, {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"  Price range: {df['close'].min():.2f} - {df['close'].max():.2f} KRW")

