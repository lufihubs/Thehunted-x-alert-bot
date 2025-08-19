import sqlite3

def check_and_fix_chat_ids():
    print("📱 Checking chat IDs in your database...")
    
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    # Check current chat IDs
    cursor.execute('SELECT DISTINCT chat_id FROM tokens WHERE is_active = 1')
    chat_ids = cursor.fetchall()
    
    print("🎯 Current chat IDs in database:")
    for chat_id in chat_ids:
        print(f"  - {chat_id[0]}")
    
    # Show which tokens are using which chat IDs
    cursor.execute('SELECT contract_address, symbol, chat_id FROM tokens WHERE is_active = 1')
    tokens = cursor.fetchall()
    
    print("\n📊 Tokens and their chat IDs:")
    for token in tokens:
        contract, symbol, chat_id = token
        print(f"  - {symbol} ({contract[:8]}...) → Chat: {chat_id}")
    
    # Check for test/invalid chat IDs
    test_chat_ids = [-1001234567890]  # Common test chat ID
    
    print("\n🧹 Checking for test/invalid chat IDs...")
    for test_id in test_chat_ids:
        cursor.execute('SELECT COUNT(*) FROM tokens WHERE chat_id = ? AND is_active = 1', (test_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"⚠️ Found {count} tokens using test chat ID {test_id}")
            print(f"   This chat doesn't exist, which is why alerts can't be sent!")
    
    conn.close()

if __name__ == "__main__":
    check_and_fix_chat_ids()
