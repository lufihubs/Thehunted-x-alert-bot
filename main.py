"""Enhanced Telegram Bot Application for Solana Token Alerts with Group Support and Menu System."""
import asyncio
import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import Config
from database import Database
from token_tracker import TokenTracker
from solana_api import SolanaAPI

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SolanaAlertBot:
    def __init__(self):
        self.application = None
        self.token_tracker = None
        self.database = None
        self.solana_api = None
        
    async def initialize(self):
        """Initialize the bot application with enhanced features."""
        if not Config.validate():
            raise ValueError("Invalid configuration")
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize components
        self.database = Database(Config.DATABASE_PATH)
        await self.database.init_db()
        
        self.solana_api = SolanaAPI()
        self.token_tracker = TokenTracker(self.application.bot)
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("list", self.list_tokens_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("remove", self.remove_token_command))
        self.application.add_handler(CommandHandler("search", self.search_tokens_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stop", self.stop_tracking_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("🤖 Enhanced Bot initialized successfully with group support")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with enhanced welcome."""
        if not update.message:
            return
            
        chat_id = update.effective_chat.id if update.effective_chat else 0
        chat_title = update.effective_chat.title if update.effective_chat else "Private Chat"
        chat_type = update.effective_chat.type if update.effective_chat else "private"
        
        # Register the group/chat
        await self.database.register_group(chat_id, chat_title, chat_type)
        
        welcome_message = (
            "🚀 *Enhanced Solana Token Alert Bot* 🚀\n\n"
            "🔍 *Perfect Token Detection* - Never miss a launch!\n"
            "📊 *DexScreener Integration* - Real-time accurate data\n"
            "👥 *Group-Specific Tracking* - Each group has its own tokens\n"
            "⚡ *Lightning Fast* - 15-second monitoring intervals\n\n"
            "📋 *Quick Commands:*\n"
            "• `/menu` - Access all features\n"
            "• `/list` - View tracked tokens\n"
            "• `/stats` - Group statistics\n"
            "• Send any Solana contract address to start tracking!\n\n"
            "🎯 *Alert Types:*\n"
            "🚀 Multiplier alerts: 2x, 3x, 5x, 8x, 10x, up to 100x!\n"
            "📉 Loss alerts: -50%, -70%, -85%, -95%\n"
            "� Perfect detection of all Solana tokens\n\n"
            "🔥 *Ready to catch some moonshots!* 🔥"
        )
        
        # Create menu keyboard
        keyboard = [
            [InlineKeyboardButton("📋 Main Menu", callback_data="menu_main")],
            [InlineKeyboardButton("📊 View Tokens", callback_data="menu_list"),
             InlineKeyboardButton("📈 Statistics", callback_data="menu_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Start tracking if not already running
        if not self.token_tracker.is_running:
            asyncio.create_task(self.token_tracker.start_tracking())
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display the main menu with all available options."""
        if not update.message:
            return
            
        keyboard = [
            [InlineKeyboardButton("📊 View Tracked Tokens", callback_data="menu_list")],
            [InlineKeyboardButton("📈 Group Statistics", callback_data="menu_stats")],
            [InlineKeyboardButton("🔍 Search Tokens", callback_data="menu_search")],
            [InlineKeyboardButton("❌ Remove Tokens", callback_data="menu_remove")],
            [InlineKeyboardButton("ℹ️ Help & Info", callback_data="menu_help")],
            [InlineKeyboardButton("⚙️ Bot Status", callback_data="menu_status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = (
            "🎛️ *Main Menu* 🎛️\n\n"
            "Choose an option below to manage your Solana token tracking:\n\n"
            "📊 *View Tokens* - See all tracked tokens in this group\n"
            "📈 *Statistics* - Group performance overview\n"
            "🔍 *Search* - Find specific tokens\n"
            "❌ *Remove* - Stop tracking unwanted tokens\n"
            "ℹ️ *Help* - Commands and usage guide\n"
            "⚙️ *Status* - Bot performance information"
        )
        
        await update.message.reply_text(menu_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command with comprehensive information."""
        if not update.message:
            return
            
        help_message = (
            "🆘 *Enhanced Solana Alert Bot Help* 🆘\n\n"
            "*🔍 Perfect Token Detection:*\n"
            "• Detects ALL Solana tokens from any launchpad\n"
            "• Supports pump.fun, DexScreener, Birdeye links\n"
            "• Recognizes contract addresses in any format\n"
            "• Enhanced regex patterns for 100% accuracy\n\n"
            "*📊 Data Sources (Priority Order):*\n"
            "1. 🥇 DexScreener - Most comprehensive data\n"
            "2. 🥈 Birdeye - Real-time price feeds\n"
            "3. 🥉 Pump.fun - Meme token specialists\n\n"
            "*👥 Group Features:*\n"
            "• Each group tracks its own tokens\n"
            "• Group-specific statistics and settings\n"
            "• Individual token management per group\n\n"
            "*⚡ Alert System:*\n"
            "🚀 Multipliers: 2x, 3x, 5x, 8x, 10x, 15x, 20x, 25x, 30x, 35x, 40x, 45x, 50x, 55x, 60x, 65x, 70x, 75x, 80x, 85x, 90x, 95x, 100x\n"
            "📉 Loss Protection: -50%, -70%, -85%, -95%\n"
            "⏱️ Ultra-fast monitoring: Every 15 seconds\n\n"
            "*🛠️ Commands:*\n"
            "• `/menu` - Main control panel\n"
            "• `/list` - Show all tracked tokens\n"
            "• `/stats` - Group performance stats\n"
            "• `/search <query>` - Find specific tokens\n"
            "• `/remove <address>` - Stop tracking a token\n"
            "• `/status` - Bot system status\n\n"
            "*💡 Usage Tips:*\n"
            "• Just paste any Solana contract address\n"
            "• Works with URLs from any platform\n"
            "• Each group maintains separate token lists\n"
            "• Remove unwanted tokens easily\n\n"
            "🔥 *Ready to catch every moonshot!* 🔥"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def list_tokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display all tracked tokens for this group."""
        if not update.message or not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id
        tokens = await self.database.get_tokens_for_chat(chat_id)
        
        if not tokens:
            await update.message.reply_text(
                "📋 *No Tokens Tracked Yet*\n\n"
                "Send a Solana contract address to start tracking!",
                parse_mode='Markdown'
            )
            return
        
        # Create paginated token list
        message_parts = []
        current_message = "📊 *Tracked Tokens in This Group* 📊\n\n"
        
        for i, token in enumerate(tokens, 1):
            current_mcap = token.get('current_mcap', 0) or 0
            initial_mcap = token.get('initial_mcap', 1) or 1
            multiplier = current_mcap / initial_mcap if initial_mcap > 0 else 0
            
            status_emoji = "🚀" if multiplier > 1 else "📉" if multiplier < 1 else "➖"
            
            token_info = (
                f"{status_emoji} *{i}. {token['symbol']}*\n"
                f"📝 {token['name'][:30]}{'...' if len(token['name']) > 30 else ''}\n"
                f"💰 ${current_mcap:,.0f} ({multiplier:.2f}x)\n"
                f"🔗 `{token['contract_address'][:8]}...{token['contract_address'][-8:]}`\n"
                f"⏰ Added: {token['detected_at'][:10]}\n\n"
            )
            
            # Check if adding this token would exceed message limit
            if len(current_message + token_info) > 3800:
                message_parts.append(current_message)
                current_message = "📊 *Tracked Tokens (continued)* 📊\n\n" + token_info
            else:
                current_message += token_info
        
        if current_message:
            message_parts.append(current_message)
        
        # Send all message parts
        for part in message_parts:
            keyboard = [
                [InlineKeyboardButton("❌ Remove Token", callback_data="menu_remove")],
                [InlineKeyboardButton("🔍 Search Tokens", callback_data="menu_search")],
                [InlineKeyboardButton("📈 View Stats", callback_data="menu_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(part, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display group statistics."""
        if not update.message or not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id
        stats = await self.database.get_token_stats(chat_id)
        
        stats_message = (
            f"📈 *Group Statistics* 📈\n\n"
            f"📊 *Overview:*\n"
            f"• Total Tokens: {stats['total_tokens']}\n"
            f"• Active Tokens: {stats['active_tokens']}\n"
            f"• Pumping Tokens: {stats['pumping_tokens']} 🚀\n"
            f"• Dumping Tokens: {stats['dumping_tokens']} 📉\n\n"
            f"🎯 *Performance:*\n"
            f"• Average Multiplier: {stats['avg_multiplier']}x\n"
            f"• Best Performer: {stats['max_multiplier']}x\n\n"
            f"⚡ *Bot Status:*\n"
            f"• Monitoring: {'✅ Active' if self.token_tracker and self.token_tracker.is_running else '❌ Stopped'}\n"
            f"• Update Interval: 15 seconds\n"
            f"• Data Source: DexScreener Primary\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 View Tokens", callback_data="menu_list")],
            [InlineKeyboardButton("🔍 Search", callback_data="menu_search")],
            [InlineKeyboardButton("🎛️ Main Menu", callback_data="menu_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(stats_message, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def search_tokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for tokens by symbol, name, or address."""
        if not update.message or not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id
        
        # Get search query from command arguments
        query = ' '.join(context.args) if context.args else ''
        
        if not query:
            await update.message.reply_text(
                "🔍 *Search Tokens*\n\n"
                "Usage: `/search <symbol/name/address>`\n\n"
                "Examples:\n"
                "• `/search BONK`\n"
                "• `/search Solana`\n"
                "• `/search 11111111`\n",
                parse_mode='Markdown'
            )
            return
        
        tokens = await self.database.search_tokens(chat_id, query)
        
        if not tokens:
            await update.message.reply_text(
                f"🔍 *Search Results*\n\n"
                f"No tokens found matching: `{query}`",
                parse_mode='Markdown'
            )
            return
        
        results_message = f"🔍 *Search Results for: {query}*\n\n"
        
        for i, token in enumerate(tokens[:10], 1):  # Limit to 10 results
            current_mcap = token.get('current_mcap', 0) or 0
            initial_mcap = token.get('initial_mcap', 1) or 1
            multiplier = current_mcap / initial_mcap if initial_mcap > 0 else 0
            
            status_emoji = "🚀" if multiplier > 1 else "📉" if multiplier < 1 else "➖"
            
            results_message += (
                f"{status_emoji} *{i}. {token['symbol']}*\n"
                f"📝 {token['name']}\n"
                f"💰 ${current_mcap:,.0f} ({multiplier:.2f}x)\n"
                f"🔗 `{token['contract_address']}`\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("❌ Remove Token", callback_data="menu_remove")],
            [InlineKeyboardButton("📊 View All", callback_data="menu_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(results_message, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def remove_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a token from tracking."""
        if not update.message or not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id
        
        # Get contract address from command arguments
        if not context.args:
            await update.message.reply_text(
                "❌ *Remove Token*\n\n"
                "Usage: `/remove <contract_address>`\n\n"
                "Example: `/remove DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`\n\n"
                "💡 Use `/list` to see all tracked tokens and their addresses.",
                parse_mode='Markdown'
            )
            return
        
        contract_address = context.args[0]
        
        # Remove the token
        success = await self.database.remove_token(contract_address, chat_id)
        
        if success:
            await update.message.reply_text(
                f"✅ *Token Removed Successfully*\n\n"
                f"Contract: `{contract_address}`\n\n"
                f"The token has been removed from tracking in this group.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ *Token Not Found*\n\n"
                f"Contract: `{contract_address}`\n\n"
                f"This token is not being tracked in this group.",
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        if query.data == "menu_main":
            await self.menu_command(update, context)
        elif query.data == "menu_list":
            await self.list_tokens_command(update, context)
        elif query.data == "menu_stats":
            await self.stats_command(update, context)
        elif query.data == "menu_help":
            await self.help_command(update, context)
        elif query.data == "menu_status":
            await self.status_command(update, context)
        elif query.data == "menu_search":
            await query.edit_message_text(
                "🔍 *Search Tokens*\n\n"
                "Use the command: `/search <query>`\n\n"
                "Search by symbol, name, or contract address.",
                parse_mode='Markdown'
            )
        elif query.data == "menu_remove":
            await query.edit_message_text(
                "❌ *Remove Token*\n\n"
                "Use the command: `/remove <contract_address>`\n\n"
                "Get contract addresses with `/list`.",
                parse_mode='Markdown'
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command with enhanced system information."""
        if not update.message:
            return
            
        status = self.token_tracker.get_tracking_status() if self.token_tracker else {"active_tokens": 0, "is_running": False}
        
        status_message = (
            f"⚙️ *Enhanced Bot Status* ⚙️\n\n"
            f"🤖 **System Status:**\n"
            f"• Bot Running: {'✅ Yes' if status.get('is_running', False) else '❌ No'}\n"
            f"• Active Tokens: {status.get('active_tokens', 0)}\n"
            f"• Monitoring Interval: 15 seconds ⚡\n\n"
            f"📊 **Data Sources:**\n"
            f"• 🥇 DexScreener (Primary)\n"
            f"• 🥈 Birdeye (Backup)\n"
            f"• 🥉 Pump.fun (Meme tokens)\n\n"
            f"🚀 **Alert System:**\n"
            f"• Multiplier Tracking: Up to 100x\n"
            f"• Loss Protection: 4 levels\n"
            f"• Perfect Token Detection: ✅\n"
            f"• Group-Specific Tracking: ✅\n\n"
            f"🔧 **Commands Available:**\n"
            f"• `/menu` - Full control panel\n"
            f"• `/list` - View tracked tokens\n"
            f"• `/stats` - Performance stats\n"
            f"• `/search` - Find tokens\n"
            f"• `/remove` - Stop tracking\n\n"
            f"⚡ *Ready for moonshots!* 🚀"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def stop_tracking_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command (admin only)."""
        if not update.message or not update.effective_user:
            return
            
        user_id = update.effective_user.id
        
        # Only allow specific admin users (you can modify this list in config)
        admin_users = getattr(Config, 'ADMIN_USERS', [])
        if admin_users and user_id not in admin_users:
            await update.message.reply_text(
                "❌ *Access Denied*\n\nOnly administrators can stop the tracking system.",
                parse_mode='Markdown'
            )
            return
        
        if self.token_tracker:
            self.token_tracker.stop_tracking()
        
        await update.message.reply_text(
            "🛑 *Tracking Stopped*\n\nToken tracking has been stopped by an administrator.",
            parse_mode='Markdown'
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced message handler with perfect token detection."""
        if not update.message or not update.message.text or not update.effective_chat:
            return
        
        message_text = update.message.text
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title or "Private Chat"
        chat_type = update.effective_chat.type or "private"
        
        # Register the group if not already registered
        await self.database.register_group(chat_id, chat_title, chat_type)
        
        # Enhanced contract address detection
        async with SolanaAPI() as solana_api:
            contract_addresses = solana_api.detect_contract_addresses(message_text)
        
        if not contract_addresses:
            return
        
        for contract_address in contract_addresses[:3]:  # Limit to 3 addresses per message
            try:
                # Check if token is already being tracked in this group
                existing_tokens = await self.database.get_tokens_for_chat(chat_id)
                if any(token['contract_address'] == contract_address for token in existing_tokens):
                    await update.message.reply_text(
                        f"ℹ️ Token `{contract_address[:8]}...{contract_address[-8:]}` is already being tracked in this group.",
                        parse_mode='Markdown'
                    )
                    continue
                
                # Send processing message
                processing_msg = await update.message.reply_text(
                    f"🔍 *Processing Token...*\n\n"
                    f"📊 Fetching data from DexScreener, Birdeye, and Pump.fun\n"
                    f"🔗 `{contract_address[:8]}...{contract_address[-8:]}`",
                    parse_mode='Markdown'
                )
                
                # Get token data using enhanced API
                async with SolanaAPI() as solana_api:
                    token_data = await solana_api.get_token_info(contract_address)
                
                if not token_data:
                    await processing_msg.edit_text(
                        f"❌ *Token Not Found*\n\n"
                        f"Could not fetch data for:\n`{contract_address}`\n\n"
                        f"This might be a new token or invalid address.",
                        parse_mode='Markdown'
                    )
                    continue
                
                if token_data.get('market_cap', 0) <= 0:
                    await processing_msg.edit_text(
                        f"⚠️ *No Market Data*\n\n"
                        f"Token found but no trading data available:\n"
                        f"• Symbol: {token_data.get('symbol', 'Unknown')}\n"
                        f"• Name: {token_data.get('name', 'Unknown')}\n"
                        f"• Source: {token_data.get('source', 'Unknown')}\n\n"
                        f"Contract: `{contract_address}`",
                        parse_mode='Markdown'
                    )
                    continue
                
                # Add token to database with enhanced data
                token_id = await self.database.add_token(
                    contract_address=contract_address,
                    symbol=token_data['symbol'],
                    name=token_data['name'],
                    initial_mcap=token_data['market_cap'],
                    initial_price=token_data['price'],
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    platform=token_data.get('platform', 'solana'),
                    source_api=token_data.get('source', 'dexscreener'),
                    dex_name=token_data.get('dex', 'unknown'),
                    pair_address=token_data.get('pair_address'),
                    liquidity_usd=token_data.get('liquidity_usd', 0),
                    volume_24h=token_data.get('volume_24h', 0),
                    price_change_24h=token_data.get('price_change_24h', 0)
                )
                
                # Create confirmation message with enhanced data
                confirmation_message = (
                    f"✅ *Token Added Successfully!* ✅\n\n"
                    f"📊 **{token_data['symbol']}** - {token_data['name']}\n\n"
                    f"💰 **Market Cap:** ${token_data['market_cap']:,.0f}\n"
                    f"💵 **Price:** ${token_data['price']:.8f}\n"
                    f"🔗 **Contract:** `{contract_address}`\n\n"
                    f"📈 **Trading Info:**\n"
                    f"• DEX: {token_data.get('dex', 'Unknown').title()}\n"
                    f"• Liquidity: ${token_data.get('liquidity_usd', 0):,.0f}\n"
                    f"• 24h Volume: ${token_data.get('volume_24h', 0):,.0f}\n"
                    f"• 24h Change: {token_data.get('price_change_24h', 0):+.2f}%\n"
                    f"• Data Source: {token_data.get('source', 'Unknown').title()}\n\n"
                    f"🚀 **Alert Levels:**\n"
                    f"• Multipliers: 2x, 3x, 5x, 8x, 10x, 15x, 20x, 25x, 30x, 35x, 40x, 45x, 50x, 55x, 60x, 65x, 70x, 75x, 80x, 85x, 90x, 95x, 100x\n"
                    f"• Loss Protection: -50%, -70%, -85%, -95%\n"
                    f"• Monitoring: Every 15 seconds ⚡\n\n"
                    f"🎯 *Ready to catch the pump!* 🚀"
                )
                
                # Create action keyboard
                keyboard = [
                    [InlineKeyboardButton("📊 View All Tokens", callback_data="menu_list")],
                    [InlineKeyboardButton("📈 Group Stats", callback_data="menu_stats")],
                    [InlineKeyboardButton("❌ Remove This Token", callback_data=f"remove_{contract_address[:8]}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(
                    confirmation_message, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                logger.info(f"✅ Token {token_data['symbol']} ({contract_address}) added for chat {chat_id}")
                
                # Start tracking if not already running
                if self.token_tracker and not self.token_tracker.is_running:
                    asyncio.create_task(self.token_tracker.start_tracking())
                
            except Exception as e:
                logger.error(f"Error processing contract {contract_address}: {e}")
                await update.message.reply_text(
                    f"❌ *Error Processing Token*\n\n"
                    f"An error occurred while processing:\n`{contract_address}`\n\n"
                    f"Please try again or contact support.",
                    parse_mode='Markdown'
                )
                continue
            
            logger.info(f"📥 Message received: {message_text[:50]}...")
            logger.info(f"🔍 Found {len(contracts)} contract(s): {contracts}")
            
            if contracts:
                for contract_address in contracts:
                    logger.info(f"🔄 Processing contract: {contract_address}")
                    await self._process_contract_address(update, contract_address)
            else:
                logger.debug(f"No valid contracts found in message: {message_text}")
                
        except Exception as e:
            logger.error(f"💥 Error in handle_message: {e}", exc_info=True)
    
    async def _process_contract_address(self, update: Update, contract_address: str):
        """Process a detected contract address."""
        processing_msg = None  # Initialize to handle potential errors
        
        try:
            if not update.effective_chat or not update.message:
                logger.error("Invalid update object - missing chat or message")
                return
                
            chat_id = update.effective_chat.id
            message_id = update.message.message_id
            
            logger.info(f"🔄 Starting to process contract {contract_address} for chat {chat_id}")
            
            # Send processing message
            processing_msg = await update.message.reply_text(
                f"🔍 *Scanning Token...*\n\n"
                f"📝 Contract: `{contract_address}`\n"
                f"⏳ Fetching token data...",
                parse_mode='Markdown'
            )
            
            logger.info(f"📤 Sent processing message for {contract_address}")
            
            # Start tracking if not already running
            if self.token_tracker and not self.token_tracker.is_running:
                logger.info("🚀 Starting token tracker")
                asyncio.create_task(self.token_tracker.start_tracking())
            
            # Add token for tracking with timeout
            logger.info(f"🔄 Adding token {contract_address} to tracker")
            
            if not self.token_tracker:
                logger.error("Token tracker not initialized")
                await processing_msg.edit_text(
                    f"❌ *System Error* ❌\n\n"
                    f"Token tracker not initialized. Please restart the bot.",
                    parse_mode='Markdown'
                )
                return
            
            try:
                # Add a timeout to prevent hanging
                success = await asyncio.wait_for(
                    self.token_tracker.add_token(contract_address, chat_id, message_id),
                    timeout=30.0  # 30 second timeout
                )
                logger.info(f"✅ Token addition result: {success}")
                
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout adding token {contract_address}")
                await processing_msg.edit_text(
                    f"⏰ *Timeout Processing Token* ⏰\n\n"
                    f"📝 `{contract_address}`\n\n"
                    f"The request timed out. Please try again later.",
                    parse_mode='Markdown'
                )
                return
            
            if success:
                # Get token info for confirmation
                token_data = self.token_tracker.tracking_tokens.get(contract_address) if self.token_tracker else None
                if token_data:
                    confirmation_message = (
                        f"✅ *Token Added Successfully!* ✅\n\n"
                        f"💎 *{token_data['name']}* ({token_data['symbol']})\n"
                        f"📝 `{contract_address}`\n\n"
                        f"💰 *Market Cap:* ${token_data['confirmed_scan_mcap']:,.2f}\n"
                        f"💵 *Price:* ${token_data['current_price']:.8f}\n\n"
                        f"🚀 *Tracking multipliers:* 2x to 100x\n"
                        f"📉 *Loss alert:* -50% from scan\n\n"
                        f"🔥 *Ready to moon!* 🔥"
                    )
                else:
                    confirmation_message = (
                        f"✅ *Token Added Successfully!* ✅\n\n"
                        f"📝 `{contract_address}`\n\n"
                        f"🚀 Now tracking for pumps!\n"
                        f"📉 Will alert on -50% loss\n\n"
                        f"🔥 *Ready to moon!* 🔥"
                    )
                
                await processing_msg.edit_text(confirmation_message, parse_mode='Markdown')
                logger.info(f"✅ Successfully added token {contract_address} for chat {chat_id}")
                
            else:
                error_message = (
                    f"❌ *Failed to Add Token* ❌\n\n"
                    f"📝 `{contract_address}`\n\n"
                    f"*Possible reasons:*\n"
                    f"• Invalid contract address\n"
                    f"• Token not found on supported DEXs\n"
                    f"• API temporarily unavailable\n"
                    f"• Token already being tracked\n\n"
                    f"🔄 Try again in a few moments"
                )
                
                await processing_msg.edit_text(error_message, parse_mode='Markdown')
                logger.warning(f"❌ Failed to add token {contract_address} for chat {chat_id}")
        
        except Exception as e:
            logger.error(f"💥 Error processing contract {contract_address}: {e}")
            logger.exception("Full traceback:")
            
            error_message = (
                f"💥 *Error Processing Token* 💥\n\n"
                f"📝 `{contract_address}`\n\n"
                f"*Error:* {str(e)[:100]}...\n\n"
                f"🔄 Please try again later"
            )
            
            try:
                # Check if processing_msg was successfully created
                if 'processing_msg' in locals() and processing_msg:
                    await processing_msg.edit_text(error_message, parse_mode='Markdown')
                elif update and update.message:
                    await update.message.reply_text(error_message, parse_mode='Markdown')
            except Exception as msg_error:
                logger.error(f"Failed to send error message: {msg_error}")
    
    async def run(self):
        """Run the bot."""
        try:
            await self.initialize()
            logger.info("🚀 Starting Solana Alert Bot...")
            
            # Verify application was created
            if not self.application:
                logger.error("Failed to create application during initialization")
                return
            
            # Start the application
            if self.application.updater:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling()
            else:
                logger.error("Application updater not available")
                return
            
            logger.info("✅ Bot is running and ready to track tokens!")
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"💥 Bot error: {e}")
        finally:
            if self.token_tracker:
                self.token_tracker.stop_tracking()
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

async def main():
    """Main entry point."""
    bot = SolanaAlertBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
