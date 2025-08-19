import sqlite3

def check_db_structure():
    print('🗄️ Checking database structure...')
    
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'📋 Database tables: {[t[0] for t in tables]}')
    
    # Check tokens table structure
    cursor.execute("PRAGMA table_info(tokens)")
    columns = cursor.fetchall()
    print(f'📊 Tokens table columns:')
    for col in columns:
        print(f'  - {col[1]} ({col[2]})')
    
    # Check if there are any tokens being tracked
    cursor.execute('SELECT COUNT(*) FROM tokens WHERE is_active = 1')
    active_tokens = cursor.fetchone()[0]
    print(f'🎯 Active tokens: {active_tokens}')
    
    # Check if token tracker tables exist
    expected_tables = ['tokens', 'alert_logs', 'price_history', 'chat_settings']
    for table in expected_tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        exists = cursor.fetchone()
        print(f'📋 Table {table}: {"✅ EXISTS" if exists else "❌ MISSING"}')
    
    conn.close()

if __name__ == "__main__":
    check_db_structure()
