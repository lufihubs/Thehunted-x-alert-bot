"""Enhanced Solana API module with DexScreener as primary source and comprehensive token detection."""
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class SolanaAPI:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        # DexScreener as primary, others as fallbacks
        self.api_sources = {
            'dexscreener': 'https://api.dexscreener.com/latest/dex',
            'birdeye': 'https://public-api.birdeye.so/defi',
            'pump': 'https://frontend-api.pump.fun/coins',
            'jupiter': 'https://quote-api.jup.ag/v6',
            'raydium': 'https://api.raydium.io/v2'
        }
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'SolanaAlertBot/2.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def detect_contract_addresses(self, text: str) -> List[str]:
        """Enhanced contract address detection for all Solana token formats"""
        # Comprehensive regex patterns for different Solana address formats
        patterns = [
            # Standard Solana address (44 chars base58) - most common
            r'(?:^|(?<=\s)|(?<=\W))([1-9A-HJ-NP-Za-km-z]{43,44})(?=\s|[\.\,\!\?\;\:\)\]\}]|$|(?=\W))',
            # Pump.fun specific format
            r'(?:pump\.fun/)?([1-9A-HJ-NP-Za-km-z]{43,44})(?:pump)?',
            # DexScreener URL format
            r'dexscreener\.com/solana/([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Birdeye URL format  
            r'birdeye\.so/token/([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Jupiter URL format
            r'jup\.ag/swap/[^-]+-([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Raydium URL format
            r'raydium\.io/swap/\?inputCurrency=[^&]*&outputCurrency=([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Generic token address in any context
            r'(?:token|contract|address|ca)[:=\s]*([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Solscan format
            r'solscan\.io/token/([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Solana Beach format
            r'solanabeach\.io/token/([1-9A-HJ-NP-Za-km-z]{43,44})',
            # Direct address without context
            r'\b([1-9A-HJ-NP-Za-km-z]{44})\b',
            # Address with common prefixes
            r'(?:CA|ca|Contract|ADDRESS|Token)[:=\s]+([1-9A-HJ-NP-Za-km-z]{43,44})',
        ]
        
        addresses = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # Handle tuple results from capture groups
                    for addr in match:
                        if addr and len(addr) >= 43:
                            addresses.add(addr)
                else:
                    if match and len(match) >= 43:
                        addresses.add(match)
        
        # Validate addresses (basic Solana address validation)
        valid_addresses = []
        for addr in addresses:
            if self._is_valid_solana_address(addr):
                valid_addresses.append(addr)
        
        return valid_addresses
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """Validate Solana address format"""
        if not address or len(address) < 43 or len(address) > 44:
            return False
        
        # Check if it's valid base58
        base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        if not all(c in base58_chars for c in address):
            return False
        
        # Exclude common false positives
        false_positives = [
            '11111111111111111111111111111111',  # System program
            'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',  # Token program
            'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
        ]
        
        return address not in false_positives
    
    async def get_token_data_dexscreener(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token data from DexScreener (primary source)"""
        try:
            if not self.session:
                return None
                
            # Try multiple DexScreener endpoints
            endpoints = [
                f"{self.api_sources['dexscreener']}/tokens/{contract_address}",
                f"{self.api_sources['dexscreener']}/search/?q={contract_address}",
                f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            ]
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Parse DexScreener response format
                            token_info = self._parse_dexscreener_data(data, contract_address)
                            if token_info:
                                logger.info(f"✅ DexScreener data found for {contract_address}")
                                return token_info
                                
                except Exception as e:
                    logger.debug(f"DexScreener endpoint {endpoint} failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ DexScreener API error for {contract_address}: {e}")
        
        return None
    
    def _parse_dexscreener_data(self, data: Dict, contract_address: str) -> Optional[Dict[str, Any]]:
        """Parse DexScreener API response"""
        try:
            # Handle different DexScreener response formats
            pairs = []
            
            if 'pairs' in data:
                pairs = data['pairs']
            elif 'tokens' in data:
                # Search response format
                for token in data['tokens']:
                    if token.get('address') == contract_address:
                        pairs = token.get('pairs', [])
            elif isinstance(data, list):
                pairs = data
            
            if not pairs:
                return None
            
            # Find the best pair (highest liquidity)
            best_pair = max(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0) or 0))
            
            if not best_pair:
                return None
            
            # Extract token info
            base_token = best_pair.get('baseToken', {})
            quote_token = best_pair.get('quoteToken', {})
            
            # Determine which token is our target
            target_token = base_token if base_token.get('address') == contract_address else quote_token
            
            if not target_token:
                return None
            
            price_usd = float(best_pair.get('priceUsd', 0) or 0)
            market_cap = float(best_pair.get('marketCap', 0) or 0)
            
            # Calculate market cap if not provided
            if not market_cap and price_usd:
                total_supply = float(target_token.get('totalSupply', 0) or 0)
                if total_supply:
                    market_cap = price_usd * total_supply
            
            return {
                'symbol': target_token.get('symbol', 'UNKNOWN'),
                'name': target_token.get('name', 'Unknown Token'),
                'price': price_usd,
                'market_cap': market_cap,
                'contract_address': contract_address,
                'platform': 'solana',
                'dex': best_pair.get('dexId', 'unknown'),
                'pair_address': best_pair.get('pairAddress'),
                'liquidity_usd': float(best_pair.get('liquidity', {}).get('usd', 0) or 0),
                'volume_24h': float(best_pair.get('volume', {}).get('h24', 0) or 0),
                'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0) or 0),
                'source': 'dexscreener',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing DexScreener data: {e}")
            return None
    
    async def get_token_data_birdeye(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token data from Birdeye (fallback)"""
        try:
            if not self.session:
                return None
                
            # Multiple Birdeye endpoints
            endpoints = [
                f"{self.api_sources['birdeye']}/token/overview?address={contract_address}",
                f"{self.api_sources['birdeye']}/token/price?address={contract_address}",
            ]
            
            token_data = {}
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if 'data' in data and data['data']:
                                token_info = data['data']
                                
                                # Merge data from different endpoints
                                token_data.update({
                                    'symbol': token_info.get('symbol', 'UNKNOWN'),
                                    'name': token_info.get('name', 'Unknown Token'),
                                    'price': float(token_info.get('price', 0) or 0),
                                    'market_cap': float(token_info.get('mc', 0) or 0),
                                    'contract_address': contract_address,
                                    'platform': 'solana',
                                    'source': 'birdeye',
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                except Exception as e:
                    logger.debug(f"Birdeye endpoint failed: {e}")
                    continue
            
            return token_data if token_data else None
            
        except Exception as e:
            logger.error(f"❌ Birdeye API error for {contract_address}: {e}")
        
        return None
    
    async def get_token_data_pump(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get token data from Pump.fun (fallback for meme tokens)"""
        try:
            if not self.session:
                return None
                
            endpoints = [
                f"{self.api_sources['pump']}/{contract_address}",
                f"https://frontend-api.pump.fun/coins/search?q={contract_address}"
            ]
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if isinstance(data, dict) and data:
                                return {
                                    'symbol': data.get('symbol', 'PUMP'),
                                    'name': data.get('name', 'Pump Token'),
                                    'price': float(data.get('usd_market_cap', 0)) / float(data.get('total_supply', 1)) if data.get('total_supply') else 0,
                                    'market_cap': float(data.get('usd_market_cap', 0) or 0),
                                    'contract_address': contract_address,
                                    'platform': 'pump.fun',
                                    'source': 'pump.fun',
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                except Exception as e:
                    logger.debug(f"Pump.fun endpoint failed: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Pump.fun API error for {contract_address}: {e}")
        
        return None
    
    async def get_token_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive token data using all available sources"""
        logger.info(f"🔍 Fetching token data for {contract_address}")
        
        # Try DexScreener first (most comprehensive)
        token_data = await self.get_token_data_dexscreener(contract_address)
        if token_data and token_data.get('market_cap', 0) > 0:
            return token_data
        
        # Try Birdeye as fallback
        token_data = await self.get_token_data_birdeye(contract_address)
        if token_data and token_data.get('market_cap', 0) > 0:
            return token_data
        
        # Try Pump.fun for meme tokens
        token_data = await self.get_token_data_pump(contract_address)
        if token_data and token_data.get('market_cap', 0) > 0:
            return token_data
        
        # If all APIs fail, return basic data
        logger.warning(f"⚠️ No market data found for {contract_address}, using basic info")
        return {
            'symbol': 'UNKNOWN',
            'name': 'Unknown Token',
            'price': 0.0,
            'market_cap': 0.0,
            'contract_address': contract_address,
            'platform': 'solana',
            'source': 'fallback',
            'timestamp': datetime.now().isoformat()
        }
