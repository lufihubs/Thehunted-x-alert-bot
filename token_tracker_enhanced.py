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
        self.last_alert_time: Dict[str, Dict[int, Dict[str, datetime]]] = {}  # contract -> {chat_id -> {alert_type -> last_alert_time}}
        self.is_running = False
        self.database = Database(Config.DATABASE_PATH)
        self.last_save_time = datetime.now()
        self.save_interval = 300  # Auto-save every 5 minutes
        
    async def start_tracking(self):
        """Start the enhanced multi-group token tracking loop."""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("🚀 Enhanced Multi-Group Token tracking started with auto-save")
        logger.info(f"🎯 PRIMARY FOCUS: The Hunted Group ({Config.THE_HUNTED_GROUP_ID})")
        
        # Load existing tokens from database organized by group
        await self._load_tokens_by_group()
        
        # Create initial backup
        await self.database.auto_save_on_update()
        
        # Start the tracking loop with enhanced real-time monitoring for ALL TOKENS
        while self.is_running:
            try:
                # Real-time check of ALL tokens across ALL groups (prioritizing The Hunted)
                await self._check_all_groups()
                await self._auto_remove_rugged_tokens()
                
                # Auto-save every 5 minutes
                if (datetime.now() - self.last_save_time).seconds >= self.save_interval:
                    await self._auto_save_data()
                
                # Enhanced real-time monitoring with 5-second intervals
                await asyncio.sleep(5)  # Faster updates for real-time alerts
            except Exception as e:
                logger.error(f"Error in enhanced tracking loop: {e}")
                await asyncio.sleep(5)  # Shorter retry interval for better real-time response
    
    async def _auto_save_data(self):
        """Automatically save all tracking data."""
        try:
            await self.database.save_all_group_data()
            self.last_save_time = datetime.now()
            logger.info("💾 Auto-saved all group tracking data")
        except Exception as e:
            logger.error(f"Error in auto-save: {e}")
    
    def stop_tracking(self):
        """Stop the token tracking loop and save data."""
        self.is_running = False
        logger.info("⏹️ Enhanced Token tracking stopped")
        
        # Save data before stopping
        asyncio.create_task(self._auto_save_data())
    
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
                    
                    # Auto-save after adding new token
                    await self.database.auto_save_on_update()
                    logger.info("💾 Auto-saved after adding new token")
                    
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
        """Check all groups for token price changes with REAL-TIME monitoring for ALL tokens."""
        if not self.tracking_tokens_by_group:
            logger.info("🔍 No groups with tokens to check")
            return
        
        total_groups = len(self.tracking_tokens_by_group)
        total_tokens = sum(len(tokens) for tokens in self.tracking_tokens_by_group.values())
        
        logger.info(f"🔄 REAL-TIME UPDATE: Starting price check for {total_tokens} tokens across {total_groups} groups")
        
        # NEW: Get ALL unique tokens for parallel processing
        all_unique_tokens = {}
        for chat_id, tokens in self.tracking_tokens_by_group.items():
            for contract_address, token_data in tokens.items():
                if contract_address not in all_unique_tokens:
                    all_unique_tokens[contract_address] = token_data
        
        logger.info(f"🎯 Processing {len(all_unique_tokens)} unique tokens for real-time updates")
        
        # Create parallel tasks for ALL unique tokens
        api = SolanaAPI()
        update_tasks = []
        async with api:
            for contract_address, token_data in all_unique_tokens.items():
                task = self._update_single_token_realtime(api, contract_address, token_data)
                update_tasks.append(task)
            
            if update_tasks:
                # Execute ALL token updates in parallel
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                
                # Count and log results
                successful_updates = sum(1 for r in results if r is True)
                failed_updates = len(results) - successful_updates
                
                logger.info(f"✅ REAL-TIME UPDATE COMPLETE: {successful_updates} tokens updated, {failed_updates} failed")
                
                # Now check alerts for all groups after ALL tokens are updated
                await self._check_alerts_for_all_updated_tokens()
            else:
                logger.warning("⚠️ No update tasks created")
    
    async def _update_single_token_realtime(self, api: SolanaAPI, contract_address: str, token_data: Dict):
        """Update a single token with real-time price data for ALL groups tracking it."""
        try:
            # Get current token info from API
            current_info = await api.get_token_info(contract_address)
            
            if current_info and current_info.get('market_cap', 0) > 0:
                new_mcap = current_info['market_cap']
                new_price = current_info['price']
                
                # Log significant price changes
                old_mcap = token_data.get('current_mcap', token_data.get('initial_mcap', 0))
                if old_mcap > 0:
                    change_pct = ((new_mcap - old_mcap) / old_mcap) * 100
                    if abs(change_pct) > 1:  # Log changes > 1%
                        logger.info(f"📈 {token_data.get('symbol', 'UNKNOWN')}: {change_pct:+.2f}% (${old_mcap:,.0f} → ${new_mcap:,.0f})")
                
                # Update database immediately
                await self.database.update_token_price(contract_address, new_mcap, new_price)
                
                # Update token data for ALL groups tracking this token
                await self._update_token_across_all_groups(contract_address, new_mcap, new_price)
                
                return True
            else:
                logger.warning(f"⚠️ No data for {token_data.get('symbol', 'Unknown')} ({contract_address[:8]}...)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating {contract_address}: {e}")
            return False
    
    async def _check_alerts_for_all_updated_tokens(self):
        """Check alerts for all tokens across all groups after real-time updates."""
        try:
            logger.info("🚨 Checking alerts for all updated tokens across all groups...")
            
            alert_tasks = []
            for chat_id, tokens in self.tracking_tokens_by_group.items():
                for contract_address, token_data in tokens.items():
                    # Create alert check tasks for each token in each group
                    task = self._check_all_alerts_for_token_in_group(contract_address, token_data, chat_id)
                    alert_tasks.append(task)
            
            if alert_tasks:
                alert_results = await asyncio.gather(*alert_tasks, return_exceptions=True)
                
                # Count alert notifications sent
                successful_alerts = sum(1 for r in alert_results if r is True)
                failed_alerts = sum(1 for r in alert_results if isinstance(r, Exception))
                
                if successful_alerts > 0:
                    logger.info(f"🚨 Alert check complete: {successful_alerts} alerts processed, {failed_alerts} errors")
                    
        except Exception as e:
            logger.error(f"❌ Error checking alerts for all tokens: {e}")
    
    async def _check_all_alerts_for_token_in_group(self, contract_address: str, token_data: Dict, chat_id: int):
        """Check all alert types for a specific token in a specific group."""
        try:
            # Check multiplier alerts
            await self._check_multiplier_alerts_for_group(contract_address, token_data, chat_id)
            
            # Check loss alerts
            await self._check_loss_alerts_for_group(contract_address, token_data, chat_id)
            
            # Check rug detection
            baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
            current_mcap = token_data['current_mcap']
            if baseline_mcap > 0:
                loss_percentage = ((current_mcap - baseline_mcap) / baseline_mcap) * 100
                await self._check_rug_detection_alert(contract_address, token_data, chat_id, loss_percentage)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking alerts for {contract_address} in group {chat_id}: {e}")
            return False
    
    async def _check_group_tokens(self, chat_id: int, tokens: Dict[str, Dict]):
        """Check tokens for a specific group with detailed logging."""
        group_token_count = len(tokens)
        logger.info(f"🔍 Checking {group_token_count} tokens in group {chat_id}")
        
        api = SolanaAPI()
        updated_count = 0
        error_count = 0
        
        async with api:
            for contract_address, token_data in list(tokens.items()):
                try:
                    # Get current token info
                    current_info = await api.get_token_info(contract_address)
                    
                    if current_info and current_info.get('market_cap', 0) > 0:
                        # Update token data with real-time price information
                        old_mcap = token_data['current_mcap']
                        new_mcap = current_info['market_cap']
                        new_price = current_info['price']
                        
                        # Log price change if significant
                        if old_mcap > 0:
                            price_change = ((new_mcap - old_mcap) / old_mcap) * 100
                            if abs(price_change) > 1:  # Log changes > 1%
                                logger.info(f"📈 {token_data['symbol']} price change: {price_change:+.2f}% (Group {chat_id})")
                        
                        # Update tracking data with all current values for THIS group
                        token_data['current_mcap'] = new_mcap
                        token_data['current_price'] = new_price
                        token_data['highest_mcap'] = max(token_data['highest_mcap'], new_mcap)
                        token_data['lowest_mcap'] = min(token_data['lowest_mcap'], new_mcap)
                        token_data['last_updated'] = datetime.now()
                        
                        # Calculate real-time loss percentage for rug detection
                        baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
                        if baseline_mcap > 0:
                            loss_percentage = ((new_mcap - baseline_mcap) / baseline_mcap) * 100
                            token_data['current_loss_percentage'] = loss_percentage
                            
                            # Real-time rug detection alert
                            await self._check_rug_detection_alert(contract_address, token_data, chat_id, loss_percentage)
                        
                        # Update database with latest prices (updates ALL groups in database)
                        await self.database.update_token_price(contract_address, new_mcap, new_price)
                        
                        # CRITICAL: Update tracking data for this token in ALL groups
                        await self._update_token_across_all_groups(contract_address, new_mcap, new_price)
                        
                        # CRITICAL: Check alerts for ALL groups tracking this token
                        await self._check_alerts_across_all_groups(contract_address, new_mcap, new_price)
                        
                        updated_count += 1
                        
                    else:
                        # Token might be rugged or delisted
                        logger.warning(f"⚠️ No data found for {token_data['symbol']} in group {chat_id}")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error checking token {contract_address} in group {chat_id}: {e}")
                    error_count += 1
        
        logger.info(f"✅ Group {chat_id}: {updated_count} tokens updated, {error_count} errors")
        return updated_count

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
            
            # Initialize sent_alerts if needed
            if contract_address not in self.sent_alerts:
                self.sent_alerts[contract_address] = {}
            if chat_id not in self.sent_alerts[contract_address]:
                self.sent_alerts[contract_address][chat_id] = set()
            
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
    
    async def _update_token_across_all_groups(self, contract_address: str, new_mcap: float, new_price: float):
        """Update token data across all groups that are tracking this token."""
        for group_id, group_tokens in self.tracking_tokens_by_group.items():
            if contract_address in group_tokens:
                token_data = group_tokens[contract_address]
                
                # Update all price-related data for this token in this group
                token_data['current_mcap'] = new_mcap
                token_data['current_price'] = new_price
                token_data['highest_mcap'] = max(token_data['highest_mcap'], new_mcap)
                token_data['lowest_mcap'] = min(token_data['lowest_mcap'], new_mcap)
                token_data['last_updated'] = datetime.now()
                
                # Update loss percentage for this group's tracking
                baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
                if baseline_mcap > 0:
                    loss_percentage = ((new_mcap - baseline_mcap) / baseline_mcap) * 100
                    token_data['current_loss_percentage'] = loss_percentage
                
                logger.debug(f"📊 Updated {token_data.get('symbol', 'Unknown')} in group {group_id}: ${new_mcap:,.0f}")
    
    async def _check_alerts_across_all_groups(self, contract_address: str, new_mcap: float, new_price: float):
        """Check and send alerts to ALL groups tracking this token."""
        for group_id, group_tokens in self.tracking_tokens_by_group.items():
            if contract_address in group_tokens:
                token_data = group_tokens[contract_address]
                
                # Check multiplier alerts for this group
                await self._check_multiplier_alerts_for_group(contract_address, token_data, group_id)
                
                # Check loss alerts for this group
                await self._check_loss_alerts_for_group(contract_address, token_data, group_id)
                
                # Check rug detection for this group (if significant loss)
                baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
                if baseline_mcap > 0:
                    loss_percentage = ((new_mcap - baseline_mcap) / baseline_mcap) * 100
                    await self._check_rug_detection_alert(contract_address, token_data, group_id, loss_percentage)
    
    async def _check_rug_detection_alert(self, contract_address: str, token_data: Dict, chat_id: int, loss_percentage: float):
        """Check and send real-time rug detection alerts."""
        try:
            # Check if token is potentially rugged (below rug detection threshold)
            if loss_percentage <= Config.RUG_DETECTION_THRESHOLD:
                # Use a special rug alert tracking system
                if not hasattr(self, 'rug_alerts_sent'):
                    self.rug_alerts_sent = set()
                
                rug_alert_key = f"rug_{contract_address}_{chat_id}"
                if rug_alert_key in self.rug_alerts_sent:
                    return
                
                # Check alert cooldown
                if self._is_alert_on_cooldown(contract_address, chat_id, 'rug'):
                    return
                
                # Send rug detection alert
                await self._send_rug_detection_alert(contract_address, token_data, chat_id, loss_percentage)
                
                # Mark as sent to prevent spam
                self.rug_alerts_sent.add(rug_alert_key)
                
                # Set cooldown
                self._set_alert_cooldown(contract_address, chat_id, 'rug')
                
        except Exception as e:
            logger.error(f"Error checking rug detection for {contract_address} in group {chat_id}: {e}")
    
    async def _send_rug_detection_alert(self, contract_address: str, token_data: Dict, chat_id: int, loss_percentage: float):
        """Send real-time rug detection alert."""
        try:
            message = f"""🚨 **POTENTIAL RUG DETECTED** 🚨

🪙 **{token_data['symbol']}** ({token_data['name']})
📉 **SEVERE LOSS**: {loss_percentage:.1f}%
💰 **Current MCap**: ${token_data['current_mcap']:,.0f}
📊 **Baseline MCap**: ${token_data.get('confirmed_scan_mcap', token_data['initial_mcap']):,.0f}

⚠️ **WARNING**: Token has dropped below {Config.RUG_DETECTION_THRESHOLD}%
⚠️ **CAUTION**: This may indicate a rug pull or major dump
⚠️ **ADVICE**: Consider exit strategy immediately

🔗 **Contract**: `{contract_address}`"""

            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"🚨 Sent rug detection alert for {token_data['symbol']} in group {chat_id} ({loss_percentage:.1f}% loss)")
            
        except Exception as e:
            logger.error(f"Error sending rug detection alert: {e}")

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
        """Check if alert is on cooldown for this token-group-type combination."""
        if contract_address not in self.last_alert_time:
            return False
        
        if chat_id not in self.last_alert_time[contract_address]:
            return False
        
        if alert_type not in self.last_alert_time[contract_address][chat_id]:
            return False
        
        last_alert = self.last_alert_time[contract_address][chat_id][alert_type]
        cooldown_time = timedelta(seconds=Config.ALERT_COOLDOWN)
        
        return datetime.now() - last_alert < cooldown_time
    
    def _set_alert_cooldown(self, contract_address: str, chat_id: int, alert_type: str):
        """Set alert cooldown for this token-group-type combination."""
        if contract_address not in self.last_alert_time:
            self.last_alert_time[contract_address] = {}
        
        if chat_id not in self.last_alert_time[contract_address]:
            self.last_alert_time[contract_address][chat_id] = {}
        
        self.last_alert_time[contract_address][chat_id][alert_type] = datetime.now()
    
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
            sent_multipliers = [float(m) for m in self.sent_alerts[contract_address][chat_id]]
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
