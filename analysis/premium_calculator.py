"""
Kimchi Premium calculator for cryptocurrency markets
"""
import pandas as pd
import numpy as np
import os
from typing import Dict, Tuple

from config import COINS, DATA_DIR


class PremiumCalculator:
    """Calculates kimchi premium for different cryptocurrencies"""
    
    def __init__(self):
        self.upbit_data = {}
        self.binance_data = {}
        self.exchange_rate = None
        
    def load_data(self):
        """Load all necessary data files"""
        print("Loading price data...")
        
        # Load Upbit data
        for coin in COINS.keys():
            upbit_file = os.path.join(DATA_DIR, f"upbit_{coin.lower()}_hourly.csv")
            if os.path.exists(upbit_file):
                df = pd.read_csv(upbit_file)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                self.upbit_data[coin] = df
                print(f"  Loaded Upbit {coin}: {len(df)} records")
            else:
                print(f"  Warning: Upbit {coin} data not found")
        
        # Load Binance data
        for coin in COINS.keys():
            if COINS[coin]["binance_symbol"] is None:
                continue
                
            binance_file = os.path.join(DATA_DIR, f"binance_{coin.lower()}_hourly.csv")
            if os.path.exists(binance_file):
                df = pd.read_csv(binance_file)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                self.binance_data[coin] = df
                print(f"  Loaded Binance {coin}: {len(df)} records")
            else:
                print(f"  Warning: Binance {coin} data not found")
        
        # Load exchange rate
        exchange_file = os.path.join(DATA_DIR, "exchange_rates_hourly.csv")
        if os.path.exists(exchange_file):
            self.exchange_rate = pd.read_csv(exchange_file)
            self.exchange_rate["timestamp"] = pd.to_datetime(self.exchange_rate["timestamp"])
            print(f"  Loaded exchange rates: {len(self.exchange_rate)} records")
        else:
            print("  Warning: Exchange rate data not found")
    
    def calculate_btc_eth_premium(self, coin: str) -> pd.DataFrame:
        """
        Calculate premium for BTC or ETH
        
        Premium = ((Upbit KRW Price / Exchange Rate) - Binance USD Price) / Binance USD Price * 100
        
        Args:
            coin: Coin symbol (BTC or ETH)
            
        Returns:
            DataFrame with timestamp and premium columns
        """
        if coin not in self.upbit_data or coin not in self.binance_data:
            print(f"Warning: Missing data for {coin}")
            return pd.DataFrame()
        
        # Merge data on timestamp
        upbit_df = self.upbit_data[coin][["timestamp", "close"]].rename(columns={"close": "krw_price"})
        binance_df = self.binance_data[coin][["timestamp", "close"]].rename(columns={"close": "usd_price"})
        
        merged = upbit_df.merge(binance_df, on="timestamp", how="inner")
        merged = merged.merge(self.exchange_rate, on="timestamp", how="inner")
        
        # Calculate premium
        merged["upbit_usd_price"] = merged["krw_price"] / merged["rate"]
        merged["premium"] = ((merged["upbit_usd_price"] - merged["usd_price"]) / merged["usd_price"]) * 100
        
        result = merged[["timestamp", "premium"]].copy()
        result = result.rename(columns={"premium": f"{coin}_premium"})
        
        print(f"{coin} premium calculated: {len(result)} records")
        print(f"  Range: {result[f'{coin}_premium'].min():.2f}% to {result[f'{coin}_premium'].max():.2f}%")
        print(f"  Mean: {result[f'{coin}_premium'].mean():.2f}%")
        
        return result
    
    def calculate_usdt_premium(self) -> pd.DataFrame:
        """
        Calculate premium for USDT
        
        USDT Premium = (Upbit USDT-KRW Price - Exchange Rate) / Exchange Rate * 100
        
        Returns:
            DataFrame with timestamp and premium columns
        """
        if "USDT" not in self.upbit_data:
            print("Warning: Missing USDT data")
            return pd.DataFrame()
        
        # USDT should theoretically be equal to 1 USD
        # So we compare Upbit's USDT-KRW price with the exchange rate
        upbit_df = self.upbit_data["USDT"][["timestamp", "close"]].rename(columns={"close": "usdt_krw_price"})
        
        merged = upbit_df.merge(self.exchange_rate, on="timestamp", how="inner")
        
        # Calculate premium
        merged["premium"] = ((merged["usdt_krw_price"] - merged["rate"]) / merged["rate"]) * 100
        
        result = merged[["timestamp", "premium"]].copy()
        result = result.rename(columns={"premium": "USDT_premium"})
        
        print(f"USDT premium calculated: {len(result)} records")
        print(f"  Range: {result['USDT_premium'].min():.2f}% to {result['USDT_premium'].max():.2f}%")
        print(f"  Mean: {result['USDT_premium'].mean():.2f}%")
        
        return result
    
    def calculate_all_premiums(self) -> pd.DataFrame:
        """
        Calculate premiums for all coins and merge into single DataFrame
        
        Returns:
            DataFrame with timestamp and all premium columns
        """
        self.load_data()
        
        all_premiums = []
        
        # Calculate BTC premium
        if "BTC" in COINS:
            btc_premium = self.calculate_btc_eth_premium("BTC")
            if not btc_premium.empty:
                all_premiums.append(btc_premium)
        
        # Calculate ETH premium
        if "ETH" in COINS:
            eth_premium = self.calculate_btc_eth_premium("ETH")
            if not eth_premium.empty:
                all_premiums.append(eth_premium)
        
        # Calculate USDT premium
        if "USDT" in COINS:
            usdt_premium = self.calculate_usdt_premium()
            if not usdt_premium.empty:
                all_premiums.append(usdt_premium)
        
        # Merge all premiums
        if not all_premiums:
            print("Error: No premium data calculated")
            return pd.DataFrame()
        
        result = all_premiums[0]
        for premium_df in all_premiums[1:]:
            result = result.merge(premium_df, on="timestamp", how="outer")
        
        result = result.sort_values("timestamp").reset_index(drop=True)
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "kimchi_premiums_hourly.csv")
        result.to_csv(output_file, index=False)
        print(f"\nSaved all premiums to {output_file}")
        
        return result
    
    def add_moving_averages(self, df: pd.DataFrame, windows: list = [24, 168]) -> pd.DataFrame:
        """
        Add moving averages to premium data
        
        Args:
            df: DataFrame with premium columns
            windows: List of window sizes (in hours). Default: 24h and 168h (1 week)
            
        Returns:
            DataFrame with additional MA columns
        """
        result = df.copy()
        
        for col in df.columns:
            if col == "timestamp":
                continue
            
            for window in windows:
                ma_col = f"{col}_ma{window}"
                result[ma_col] = result[col].rolling(window=window, min_periods=1).mean()
        
        return result


if __name__ == "__main__":
    calculator = PremiumCalculator()
    premiums = calculator.calculate_all_premiums()
    
    print("\nSample premium data:")
    print(premiums.head())
    print(f"\nTotal records: {len(premiums)}")
    print(f"Date range: {premiums['timestamp'].min()} to {premiums['timestamp'].max()}")

