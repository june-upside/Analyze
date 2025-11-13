"""
Exchange rate data collector for USD/KRW conversion
"""
import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict

from config import (
    EXCHANGE_RATE_API,
    DATA_DIR,
    START_DATE,
    END_DATE
)


class ExchangeRateCollector:
    """Collects USD/KRW exchange rate data"""
    
    def __init__(self):
        self.api_url = EXCHANGE_RATE_API
        
    def fetch_current_rate(self) -> float:
        """
        Fetch current USD to KRW exchange rate
        
        Returns:
            Exchange rate (KRW per USD)
        """
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # The API returns rates with USD as base
            # We need KRW per USD
            if "rates" in data and "KRW" in data["rates"]:
                return data["rates"]["KRW"]
            else:
                print("Warning: KRW rate not found in API response")
                return 1300.0  # Fallback approximate rate
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching exchange rate: {e}")
            return 1300.0  # Fallback approximate rate
    
    def generate_hourly_rates(self, daily_rate: float, 
                             start_date: datetime, 
                             end_date: datetime) -> pd.DataFrame:
        """
        Generate hourly exchange rates by interpolating daily rate
        
        Since we typically only have daily exchange rates, we'll use the same
        rate for all hours in a day. In a production system, you'd want to
        fetch actual historical rates from a financial data provider.
        
        Args:
            daily_rate: The exchange rate to use
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with hourly rates
        """
        # Generate hourly timestamps
        hours = []
        current = start_date.replace(minute=0, second=0, microsecond=0)
        
        while current <= end_date:
            hours.append(current)
            current += timedelta(hours=1)
        
        # For simplicity, use the current rate for all historical data
        # In production, you'd fetch actual historical rates
        df = pd.DataFrame({
            "timestamp": hours,
            "rate": daily_rate
        })
        
        return df
    
    def collect(self) -> pd.DataFrame:
        """
        Collect exchange rate data for the analysis period
        
        Returns:
            DataFrame with hourly exchange rates
        """
        print("Fetching USD/KRW exchange rate...")
        
        # Get current rate
        current_rate = self.fetch_current_rate()
        print(f"Current USD/KRW rate: {current_rate:.2f}")
        
        # Generate hourly data
        # Note: This uses current rate for all historical data
        # For better accuracy, integrate with a historical exchange rate API
        df = self.generate_hourly_rates(current_rate, START_DATE, END_DATE)
        
        print(f"Generated {len(df)} hourly exchange rate records")
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "exchange_rates_hourly.csv")
        df.to_csv(output_file, index=False)
        print(f"Saved exchange rate data to {output_file}")
        
        return df
    
    def fetch_historical_rates_alternative(self) -> pd.DataFrame:
        """
        Alternative method using a mock/estimated historical rate
        This provides a more realistic varying exchange rate
        
        Returns:
            DataFrame with estimated historical rates
        """
        print("Generating estimated historical exchange rates...")
        
        # Generate timestamps
        hours = []
        current = START_DATE.replace(minute=0, second=0, microsecond=0)
        
        while current <= END_DATE:
            hours.append(current)
            current += timedelta(hours=1)
        
        # Create synthetic rate with some variation
        # Base rate around 1300 with small fluctuations
        import numpy as np
        np.random.seed(42)  # For reproducibility
        
        base_rate = 1300
        variation = np.random.normal(0, 10, len(hours))  # Small daily variations
        rates = base_rate + variation.cumsum() / 10  # Cumulative for trending
        
        # Keep rates in realistic range (1250-1350)
        rates = np.clip(rates, 1250, 1350)
        
        df = pd.DataFrame({
            "timestamp": hours,
            "rate": rates
        })
        
        return df


if __name__ == "__main__":
    collector = ExchangeRateCollector()
    data = collector.collect()
    
    print("\nSummary:")
    print(f"Total hours: {len(data)}")
    print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"Rate range: {data['rate'].min():.2f} - {data['rate'].max():.2f} KRW/USD")

