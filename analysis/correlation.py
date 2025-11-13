"""
Correlation analysis between wallet flows and kimchi premium
"""
import pandas as pd
import numpy as np
import os
from scipy import stats
from typing import Dict, Tuple, List

from config import DATA_DIR


class CorrelationAnalyzer:
    """Analyzes correlation between wallet flows and premiums"""
    
    def __init__(self):
        self.wallet_data = None
        self.premium_data = None
        self.merged_data = None
        
    def load_data(self):
        """Load wallet and premium data"""
        print("Loading data for correlation analysis...")
        
        # Load wallet data
        wallet_file = os.path.join(DATA_DIR, "wallet_transfers_hourly.csv")
        if os.path.exists(wallet_file):
            self.wallet_data = pd.read_csv(wallet_file)
            self.wallet_data["timestamp"] = pd.to_datetime(self.wallet_data["timestamp"])
            print(f"  Loaded wallet data: {len(self.wallet_data)} records")
        else:
            print("  Error: Wallet data not found")
            return False
        
        # Load premium data
        premium_file = os.path.join(DATA_DIR, "kimchi_premiums_hourly.csv")
        if os.path.exists(premium_file):
            self.premium_data = pd.read_csv(premium_file)
            self.premium_data["timestamp"] = pd.to_datetime(self.premium_data["timestamp"])
            print(f"  Loaded premium data: {len(self.premium_data)} records")
        else:
            print("  Error: Premium data not found")
            return False
        
        return True
    
    def merge_data(self) -> pd.DataFrame:
        """
        Merge wallet and premium data on timestamp
        
        Returns:
            Merged DataFrame
        """
        if self.wallet_data is None or self.premium_data is None:
            if not self.load_data():
                return pd.DataFrame()
        
        merged = self.wallet_data.merge(self.premium_data, on="timestamp", how="inner")
        merged = merged.sort_values("timestamp").reset_index(drop=True)
        
        print(f"\nMerged data: {len(merged)} records")
        print(f"Date range: {merged['timestamp'].min()} to {merged['timestamp'].max()}")
        
        self.merged_data = merged
        return merged
    
    def calculate_correlation(self, x: pd.Series, y: pd.Series) -> Tuple[float, float]:
        """
        Calculate Pearson correlation coefficient and p-value
        
        Args:
            x: First series
            y: Second series
            
        Returns:
            Tuple of (correlation, p-value)
        """
        # Remove NaN values
        mask = ~(x.isna() | y.isna())
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 2:
            return 0.0, 1.0
        
        corr, pval = stats.pearsonr(x_clean, y_clean)
        return corr, pval
    
    def calculate_lag_correlation(self, x: pd.Series, y: pd.Series, 
                                  max_lag: int = 48) -> Dict[int, Tuple[float, float]]:
        """
        Calculate correlation at different time lags
        
        Args:
            x: First series (e.g., net flow)
            y: Second series (e.g., premium)
            max_lag: Maximum lag in hours (positive = x leads y, negative = y leads x)
            
        Returns:
            Dictionary mapping lag to (correlation, p-value)
        """
        results = {}
        
        for lag in range(-max_lag, max_lag + 1):
            if lag == 0:
                corr, pval = self.calculate_correlation(x, y)
            elif lag > 0:
                # Positive lag: x leads y (shift y backward)
                y_shifted = y.shift(-lag)
                corr, pval = self.calculate_correlation(x, y_shifted)
            else:
                # Negative lag: y leads x (shift x backward)
                x_shifted = x.shift(lag)
                corr, pval = self.calculate_correlation(x_shifted, y)
            
            results[lag] = (corr, pval)
        
        return results
    
    def analyze_all_correlations(self) -> pd.DataFrame:
        """
        Calculate correlations between wallet flows and all premium types
        
        Returns:
            DataFrame with correlation results
        """
        if self.merged_data is None:
            self.merge_data()
        
        if self.merged_data.empty:
            print("Error: No merged data available")
            return pd.DataFrame()
        
        results = []
        
        # Get premium columns
        premium_cols = [col for col in self.merged_data.columns if col.endswith("_premium")]
        
        print("\n" + "="*60)
        print("CORRELATION ANALYSIS: Wallet Flow vs Kimchi Premium")
        print("="*60)
        
        for premium_col in premium_cols:
            coin = premium_col.replace("_premium", "")
            
            # Net flow correlation
            corr, pval = self.calculate_correlation(
                self.merged_data["net_flow"],
                self.merged_data[premium_col]
            )
            
            results.append({
                "coin": coin,
                "metric": "net_flow",
                "correlation": corr,
                "p_value": pval,
                "significant": pval < 0.05
            })
            
            print(f"\n{coin}:")
            print(f"  Net Flow vs Premium: r={corr:.4f}, p={pval:.4f} {'***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''}")
            
            # Inflow correlation
            corr, pval = self.calculate_correlation(
                self.merged_data["inflow"],
                self.merged_data[premium_col]
            )
            
            results.append({
                "coin": coin,
                "metric": "inflow",
                "correlation": corr,
                "p_value": pval,
                "significant": pval < 0.05
            })
            
            print(f"  Inflow vs Premium: r={corr:.4f}, p={pval:.4f} {'***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''}")
            
            # Outflow correlation
            corr, pval = self.calculate_correlation(
                self.merged_data["outflow"],
                self.merged_data[premium_col]
            )
            
            results.append({
                "coin": coin,
                "metric": "outflow",
                "correlation": corr,
                "p_value": pval,
                "significant": pval < 0.05
            })
            
            print(f"  Outflow vs Premium: r={corr:.4f}, p={pval:.4f} {'***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else ''}")
        
        print("\n" + "="*60)
        print("*** p < 0.001, ** p < 0.01, * p < 0.05")
        print("="*60)
        
        results_df = pd.DataFrame(results)
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "correlation_results.csv")
        results_df.to_csv(output_file, index=False)
        print(f"\nSaved correlation results to {output_file}")
        
        return results_df
    
    def analyze_lag_correlations(self, max_lag: int = 48) -> Dict[str, pd.DataFrame]:
        """
        Calculate lag correlations for all premium types
        
        Args:
            max_lag: Maximum lag in hours
            
        Returns:
            Dictionary mapping coin names to DataFrames with lag correlation results
        """
        if self.merged_data is None:
            self.merge_data()
        
        if self.merged_data.empty:
            print("Error: No merged data available")
            return {}
        
        results = {}
        premium_cols = [col for col in self.merged_data.columns if col.endswith("_premium")]
        
        print(f"\n{'='*60}")
        print(f"LAG CORRELATION ANALYSIS (max_lag={max_lag} hours)")
        print(f"{'='*60}")
        
        for premium_col in premium_cols:
            coin = premium_col.replace("_premium", "")
            
            print(f"\nCalculating lag correlations for {coin}...")
            
            lag_results = self.calculate_lag_correlation(
                self.merged_data["net_flow"],
                self.merged_data[premium_col],
                max_lag=max_lag
            )
            
            # Convert to DataFrame
            lag_df = pd.DataFrame([
                {"lag": lag, "correlation": corr, "p_value": pval}
                for lag, (corr, pval) in lag_results.items()
            ])
            
            lag_df = lag_df.sort_values("lag")
            
            # Find best correlation
            best_idx = lag_df["correlation"].abs().idxmax()
            best_lag = lag_df.loc[best_idx, "lag"]
            best_corr = lag_df.loc[best_idx, "correlation"]
            best_pval = lag_df.loc[best_idx, "p_value"]
            
            print(f"  Best correlation at lag {best_lag}h: r={best_corr:.4f}, p={best_pval:.4f}")
            
            if best_lag > 0:
                print(f"    -> Net flow leads premium by {best_lag} hours")
            elif best_lag < 0:
                print(f"    -> Premium leads net flow by {abs(best_lag)} hours")
            else:
                print(f"    -> Simultaneous correlation")
            
            results[coin] = lag_df
            
            # Save to CSV
            output_file = os.path.join(DATA_DIR, f"lag_correlation_{coin.lower()}.csv")
            lag_df.to_csv(output_file, index=False)
            print(f"  Saved to {output_file}")
        
        return results
    
    def get_summary_statistics(self) -> pd.DataFrame:
        """
        Calculate summary statistics for the merged data
        
        Returns:
            DataFrame with summary statistics
        """
        if self.merged_data is None:
            self.merge_data()
        
        if self.merged_data.empty:
            return pd.DataFrame()
        
        summary = self.merged_data.describe()
        
        # Save to CSV
        output_file = os.path.join(DATA_DIR, "summary_statistics.csv")
        summary.to_csv(output_file)
        print(f"\nSaved summary statistics to {output_file}")
        
        return summary


if __name__ == "__main__":
    analyzer = CorrelationAnalyzer()
    
    # Merge data
    merged = analyzer.merge_data()
    
    # Calculate correlations
    correlations = analyzer.analyze_all_correlations()
    
    # Calculate lag correlations
    lag_correlations = analyzer.analyze_lag_correlations(max_lag=48)
    
    # Get summary statistics
    summary = analyzer.get_summary_statistics()
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print("="*60)

