#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime

def restore_tokens():
    """Restore all tokens to active status and check auto-save functionality"""
    
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    try:
        # First, let's see what we have
        cursor.execute('SELECT contract_address, symbol, chat_id, is_active FROM tokens')
        all_tokens = cursor.fetchall()
        
        print("🔍 Current token status:")
        for token in all_tokens:
            address, symbol, chat_id, is_active = token
            status = "✅ Active" if is_active else "❌ Inactive"
            short_addr = address[:8] + '...'
            print(f"   {symbol} ({short_addr}) in Group {chat_id}: {status}")
        
        # Reactivate all tokens that were previously added
        print("\n🔄 Reactivating all tokens...")
        cursor.execute('UPDATE tokens SET is_active = 1 WHERE contract_address IS NOT NULL')
        reactivated = cursor.rowcount
        
        conn.commit()
        print(f"✅ Reactivated {reactivated} tokens")
        
        # Show updated status
        print("\n📊 Updated token status:")
        cursor.execute('SELECT chat_id, COUNT(*) FROM tokens WHERE is_active = 1 GROUP BY chat_id')
        active_by_group = cursor.fetchall()
        
        for chat_id, count in active_by_group:
            print(f"   Group {chat_id}: {count} active tokens")
        
        # Create a fresh backup with all tokens active
        backup_name = f"backups/tokens_restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.makedirs('backups', exist_ok=True)
        
        # Copy current database to backup
        import shutil
        shutil.copy2('tokens.db', backup_name)
        print(f"\n💾 Created backup: {backup_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    restore_tokens()
