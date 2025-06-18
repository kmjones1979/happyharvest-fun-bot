import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from rich.console import Console
from config import ENDPOINTS

console = Console()

class HappyHarvestAPI:
    """API client for HappyHarvest farming game"""
    
    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ""
        self.token_expires_at = datetime.now()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'HappyHarvest-Bot/1.0'
        })
    
    def _make_request(self, method: str, url: str, data: Dict = None, 
                     auth_required: bool = False, retry_count: int = 3) -> Dict:
        """Make HTTP request with error handling and retries"""
        if auth_required and not self._is_token_valid():
            if not self.refresh_token():
                raise Exception("Failed to refresh token")
        
        headers = {}
        if auth_required:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        for attempt in range(retry_count):
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=10)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                console.print(f"[red]Request failed (attempt {attempt + 1}/{retry_count}): {e}[/red]")
                if attempt == retry_count - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Max retries exceeded")
    
    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        return (self.access_token and 
                datetime.now() < self.token_expires_at - timedelta(minutes=1))
    
    def register_farmer(self, farmer_name: str) -> Dict:
        """Register a new farmer (ONE TIME ONLY!)"""
        console.print(f"[yellow]🔄 Registering farmer: {farmer_name}[/yellow]")
        data = {"playername": farmer_name}
        result = self._make_request('POST', ENDPOINTS['register'], data)
        
        if 'client_id' in result and 'client_secret' in result:
            self.client_id = result['client_id']
            self.client_secret = result['client_secret']
            console.print(f"[green]✅ Farmer registered successfully![/green]")
            console.print(f"[cyan]📋 Save these credentials:[/cyan]")
            console.print(f"CLIENT_ID={result['client_id']}")
            console.print(f"CLIENT_SECRET={result['client_secret']}")
        
        return result
    
    def get_token(self) -> Dict:
        """Get JWT access token"""
        if not self.client_id or not self.client_secret:
            raise Exception("Client credentials not set")
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }
        
        result = self._make_request('POST', ENDPOINTS['token'], data)
        
        if 'access_token' in result:
            self.access_token = result['access_token']
            expires_in = result.get('expires_in', 300)  # Default 5 minutes
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            console.print(f"[green]🔑 Token obtained, expires at {self.token_expires_at.strftime('%H:%M:%S')}[/green]")
        
        return result
    
    def refresh_token(self) -> bool:
        """Refresh JWT token"""
        try:
            self.get_token()
            return True
        except Exception as e:
            console.print(f"[red]❌ Token refresh failed: {e}[/red]")
            return False
    
    def collect_water(self) -> Dict:
        """Collect water (call every 30 seconds)"""
        return self._make_request('POST', ENDPOINTS['collect'], auth_required=True)
    
    def get_profile(self) -> Dict:
        """Get farmer profile and stats"""
        return self._make_request('GET', ENDPOINTS['profile'], auth_required=True)
    
    def claim_land(self) -> Dict:
        """Claim first plot of land (costs 5 water)"""
        return self._make_request('POST', ENDPOINTS['claim_land'], auth_required=True)
    
    def expand_land(self) -> Dict:
        """Expand farming territory"""
        return self._make_request('POST', ENDPOINTS['expand_land'], auth_required=True)
    
    def get_land(self) -> Dict:
        """View your farming land"""
        return self._make_request('GET', ENDPOINTS['land'], auth_required=True)
    
    def get_crops(self) -> Dict:
        """Get crop data with live market pricing"""
        return self._make_request('GET', ENDPOINTS['crops'])
    
    def plant_crop(self, crop_type: str, row: int, col: int) -> Dict:
        """Plant a crop on your land"""
        data = {
            "cropType": crop_type,
            "row": row,
            "col": col
        }
        return self._make_request('POST', ENDPOINTS['plant'], data, auth_required=True)
    
    def harvest_crop(self, row: int, col: int) -> Dict:
        """Harvest a mature crop"""
        data = {
            "row": row,
            "col": col
        }
        return self._make_request('POST', ENDPOINTS['harvest'], data, auth_required=True)
    
    def get_leaderboard(self) -> Dict:
        """Get current farmer rankings"""
        return self._make_request('GET', ENDPOINTS['leaderboard']) 