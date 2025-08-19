"""Configuration settings for the Telegram Solana Alert Bot."""
import os
from typing import Optional

class Config:
    # Telegram Bot Token - Use environment variable for production
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN', "8301492869:AAE1sP4G54PqDQEIHs-9v49GCJ8rnz1aKqQ")
    
    # API Keys (optional, but recommended for rate limits)
    BIRDEYE_API_KEY: Optional[str] = os.getenv('BIRDEYE_API_KEY')
    DEXSCREENER_API_KEY: Optional[str] = os.getenv('DEXSCREENER_API_KEY')
    
    # Database settings - Railway compatible
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'tokens.db')
    
    # Tracking settings
    PRICE_CHECK_INTERVAL: int = 15  # seconds - faster monitoring for better rug detection
    MAX_TOKENS_PER_GROUP: int = 100
    
    # Alert multipliers
    ALERT_MULTIPLIERS = [2, 3, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    # Loss alert thresholds (multiple levels)
    LOSS_THRESHOLDS = [-50, -70, -85, -95]  # Multiple loss alert levels
    LOSS_THRESHOLD = -50  # Primary loss threshold for backward compatibility
    
    # Logging settings
    LOG_LEVEL: str = 'INFO'
    LOG_FILE: str = 'bot.log'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN is required!")
            return False
        return True
