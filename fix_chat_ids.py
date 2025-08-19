import sqlite3

def fix_chat_ids():
    print("🔧 Fixing chat IDs in database...")
    
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    # The real chat ID appears to be -4873290500
    real_chat_id = -4873290500
    test_chat_id = -1001234567890
    
    print(f"📍 Real chat ID: {real_chat_id}")
    print(f"🧪 Test chat ID to fix: {test_chat_id}")
    
    # Update test tokens to use the real chat ID
    cursor.execute('''
        UPDATE tokens 
        SET chat_id = ? 
        WHERE chat_id = ? AND is_active = 1
    ''', (real_chat_id, test_chat_id))
    
    updated_count = cursor.rowcount
    print(f"✅ Updated {updated_count} tokens to use real chat ID")
    
    # Show the updated state
    cursor.execute('SELECT contract_address, symbol, chat_id FROM tokens WHERE is_active = 1')
    tokens = cursor.fetchall()
    
    print("\n📊 Updated tokens:")
    for token in tokens:
        contract, symbol, chat_id = token
        print(f"  - {symbol} ({contract[:8]}...) → Chat: {chat_id}")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 All tokens now use the same real chat ID!")
    print("📱 Alerts should now be sent to your group chat.")

if __name__ == "__main__":
    fix_chat_ids()
