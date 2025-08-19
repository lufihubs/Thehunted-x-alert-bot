"""Token tracking and alert system."""
import asyncio
import logging
from typing import Dict, Set
from datetime import datetime, timedelta
from database import Database
from solana_api import SolanaAPI
from config import Config

logger = logging.getLogger(__name__)

class TokenTracker:
    def __init__(self, bot):
        self.bot = bot
        self.tracking_tokens: Dict[str, Dict] = {}
        self.sent_alerts: Dict[str, Set[int]] = {}  # contract -> set of multipliers sent
        self.is_running = False
        
    async def start_tracking(self):
        """Start the token tracking loop."""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🚀 Token tracking started")
        
        # Load existing tokens from database
        await self._load_existing_tokens()
        
        # Start the tracking loop
        while self.is_running:
            try:
                await self._check_all_tokens()
                await asyncio.sleep(Config.PRICE_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    def stop_tracking(self):
        """Stop the token tracking loop."""
        self.is_running = False
        logger.info("⏹️ Token tracking stopped")
    
    async def add_token(self, contract_address: str, chat_id: int, message_id: int) -> bool:
        """Add a new token for tracking."""
        try:
            # Check if token is already being tracked
            if contract_address in self.tracking_tokens:
                logger.warning(f"Token {contract_address} is already being tracked")
                return False
            
            async with SolanaAPI() as api:
                # Get initial token info with multiple confirmation attempts
                token_info = None
                for attempt in range(3):
                    token_info = await api.get_token_info(contract_address)
                    if token_info and token_info.get('market_cap', 0) > 0:
                        break
                    await asyncio.sleep(2)  # Wait before retry
                
                if not token_info or token_info.get('market_cap', 0) <= 0:
                    logger.warning(f"Could not get valid token info for {contract_address}")
                    return False
                
                # Store in database with confirmed scan mcap
                db = Database('tokens.db')
                success = await db.add_token(
                    contract_address=contract_address,
                    name=token_info['name'],
                    symbol=token_info['symbol'],
                    initial_price=token_info['price'],
                    initial_mcap=token_info['market_cap'],
                    chat_id=chat_id,
                    message_id=message_id
                )
                
                if success:
                        # Add to tracking
                        self.tracking_tokens[contract_address] = {
                            'name': token_info['name'],
                            'symbol': token_info['symbol'],
                            'initial_price': token_info['price'],
                            'initial_mcap': token_info['market_cap'],
                            'confirmed_scan_mcap': token_info['market_cap'],
                            'current_price': token_info['price'],
                            'current_mcap': token_info['market_cap'],
                            'highest_mcap': token_info['market_cap'],
                            'lowest_mcap': token_info['market_cap'],
                            'chat_id': chat_id,
                            'message_id': message_id,
                            'last_updated': datetime.now(),
                            'loss_50_alerted': False,
                            'loss_alerts_sent': '[]'  # Initialize empty JSON array
                        }
                        
                        self.sent_alerts[contract_address] = set()
                        
                        logger.info(f"✅ Added token {token_info['symbol']} ({contract_address[:8]}...) for tracking")
                        logger.info(f"💰 Initial market cap: ${token_info['market_cap']:,.2f}")
                        return True
                    
        except Exception as e:
            logger.error(f"Error adding token {contract_address}: {e}")
        
        return False
    
    async def _load_existing_tokens(self):
        """Load existing tokens from database."""
        try:
            db = Database('tokens.db')
            tokens = await db.get_active_tokens()
            
            for token in tokens:
                contract_address = token['contract_address']
                self.tracking_tokens[contract_address] = {
                    'name': token['name'],
                    'symbol': token['symbol'],
                    'initial_price': token['initial_price'],
                    'initial_mcap': token['initial_mcap'],
                    'confirmed_scan_mcap': token.get('confirmed_scan_mcap') or token['initial_mcap'],
                    'current_price': token['current_price'],
                    'current_mcap': token['current_mcap'],
                    'highest_mcap': token.get('highest_mcap') or token['initial_mcap'],
                    'lowest_mcap': token.get('lowest_mcap') or token['initial_mcap'],
                    'chat_id': token['chat_id'],
                    'message_id': token['message_id'],
                    'last_updated': datetime.fromisoformat(token['last_updated']),
                    'loss_50_alerted': bool(token.get('loss_50_alerted', False)),
                    'loss_alerts_sent': token.get('loss_alerts_sent', '[]')  # Load loss alert history
                }
                
                # Load sent alerts - for now use empty set, will add method later
                self.sent_alerts[contract_address] = set()
            
            logger.info(f"📊 Loaded {len(tokens)} tokens from database")
            
        except Exception as e:
            logger.error(f"Error loading existing tokens: {e}")
    
    async def _check_all_tokens(self):
        """Check all tracked tokens for price changes."""
        if not self.tracking_tokens:
            return
        
        async with SolanaAPI() as api:
            for contract_address, token_data in list(self.tracking_tokens.items()):
                try:
                    await self._check_token(api, contract_address, token_data)
                except Exception as e:
                    logger.error(f"Error checking token {contract_address}: {e}")
    
    async def _check_token(self, api: SolanaAPI, contract_address: str, token_data: Dict):
        """Check a single token for price changes and send alerts."""
        try:
            # Get current token info
            current_info = await api.get_token_info(contract_address)
            if not current_info:
                return
            
            # Update token data
            old_mcap = token_data['current_mcap']
            token_data['current_price'] = current_info['price']
            token_data['current_mcap'] = current_info['market_cap']
            token_data['last_updated'] = datetime.now()
            
            # Update highest and lowest mcap
            if current_info['market_cap'] > token_data['highest_mcap']:
                token_data['highest_mcap'] = current_info['market_cap']
            if current_info['market_cap'] < token_data['lowest_mcap']:
                token_data['lowest_mcap'] = current_info['market_cap']
            
            # Use confirmed scan mcap for calculations
            base_mcap = token_data['confirmed_scan_mcap']
            
            # Calculate multiplier based on confirmed scan mcap
            if base_mcap > 0:
                current_multiplier = current_info['market_cap'] / base_mcap
                
                # Check for multiplier alerts
                await self._check_multiplier_alerts(contract_address, token_data, current_multiplier)
                
                # Check for -50% loss alert
                await self._check_loss_alerts(contract_address, token_data, current_multiplier)
            
            # Update database
            db = Database('tokens.db')
            await db.update_token_price(
                contract_address=contract_address,
                current_price=current_info['price'],
                current_mcap=current_info['market_cap']
            )
            
        except Exception as e:
            logger.error(f"Error checking token {contract_address}: {e}")
    
    async def _check_multiplier_alerts(self, contract_address: str, token_data: Dict, current_multiplier: float):
        """Check and send multiplier alerts."""
        for multiplier in Config.ALERT_MULTIPLIERS:
            if (current_multiplier >= multiplier and 
                multiplier not in self.sent_alerts[contract_address]):
                
                # Send alert
                await self._send_multiplier_alert(contract_address, token_data, multiplier, current_multiplier)
                
                # Mark as sent
                self.sent_alerts[contract_address].add(multiplier)
                
                # Store in database
                db = Database('tokens.db')
                # For now, skip storing individual alerts
                # await db.add_sent_alert(contract_address, multiplier, current_multiplier)
    
    async def _check_loss_alerts(self, contract_address: str, token_data: Dict, current_multiplier: float):
        """Check and send loss alerts for multiple thresholds."""
        loss_percentage = (current_multiplier - 1) * 100
        
        # Get already sent loss alerts
        import json
        sent_alerts = set()
        try:
            if 'loss_alerts_sent' in token_data:
                sent_alerts = set(json.loads(token_data.get('loss_alerts_sent', '[]')))
        except (json.JSONDecodeError, TypeError):
            sent_alerts = set()
        
        # Check each loss threshold
        for threshold in Config.LOSS_THRESHOLDS:
            if (loss_percentage <= threshold and 
                threshold not in sent_alerts):
                
                # Send loss alert for this threshold
                await self._send_loss_alert(contract_address, token_data, loss_percentage, threshold)
                
                # Mark this threshold as sent
                sent_alerts.add(threshold)
                token_data['loss_alerts_sent'] = json.dumps(list(sent_alerts))
                
                # Also maintain backward compatibility with old field
                if threshold == -50:
                    token_data['loss_50_alerted'] = True
    
    async def _send_multiplier_alert(self, contract_address: str, token_data: Dict, target_multiplier: int, actual_multiplier: float):
        """Send a multiplier alert to the chat."""
        try:
            symbol = token_data['symbol']
            name = token_data['name']
            current_mcap = token_data['current_mcap']
            confirmed_scan_mcap = token_data['confirmed_scan_mcap']
            
            # Create alert message
            alert_message = (
                f"🚀 *{target_multiplier}x ALERT* 🚀\n\n"
                f"💎 *{name}* ({symbol})\n"
                f"📝 `{contract_address}`\n\n"
                f"📊 *Current Multiplier:* {actual_multiplier:.2f}x\n"
                f"💰 *Scan Market Cap:* ${confirmed_scan_mcap:,.2f}\n"
                f"💰 *Current Market Cap:* ${current_mcap:,.2f}\n"
                f"📈 *Gain:* +{(actual_multiplier-1)*100:.1f}%\n\n"
                f"🔥 *{target_multiplier}X PUMP!* 🔥"
            )
            
            await self.bot.send_message(
                chat_id=token_data['chat_id'],
                text=alert_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚀 Sent {target_multiplier}x alert for {symbol} ({actual_multiplier:.2f}x)")
            
        except Exception as e:
            logger.error(f"Error sending multiplier alert: {e}")
    
    async def _send_loss_alert(self, contract_address: str, token_data: Dict, loss_percentage: float, threshold: int = -50):
        """Send a loss alert to the chat."""
        try:
            symbol = token_data['symbol']
            name = token_data['name']
            current_mcap = token_data['current_mcap']
            confirmed_scan_mcap = token_data['confirmed_scan_mcap']
            
            # Create dynamic alert message based on threshold
            alert_emoji = "📉" if threshold >= -50 else "💥" if threshold >= -80 else "🚨"
            severity = "LOSS ALERT" if threshold >= -50 else "MAJOR LOSS" if threshold >= -80 else "CRITICAL LOSS"
            
            alert_message = (
                f"{alert_emoji} *{severity}* {alert_emoji}\n\n"
                f"💎 *{name}* ({symbol})\n"
                f"📝 `{contract_address}`\n\n"
                f"💰 *Scan Market Cap:* ${confirmed_scan_mcap:,.2f}\n"
                f"💰 *Current Market Cap:* ${current_mcap:,.2f}\n"
                f"📉 *Loss:* {loss_percentage:.1f}%\n\n"
                f"⚠️ *{threshold}% FROM SCAN!* ⚠️"
            )
            
            await self.bot.send_message(
                chat_id=token_data['chat_id'],
                text=alert_message,
                parse_mode='Markdown'
            )
            
            logger.info(f"📉 Sent loss alert for {symbol} ({loss_percentage:.1f}%)")
            
        except Exception as e:
            logger.error(f"Error sending loss alert: {e}")
    
    def get_tracking_status(self) -> Dict:
        """Get current tracking status."""
        return {
            'total_tokens': len(self.tracking_tokens),
            'is_running': self.is_running,
            'tokens': list(self.tracking_tokens.keys())
        }
