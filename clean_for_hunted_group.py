"""
Clean Database and Focus on The Hunted Group (-1002350881772)
Remove all previous tokens and prepare for real-time tracking
"""

import sqlite3
import asyncio
import sys
sys.path.append('.')

def clean_database_for_hunted_group():
    """Clean database and focus on The Hunted group only."""
    try:
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        # Show current status
        cursor.execute('SELECT chat_id, COUNT(*) as count FROM tokens GROUP BY chat_id')
        current = cursor.fetchall()
        print('🔍 CURRENT DATABASE STATUS:')
        total_tokens = 0
        for chat_id, count in current:
            print(f'   Group {chat_id}: {count} tokens')
            total_tokens += count
        
        print(f'   TOTAL: {total_tokens} tokens across {len(current)} groups')
        
        # Remove ALL existing tokens to start fresh
        deleted_tokens = cursor.execute('DELETE FROM tokens').rowcount
        deleted_alerts = cursor.execute('DELETE FROM alerts').rowcount
        
        print(f'\n🧹 CLEANED DATABASE:')
        print(f'   • Removed {deleted_tokens} previous tokens')
        print(f'   • Cleared {deleted_alerts} alerts')
        print('   • Ready for fresh tracking')
        
        # Reset auto-increment sequences
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = ?', ('tokens',))
        cursor.execute('DELETE FROM sqlite_sequence WHERE name = ?', ('alerts',))
        
        conn.commit()
        conn.close()
        
        print(f'\n✅ DATABASE READY FOR "THE HUNTED" GROUP')
        print('🎯 Target Group: -1002350881772')
        print('🚀 Focus: Real-time tracking for NEW tokens only')
        print('⚡ Enhanced monitoring: ALL tokens get real-time updates')
        print('🔄 Sync: Ready for Railway deployment')
        
        return True
        
    except Exception as e:
        print(f'❌ Error cleaning database: {e}')
        return False

if __name__ == "__main__":
    clean_database_for_hunted_group()
