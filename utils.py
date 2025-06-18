import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table

console = Console()

def format_duration(seconds: int) -> str:
    """Format seconds into a human-readable duration"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours}h {remaining_minutes}m"

def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to human-readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def calculate_water_per_hour(water_collected: int, runtime_seconds: int) -> float:
    """Calculate water collection rate per hour"""
    if runtime_seconds == 0:
        return 0
    return (water_collected * 3600) / runtime_seconds

def display_crop_market_table(crops_data: Dict):
    """Display a formatted table of crop market data"""
    if 'crops' not in crops_data:
        console.print("[red]No crop data available[/red]")
        return
    
    table = Table(title="🌾 Crop Market Analysis")
    table.add_column("Crop", style="cyan")
    table.add_column("💧 Water", justify="right")
    table.add_column("⏰ Time", justify="right")
    table.add_column("💰 Price", justify="right", style="green")
    table.add_column("📈 Efficiency", justify="right", style="yellow")
    table.add_column("📊 ROI/hr", justify="right", style="magenta")
    
    # Sort crops by efficiency (descending)
    crops = sorted(crops_data['crops'], key=lambda x: x.get('efficiency', 0), reverse=True)
    
    for crop in crops[:10]:  # Show top 10
        water_cost = crop.get('waterCost', 0)
        grow_time = crop.get('growTimeMinutes', 0)
        price = crop.get('marketPrice', 0)
        efficiency = crop.get('efficiency', 0)
        
        # Calculate ROI per hour
        if grow_time > 0:
            roi_per_hour = (price * 60) / grow_time
        else:
            roi_per_hour = 0
        
        table.add_row(
            f"{crop.get('emoji', '🌱')} {crop.get('name', 'Unknown')}",
            str(water_cost),
            f"{grow_time}min",
            f"{price:.2f}",
            f"{efficiency:.3f}",
            f"{roi_per_hour:.2f}"
        )
    
    console.print(table)

def display_land_visualization(land_data: Dict):
    """Display a visual representation of the farm land"""
    if not land_data.get('landClaimed'):
        console.print("[yellow]No land claimed yet[/yellow]")
        return
    
    grid_data = land_data.get('landData', [])
    grid_size = land_data.get('gridSize', 0)
    
    console.print(f"\n[cyan]🏞️ Your Farm ({grid_size}×{grid_size})[/cyan]")
    
    # Emoji mapping for land states
    land_emojis = {
        0: "🟫",  # Empty dirt
        1: "🌱",  # Sprout
        2: "🌿",  # Herb
        3: "🥬",  # Lettuce
        4: "🧅",  # Onion
        5: "🫛",  # Peas
        6: "🫘",  # Bean
        7: "🍅",  # Tomato
        8: "🍓",  # Strawberry
        9: "🌽",  # Corn
        10: "🥔", # Potato
        11: "🥕", # Carrot
        12: "🍄", # Mushroom
        13: "🍆", # Eggplant
        14: "🌾", # Wheat
        15: "🍉", # Watermelon
        16: "🎃", # Pumpkin
        17: "🌶️", # Chili
        18: "🥒", # Cucumber
        19: "🥦", # Broccoli
        20: "🌻", # Sunflower
    }
    
    for row in grid_data:
        row_display = ""
        for cell in row:
            emoji = land_emojis.get(cell, "❓")
            row_display += emoji + " "
        console.print(row_display)

def save_bot_state(bot_state: Dict, filename: str = "bot_state.json"):
    """Save bot state to file"""
    try:
        # Convert datetime objects to strings
        state = bot_state.copy()
        if 'start_time' in state:
            state['start_time'] = state['start_time'].isoformat()
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        console.print(f"[red]Failed to save bot state: {e}[/red]")

def load_bot_state(filename: str = "bot_state.json") -> Dict:
    """Load bot state from file"""
    try:
        with open(filename, 'r') as f:
            state = json.load(f)
        
        # Convert string back to datetime
        if 'start_time' in state:
            state['start_time'] = datetime.fromisoformat(state['start_time'])
        
        return state
    except FileNotFoundError:
        return {}
    except Exception as e:
        console.print(f"[red]Failed to load bot state: {e}[/red]")
        return {}

def estimate_next_harvest(land_data: Dict, crops_data: Dict) -> List[Dict]:
    """Estimate when crops will be ready for harvest"""
    if not land_data.get('landClaimed'):
        return []
    
    # This is a simplified version - in reality, we'd need to track planting times
    # For now, we'll just identify what crops are growing
    grid_data = land_data.get('landData', [])
    growing_crops = []
    
    crop_lookup = {}
    if 'crops' in crops_data:
        for crop in crops_data['crops']:
            crop_lookup[crop.get('id')] = crop
    
    for row_idx, row in enumerate(grid_data):
        for col_idx, cell in enumerate(row):
            if cell == 1:  # Sprout (growing)
                growing_crops.append({
                    'row': row_idx,
                    'col': col_idx,
                    'status': 'growing',
                    'estimated_harvest': 'unknown'
                })
    
    return growing_crops

def check_api_rate_limit(last_call_time: datetime, min_interval: int) -> bool:
    """Check if enough time has passed since last API call"""
    if not last_call_time:
        return True
    
    time_since_last = (datetime.now() - last_call_time).total_seconds()
    return time_since_last >= min_interval

def get_optimal_planting_schedule(crops_data: Dict, available_water: int) -> List[Dict]:
    """Generate optimal planting schedule based on market conditions"""
    if 'crops' not in crops_data:
        return []
    
    # Sort crops by efficiency and affordability
    affordable_crops = [
        crop for crop in crops_data['crops']
        if crop.get('waterCost', 0) <= available_water
    ]
    
    # Sort by efficiency (descending)
    affordable_crops.sort(key=lambda x: x.get('efficiency', 0), reverse=True)
    
    schedule = []
    remaining_water = available_water
    
    for crop in affordable_crops[:5]:  # Top 5 recommendations
        water_cost = crop.get('waterCost', 0)
        if water_cost <= remaining_water:
            schedule.append({
                'crop': crop,
                'priority': 'HIGH' if crop.get('efficiency', 0) > 0.3 else 'MEDIUM',
                'water_needed': water_cost,
                'expected_credits': crop.get('marketPrice', 0)
            })
            remaining_water -= water_cost
    
    return schedule 