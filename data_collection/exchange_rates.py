"""
Exchange rate data collector for USD/KRW conversion using Yahoo Finance
"""
import pandas as pd
import os
from datetime import datetime, timedelta

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not installed. Install with: pip install yfinance")

from config import (
    DATA_DIR,
    START_DATE,
    END_DATE
)


class ExchangeRateCollector:
    """Collects USD/KRW exchange rate data from Yahoo Finance"""
    
    def __init__(self):
        self.ticker = "KRW=X"  # Yahoo Finance ticker for USD/KRW
        
    def fetch_historical_rates(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch historical USD/KRW exchange rates from Yahoo Finance
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with daily exchange rates
        """
        if not YFINANCE_AVAILABLE:
            print("Error: yfinance not available. Using fallback rate.")
            return self.generate_fallback_rates(start_date, end_date)
        
        try:
            print(f"Fetching USD/KRW rates from Yahoo Finance ({start_date.date()} to {end_date.date()})...")
            
            # Download data from Yahoo Finance
            forex_data = yf.download(
                self.ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),  # Include end date
                progress=False
            )
            
            if forex_data.empty:
                print("Warning: No data received from Yahoo Finance. Using fallback.")
                return self.generate_fallback_rates(start_date, end_date)
            
            # Process the data
            df = pd.DataFrame({
                "date": forex_data.index,
                "rate": forex_data["Close"].values
            })
            
            # Reset index and convert to datetime
            df = df.reset_index(drop=True)
            df["date"] = pd.to_datetime(df["date"])
            
            print(f"  Fetched {len(df)} daily rates")
            print(f"  Rate range: {df['rate'].min():.2f} - {df['rate'].max():.2f} KRW/USD")
            
            return df
            
        except Exception as e:
            print(f"Error fetching exchange rates from Yahoo Finance: {e}")
            print("Using fallback rate...")
            return self.generate_fallback_rates(start_date, end_date)
    
    def generate_fallback_rates(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Generate fallback rates if Yahoo Finance fails
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with approximate rates
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        df = pd.DataFrame({
            "date": dates,
            "rate": 1350.0  # Approximate average rate
        })
        return df
    
    def expand_to_hourly(self, daily_df: pd.DataFrame, 
                        start_date: datetime, 
                        end_date: datetime) -> pd.DataFrame:
        """
        Expand daily exchange rates to hourly by forward-filling
        
        Args:
            daily_df: DataFrame with daily rates
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with hourly rates
        """
        # Generate hourly timestamps
        hourly_timestamps = pd.date_range(
            start=start_date.replace(hour=0, minute=0, second=0, microsecond=0),
            end=end_date,
            freq='H'
        )
        
        # Create hourly dataframe
        hourly_df = pd.DataFrame({"timestamp": hourly_timestamps})
        hourly_df["date"] = hourly_df["timestamp"].dt.date
        
        # Merge with daily rates
        daily_df["date"] = pd.to_datetime(daily_df["date"]).dt.date
        hourly_df = hourly_df.merge(daily_df[["date", "rate"]], on="date", how="left")
        
        # Forward fill missing values
        hourly_df["rate"] = hourly_df["rate"].ffill().bfill()
        
        # Drop the date column
        hourly_df = hourly_df[["timestamp", "rate"]]
        
        return hourly_df
    
    def collect(self) -> pd.DataFrame:
        """
        Collect exchange rate data for the analysis period
        
        Returns:
            DataFrame with hourly exchange rates
        """
        print("Collecting USD/KRW exchange rates from Yahoo Finance...")
        
        # Fetch historical daily rates
        daily_df = self.fetch_historical_rates(START_DATE, END_DATE)
        
        # Expand to hourly
        hourly_df = self.expand_to_hourly(daily_df, START_DATE, END_DATE)
        
        print(f"Generated {len(hourly_df)} hourly exchange rate records")
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "exchange_rates_hourly.csv")
        hourly_df.to_csv(output_file, index=False)
        print(f"Saved exchange rate data to {output_file}")
        
        return hourly_df
    


if __name__ == "__main__":
    collector = ExchangeRateCollector()
    data = collector.collect()
    
    print("\nSummary:")
    print(f"Total hours: {len(data)}")
    print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"Rate range: {data['rate'].min():.2f} - {data['rate'].max():.2f} KRW/USD")

