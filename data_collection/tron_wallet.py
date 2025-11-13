"""
TronScan API client for fetching USDT transfers from Upbit hot wallet
"""
import requests
import pandas as pd
import time
import json
from datetime import datetime
from typing import List, Dict
import os

from config import (
    TRONSCAN_API_BASE,
    UPBIT_WALLET_ADDRESS,
    USDT_TRC20_CONTRACT,
    RATE_LIMIT_DELAY,
    DATA_DIR,
    START_DATE,
    END_DATE
)


class TronWalletCollector:
    """Collects USDT transfer data from Tron blockchain for Upbit hot wallet"""
    
    def __init__(self):
        self.base_url = TRONSCAN_API_BASE
        self.wallet_address = UPBIT_WALLET_ADDRESS
        self.contract_address = USDT_TRC20_CONTRACT
        self.cache_file = os.path.join(DATA_DIR, "tron_wallet_transfers.json")
        
    def fetch_transfers(self, start_timestamp: int, end_timestamp: int, 
                       limit: int = 50, max_records: int = 10000) -> List[Dict]:
        """
        Fetch USDT transfers for the wallet address
        
        Note: TronScan API may not support filtering by date range effectively,
        so we fetch recent transactions and filter them manually.
        
        Args:
            start_timestamp: Start time in milliseconds
            end_timestamp: End time in milliseconds
            limit: Number of records per page
            max_records: Maximum number of records to fetch
            
        Returns:
            List of transfer records within the date range
        """
        all_transfers = []
        start = 0
        
        print(f"Fetching Tron wallet transfers from {datetime.fromtimestamp(start_timestamp/1000)} to {datetime.fromtimestamp(end_timestamp/1000)}...")
        print(f"Note: This may take several minutes as we need to paginate through the data...")
        
        oldest_timestamp = end_timestamp  # Track oldest timestamp we've seen
        
        while len(all_transfers) < max_records:
            try:
                # TronScan API endpoint for TRC20 transfers
                # Note: The API returns most recent first and may not filter by date correctly
                url = f"{self.base_url}/token_trc20/transfers"
                params = {
                    "relatedAddress": self.wallet_address,
                    "start": start,
                    "limit": limit,
                    "contract_address": self.contract_address
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if "token_transfers" not in data or len(data["token_transfers"]) == 0:
                    print("  No more transfers available from API")
                    break
                    
                transfers = data["token_transfers"]
                
                # Filter transfers by date range
                filtered_transfers = []
                for transfer in transfers:
                    transfer_ts = transfer.get("block_ts", 0)
                    if start_timestamp <= transfer_ts <= end_timestamp:
                        filtered_transfers.append(transfer)
                    
                    # Update oldest timestamp
                    if transfer_ts < oldest_timestamp:
                        oldest_timestamp = transfer_ts
                
                all_transfers.extend(filtered_transfers)
                
                print(f"  Fetched {len(all_transfers)} transfers in date range (total checked: {start + len(transfers)})...")
                print(f"  Oldest transaction so far: {datetime.fromtimestamp(oldest_timestamp/1000)}")
                
                # Stop if we've gone past our start date
                if oldest_timestamp < start_timestamp:
                    print("  Reached transactions older than start date")
                    break
                
                # Check if we've reached the end of available data
                if len(transfers) < limit:
                    print("  Reached end of available data")
                    break
                    
                start += limit
                time.sleep(RATE_LIMIT_DELAY)
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching transfers: {e}")
                break
                
        print(f"Total transfers fetched: {len(all_transfers)}")
        return all_transfers
    
    def process_transfers(self, transfers: List[Dict]) -> pd.DataFrame:
        """
        Process raw transfer data into a structured DataFrame
        
        Args:
            transfers: List of raw transfer records
            
        Returns:
            Processed DataFrame with columns: timestamp, direction, amount, tx_hash
        """
        processed = []
        
        for transfer in transfers:
            timestamp = transfer.get("block_ts", 0) / 1000  # Convert to seconds
            from_address = transfer.get("from_address", "").lower()
            to_address = transfer.get("to_address", "").lower()
            amount = float(transfer.get("quant", 0)) / 1e6  # USDT has 6 decimals
            tx_hash = transfer.get("transaction_id", "")
            
            wallet_lower = self.wallet_address.lower()
            
            # Determine if it's an inflow or outflow
            if to_address == wallet_lower:
                direction = "inflow"
            elif from_address == wallet_lower:
                direction = "outflow"
                amount = -amount  # Make outflows negative
            else:
                continue  # Skip if wallet is not involved
                
            processed.append({
                "timestamp": datetime.fromtimestamp(timestamp),
                "direction": direction,
                "amount": amount,
                "tx_hash": tx_hash
            })
        
        df = pd.DataFrame(processed)
        if not df.empty:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    def aggregate_by_hour(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate transfers by hour
        
        Args:
            df: DataFrame with individual transfers
            
        Returns:
            DataFrame aggregated by hour with net flow
        """
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "net_flow", "inflow", "outflow"])
        
        df_copy = df.copy()
        df_copy["hour"] = df_copy["timestamp"].dt.floor("H")
        
        # Calculate inflow, outflow, and net flow
        hourly = df_copy.groupby("hour").agg({
            "amount": "sum"  # Sum gives net flow (inflows positive, outflows negative)
        }).reset_index()
        
        # Calculate separate inflow and outflow
        inflow = df_copy[df_copy["amount"] > 0].groupby("hour")["amount"].sum()
        outflow = df_copy[df_copy["amount"] < 0].groupby("hour")["amount"].sum().abs()
        
        hourly = hourly.rename(columns={"hour": "timestamp", "amount": "net_flow"})
        hourly["inflow"] = hourly["timestamp"].map(inflow).fillna(0)
        hourly["outflow"] = hourly["timestamp"].map(outflow).fillna(0)
        
        return hourly
    
    def save_cache(self, transfers: List[Dict]):
        """Save raw transfers to cache file"""
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(transfers, f)
        print(f"Cached {len(transfers)} transfers to {self.cache_file}")
    
    def load_cache(self) -> List[Dict]:
        """Load transfers from cache file"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                transfers = json.load(f)
            print(f"Loaded {len(transfers)} transfers from cache")
            return transfers
        return []
    
    def collect(self, use_cache: bool = True, max_records: int = 50000) -> pd.DataFrame:
        """
        Main method to collect and process wallet transfer data
        
        Args:
            use_cache: Whether to use cached data if available
            max_records: Maximum number of records to fetch (increase for more history)
            
        Returns:
            DataFrame with hourly aggregated transfer data
        """
        start_ts = int(START_DATE.timestamp() * 1000)
        end_ts = int(END_DATE.timestamp() * 1000)
        
        # Try to load from cache
        if use_cache:
            transfers = self.load_cache()
        else:
            transfers = []
        
        # Fetch new data if cache is empty or use_cache is False
        if not transfers:
            transfers = self.fetch_transfers(start_ts, end_ts, max_records=max_records)
            if transfers:
                self.save_cache(transfers)
        
        # Process transfers
        df = self.process_transfers(transfers)
        
        if df.empty:
            print("Warning: No transfer data available")
            return pd.DataFrame(columns=["timestamp", "net_flow", "inflow", "outflow"])
        
        # Aggregate by hour
        hourly_df = self.aggregate_by_hour(df)
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "wallet_transfers_hourly.csv")
        hourly_df.to_csv(output_file, index=False)
        print(f"Saved hourly data to {output_file}")
        
        return hourly_df


if __name__ == "__main__":
    collector = TronWalletCollector()
    data = collector.collect(use_cache=False)
    print("\nSample data:")
    print(data.head())
    print(f"\nTotal hours: {len(data)}")
    print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

