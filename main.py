"""Main Telegram Bot Application for Solana Token Alerts."""
import asyncio
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import Config
from database import Database
from token_tracker import TokenTracker

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
        
    async def initialize(self):
        """Initialize the bot application."""
        if not Config.validate():
            raise ValueError("Invalid configuration")
        
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Initialize token tracker
        self.token_tracker = TokenTracker(self.application.bot)
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("stop", self.stop_tracking_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Initialize database
        db = Database(Config.DATABASE_PATH)
        await db.init_db()
        
        logger.info("🤖 Bot initialized successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🤖 *Solana Token Alert Bot* 🚀\n\n"
            "I monitor Solana token contract addresses and send alerts when they pump!\n\n"
            "📋 *How to use:*\n"
            "• Send a Solana contract address to this chat\n"
            "• I'll start tracking it automatically\n"
            "• Get alerts at 2x, 3x, 5x, 8x, 10x, 15x, 20x, 25x, up to 100x!\n"
            "• Get -50% loss alerts from scan price\n\n"
            "📊 *Commands:*\n"
            "• /start - Show this message\n"
            "• /help - Get help\n"
            "• /status - Check tracking status\n"
            "• /stop - Stop tracking (admin only)\n\n"
            "🔥 *Ready to track some pumps!* 🔥"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        # Start tracking if not already running
        if not self.token_tracker.is_running:
            asyncio.create_task(self.token_tracker.start_tracking())
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🆘 *Help - Solana Alert Bot* 🆘\n\n"
            "*How it works:*\n"
            "1. Send a Solana contract address (44 characters)\n"
            "2. Bot validates and starts tracking the token\n"
            "3. Receive alerts when the token pumps!\n\n"
            "*Alert Types:*\n"
            "🚀 Multiplier alerts: 2x, 3x, 5x, 8x, 10x, 15x, 20x, 25x, 30x, 35x, 40x, 45x, 50x, 55x, 60x, 65x, 70x, 75x, 80x, 85x, 90x, 95x, 100x\n"
            "📉 Loss alert: -50% from scan price\n\n"
            "*Features:*\n"
            "✅ Multi-API support (Birdeye, DexScreener, pump.fun)\n"
            "✅ Accurate market cap tracking\n"
            "✅ Real-time price monitoring\n"
            "✅ Loss protection alerts\n\n"
            "*Contract Address Format:*\n"
            "• Must be exactly 44 characters\n"
            "• Base58 encoded Solana address\n"
            "• Example: `11111111111111111111111111111111111111111111`\n\n"
            "Need more help? Contact the developer!"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status = self.token_tracker.get_tracking_status()
        
        status_message = (
            f"📊 *Bot Status* 📊\n\n"
            f"🔄 *Tracking:* {'✅ Active' if status['is_running'] else '❌ Inactive'}\n"
            f"📈 *Tokens Tracked:* {status['total_tokens']}\n"
            f"⏰ *Check Interval:* {Config.PRICE_CHECK_INTERVAL} seconds\n"
            f"🎯 *Alert Multipliers:* {len(Config.ALERT_MULTIPLIERS)} levels\n"
            f"📉 *Loss Threshold:* {Config.LOSS_THRESHOLD}%\n\n"
            f"💡 Send a contract address to start tracking!"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def stop_tracking_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop_tracking command."""
        # Basic admin check (you can enhance this)
        user_id = update.effective_user.id
        
        self.token_tracker.stop_tracking()
        
        await update.message.reply_text(
            "⏹️ *Tracking Stopped*\n\n"
            "Token tracking has been stopped. Use /start to restart.",
            parse_mode='Markdown'
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages and detect contract addresses."""
        try:
            if not update.message or not update.message.text:
                logger.debug("Received update without message or text")
                return
                
            message_text = update.message.text.strip()
            
            # Regex to match Solana contract addresses (44 characters, base58)
            # Updated pattern to handle punctuation and whitespace around addresses
            contract_pattern = r'(?:^|[\s,\.\-\(\)\[\]\{\}])?([1-9A-HJ-NP-Za-km-z]{44})(?:[\s,\.\-\(\)\[\]\{\}]|$)'
            matches = re.findall(contract_pattern, message_text)
            
            # Also try simpler pattern for addresses that might be standalone
            simple_pattern = r'[1-9A-HJ-NP-Za-km-z]{44}'
            simple_matches = re.findall(simple_pattern, message_text)
            
            # Combine and deduplicate
            all_contracts = list(set(matches + simple_matches))
            contracts = [addr for addr in all_contracts if len(addr) == 44]
            
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
