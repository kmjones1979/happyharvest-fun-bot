# 🌾 HappyHarvest Farming Bot 🚜

A comprehensive automated farming system for [HappyHarvest.fun](https://happyharvest.fun/) - the API-based farming game that teaches JWT authentication, rate limiting, and strategic resource management.

## ✨ Features

-   **🔄 Automated Water Collection**: Perfect 30-second timing for maximum water efficiency
-   **🔑 Smart Authentication**: Automatic JWT token management with 5-minute refresh cycles
-   **📈 Market Analysis**: Real-time crop pricing analysis with dynamic market timing
-   **🌱 Strategic Farming**: Intelligent crop selection based on efficiency and market conditions
-   **🏞️ Land Management**: Automated land expansion and plot optimization
-   **📊 Live Dashboard**: Real-time statistics and performance monitoring
-   **🏆 Leaderboard Tracking**: Monitor your ranking against other farmers

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. First-Time Setup (New Farmer)

```bash
python main.py --farmer YourFarmerName
```

The bot will automatically register your farmer and save credentials to `.env`.

### 3. Running with Existing Credentials

If you already have credentials in your `.env` file:

```bash
python main.py
```

## 🛠️ Configuration

Create a `.env` file in the project directory:

```env
# Your HappyHarvest credentials (auto-generated on first registration)
FARMER_NAME=your_farmer_name
CLIENT_ID=farmer-your_farmer_name-abc123
CLIENT_SECRET=secret-xyz789...

# Optional settings
LOG_LEVEL=INFO
```

## 📋 Command Line Options

```bash
# Start farming bot
python main.py

# Start with specific farmer name
python main.py --farmer MyFarmerName

# View current stats only
python main.py --stats

# View leaderboard
python main.py --leaderboard

# Register new farmer
python main.py --register --farmer NewFarmerName
```

## 🎯 Strategy Overview

The bot implements a sophisticated farming strategy:

### 💧 Water Collection

-   Collects water every **exactly 30 seconds** for optimal efficiency
-   Avoids penalties from early collection (10 water loss)
-   Maintains perfect timing even with network delays

### 🌾 Crop Selection

-   Analyzes market conditions every minute
-   Prioritizes crops with **high efficiency** (credits per water)
-   Considers **market premiums** (±15% price fluctuations)
-   Balances quick crops vs. long-term investments

### 🏞️ Land Management

-   Claims initial land when reaching 5 water
-   Expands strategically when profitable
-   Manages expansion costs: 1×1→2×2 (30), 2×2→3×3 (100), etc.

### 📈 Market Timing

-   Monitors real-time price fluctuations
-   Plants crops during premium pricing periods
-   Adapts strategy based on market averages

## 📊 Dashboard Features

The live dashboard displays:

-   **🚜 Farm Status**: Current water, land size, runtime
-   **📊 Bot Statistics**: Water collected, crops planted/harvested, credits earned
-   **📈 Market Status**: Average prices, best efficiency, market trends

## 🏆 Game Mechanics

### Water Collection Rules

-   Collect 1 water every 30 seconds
-   JWT tokens expire every 5 minutes
-   Max capacity: 1,024 water
-   Penalty for early collection: -10 water

### Land & Farming

-   Initial land claim: 5 water
-   Expansion costs increase exponentially
-   19 different crop types with varying strategies
-   Dynamic pricing updates every minute

### Crop Categories

-   **🌱 Starter**: Quick, low-cost (Herb, Lettuce, Onion)
-   **⚖️ Balanced**: Medium investment (Strawberry, Peas, Bean, Tomato, Corn)
-   **🚀 Advanced**: Higher investment (Potato, Carrot, Mushroom, Eggplant)
-   **🏭 Bulk**: High investment, high reward (Wheat, Watermelon, Pumpkin)
-   **⭐ Specialty**: Unique strategies (Cucumber, Chili, Sunflower, Broccoli)

## 🔧 Advanced Usage

### Custom Strategy Configuration

Edit `config.py` to adjust strategy parameters:

```python
# Strategy Constants
MIN_WATER_RESERVE = 20         # Keep minimum water for emergencies
EXPANSION_WATER_THRESHOLD = 100 # Only expand when we have plenty of water
MARKET_PREMIUM_THRESHOLD = 1.1  # Plant crops when price is 10% above average
```

### Monitoring Multiple Farms

You can run multiple bot instances with different farmer names:

```bash
# Terminal 1
python main.py --farmer Farmer1

# Terminal 2
python main.py --farmer Farmer2
```

## 📈 Performance Tips

1. **Stable Internet**: Ensure reliable connection for perfect 30-second timing
2. **Market Timing**: Run during active periods for better market opportunities
3. **Land Strategy**: Expand gradually - don't rush expensive expansions
4. **Crop Diversity**: Balance quick herbs with profitable long-term crops

## 🛡️ Error Handling

The bot includes robust error handling:

-   **Network Issues**: Automatic retry with exponential backoff
-   **Token Expiration**: Proactive refresh before expiration
-   **Rate Limiting**: Respects API timing requirements
-   **Market Changes**: Adapts to price fluctuations

## 🏆 Leaderboard Strategy

To climb the leaderboard:

1. **Consistency**: Perfect 30-second timing beats sporadic high activity
2. **Efficiency**: Focus on high-efficiency crops over expensive ones
3. **Market Timing**: Take advantage of premium pricing windows
4. **Land Investment**: Expand strategically, not aggressively

## 🐛 Troubleshooting

### Common Issues

**"Authentication failed"**

-   Check your `.env` file credentials
-   Try re-registering with `--register` flag

**"Water collection penalty"**

-   Bot timing might be off - restart the bot
-   Check network stability

**"No profitable crops found"**

-   Market conditions may be poor - bot will wait for better opportunities
-   Increase `MIN_WATER_RESERVE` if too conservative

### Debug Mode

Set `LOG_LEVEL=DEBUG` in `.env` for detailed logging.

## 📜 API Reference

The bot interacts with these HappyHarvest endpoints:

-   `POST /register` - Register farmer (one-time only!)
-   `POST /auth/token` - Get JWT tokens
-   `POST /collect` - Collect water every 30 seconds
-   `GET /profile` - View farmer stats
-   `POST /claimLand` - Claim initial land (5 water)
-   `POST /expandLand` - Expand territory
-   `GET /land` - View your farm
-   `GET /crops` - Get crop data with live pricing
-   `POST /plant` - Plant crops
-   `POST /harvest` - Harvest mature crops
-   `GET /leaderboard` - View rankings

## 🤝 Contributing

Want to improve the bot? Consider:

-   Enhanced market prediction algorithms
-   Better crop timing strategies
-   UI improvements
-   Multi-farm management features

## ⚠️ Disclaimer

This bot is for educational purposes and to demonstrate API interaction patterns. Use responsibly and in accordance with HappyHarvest's terms of service.

## 🌟 Happy Farming!

Ready to dominate the HappyHarvest leaderboard? Start your farming empire today! 🚜🌾

---

_Built with Python, Rich, and lots of farming enthusiasm_ 🌱
