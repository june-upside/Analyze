"""
Main script for Kimchi Premium Analysis
Orchestrates the entire workflow: data collection, analysis, and visualization
"""
import sys
import os
from datetime import datetime
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_collection.tron_wallet import TronWalletCollector
from data_collection.upbit_prices import UpbitPriceCollector
from data_collection.binance_prices import BinancePriceCollector
from data_collection.exchange_rates import ExchangeRateCollector
from analysis.premium_calculator import PremiumCalculator
from analysis.correlation import CorrelationAnalyzer
from visualization.charts import ChartGenerator
from config import START_DATE, END_DATE, CHART_DIR


def print_header(text: str):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70 + "\n")


def collect_data(use_cache: bool = True):
    """
    Step 1: Collect all data from APIs
    
    Args:
        use_cache: Whether to use cached data if available
    """
    print_header("STEP 1: DATA COLLECTION")
    
    print(f"Analysis Period: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Duration: {(END_DATE - START_DATE).days} days\n")
    
    # Collect Tron wallet data
    print("1. Collecting Upbit Hot Wallet Transfer Data...")
    print("-" * 70)
    from config import MAX_TRON_RECORDS
    wallet_collector = TronWalletCollector()
    wallet_data = wallet_collector.collect(use_cache=use_cache, max_records=MAX_TRON_RECORDS)
    print(f"✓ Wallet data collected: {len(wallet_data)} hourly records")
    if len(wallet_data) > 0:
        print(f"  Date range: {wallet_data['timestamp'].min()} to {wallet_data['timestamp'].max()}")
    print()
    
    # Collect Upbit prices
    print("2. Collecting Upbit Price Data...")
    print("-" * 70)
    upbit_collector = UpbitPriceCollector()
    upbit_data = upbit_collector.collect_all_coins()
    print(f"✓ Upbit prices collected for {len(upbit_data)} coins\n")
    
    # Collect Binance prices
    print("3. Collecting Binance Price Data...")
    print("-" * 70)
    binance_collector = BinancePriceCollector()
    binance_data = binance_collector.collect_all_coins()
    print(f"✓ Binance prices collected for {len(binance_data)} coins\n")
    
    # Collect exchange rates
    print("4. Collecting USD/KRW Exchange Rate Data...")
    print("-" * 70)
    rate_collector = ExchangeRateCollector()
    rate_data = rate_collector.collect()
    print(f"✓ Exchange rates collected: {len(rate_data)} hourly records\n")
    
    print_header("DATA COLLECTION COMPLETE")


def calculate_premiums():
    """Step 2: Calculate kimchi premiums"""
    print_header("STEP 2: PREMIUM CALCULATION")
    
    calculator = PremiumCalculator()
    premiums = calculator.calculate_all_premiums()
    
    if premiums.empty:
        print("✗ Error: Failed to calculate premiums")
        return False
    
    print(f"\n✓ Premiums calculated: {len(premiums)} hourly records")
    print_header("PREMIUM CALCULATION COMPLETE")
    return True


def analyze_correlations():
    """Step 3: Analyze correlations"""
    print_header("STEP 3: CORRELATION ANALYSIS")
    
    analyzer = CorrelationAnalyzer()
    
    # Merge data
    merged = analyzer.merge_data()
    if merged.empty:
        print("✗ Error: Failed to merge data")
        return False
    
    # Basic correlations
    correlations = analyzer.analyze_all_correlations()
    
    # Lag correlations
    lag_correlations = analyzer.analyze_lag_correlations(max_lag=48)
    
    # Summary statistics
    summary = analyzer.get_summary_statistics()
    
    print_header("CORRELATION ANALYSIS COMPLETE")
    return True


def generate_visualizations():
    """Step 4: Generate visualizations"""
    print_header("STEP 4: VISUALIZATION")
    
    generator = ChartGenerator()
    generator.create_all_charts()
    
    print_header("VISUALIZATION COMPLETE")
    return True


def print_summary():
    """Print analysis summary"""
    print_header("ANALYSIS SUMMARY")
    
    print("Generated Files:")
    print("-" * 70)
    
    print("\nData Files (in data/):")
    print("  • wallet_transfers_hourly.csv")
    print("  • upbit_btc_hourly.csv")
    print("  • upbit_eth_hourly.csv")
    print("  • upbit_usdt_hourly.csv")
    print("  • binance_btc_hourly.csv")
    print("  • binance_eth_hourly.csv")
    print("  • exchange_rates_hourly.csv")
    print("  • kimchi_premiums_hourly.csv")
    print("  • correlation_results.csv")
    print("  • lag_correlation_*.csv")
    print("  • summary_statistics.csv")
    
    print(f"\nChart Files (in {CHART_DIR}/):")
    print("  • timeline_chart_interactive.html  (Interactive timeline)")
    print("  • timeline_chart.png              (Static timeline)")
    print("  • correlation_scatter_plots.png   (Scatter plots)")
    print("  • lag_correlation_heatmap.png     (Lag correlation heatmap)")
    print("  • lag_correlation_plots.png       (Individual lag plots)")
    
    print("\nNext Steps:")
    print("-" * 70)
    print(f"1. Open {CHART_DIR}/timeline_chart_interactive.html in your browser")
    print("   to explore the interactive timeline chart")
    print(f"2. View PNG charts in {CHART_DIR}/ for publication-ready figures")
    print("3. Check data/ folder for raw analysis data and statistics")
    
    print_header("ANALYSIS COMPLETE!")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Analyze correlation between Upbit wallet flows and Kimchi premium"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force fresh data collection (ignore cached data)"
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect data, skip analysis and visualization"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only run analysis (requires existing data)"
    )
    parser.add_argument(
        "--visualize-only",
        action="store_true",
        help="Only generate visualizations (requires existing analysis)"
    )
    
    args = parser.parse_args()
    
    try:
        start_time = datetime.now()
        
        print_header("KIMCHI PREMIUM ANALYSIS")
        print("Analyzing correlation between Upbit hot wallet flows")
        print("and Kimchi premium for BTC, ETH, and USDT")
        print(f"\nStarted at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Execute based on arguments
        if args.visualize_only:
            generate_visualizations()
        elif args.analyze_only:
            if not calculate_premiums():
                return 1
            if not analyze_correlations():
                return 1
            generate_visualizations()
        elif args.collect_only:
            collect_data(use_cache=not args.no_cache)
        else:
            # Full workflow
            collect_data(use_cache=not args.no_cache)
            if not calculate_premiums():
                return 1
            if not analyze_correlations():
                return 1
            generate_visualizations()
        
        # Print summary
        print_summary()
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f"\nTotal execution time: {duration.total_seconds():.1f} seconds")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

