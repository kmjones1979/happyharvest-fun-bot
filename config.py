# HappyHarvest API Configuration
import os
from dotenv import load_dotenv

load_dotenv()

# API Base URL
BASE_URL = "https://happyharvest.fun"

# API Endpoints
ENDPOINTS = {
    'register': f"{BASE_URL}/register",
    'token': f"{BASE_URL}/auth/token",
    'collect': f"{BASE_URL}/collect",
    'profile': f"{BASE_URL}/profile",
    'claim_land': f"{BASE_URL}/claimLand",
    'expand_land': f"{BASE_URL}/expandLand",
    'land': f"{BASE_URL}/land",
    'crops': f"{BASE_URL}/crops",
    'plant': f"{BASE_URL}/plant",
    'harvest': f"{BASE_URL}/harvest",
    'leaderboard': f"{BASE_URL}/leaderboard"
}

# Timing Constants (in seconds)
WATER_COLLECTION_INTERVAL = 30  # Collect water every 30 seconds
TOKEN_REFRESH_INTERVAL = 240    # Refresh token every 4 minutes (5min expiry - 1min buffer)
CROP_CHECK_INTERVAL = 30       # Check crops every 30 seconds for competitive mode
MARKET_CHECK_INTERVAL = 65     # Check market prices every 65 seconds

# Game Constants
MAX_WATER_CAPACITY = 1024
LAND_CLAIM_COST = 5
WATER_WASTE_PENALTY = 10

# Strategy Constants
MIN_WATER_RESERVE = 1          # ULTRA-AGGRESSIVE: Keep only 1 water for emergency victory mode
EXPANSION_WATER_THRESHOLD = 20  # Lowered threshold for first expansion (1x1→2x2)
MARKET_PREMIUM_THRESHOLD = 1.1  # Plant crops when price is 10% above average

# Land Expansion Strategy
FIRST_EXPANSION_WATER_RATIO = 0.67   # Expand to 2x2 when we have 67% of cost (20 water for 30 cost)
AGGRESSIVE_EXPANSION_THRESHOLD = 25   # Start seriously considering expansion at 25 water

# Farmer credentials (will be loaded from .env file)
FARMER_NAME = os.getenv('FARMER_NAME', '')
CLIENT_ID = os.getenv('CLIENT_ID', '')
CLIENT_SECRET = os.getenv('CLIENT_SECRET', '')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO') 