#!/usr/bin/env python3
"""
Railway deployment startup script for Telegram Solana Alert Bot
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Ensure the script directory is in Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

def setup_railway_environment():
    """Setup environment for Railway deployment"""
    
    # Set up logging for Railway
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Telegram Solana Alert Bot on Railway...")
    
    # Check required environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ TELEGRAM_BOT_TOKEN environment variable is required!")
        logger.error("🔧 Fix: In Railway dashboard → Variables tab → Add:")
        logger.error("   Variable: TELEGRAM_BOT_TOKEN")
        logger.error("   Value: 8301492869:AAE1sP4G54PqDQEIHs-9v49GCJ8rnz1aKqQ")
        logger.error("🔄 Railway will auto-redeploy after adding the variable")
        sys.exit(1)
    
    # Log configuration
    logger.info("✅ Environment variables configured")
    logger.info(f"📊 Database path: {os.getenv('DATABASE_PATH', 'tokens.db')}")
    logger.info(f"🔑 Bot token: ✅ Configured")
    logger.info(f"🌐 Port: {os.getenv('PORT', '8000')}")
    
    return logger

async def main():
    """Main entry point for Railway deployment"""
    logger = setup_railway_environment()
    
    try:
        # Start health check server for Railway
        from health_check import HealthCheckServer
        health_server = HealthCheckServer(port=int(os.getenv('PORT', 8000)))
        health_server.start()
        
        # Import and run the bot
        from main import main as bot_main
        logger.info("🤖 Initializing bot...")
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
