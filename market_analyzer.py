#!/usr/bin/env python3
"""
HappyHarvest Market Analyzer
Standalone tool for analyzing crop markets and farming strategies
"""

import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.live import Live

from api_client import HappyHarvestAPI
from utils import display_crop_market_table

console = Console()

class MarketAnalyzer:
    """Analyzes HappyHarvest crop markets and provides insights"""
    
    def __init__(self):
        self.api = HappyHarvestAPI()
        self.price_history = []
        self.analysis_cache = {}
    
    def get_market_snapshot(self) -> Dict:
        """Get current market snapshot"""
        try:
            crops_data = self.api.get_crops()
            
            if 'crops' not in crops_data:
                return {}
            
            snapshot = {
                'timestamp': datetime.now(),
                'crops': crops_data['crops'],
                'market_info': crops_data.get('marketInfo', {}),
                'analysis': self._analyze_market_conditions(crops_data)
            }
            
            # Store in price history
            self.price_history.append(snapshot)
            if len(self.price_history) > 100:  # Keep last 100 snapshots
                self.price_history.pop(0)
            
            return snapshot
            
        except Exception as e:
            console.print(f"[red]Failed to get market data: {e}[/red]")
            return {}
    
    def _analyze_market_conditions(self, crops_data: Dict) -> Dict:
        """Analyze current market conditions"""
        crops = crops_data.get('crops', [])
        market_info = crops_data.get('marketInfo', {})
        
        if not crops:
            return {}
        
        # Calculate statistics
        prices = [crop.get('marketPrice', 0) for crop in crops]
        efficiencies = [crop.get('efficiency', 0) for crop in crops]
        water_costs = [crop.get('waterCost', 0) for crop in crops]
        
        analysis = {
            'total_crops': len(crops),
            'price_stats': {
                'min': min(prices),
                'max': max(prices),
                'avg': sum(prices) / len(prices),
                'median': sorted(prices)[len(prices)//2]
            },
            'efficiency_stats': {
                'min': min(efficiencies),
                'max': max(efficiencies),
                'avg': sum(efficiencies) / len(efficiencies),
                'median': sorted(efficiencies)[len(efficiencies)//2]
            },
            'cost_stats': {
                'min': min(water_costs),
                'max': max(water_costs),
                'avg': sum(water_costs) / len(water_costs),
                'median': sorted(water_costs)[len(water_costs)//2]
            }
        }
        
        # Find best opportunities
        analysis['top_efficiency'] = sorted(crops, key=lambda x: x.get('efficiency', 0), reverse=True)[:5]
        analysis['best_value'] = sorted(crops, key=lambda x: x.get('marketPrice', 0), reverse=True)[:5]
        analysis['quick_turnaround'] = sorted(crops, key=lambda x: x.get('growTimeMinutes', 999))[:5]
        
        return analysis
    
    def display_market_overview(self, snapshot: Dict):
        """Display comprehensive market overview"""
        if not snapshot:
            console.print("[red]No market data available[/red]")
            return
        
        analysis = snapshot.get('analysis', {})
        market_info = snapshot.get('market_info', {})
        
        # Market summary panel
        summary_table = Table(title="📊 Market Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("⏰ Last Updated", snapshot['timestamp'].strftime('%H:%M:%S'))
        summary_table.add_row("🌾 Total Crops", str(analysis.get('total_crops', 0)))
        summary_table.add_row("💰 Avg Price", f"{analysis.get('price_stats', {}).get('avg', 0):.2f}")
        summary_table.add_row("📈 Best Efficiency", f"{analysis.get('efficiency_stats', {}).get('max', 0):.3f}")
        summary_table.add_row("💧 Avg Water Cost", f"{analysis.get('cost_stats', {}).get('avg', 0):.1f}")
        
        # Top opportunities
        opportunities_table = Table(title="🎯 Top Opportunities")
        opportunities_table.add_column("Category", style="cyan")
        opportunities_table.add_column("Crop", style="yellow")
        opportunities_table.add_column("Value", style="green")
        
        # Best efficiency crops
        top_efficiency = analysis.get('top_efficiency', [])[:3]
        for i, crop in enumerate(top_efficiency):
            opportunities_table.add_row(
                "High Efficiency" if i == 0 else "",
                f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
                f"{crop.get('efficiency', 0):.3f}"
            )
        
        # Best value crops
        best_value = analysis.get('best_value', [])[:3]
        for i, crop in enumerate(best_value):
            opportunities_table.add_row(
                "High Value" if i == 0 else "",
                f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
                f"{crop.get('marketPrice', 0):.2f} credits"
            )
        
        # Quick turnaround crops
        quick_crops = analysis.get('quick_turnaround', [])[:3]
        for i, crop in enumerate(quick_crops):
            opportunities_table.add_row(
                "Quick Growth" if i == 0 else "",
                f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
                f"{crop.get('growTimeMinutes', 0)}min"
            )
        
        # Display in columns
        console.print(Columns([Panel(summary_table), Panel(opportunities_table)]))
    
    def display_price_trends(self):
        """Display price trends over time"""
        if len(self.price_history) < 2:
            console.print("[yellow]Need more data to show trends[/yellow]")
            return
        
        # Compare current vs previous snapshot
        current = self.price_history[-1]
        previous = self.price_history[-2]
        
        trends_table = Table(title="📈 Price Trends")
        trends_table.add_column("Crop", style="cyan")
        trends_table.add_column("Current Price", style="green")
        trends_table.add_column("Change", style="yellow")
        trends_table.add_column("Trend", style="magenta")
        
        current_crops = {crop['type']: crop for crop in current.get('crops', [])}
        previous_crops = {crop['type']: crop for crop in previous.get('crops', [])}
        
        for crop_type, crop in current_crops.items():
            if crop_type in previous_crops:
                current_price = crop.get('marketPrice', 0)
                previous_price = previous_crops[crop_type].get('marketPrice', 0)
                
                if previous_price > 0:
                    change = ((current_price - previous_price) / previous_price) * 100
                    trend_indicator = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    
                    trends_table.add_row(
                        f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
                        f"{current_price:.2f}",
                        f"{change:+.1f}%",
                        trend_indicator
                    )
        
        console.print(trends_table)
    
    def find_arbitrage_opportunities(self, max_water: int = 100) -> List[Dict]:
        """Find potential arbitrage opportunities"""
        snapshot = self.get_market_snapshot()
        if not snapshot:
            return []
        
        crops = snapshot.get('crops', [])
        analysis = snapshot.get('analysis', {})
        
        avg_price = analysis.get('price_stats', {}).get('avg', 0)
        avg_efficiency = analysis.get('efficiency_stats', {}).get('avg', 0)
        
        opportunities = []
        
        for crop in crops:
            water_cost = crop.get('waterCost', 0)
            market_price = crop.get('marketPrice', 0)
            efficiency = crop.get('efficiency', 0)
            grow_time = crop.get('growTimeMinutes', 0)
            
            if water_cost <= max_water:
                # Calculate opportunity score
                price_premium = market_price / avg_price if avg_price > 0 else 1
                efficiency_bonus = efficiency / avg_efficiency if avg_efficiency > 0 else 1
                time_factor = 60 / grow_time if grow_time > 0 else 0
                
                opportunity_score = (price_premium * efficiency_bonus * time_factor)
                
                if opportunity_score > 1.2:  # 20% above average
                    opportunities.append({
                        'crop': crop,
                        'score': opportunity_score,
                        'price_premium': price_premium,
                        'efficiency_bonus': efficiency_bonus,
                        'time_factor': time_factor
                    })
        
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)
    
    def display_arbitrage_opportunities(self, max_water: int = 100):
        """Display arbitrage opportunities"""
        opportunities = self.find_arbitrage_opportunities(max_water)
        
        if not opportunities:
            console.print(f"[yellow]No strong arbitrage opportunities found with {max_water} water budget[/yellow]")
            return
        
        arb_table = Table(title=f"💎 Arbitrage Opportunities (Max {max_water} water)")
        arb_table.add_column("Crop", style="cyan")
        arb_table.add_column("💧 Cost", justify="right")
        arb_table.add_column("⏰ Time", justify="right")
        arb_table.add_column("💰 Price", justify="right", style="green")
        arb_table.add_column("📊 Score", justify="right", style="yellow")
        
        for opp in opportunities[:10]:  # Top 10
            crop = opp['crop']
            arb_table.add_row(
                f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
                str(crop.get('waterCost', 0)),
                f"{crop.get('growTimeMinutes', 0)}min",
                f"{crop.get('marketPrice', 0):.2f}",
                f"{opp['score']:.2f}"
            )
        
        console.print(arb_table)
    
    def live_market_monitor(self, update_interval: int = 60):
        """Live market monitoring with auto-refresh"""
        console.print("[cyan]🔄 Starting live market monitor... (Ctrl+C to stop)[/cyan]")
        
        def create_live_display():
            snapshot = self.get_market_snapshot()
            if not snapshot:
                return Panel("[red]No market data available[/red]")
            
            # Create comprehensive display
            self.display_market_overview(snapshot)
            return Panel("Market data refreshed", title=f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        try:
            while True:
                snapshot = self.get_market_snapshot()
                if snapshot:
                    console.clear()
                    self.display_market_overview(snapshot)
                    self.display_arbitrage_opportunities()
                    if len(self.price_history) >= 2:
                        self.display_price_trends()
                
                console.print(f"\n[dim]Next update in {update_interval} seconds... (Ctrl+C to stop)[/dim]")
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Market monitoring stopped[/yellow]")

def main():
    parser = argparse.ArgumentParser(description="HappyHarvest Market Analyzer")
    parser.add_argument("--live", "-l", action="store_true", help="Start live market monitoring")
    parser.add_argument("--interval", "-i", type=int, default=60, help="Update interval for live monitoring (seconds)")
    parser.add_argument("--budget", "-b", type=int, default=100, help="Water budget for arbitrage analysis")
    parser.add_argument("--snapshot", "-s", action="store_true", help="Show current market snapshot")
    parser.add_argument("--arbitrage", "-a", action="store_true", help="Show arbitrage opportunities")
    
    args = parser.parse_args()
    
    analyzer = MarketAnalyzer()
    
    if args.live:
        analyzer.live_market_monitor(args.interval)
    elif args.snapshot:
        snapshot = analyzer.get_market_snapshot()
        analyzer.display_market_overview(snapshot)
    elif args.arbitrage:
        analyzer.display_arbitrage_opportunities(args.budget)
    else:
        # Default: show comprehensive analysis
        console.print("[cyan]🌾 HappyHarvest Market Analysis[/cyan]\n")
        
        snapshot = analyzer.get_market_snapshot()
        analyzer.display_market_overview(snapshot)
        
        console.print()
        analyzer.display_arbitrage_opportunities(args.budget)
        
        console.print(f"\n[dim]Use --live for continuous monitoring[/dim]")

if __name__ == "__main__":
    main() 