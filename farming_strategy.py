import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from config import *

console = Console()

class FarmingStrategy:
    """Smart farming strategy with market analysis and land management"""
    
    def __init__(self):
        self.crop_data = {}
        self.market_history = []
        self.land_data = None
        self.last_market_update = None
        
    def analyze_market(self, crops_response: Dict) -> Dict:
        """Analyze current market conditions and identify opportunities"""
        if 'crops' not in crops_response:
            return {}
        
        crops = crops_response['crops']
        market_info = crops_response.get('marketInfo', {})
        
        analysis = {
            'timestamp': datetime.now(),
            'average_price': market_info.get('averagePrice', 0),
            'best_efficiency': market_info.get('bestEfficiency', 0),
            'opportunities': [],
            'recommendations': [],
            'crops': crops  # Include all crops data for fallback
        }
        
        # Calculate average efficiency for comparison
        avg_efficiency = sum(crop.get('efficiency', 0) for crop in crops) / len(crops)
        avg_price = market_info.get('averagePrice', 0)
        
        # VICTORY MODE: Include more crop opportunities, not just premium ones
        for crop in crops:
            efficiency = crop.get('efficiency', 0)
            market_price = crop.get('marketPrice', 0)
            water_cost = crop.get('waterCost', 0)
            
            # Add high-efficiency crops (premium)
            if efficiency > avg_efficiency * 1.2:  # 20% above average
                analysis['opportunities'].append({
                    'crop': crop,
                    'reason': f"High efficiency: {efficiency:.3f} (avg: {avg_efficiency:.3f})",
                    'priority': 'HIGH'
                })
            
            # Add premium-priced crops
            elif market_price > avg_price * MARKET_PREMIUM_THRESHOLD:
                analysis['opportunities'].append({
                    'crop': crop,
                    'reason': f"Premium price: {market_price:.2f} (avg: {avg_price:.2f})",
                    'priority': 'MEDIUM'
                })
            
            # VICTORY ADDITION: Add affordable crops for immediate planting
            elif water_cost <= 20:  # Affordable crops for quick planting
                analysis['opportunities'].append({
                    'crop': crop,
                    'reason': f"Affordable: {water_cost} water, {efficiency:.3f} efficiency",
                    'priority': 'MEDIUM'
                })
            
            # VICTORY ADDITION: Add all remaining crops as backup options
            else:
                analysis['opportunities'].append({
                    'crop': crop,
                    'reason': f"Standard crop: {water_cost} water, {efficiency:.3f} efficiency",
                    'priority': 'LOW'
                })
        
        # Store market history
        self.market_history.append(analysis)
        if len(self.market_history) > 60:  # Keep last hour of data
            self.market_history.pop(0)
        
        return analysis
    
    def recommend_crop(self, available_water: int, land_size: int, market_analysis: Dict) -> Optional[Dict]:
        """Recommend the best crop to plant based on strategy"""
        # VICTORY MODE: Be more aggressive with water reserves
        # If we have multiple empty plots, be more aggressive about planting
        if land_size >= 3:  # 3+ empty plots = victory opportunity!
            min_reserve = max(3, MIN_WATER_RESERVE // 4)  # Use 1/4 normal reserve
        elif land_size >= 2:  # 2 empty plots = good opportunity  
            min_reserve = max(5, MIN_WATER_RESERVE // 3)  # Use 1/3 normal reserve
        else:
            min_reserve = max(8, MIN_WATER_RESERVE // 2)  # Use half normal reserve
        
        if available_water < min_reserve:
            return None
        
        affordable_water = available_water - min_reserve
        
        # If no market analysis opportunities, try all crops
        opportunities = market_analysis.get('opportunities', [])
        if not opportunities:
            # Fall back to all crops if no specific opportunities
            crops_data = market_analysis.get('crops', [])
            if crops_data:
                # Create basic opportunities from all crops
                opportunities = [
                    {'crop': crop, 'priority': 'MEDIUM', 'reason': 'Standard crop'}
                    for crop in crops_data
                ]
        
        if not opportunities:
            return None
        
        # Filter affordable crops
        affordable_crops = [
            opp for opp in opportunities 
            if opp['crop'].get('waterCost', 0) <= affordable_water
        ]
        
        if not affordable_crops:
            return None
        
        # Sort by efficiency primarily, but also consider market price for victory
        affordable_crops.sort(
            key=lambda x: (
                x['crop'].get('efficiency', 0),  # Primary: efficiency
                x['crop'].get('marketPrice', 0)  # Secondary: market price
            ),
            reverse=True
        )
        
        return affordable_crops[0]['crop']
    
    def find_empty_plots(self, land_data: Dict) -> List[Tuple[int, int]]:
        """Find empty plots on the farm"""
        if not land_data.get('landClaimed'):
            return []
        
        empty_plots = []
        grid_data = land_data.get('landData', [])
        
        for row_idx, row in enumerate(grid_data):
            for col_idx, cell in enumerate(row):
                if cell == 0:  # Empty dirt
                    empty_plots.append((row_idx, col_idx))
        
        return empty_plots
    
    def find_harvestable_crops(self, land_data: Dict, crops_data: Dict) -> List[Tuple[int, int, Dict]]:
        """Find crops that are ready to harvest"""
        if not land_data.get('landClaimed'):
            return []
        
        harvestable = []
        grid_data = land_data.get('landData', [])
        
        # Create crop lookup by ID
        crop_lookup = {}
        if 'crops' in crops_data:
            for crop in crops_data['crops']:
                crop_lookup[crop.get('id')] = crop
        
        for row_idx, row in enumerate(grid_data):
            for col_idx, cell in enumerate(row):
                # Based on documentation: 0=empty dirt, 1=sprout, 2+=mature crops
                if cell >= 2:  # Mature crops (any ID 2 or higher)
                    crop_info = crop_lookup.get(cell)
                    if crop_info:
                        harvestable.append((row_idx, col_idx, crop_info))
                    else:
                        # If we can't identify the specific crop, still try to harvest
                        harvestable.append((row_idx, col_idx, {'name': 'Unknown Crop', 'id': cell}))
        
        return harvestable
    
    def should_expand_land(self, profile: Dict, land_data: Dict) -> bool:
        """Determine if we should expand our land with better economic analysis"""
        current_water = profile.get('score', 0)
        
        if not land_data.get('landClaimed'):
            return current_water >= LAND_CLAIM_COST
        
        # Get expansion economics
        next_expansion_cost = land_data.get('nextExpansionCost', float('inf'))
        current_land_tiles = land_data.get('landTiles', 0)
        
        # Don't expand if we can't afford it
        if current_water < next_expansion_cost:
            return False
        
        # Calculate expansion ROI
        expansion_roi = self.calculate_expansion_roi(land_data, current_water)
        
        # Expansion strategy based on current situation
        if current_land_tiles == 1:  # 1x1 → 2x2 (adds 3 tiles)
            # This is the most important expansion - 4x more land!
            # Be more aggressive: expand when we have 2/3 of the cost
            return current_water >= next_expansion_cost * 0.67
        
        elif current_land_tiles <= 4:  # 2x2 → 3x3 (adds 5 tiles)
            # Good ROI expansion, but be more conservative
            return (current_water >= next_expansion_cost + MIN_WATER_RESERVE and
                    expansion_roi > 0.15)  # 15% ROI threshold
        
        elif current_land_tiles <= 9:  # 3x3 → 4x4 (adds 7 tiles)
            # Only expand if we're swimming in water and ROI is excellent
            return (current_water >= next_expansion_cost + (MIN_WATER_RESERVE * 2) and
                    expansion_roi > 0.25)  # 25% ROI threshold
        
        else:
            # Beyond 4x4, only expand if extremely profitable
            return (current_water >= next_expansion_cost + 100 and
                    expansion_roi > 0.35)  # 35% ROI threshold
    
    def calculate_expansion_roi(self, land_data: Dict, current_water: int) -> float:
        """Calculate the expected ROI from land expansion"""
        next_expansion_cost = land_data.get('nextExpansionCost', float('inf'))
        current_land_tiles = land_data.get('landTiles', 0)
        
        if next_expansion_cost == float('inf'):
            return 0.0
        
        # Calculate new tiles gained from expansion
        if current_land_tiles == 1:    # 1x1 → 2x2
            new_tiles = 3
        elif current_land_tiles == 4:  # 2x2 → 3x3  
            new_tiles = 5
        elif current_land_tiles == 9:  # 3x3 → 4x4
            new_tiles = 7
        else:
            # Estimate for larger expansions
            new_tiles = max(1, int(current_land_tiles * 0.5))
        
        # Estimate credits per hour per tile (conservative estimate)
        # Assume average crop: 8 water cost, 0.15 credits, 0.5 hour grow time
        credits_per_tile_per_hour = 0.15 / 0.5  # 0.3 credits/hour per tile
        
        # Total additional credits per hour from expansion
        additional_credits_per_hour = new_tiles * credits_per_tile_per_hour
        
        # Convert water cost to equivalent credit cost (rough estimate)
        # Assume 1 water = 0.02 credits (based on water collection rate vs crop values)
        expansion_cost_in_credits = next_expansion_cost * 0.02
        
        # ROI = Annual return / Investment
        # Use 24 hours as the investment horizon
        annual_return = additional_credits_per_hour * 24
        roi = annual_return / expansion_cost_in_credits if expansion_cost_in_credits > 0 else 0
        
        return roi
        
    def get_expansion_recommendation(self, profile: Dict, land_data: Dict) -> Dict:
        """Get detailed expansion recommendation with analysis"""
        current_water = profile.get('score', 0)
        next_expansion_cost = land_data.get('nextExpansionCost', float('inf'))
        current_land_tiles = land_data.get('landTiles', 0)
        
        recommendation = {
            'should_expand': self.should_expand_land(profile, land_data),
            'current_water': current_water,
            'expansion_cost': next_expansion_cost,
            'current_tiles': current_land_tiles,
            'roi': self.calculate_expansion_roi(land_data, current_water),
            'reasoning': ""
        }
        
        if next_expansion_cost == float('inf'):
            recommendation['reasoning'] = "No expansion available"
            return recommendation
        
        if current_water < next_expansion_cost:
            water_needed = next_expansion_cost - current_water
            minutes_to_wait = (water_needed * 30) / 60  # 1 water per 30 seconds
            recommendation['reasoning'] = f"Need {water_needed} more water (~{minutes_to_wait:.1f} minutes)"
        elif recommendation['should_expand']:
            if current_land_tiles == 1:
                recommendation['reasoning'] = f"HIGH PRIORITY: 1x1→2x2 expansion gives 4x land for {next_expansion_cost} water!"
            else:
                recommendation['reasoning'] = f"Good ROI ({recommendation['roi']:.1%}) - expand for {next_expansion_cost} water"
        else:
            recommendation['reasoning'] = f"Low ROI ({recommendation['roi']:.1%}) - focus on crops first"
        
        return recommendation
    
    def calculate_crop_roi(self, crop: Dict) -> float:
        """Calculate return on investment for a crop"""
        water_cost = crop.get('waterCost', 1)
        credits_earned = crop.get('marketPrice', 0)
        grow_time_hours = crop.get('growTimeHours', 1)
        
        # ROI = (Credits per hour) / Water cost
        credits_per_hour = credits_earned / grow_time_hours
        roi = credits_per_hour / water_cost
        
        return roi
    
    def get_farming_plan(self, profile: Dict, land_data: Dict, crops_data: Dict) -> Dict:
        """Create a comprehensive farming plan with better harvest/expansion balance"""
        market_analysis = self.analyze_market(crops_data)
        current_water = profile.get('score', 0)
        
        plan = {
            'timestamp': datetime.now(),
            'current_water': current_water,
            'actions': [],
            'market_summary': market_analysis
        }
        
        # First, always check for harvestable crops (immediate credits!)
        harvestable = self.find_harvestable_crops(land_data, crops_data)
        harvestable_credits = len(harvestable) * 0.15  # Estimate credits from harvesting
        
        # Find empty plots for future planning
        empty_plots = self.find_empty_plots(land_data)
        
        # 1. PRIORITY: Harvest ready crops (immediate profit, frees up space)
        for row, col, crop_info in harvestable:
            plan['actions'].append({
                'type': 'harvest',
                'priority': 'CRITICAL',  # Highest priority - immediate credits!
                'row': row,
                'col': col,
                'crop': crop_info,
                'description': f"Harvest {crop_info.get('name', 'crop')} at ({row},{col})"
            })
        
        # 2. SMART EXPANSION LOGIC: Consider current situation
        should_expand = False
        expansion_reasoning = ""
        
        if not land_data.get('landClaimed') and current_water >= LAND_CLAIM_COST:
            should_expand = True
            expansion_reasoning = "Claim initial land"
        elif self.should_expand_land(profile, land_data):
            # Enhanced expansion logic considering immediate situation
            current_land_tiles = land_data.get('landTiles', 0)
            next_expansion_cost = land_data.get('nextExpansionCost', float('inf'))
            
            # Special case: If we have harvestable crops, wait for harvest first
            # unless expansion is super cheap or we have tons of water
            if harvestable and current_land_tiles == 1:
                # For 1x1→2x2 expansion, be more aggressive even with harvestable crops
                water_after_harvest = current_water + harvestable_credits * 50  # Rough water equivalent
                if water_after_harvest >= next_expansion_cost:
                    should_expand = True
                    expansion_reasoning = "Expand after harvest - will have enough water"
                else:
                    should_expand = False
                    expansion_reasoning = f"Wait for harvest + {int(next_expansion_cost - water_after_harvest)} more water"
            elif not harvestable and empty_plots:
                # No crops to harvest, but have empty space - focus on planting first
                if current_water >= next_expansion_cost + 20:  # Plenty of water
                    should_expand = True
                    expansion_reasoning = "Plenty of water - expand for more capacity"
                else:
                    should_expand = False
                    expansion_reasoning = "Use current space efficiently first"
            else:
                # Default expansion logic
                should_expand = True
                expansion_reasoning = "Standard expansion criteria met"
        
        if should_expand:
            if not land_data.get('landClaimed'):
                plan['actions'].append({
                    'type': 'claim_land',
                    'priority': 'HIGH',
                    'description': 'Claim first plot of farming land'
                })
            else:
                plan['actions'].append({
                    'type': 'expand_land',
                    'priority': 'HIGH' if not empty_plots else 'MEDIUM',  # Higher priority if no space
                    'description': f"Expand land (cost: {land_data.get('nextExpansionCost', 'unknown')}) - {expansion_reasoning}"
                })
        
        # 3. PLANTING: Fill available space efficiently
        if empty_plots:
            recommended_crop = self.recommend_crop(current_water, len(empty_plots), market_analysis)
            if recommended_crop:
                # Plant on first empty plot
                row, col = empty_plots[0]
                
                # Adjust planting priority based on situation
                if harvestable:
                    plant_priority = 'LOW'  # Wait for harvest first
                elif should_expand and land_data.get('landTiles', 0) == 1:
                    plant_priority = 'LOW'  # Wait for expansion for better efficiency
                else:
                    plant_priority = 'MEDIUM'  # Normal planting
                
                plan['actions'].append({
                    'type': 'plant',
                    'priority': plant_priority,
                    'row': row,
                    'col': col,
                    'crop': recommended_crop,
                    'description': f"Plant {recommended_crop.get('name')} at ({row},{col}) - {recommended_crop.get('waterCost')} water"
                })
        
        # Sort actions by priority: CRITICAL > HIGH > MEDIUM > LOW
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        plan['actions'].sort(key=lambda x: priority_order.get(x.get('priority', 'MEDIUM'), 2))
        
        return plan 