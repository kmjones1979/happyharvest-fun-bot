#!/usr/bin/env python3
"""
HappyHarvest Farming Bot
A comprehensive automated farming system for HappyHarvest.fun

Features:
- Automated water collection every 30 seconds
- JWT token management and refresh
- Strategic crop planting and harvesting
- Market analysis and timing
- Land expansion management
- Real-time dashboard with statistics
"""

import argparse
import sys
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from farm_bot import HappyHarvestBot
from config import FARMER_NAME, CLIENT_ID, CLIENT_SECRET

console = Console()

def show_banner():
    """Display welcome banner"""
    banner = """
🌾 HappyHarvest Farming Bot 🚜
═══════════════════════════════

Automated farming system for HappyHarvest.fun
• Perfect 30-second water collection timing
• Smart crop selection based on market analysis
• Automated land expansion and management
• Real-time statistics dashboard

Ready to dominate the leaderboard? Let's farm! 🌱
"""
    console.print(Panel(banner, style="green"))

def get_farmer_credentials():
    """Get farmer credentials from user or environment"""
    farmer_name = FARMER_NAME
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET
    
    if not farmer_name:
        console.print("[yellow]👋 Welcome to HappyHarvest![/yellow]")
        farmer_name = Prompt.ask("Enter your farmer name", default="farmer_" + str(int(time.time())))
    
    return farmer_name, client_id, client_secret

def main():
    parser = argparse.ArgumentParser(description="HappyHarvest Farming Bot")
    parser.add_argument("--farmer", "-f", help="Farmer name")
    parser.add_argument("--register", "-r", action="store_true", help="Register new farmer")
    parser.add_argument("--stats", "-s", action="store_true", help="Show current stats only")
    parser.add_argument("--leaderboard", "-l", action="store_true", help="Show leaderboard")
    
    args = parser.parse_args()
    
    show_banner()
    
    # Get credentials
    if args.farmer:
        farmer_name = args.farmer
        client_id = CLIENT_ID
        client_secret = CLIENT_SECRET
    else:
        farmer_name, client_id, client_secret = get_farmer_credentials()
    
    # Create bot instance
    bot = HappyHarvestBot(farmer_name, client_id, client_secret)
    
    # Handle specific commands
    if args.leaderboard:
        try:
            leaderboard = bot.api.get_leaderboard()
            console.print("\n[cyan]🏆 HappyHarvest Leaderboard[/cyan]")
            for i, player in enumerate(leaderboard.get('leaderboard', [])[:10], 1):
                console.print(f"{i:2d}. {player['playername']:20} - {player['score']:4d} water")
        except Exception as e:
            console.print(f"[red]❌ Failed to get leaderboard: {e}[/red]")
        return
    
    if args.stats:
        try:
            # Just show current profile
            profile = bot.api.get_profile()
            land = bot.api.get_land()
            
            console.print(f"\n[cyan]📊 Stats for {farmer_name}[/cyan]")
            console.print(f"💧 Water: {profile.get('score', 0)}")
            console.print(f"📞 Total API Calls: {profile.get('totalCalls', 0)}")
            console.print(f"🏞️ Land: {land.get('gridSize', 0)}×{land.get('gridSize', 0)} ({land.get('landTiles', 0)} tiles)")
            console.print(f"📅 Registered: {profile.get('registeredAt', 'Unknown')}")
        except Exception as e:
            console.print(f"[red]❌ Failed to get stats: {e}[/red]")
        return
    
    # Start the farming bot
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        console.print(f"[red]❌ Bot crashed: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    import time
    main() 