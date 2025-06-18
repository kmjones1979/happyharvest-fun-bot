import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

from api_client import HappyHarvestAPI
from farming_strategy import FarmingStrategy
from config import *

console = Console()

class HappyHarvestBot:
    """Main farming bot that manages all farming operations"""
    
    def __init__(self, farmer_name: str, client_id: str = "", client_secret: str = ""):
        self.farmer_name = farmer_name
        self.api = HappyHarvestAPI(client_id, client_secret)
        self.strategy = FarmingStrategy()
        
        # Bot state
        self.running = False
        self.last_water_collection = None
        self.last_token_refresh = None
        self.last_crop_check = None
        self.last_market_check = None
        
        # Game state
        self.current_profile = {}
        self.current_land = {}
        self.current_crops = {}
        self.stats = {
            'water_collected': 0,
            'crops_planted': 0,
            'crops_harvested': 0,
            'land_expansions': 0,
            'total_credits_earned': 0,
            'start_time': datetime.now()
        }
        
        # Threading
        self.main_thread = None
        self.stop_event = threading.Event()
    
    def register_or_login(self) -> bool:
        """Register new farmer or login with existing credentials"""
        if not self.api.client_id or not self.api.client_secret:
            try:
                console.print(f"[yellow]🚜 Registering new farmer: {self.farmer_name}[/yellow]")
                result = self.api.register_farmer(self.farmer_name)
                if 'error' in result:
                    console.print(f"[red]❌ Registration failed: {result.get('error_description', 'Unknown error')}[/red]")
                    return False
                
                # Save credentials to .env file
                self._save_credentials_to_env(result['client_id'], result['client_secret'])
                
            except Exception as e:
                console.print(f"[red]❌ Registration error: {e}[/red]")
                return False
        
        # Get initial token
        try:
            self.api.get_token()
            console.print(f"[green]✅ Successfully authenticated as {self.farmer_name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Authentication failed: {e}[/red]")
            return False
    
    def _save_credentials_to_env(self, client_id: str, client_secret: str):
        """Save credentials to .env file"""
        env_content = f"""# HappyHarvest Bot Credentials
FARMER_NAME={self.farmer_name}
CLIENT_ID={client_id}
CLIENT_SECRET={client_secret}
LOG_LEVEL=INFO
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        console.print(f"[cyan]💾 Credentials saved to .env file[/cyan]")
    
    def collect_water_cycle(self):
        """Main water collection cycle - runs every 30 seconds"""
        while not self.stop_event.is_set():
            try:
                # Collect water
                result = self.api.collect_water()
                
                if 'score' in result:
                    self.stats['water_collected'] += 1
                    console.print(f"[green]💧 Water collected! Score: {result['score']} (+1)[/green]")
                elif 'error' in result:
                    console.print(f"[red]⚠️ Water collection issue: {result.get('error_description', 'Unknown')}[/red]")
                else:
                    console.print(f"[yellow]⚠️ {result.get('message', 'Unknown response')}[/yellow]")
                
                self.last_water_collection = datetime.now()
                
            except Exception as e:
                console.print(f"[red]❌ Water collection failed: {e}[/red]")
            
            # Wait exactly 30 seconds
            self.stop_event.wait(WATER_COLLECTION_INTERVAL)
    
    def token_refresh_cycle(self):
        """Token refresh cycle - runs every 4 minutes"""
        while not self.stop_event.is_set():
            try:
                if self.api.refresh_token():
                    self.last_token_refresh = datetime.now()
                    console.print(f"[blue]🔄 Token refreshed successfully[/blue]")
            except Exception as e:
                console.print(f"[red]❌ Token refresh failed: {e}[/red]")
            
            # Wait 4 minutes
            self.stop_event.wait(TOKEN_REFRESH_INTERVAL)
    
    def farming_cycle(self):
        """Main farming cycle - checks crops and executes farming strategy"""
        while not self.stop_event.is_set():
            try:
                # Get current game state
                self.current_profile = self.api.get_profile()
                self.current_land = self.api.get_land()
                self.current_crops = self.api.get_crops()
                
                # Get farming plan
                plan = self.strategy.get_farming_plan(
                    self.current_profile, 
                    self.current_land, 
                    self.current_crops
                )
                
                # Execute farming actions
                self._execute_farming_plan(plan)
                
                self.last_crop_check = datetime.now()
                
            except Exception as e:
                console.print(f"[red]❌ Farming cycle error: {e}[/red]")
            
            # Wait 1 minute
            self.stop_event.wait(CROP_CHECK_INTERVAL)
    
    def _execute_farming_plan(self, plan: Dict):
        """Execute the farming plan actions"""
        actions = plan.get('actions', [])
        
        for action in actions:
            try:
                action_type = action['type']
                
                if action_type == 'claim_land':
                    result = self.api.claim_land()
                    if 'error' not in result:
                        console.print(f"[green]🏞️ Land claimed successfully![/green]")
                        self.stats['land_expansions'] += 1
                    else:
                        console.print(f"[red]❌ Land claim failed: {result.get('error_description')}[/red]")
                
                elif action_type == 'expand_land':
                    result = self.api.expand_land()
                    if 'error' not in result:
                        console.print(f"[green]🏗️ Land expanded successfully![/green]")
                        self.stats['land_expansions'] += 1
                    else:
                        console.print(f"[red]❌ Land expansion failed: {result.get('error_description')}[/red]")
                
                elif action_type == 'plant':
                    crop = action['crop']
                    row, col = action['row'], action['col']
                    result = self.api.plant_crop(crop['type'], row, col)
                    if 'error' not in result:
                        console.print(f"[green]🌱 Planted {crop['name']} at ({row},{col})[/green]")
                        self.stats['crops_planted'] += 1
                    else:
                        console.print(f"[red]❌ Planting failed: {result.get('error_description')}[/red]")
                
                elif action_type == 'harvest':
                    row, col = action['row'], action['col']
                    crop = action['crop']
                    result = self.api.harvest_crop(row, col)
                    if 'error' not in result:
                        credits = result.get('creditsEarned', 0)
                        console.print(f"[green]🌾 Harvested {crop['name']} at ({row},{col}) for {credits} credits![/green]")
                        self.stats['crops_harvested'] += 1
                        self.stats['total_credits_earned'] += credits
                    else:
                        console.print(f"[red]❌ Harvest failed: {result.get('error_description')}[/red]")
                
                # Small delay between actions
                time.sleep(1)
                
            except Exception as e:
                console.print(f"[red]❌ Action '{action_type}' failed: {e}[/red]")
    
    def create_status_display(self) -> Layout:
        """Create rich status display"""
        layout = Layout()
        
        # Farm status
        water = self.current_profile.get('score', 0)
        land_tiles = self.current_land.get('landTiles', 0)
        grid_size = self.current_land.get('gridSize', 0)
        total_credits = self.current_profile.get('credits', 0)  # Real credits from API
        
        farm_table = Table(title="🚜 Farm Status")
        farm_table.add_column("Metric", style="cyan")
        farm_table.add_column("Value", style="green")
        
        farm_table.add_row("💧 Water", str(water))
        farm_table.add_row("💰 Credits", f"{total_credits:.2f}")
        farm_table.add_row("🏞️ Land Size", f"{grid_size}×{grid_size} ({land_tiles} tiles)")
        farm_table.add_row("⏰ Running Time", str(datetime.now() - self.stats['start_time']).split('.')[0])
        
        # Bot statistics
        stats_table = Table(title="📊 Bot Statistics")
        stats_table.add_column("Statistic", style="cyan")
        stats_table.add_column("Count", style="yellow")
        
        stats_table.add_row("💧 Water Collected", str(self.stats['water_collected']))
        stats_table.add_row("🌱 Crops Planted", str(self.stats['crops_planted']))
        stats_table.add_row("🌾 Crops Harvested", str(self.stats['crops_harvested']))
        stats_table.add_row("🏗️ Land Expansions", str(self.stats['land_expansions']))
        stats_table.add_row("💰 Session Credits", f"{self.stats['total_credits_earned']:.2f}")
        
        # Expansion analysis
        expansion = self.strategy.get_expansion_recommendation(
            self.current_profile, self.current_land
        )
        
        expansion_table = Table(title="🏗️ Land Expansion Analysis")
        expansion_table.add_column("Metric", style="cyan")
        expansion_table.add_column("Value", style="magenta")
        
        expansion_table.add_row("Current Land", f"{expansion['current_tiles']} tiles")
        expansion_table.add_row("Expansion Cost", f"{expansion['expansion_cost']} water")
        expansion_table.add_row("Expected ROI", f"{expansion['roi']:.1%}")
        expansion_table.add_row("Recommendation", 
                              "✅ EXPAND NOW!" if expansion['should_expand'] 
                              else "⏳ Wait/Focus crops")
        expansion_table.add_row("Strategy", expansion['reasoning'])
        
        # Market info
        market_info = self.current_crops.get('marketInfo', {})
        market_table = Table(title="📈 Market Status")
        market_table.add_column("Metric", style="cyan")
        market_table.add_column("Value", style="green")
        
        market_table.add_row("Average Price", f"{market_info.get('averagePrice', 0):.2f}")
        market_table.add_row("Highest Price", f"{market_info.get('highestPrice', 0):.2f}")
        market_table.add_row("Best Efficiency", f"{market_info.get('bestEfficiency', 0):.3f}")
        
        layout.split_column(
            Layout(Panel(farm_table)),
            Layout(Panel(stats_table)),
            Layout(Panel(expansion_table)),
            Layout(Panel(market_table))
        )
        
        return layout
    
    def start(self):
        """Start the farming bot"""
        if not self.register_or_login():
            return
        
        console.print(f"[green]🚀 Starting HappyHarvest farming bot for {self.farmer_name}[/green]")
        self.running = True
        
        # Start background threads
        threads = [
            threading.Thread(target=self.collect_water_cycle, daemon=True),
            threading.Thread(target=self.token_refresh_cycle, daemon=True),
            threading.Thread(target=self.farming_cycle, daemon=True)
        ]
        
        for thread in threads:
            thread.start()
        
        # Main loop with status display
        try:
            with Live(self.create_status_display(), refresh_per_second=1) as live:
                while self.running:
                    live.update(self.create_status_display())
                    time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the farming bot"""
        console.print(f"[yellow]🛑 Stopping farming bot...[/yellow]")
        self.running = False
        self.stop_event.set()
        
        # Display final statistics
        runtime = datetime.now() - self.stats['start_time']
        console.print(f"\n[cyan]📊 Final Statistics:[/cyan]")
        console.print(f"Runtime: {runtime}")
        console.print(f"Water Collected: {self.stats['water_collected']}")
        console.print(f"Crops Planted: {self.stats['crops_planted']}")
        console.print(f"Crops Harvested: {self.stats['crops_harvested']}")
        console.print(f"Total Credits Earned: {self.stats['total_credits_earned']:.2f}")
        console.print(f"[green]Thanks for farming! 🌾[/green]") 