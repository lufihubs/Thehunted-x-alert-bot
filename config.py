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
    PRICE_CHECK_INTERVAL: int = 5  # seconds - ultra-fast real-time monitoring
    MAX_TOKENS_PER_GROUP: int = 100
    
    # Multi-group support settings
    MAX_GROUPS: int = 50  # Maximum number of groups the bot can handle
    GROUP_ISOLATION: bool = True  # Groups operate independently
    
    # Alert multipliers - comprehensive coverage
    ALERT_MULTIPLIERS = [2, 3, 5, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    
    # Loss alert thresholds (multiple levels)
    LOSS_THRESHOLDS = [-30, -50, -70, -80, -85, -95]  # Progressive loss alerts
    
    # Auto-removal settings
    AUTO_REMOVE_THRESHOLD: float = -80.0  # Auto-remove tokens below -80%
    RUG_DETECTION_THRESHOLD: float = -90.0  # Consider token rugged at -90%
    ZERO_LIQUIDITY_REMOVAL: bool = True  # Remove tokens with zero liquidity
    
    # Real-time monitoring
    REAL_TIME_ALERTS: bool = True  # Enable real-time alert processing
    ALERT_COOLDOWN: int = 60  # Seconds between same-type alerts for same token
    
    # Data persistence and backup settings
    AUTO_SAVE_INTERVAL: int = 300  # Auto-save every 5 minutes (seconds)
    BACKUP_ON_START: bool = True  # Create backup when bot starts
    BACKUP_ON_TOKEN_ADD: bool = True  # Backup when new tokens are added
    BACKUP_ON_TOKEN_REMOVE: bool = True  # Backup when tokens are removed
    MAX_BACKUPS: int = 10  # Maximum number of backup files to keep
    SAVE_ON_SHUTDOWN: bool = True  # Save all data when bot shuts down
    
    # Group data persistence
    PERSIST_GROUP_SETTINGS: bool = True  # Save group-specific settings
    PERSIST_ALERT_HISTORY: bool = True  # Save alert history across restarts
    PERSIST_TOKEN_DATA: bool = True  # Save all token tracking data
    CROSS_SESSION_PERSISTENCE: bool = True  # Maintain data across bot restarts
    
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
