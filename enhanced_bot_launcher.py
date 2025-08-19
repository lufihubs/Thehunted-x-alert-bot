"""
Enhanced Multi-Group Bot Launcher - Production Ready
"""
import asyncio
import signal
import sys
from config import Config
from token_tracker_enhanced import TokenTracker
from database import Database
import logging

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

class EnhancedSolanaBot:
    """Enhanced Solana Alert Bot with Multi-Group Support"""
    
    def __init__(self):
        self.tracker = None
        self.database = None
        self.running = False
    
    async def initialize(self):
        """Initialize the enhanced bot"""
        logger.info("🚀 Initializing Enhanced Multi-Group Solana Alert Bot...")
        
        # Initialize database
        self.database = Database(Config.DATABASE_PATH)
        await self.database.init_db()
        logger.info("✅ Database initialized")
        
        # Create a simple bot interface (you can integrate with Telegram later)
        class SimpleBotInterface:
            async def send_message(self, chat_id: int, text: str, parse_mode: str = None):
                # For now, just log the alerts - you can integrate with Telegram API here
                logger.info(f"🚨 ALERT TO {chat_id}: {text[:100]}...")
                # You can add actual Telegram sending here when ready
        
        # Initialize enhanced tracker
        bot_interface = SimpleBotInterface()
        self.tracker = TokenTracker(bot_interface)
        
        logger.info("🎯 Enhanced tracker initialized")
    
    async def start(self):
        """Start the enhanced monitoring system"""
        if self.running:
            return
        
        self.running = True
        logger.info("🚀 Starting Enhanced Multi-Group Token Monitoring...")
        
        # Load current configuration status
        stats = await self.database.get_group_statistics(-4873290500)  # Your main group
        logger.info(f"📊 Group stats: {stats['total_active']} active tokens")
        
        # Start the tracker
        await self.tracker.start_tracking()
    
    async def stop(self):
        """Stop the monitoring system"""
        if not self.running:
            return
        
        logger.info("⏹️ Stopping Enhanced Token Monitoring...")
        self.running = False
        
        if self.tracker:
            self.tracker.stop_tracking()
        
        logger.info("✅ Enhanced monitoring stopped")

async def main():
    """Main function"""
    print("🚀 Enhanced Multi-Group Solana Alert Bot")
    print("=" * 50)
    print(f"⚡ Real-time monitoring: {Config.REAL_TIME_ALERTS}")
    print(f"⏱️ Check interval: {Config.PRICE_CHECK_INTERVAL} seconds")
    print(f"🗑️ Auto-remove threshold: {Config.AUTO_REMOVE_THRESHOLD}%")
    print(f"🔄 Alert cooldown: {Config.ALERT_COOLDOWN} seconds")
    print("=" * 50)
    
    # Create and initialize bot
    bot = EnhancedSolanaBot()
    await bot.initialize()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler():
        logger.info("📡 Received shutdown signal")
        asyncio.create_task(bot.stop())
    
    # Register signal handlers
    for sig in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(sig, lambda s, f: signal_handler())
    
    try:
        # Start the bot
        await bot.start()
        
        # Keep running until interrupted
        while bot.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("⌨️ Keyboard interrupt received")
    except Exception as e:
        logger.error(f"❌ Error in main loop: {e}")
    finally:
        await bot.stop()
        logger.info("👋 Enhanced bot shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
