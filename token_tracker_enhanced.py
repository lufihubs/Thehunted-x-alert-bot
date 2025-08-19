"""Enhanced token tracking and alert system with multi-group support."""
import asyncio
import logging
from typing import Dict, Set, List
from datetime import datetime, timedelta
from database import Database
from solana_api import SolanaAPI
from config import Config
import json

logger = logging.getLogger(__name__)

class TokenTracker:
    def __init__(self, bot):
        self.bot = bot
        self.tracking_tokens_by_group: Dict[int, Dict[str, Dict]] = {}  # chat_id -> {contract -> token_data}
        self.sent_alerts: Dict[str, Dict[int, Set[int]]] = {}  # contract -> {chat_id -> set of multipliers}
        self.last_alert_time: Dict[str, Dict[int, datetime]] = {}  # contract -> {chat_id -> last_alert_time}
        self.is_running = False
        self.database = Database(Config.DATABASE_PATH)
        
    async def start_tracking(self):
        """Start the enhanced multi-group token tracking loop."""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🚀 Enhanced Multi-Group Token tracking started")
        
        # Load existing tokens from database organized by group
        await self._load_tokens_by_group()
        
        # Start the tracking loop with real-time monitoring
        while self.is_running:
            try:
                await self._check_all_groups()
                await self._auto_remove_rugged_tokens()
                await asyncio.sleep(Config.PRICE_CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                await asyncio.sleep(5)  # Shorter retry interval for better real-time response
    
    def stop_tracking(self):
        """Stop the token tracking loop."""
        self.is_running = False
        logger.info("⏹️ Enhanced Token tracking stopped")
    
    async def add_token(self, contract_address: str, chat_id: int, message_id: int) -> bool:
        """Add a new token for tracking in a specific group."""
        try:
            # Initialize group tracking if not exists
            if chat_id not in self.tracking_tokens_by_group:
                self.tracking_tokens_by_group[chat_id] = {}
            
            # Check if token is already being tracked in this group
            if contract_address in self.tracking_tokens_by_group[chat_id]:
                logger.warning(f"Token {contract_address} is already being tracked in group {chat_id}")
                return False
            
            # Get token info from API
            api = SolanaAPI()
            async with api:
                token_info = await api.get_token_info(contract_address)
                
                if not token_info or token_info.get('market_cap', 0) <= 0:
                    logger.error(f"Invalid token data for {contract_address}")
                    return False
                
                # Add to database
                success = await self.database.add_token(
                    contract_address=contract_address,
                    symbol=token_info['symbol'],
                    name=token_info['name'],
                    initial_mcap=token_info['market_cap'],
                    initial_price=token_info['price'],
                    chat_id=chat_id,
                    message_id=message_id,
                    source_api='dexscreener',
                    liquidity_usd=token_info.get('liquidity_usd', 0),
                    volume_24h=token_info.get('volume_24h', 0),
                    price_change_24h=token_info.get('price_change_24h', 0)
                )
                
                if success:
                    # Add to group tracking
                    self.tracking_tokens_by_group[chat_id][contract_address] = {
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
                        'loss_alerts_sent': '[]',
                        'multipliers_alerted': '[]'
                    }
                    
                    # Initialize alert tracking
                    if contract_address not in self.sent_alerts:
                        self.sent_alerts[contract_address] = {}
                    self.sent_alerts[contract_address][chat_id] = set()
                    
                    logger.info(f"✅ Added token {token_info['symbol']} ({contract_address[:8]}...) for group {chat_id}")
                    logger.info(f"💰 Initial market cap: ${token_info['market_cap']:,.2f}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error adding token {contract_address} to group {chat_id}: {e}")
        
        return False
    
    async def _load_tokens_by_group(self):
        """Load existing tokens from database organized by group."""
        try:
            tokens_by_group = await self.database.get_all_active_tokens_by_group()
            
            for chat_id, tokens in tokens_by_group.items():
                self.tracking_tokens_by_group[chat_id] = {}
                
                for token in tokens:
                    contract_address = token['contract_address']
                    
                    # Initialize token data for this group
                    self.tracking_tokens_by_group[chat_id][contract_address] = {
                        'name': token['name'],
                        'symbol': token['symbol'],
                        'initial_price': token['initial_price'],
                        'initial_mcap': token['initial_mcap'],
                        'confirmed_scan_mcap': token.get('confirmed_scan_mcap') or token['initial_mcap'],
                        'current_price': token['current_price'] or token['initial_price'],
                        'current_mcap': token['current_mcap'] or token['initial_mcap'],
                        'highest_mcap': token.get('highest_mcap') or token['initial_mcap'],
                        'lowest_mcap': token.get('lowest_mcap') or token['initial_mcap'],
                        'chat_id': token['chat_id'],
                        'message_id': token['message_id'],
                        'last_updated': datetime.fromisoformat(token['last_updated']) if token['last_updated'] else datetime.now(),
                        'loss_alerts_sent': token.get('loss_alerts_sent', '[]'),
                        'multipliers_alerted': token.get('multipliers_alerted', '[]')
                    }
                    
                    # Initialize alert tracking for this token-group combination
                    if contract_address not in self.sent_alerts:
                        self.sent_alerts[contract_address] = {}
                    if chat_id not in self.sent_alerts[contract_address]:
                        self.sent_alerts[contract_address][chat_id] = set()
                    
                    # Load previously sent multiplier alerts
                    try:
                        multipliers_alerted = json.loads(token.get('multipliers_alerted', '[]'))
                        self.sent_alerts[contract_address][chat_id].update(multipliers_alerted)
                    except:
                        pass
            
            total_tokens = sum(len(tokens) for tokens in self.tracking_tokens_by_group.values())
            logger.info(f"📊 Loaded {total_tokens} tokens across {len(self.tracking_tokens_by_group)} groups")
            
        except Exception as e:
            logger.error(f"Error loading tokens by group: {e}")
    
    async def _check_all_groups(self):
        """Check all groups for token price changes."""
        if not self.tracking_tokens_by_group:
            return
        
        tasks = []
        for chat_id, tokens in self.tracking_tokens_by_group.items():
            if tokens:  # Only process groups with tokens
                tasks.append(self._check_group_tokens(chat_id, tokens))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_group_tokens(self, chat_id: int, tokens: Dict[str, Dict]):
        """Check tokens for a specific group."""
        api = SolanaAPI()
        
        async with api:
            for contract_address, token_data in list(tokens.items()):
                try:
                    # Get current token info
                    current_info = await api.get_token_info(contract_address)
                    
                    if current_info and current_info.get('market_cap', 0) > 0:
                        # Update token data
                        old_mcap = token_data['current_mcap']
                        new_mcap = current_info['market_cap']
                        new_price = current_info['price']
                        
                        # Update tracking data
                        token_data['current_mcap'] = new_mcap
                        token_data['current_price'] = new_price
                        token_data['highest_mcap'] = max(token_data['highest_mcap'], new_mcap)
                        token_data['lowest_mcap'] = min(token_data['lowest_mcap'], new_mcap)
                        token_data['last_updated'] = datetime.now()
                        
                        # Update database
                        await self.database.update_token_price(contract_address, new_mcap, new_price)
                        
                        # Check for alerts - group-specific
                        await self._check_multiplier_alerts_for_group(contract_address, token_data, chat_id)
                        await self._check_loss_alerts_for_group(contract_address, token_data, chat_id)
                        
                    else:
                        # Token might be rugged or delisted
                        logger.warning(f"⚠️ No data found for {token_data['symbol']} in group {chat_id}")
                        
                except Exception as e:
                    logger.error(f"Error checking token {contract_address} in group {chat_id}: {e}")
    
    async def _check_multiplier_alerts_for_group(self, contract_address: str, token_data: Dict, chat_id: int):
        """Check and send multiplier alerts for a specific group."""
        try:
            baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
            current_mcap = token_data['current_mcap']
            
            if baseline_mcap <= 0:
                return
            
            multiplier = current_mcap / baseline_mcap
            
            # Check alert cooldown
            if self._is_alert_on_cooldown(contract_address, chat_id, 'multiplier'):
                return
            
            # Check which multiplier alerts should be sent
            for alert_multiplier in Config.ALERT_MULTIPLIERS:
                if (multiplier >= alert_multiplier and 
                    alert_multiplier not in self.sent_alerts[contract_address][chat_id]):
                    
                    # Send alert
                    await self._send_multiplier_alert(
                        contract_address, token_data, chat_id, alert_multiplier, multiplier
                    )
                    
                    # Mark as sent
                    self.sent_alerts[contract_address][chat_id].add(alert_multiplier)
                    
                    # Update database
                    await self._update_multiplier_alerts_db(contract_address, chat_id)
                    
                    # Set cooldown
                    self._set_alert_cooldown(contract_address, chat_id, 'multiplier')
                    
        except Exception as e:
            logger.error(f"Error checking multiplier alerts for {contract_address} in group {chat_id}: {e}")
    
    async def _check_loss_alerts_for_group(self, contract_address: str, token_data: Dict, chat_id: int):
        """Check and send loss alerts for a specific group."""
        try:
            baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
            current_mcap = token_data['current_mcap']
            
            if baseline_mcap <= 0:
                return
            
            loss_percentage = ((current_mcap - baseline_mcap) / baseline_mcap) * 100
            
            # Check alert cooldown
            if self._is_alert_on_cooldown(contract_address, chat_id, 'loss'):
                return
            
            # Load sent loss alerts
            try:
                sent_loss_alerts = json.loads(token_data.get('loss_alerts_sent', '[]'))
            except:
                sent_loss_alerts = []
            
            # Check which loss alerts should be sent
            for threshold in Config.LOSS_THRESHOLDS:
                if (loss_percentage <= threshold and 
                    threshold not in sent_loss_alerts):
                    
                    # Send loss alert
                    await self._send_loss_alert(
                        contract_address, token_data, chat_id, threshold, loss_percentage
                    )
                    
                    # Mark as sent
                    sent_loss_alerts.append(threshold)
                    token_data['loss_alerts_sent'] = json.dumps(sent_loss_alerts)
                    
                    # Update database
                    await self._update_loss_alerts_db(contract_address, sent_loss_alerts)
                    
                    # Set cooldown
                    self._set_alert_cooldown(contract_address, chat_id, 'loss')
                    
        except Exception as e:
            logger.error(f"Error checking loss alerts for {contract_address} in group {chat_id}: {e}")
    
    async def _send_multiplier_alert(self, contract_address: str, token_data: Dict, chat_id: int, 
                                   alert_multiplier: int, current_multiplier: float):
        """Send multiplier alert to specific group."""
        try:
            message = f"""🚨 **{alert_multiplier}x MULTIPLIER ALERT** 🚨

🪙 **{token_data['symbol']}** ({token_data['name']})
💰 **Current Price**: ${token_data['current_price']:.8f}
📊 **Current MCap**: ${token_data['current_mcap']:,.0f}
📈 **Multiplier**: {current_multiplier:.2f}x
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

🎉 Your token has reached a {alert_multiplier}x multiplier!"""

            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚨 Sent {alert_multiplier}x alert for {token_data['symbol']} to group {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending multiplier alert: {e}")
    
    async def _send_loss_alert(self, contract_address: str, token_data: Dict, chat_id: int, 
                             threshold: float, current_loss: float):
        """Send loss alert to specific group."""
        try:
            message = f"""🚨 **{abs(threshold):.0f}% LOSS ALERT** 🚨

🪙 **{token_data['symbol']}** ({token_data['name']})
💰 **Current Price**: ${token_data['current_price']:.8f}
📊 **Current MCap**: ${token_data['current_mcap']:,.0f}
📉 **Loss**: {current_loss:.1f}%
⏰ **Time**: {datetime.now().strftime('%H:%M:%S')}

⚠️ Your token has dropped {abs(threshold):.0f}% from baseline!"""

            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚨 Sent {abs(threshold):.0f}% loss alert for {token_data['symbol']} to group {chat_id}")
            
        except Exception as e:
            logger.error(f"Error sending loss alert: {e}")
    
    async def _auto_remove_rugged_tokens(self):
        """Auto-remove rugged tokens from all groups."""
        try:
            # Check for rugged tokens
            removed_tokens = await self.database.auto_remove_rugged_tokens(Config.AUTO_REMOVE_THRESHOLD)
            
            # Remove from tracking
            for token in removed_tokens:
                contract_address = token['contract_address']
                chat_id = token['chat_id']
                
                if (chat_id in self.tracking_tokens_by_group and 
                    contract_address in self.tracking_tokens_by_group[chat_id]):
                    
                    del self.tracking_tokens_by_group[chat_id][contract_address]
                    
                    # Send removal notification
                    await self._send_auto_removal_notification(token)
                    
                    logger.info(f"🗑️ Auto-removed {token['symbol']} from group {chat_id} ({token['loss_percentage']:.1f}% loss)")
            
            # Check for zero liquidity tokens
            if Config.ZERO_LIQUIDITY_REMOVAL:
                zero_liquidity_tokens = await self.database.check_zero_liquidity_tokens()
                
                for token in zero_liquidity_tokens:
                    contract_address = token['contract_address']
                    chat_id = token['chat_id']
                    
                    if (chat_id in self.tracking_tokens_by_group and 
                        contract_address in self.tracking_tokens_by_group[chat_id]):
                        
                        del self.tracking_tokens_by_group[chat_id][contract_address]
                        await self._send_zero_liquidity_notification(token)
                        
                        logger.info(f"🗑️ Auto-removed {token['symbol']} from group {chat_id} (zero liquidity)")
            
        except Exception as e:
            logger.error(f"Error in auto-remove rugged tokens: {e}")
    
    def _is_alert_on_cooldown(self, contract_address: str, chat_id: int, alert_type: str) -> bool:
        """Check if alert is on cooldown for this token-group combination."""
        if contract_address not in self.last_alert_time:
            return False
        
        if chat_id not in self.last_alert_time[contract_address]:
            return False
        
        last_alert = self.last_alert_time[contract_address][chat_id]
        cooldown_time = timedelta(seconds=Config.ALERT_COOLDOWN)
        
        return datetime.now() - last_alert < cooldown_time
    
    def _set_alert_cooldown(self, contract_address: str, chat_id: int, alert_type: str):
        """Set alert cooldown for this token-group combination."""
        if contract_address not in self.last_alert_time:
            self.last_alert_time[contract_address] = {}
        
        self.last_alert_time[contract_address][chat_id] = datetime.now()
    
    async def _send_auto_removal_notification(self, token: Dict):
        """Send notification about auto-removed token."""
        try:
            message = f"""🗑️ **AUTO-REMOVED TOKEN**

🪙 **{token['symbol']}** ({token['name']})
📉 **Loss**: {token['loss_percentage']:.1f}%
💰 **Current MCap**: ${token['current_mcap']:,.0f}
📊 **Baseline MCap**: ${token['baseline_mcap']:,.0f}

⚠️ Token automatically removed due to severe loss (below {Config.AUTO_REMOVE_THRESHOLD}%)"""

            await self.bot.send_message(
                chat_id=token['chat_id'],
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error sending auto-removal notification: {e}")
    
    async def _send_zero_liquidity_notification(self, token: Dict):
        """Send notification about zero liquidity token removal."""
        try:
            message = f"""🗑️ **AUTO-REMOVED TOKEN**

🪙 **{token['symbol']}** ({token['name']})
💧 **Liquidity**: ${token['liquidity_usd']:,.0f}
💰 **MCap**: ${token['current_mcap']:,.0f}

⚠️ Token automatically removed due to zero/low liquidity"""

            await self.bot.send_message(
                chat_id=token['chat_id'],
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error sending zero liquidity notification: {e}")
    
    async def _update_multiplier_alerts_db(self, contract_address: str, chat_id: int):
        """Update multiplier alerts in database."""
        try:
            sent_multipliers = list(self.sent_alerts[contract_address][chat_id])
            await self.database.update_multipliers_alerted(contract_address, sent_multipliers)
        except Exception as e:
            logger.error(f"Error updating multiplier alerts in DB: {e}")
    
    async def _update_loss_alerts_db(self, contract_address: str, sent_loss_alerts: List):
        """Update loss alerts in database."""
        try:
            await self.database.update_loss_alerts_sent(contract_address, sent_loss_alerts)
        except Exception as e:
            logger.error(f"Error updating loss alerts in DB: {e}")
    
    def get_status(self) -> Dict:
        """Get tracker status with multi-group information."""
        total_tokens = sum(len(tokens) for tokens in self.tracking_tokens_by_group.values())
        
        return {
            'is_running': self.is_running,
            'total_groups': len(self.tracking_tokens_by_group),
            'total_tokens': total_tokens,
            'groups': {
                chat_id: {
                    'token_count': len(tokens),
                    'tokens': list(tokens.keys())
                }
                for chat_id, tokens in self.tracking_tokens_by_group.items()
            }
        }
