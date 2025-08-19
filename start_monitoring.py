import asyncio
import sqlite3
from token_tracker import TokenTracker

async def setup_and_start_monitoring():
    print("🔧 Setting up monitoring system...")
    
    # Create missing database tables
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    # Create alert_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_address TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            alert_details TEXT,
            multiplier REAL,
            current_mcap REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create price_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_address TEXT NOT NULL,
            price REAL NOT NULL,
            market_cap REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create chat_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_settings (
            chat_id INTEGER PRIMARY KEY,
            alert_multipliers TEXT DEFAULT '2,3,5,8,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100',
            loss_thresholds TEXT DEFAULT '-50,-70,-85,-95',
            notifications_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database tables created")
    
    # Start token tracker
    print("🚀 Starting token tracker...")
    tracker = TokenTracker()
    await tracker.start_monitoring()

if __name__ == "__main__":
    asyncio.run(setup_and_start_monitoring())
