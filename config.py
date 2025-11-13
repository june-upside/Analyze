"""
Configuration file for API endpoints and constants
"""
from datetime import datetime, timedelta

# Upbit Hot Wallet Address (USDT on Tron Network)
UPBIT_WALLET_ADDRESS = "TVreyZvJWKmcpJGioTzJ81T1JMSXMZ3pV9"

# API Endpoints
TRONSCAN_API_BASE = "https://apilist.tronscan.org/api"
UPBIT_API_BASE = "https://api.upbit.com/v1"
BINANCE_API_BASE = "https://api.binance.com/api/v3"
EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/USD"

# Analysis Period (6 months)
# Note: TronScan API may limit historical data access
# If you get less data than expected, try reducing ANALYSIS_MONTHS or use --collect-only with max_records
ANALYSIS_MONTHS = 6
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=30 * ANALYSIS_MONTHS)

# Maximum records to fetch from TronScan (increase if needed, but takes longer)
MAX_TRON_RECORDS = 50000  # Default: fetch up to 50,000 transactions

# Target Coins
COINS = {
    "BTC": {
        "upbit_market": "KRW-BTC",
        "binance_symbol": "BTCUSDT"
    },
    "ETH": {
        "upbit_market": "KRW-ETH",
        "binance_symbol": "ETHUSDT"
    },
    "USDT": {
        "upbit_market": "KRW-USDT",
        "binance_symbol": None  # USDT premium calculated differently
    }
}

# USDT Token Contract on Tron (TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t)
USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

# Rate limiting (requests per second)
RATE_LIMIT_DELAY = 0.2  # 200ms between requests

# Data cache directory
DATA_DIR = "data"

# Chart output directory
CHART_DIR = "charts"

