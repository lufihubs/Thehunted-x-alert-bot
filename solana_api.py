"""Solana API integration for fetching token data."""
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SolanaAPI:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'SolanaAlertBot/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_token_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token information with fallback to multiple APIs."""
        try:
            # Try Birdeye first (most reliable)
            token_info = await self._get_birdeye_info(contract_address)
            if token_info:
                return token_info
                
            # Fallback to DexScreener
            token_info = await self._get_dexscreener_info(contract_address)
            if token_info:
                return token_info
                
            # Fallback to pump.fun for newer tokens
            token_info = await self._get_pumpfun_info(contract_address)
            if token_info:
                return token_info
                
            logger.warning(f"No token data found for {contract_address}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching token info for {contract_address}: {e}")
            return None
    
    async def _get_birdeye_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token info from Birdeye API."""
        try:
            if not self.session:
                return None
                
            url = f"https://public-api.birdeye.so/defi/token_overview"
            params = {'address': contract_address}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and data.get('data'):
                        token_data = data['data']
                        return {
                            'name': token_data.get('name', 'Unknown'),
                            'symbol': token_data.get('symbol', 'UNKNOWN'),
                            'price': float(token_data.get('price', 0)),
                            'market_cap': float(token_data.get('mc', 0)),
                            'volume_24h': float(token_data.get('v24hUSD', 0)),
                            'price_change_24h': float(token_data.get('priceChange24hPercent', 0)),
                            'source': 'birdeye',
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception as e:
            logger.debug(f"Birdeye API error for {contract_address}: {e}")
        return None
    
    async def _get_dexscreener_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token info from DexScreener API."""
        try:
            if not self.session:
                return None
                
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        # Get the pair with highest liquidity
                        best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
                        
                        return {
                            'name': best_pair.get('baseToken', {}).get('name', 'Unknown'),
                            'symbol': best_pair.get('baseToken', {}).get('symbol', 'UNKNOWN'),
                            'price': float(best_pair.get('priceUsd', 0)),
                            'market_cap': float(best_pair.get('marketCap', 0)),
                            'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                            'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
                            'source': 'dexscreener',
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception as e:
            logger.debug(f"DexScreener API error for {contract_address}: {e}")
        return None
    
    async def _get_pumpfun_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token info from pump.fun API for newer tokens."""
        try:
            if not self.session:
                return None
                
            url = f"https://frontend-api.pump.fun/coins/{contract_address}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'name': data.get('name', 'Unknown'),
                        'symbol': data.get('symbol', 'UNKNOWN'),
                        'price': float(data.get('usd_market_cap', 0)) / float(data.get('total_supply', 1)),
                        'market_cap': float(data.get('usd_market_cap', 0)),
                        'volume_24h': 0,  # pump.fun doesn't provide 24h volume
                        'price_change_24h': 0,  # pump.fun doesn't provide 24h change
                        'source': 'pump.fun',
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.debug(f"Pump.fun API error for {contract_address}: {e}")
        return None
