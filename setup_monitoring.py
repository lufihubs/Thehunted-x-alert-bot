import sqlite3

def setup_monitoring_tables():
    print("🔧 Setting up monitoring database tables...")
    
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
    print("✅ Database tables created successfully!")
    
    # Show current active tokens
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tokens WHERE is_active = 1')
    active_count = cursor.fetchone()[0]
    print(f"📊 Found {active_count} active tokens ready for monitoring")
    conn.close()

if __name__ == "__main__":
    setup_monitoring_tables()
