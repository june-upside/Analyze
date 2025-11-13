"""
Bitquery GraphQL client for fetching USDT transfers from Upbit hot wallet on TRON
"""
import requests
import pandas as pd
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

from config import (
    UPBIT_WALLET_ADDRESS,
    USDT_TRC20_CONTRACT,
    DATA_DIR,
    START_DATE,
    END_DATE
)


class BitqueryWalletCollector:
    """Collects USDT transfer data using Bitquery GraphQL API"""
    
    def __init__(self, api_key: str = None):
        self.endpoint = "https://graphql.bitquery.io"
        self.api_key = api_key or os.environ.get("BITQUERY_API_KEY", "")
        self.wallet_address = UPBIT_WALLET_ADDRESS
        self.contract_address = USDT_TRC20_CONTRACT
        self.cache_file = os.path.join(DATA_DIR, "bitquery_wallet_transfers.json")
        
        if not self.api_key:
            print("Warning: No Bitquery API key found!")
            print("Set BITQUERY_API_KEY environment variable or pass it to the constructor")
            print("Get free API key at: https://bitquery.io/")
    
    def build_query(self, start_date: str, end_date: str, offset: int = 0, limit: int = 1000) -> str:
        """
        Build GraphQL query for TRON TRC20 transfers
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            offset: Pagination offset
            limit: Number of records per page (max 25000)
            
        Returns:
            GraphQL query string
        """
        query = """
        query ($network: TronNetwork!, $address: String!, $token: String!, $from: ISO8601DateTime, $till: ISO8601DateTime, $offset: Int!, $limit: Int!) {
          tron(network: $network) {
            transfers(
              options: {offset: $offset, limit: $limit, desc: "block.timestamp.time"}
              date: {since: $from, till: $till}
              currency: {is: $token}
              any: [
                {sender: {is: $address}}
                {receiver: {is: $address}}
              ]
            ) {
              block {
                timestamp {
                  time(format: "%Y-%m-%d %H:%M:%S")
                }
              }
              sender {
                address
              }
              receiver {
                address
              }
              amount
              currency {
                address
                symbol
              }
              txHash
            }
          }
        }
        """
        return query
    
    def fetch_transfers(self, start_date: datetime, end_date: datetime, 
                       batch_size: int = 1000) -> List[Dict]:
        """
        Fetch all transfers using pagination
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            batch_size: Records per request (max 25000, recommended 1000-5000)
            
        Returns:
            List of transfer records
        """
        all_transfers = []
        offset = 0
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        print(f"Fetching TRON wallet transfers via Bitquery from {start_str} to {end_str}...")
        
        if not self.api_key:
            print("ERROR: API key required!")
            return []
        
        query = self.build_query(start_str, end_str, offset, batch_size)
        
        while True:
            variables = {
                "network": "tron",
                "address": self.wallet_address,
                "token": self.contract_address,
                "from": start_str,
                "till": end_str,
                "offset": offset,
                "limit": batch_size
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": self.api_key
            }
            
            try:
                response = requests.post(
                    self.endpoint,
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for errors
                if "errors" in data:
                    print(f"GraphQL errors: {data['errors']}")
                    break
                
                # Extract transfers
                if "data" not in data or "tron" not in data["data"]:
                    print("No data in response")
                    break
                
                transfers = data["data"]["tron"]["transfers"]
                
                if not transfers:
                    print("No more transfers available")
                    break
                
                all_transfers.extend(transfers)
                print(f"  Fetched {len(all_transfers)} transfers (batch: {len(transfers)})...")
                
                # If we got fewer than batch_size, we've reached the end
                if len(transfers) < batch_size:
                    break
                
                offset += batch_size
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching transfers: {e}")
                break
        
        print(f"Total transfers fetched: {len(all_transfers)}")
        return all_transfers
    
    def process_transfers(self, transfers: List[Dict]) -> pd.DataFrame:
        """
        Process Bitquery transfer data into DataFrame
        
        Args:
            transfers: List of transfer records from Bitquery
            
        Returns:
            Processed DataFrame
        """
        processed = []
        
        for transfer in transfers:
            timestamp_str = transfer["block"]["timestamp"]["time"]
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            from_address = transfer["sender"]["address"].lower()
            to_address = transfer["receiver"]["address"].lower()
            amount = float(transfer["amount"])
            tx_hash = transfer.get("txHash", "")  # Use txHash instead of transaction.hash
            
            wallet_lower = self.wallet_address.lower()
            
            # Determine direction
            if to_address == wallet_lower:
                direction = "inflow"
            elif from_address == wallet_lower:
                direction = "outflow"
                amount = -amount
            else:
                continue
            
            processed.append({
                "timestamp": timestamp,
                "direction": direction,
                "amount": amount,
                "tx_hash": tx_hash
            })
        
        df = pd.DataFrame(processed)
        if not df.empty:
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    def aggregate_by_hour(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate transfers by hour"""
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "net_flow", "inflow", "outflow"])
        
        df_copy = df.copy()
        df_copy["hour"] = df_copy["timestamp"].dt.floor("H")
        
        # Calculate net flow
        hourly = df_copy.groupby("hour").agg({
            "amount": "sum"
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
    
    def collect(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Main method to collect and process wallet transfer data
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with hourly aggregated transfer data
        """
        # Try to load from cache
        if use_cache:
            transfers = self.load_cache()
        else:
            transfers = []
        
        # Fetch new data if cache is empty or use_cache is False
        if not transfers:
            transfers = self.fetch_transfers(START_DATE, END_DATE)
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
    # Example usage
    api_key = input("Enter your Bitquery API key (or press Enter to use BITQUERY_API_KEY env var): ").strip()
    
    collector = BitqueryWalletCollector(api_key=api_key if api_key else None)
    data = collector.collect(use_cache=False)
    
    if not data.empty:
        print("\nSample data:")
        print(data.head())
        print(f"\nTotal hours: {len(data)}")
        print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")

