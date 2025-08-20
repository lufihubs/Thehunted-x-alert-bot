#!/usr/bin/env python3

import sqlite3
import os

def check_database():
    db_path = 'tokens.db'
    
    if not os.path.exists(db_path):
        print("❌ Database file doesn't exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check tokens table
        cursor.execute('SELECT contract_address, symbol, name, chat_id, is_active FROM tokens ORDER BY chat_id')
        tokens = cursor.fetchall()
        
        print(f"📊 Found {len(tokens)} total tokens in database:")
        print("=" * 60)
        
        if not tokens:
            print("❌ No tokens found in database!")
            return
        
        # Group by chat_id
        by_chat = {}
        for token in tokens:
            address, symbol, name, chat_id, is_active = token
            if chat_id not in by_chat:
                by_chat[chat_id] = {'active': [], 'inactive': []}
            
            token_info = {
                'address': address,
                'symbol': symbol or 'Unknown',
                'name': name or 'Unknown'
            }
            
            if is_active:
                by_chat[chat_id]['active'].append(token_info)
            else:
                by_chat[chat_id]['inactive'].append(token_info)
        
        for chat_id, data in by_chat.items():
            active_count = len(data['active'])
            inactive_count = len(data['inactive'])
            
            print(f"🏷️  Group {chat_id}:")
            print(f"   📈 Active tokens: {active_count}")
            print(f"   ❌ Inactive tokens: {inactive_count}")
            
            # Show some active tokens
            for i, token in enumerate(data['active'][:3]):
                short_addr = token['address'][:8] + '...' if len(token['address']) > 8 else token['address']
                print(f"      • {token['symbol']} ({short_addr})")
            
            if active_count > 3:
                print(f"      ... and {active_count - 3} more")
            print()
        
        # Check backup files
        print("\n📁 Checking for backup files:")
        backup_files = [f for f in os.listdir('.') if f.endswith('.bak') or 'backup' in f.lower()]
        if backup_files:
            for backup in backup_files:
                print(f"   • {backup}")
        else:
            print("   ❌ No backup files found")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
