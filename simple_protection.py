#!/usr/bin/env python3
"""
Simple Data Protection System
Ensures your tokens are always safe and backed up
"""

import asyncio
import sqlite3
import json
import os
import shutil
from datetime import datetime

class SimpleDataProtection:
    def __init__(self, db_path: str = "tokens.db"):
        self.db_path = db_path
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_backup(self) -> str:
        """Create a backup of the current database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"protection_backup_{timestamp}.db")
            
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_file)
                print(f"Backup created: {backup_file}")
                return backup_file
            else:
                print("Source database not found!")
                return ""
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""
    
    async def export_tokens_info(self) -> str:
        """Export token information to a readable JSON file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = os.path.join(self.backup_dir, f"tokens_info_{timestamp}.json")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chat_id, contract_address, symbol, name, 
                       initial_mcap, current_mcap, is_active, detected_at
                FROM tokens 
                ORDER BY chat_id, detected_at
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Organize by group
            token_info = {
                'backup_timestamp': datetime.now().isoformat(),
                'total_tokens': len(rows),
                'groups': {}
            }
            
            for row in rows:
                chat_id, address, symbol, name, initial_mcap, current_mcap, is_active, detected_at = row
                
                if str(chat_id) not in token_info['groups']:
                    token_info['groups'][str(chat_id)] = []
                
                token_data = {
                    'contract_address': address,
                    'symbol': symbol,
                    'name': name,
                    'initial_mcap': initial_mcap,
                    'current_mcap': current_mcap,
                    'is_active': bool(is_active),
                    'detected_at': detected_at
                }
                
                token_info['groups'][str(chat_id)].append(token_data)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(token_info, f, indent=2, ensure_ascii=False)
            
            print(f"Token info exported: {json_file}")
            return json_file
            
        except Exception as e:
            print(f"Error exporting token info: {e}")
            return ""
    
    async def verify_data_integrity(self) -> bool:
        """Verify that data is intact"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT chat_id, COUNT(*) as total,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
                FROM tokens 
                GROUP BY chat_id
                ORDER BY chat_id
            """)
            
            groups = cursor.fetchall()
            conn.close()
            
            print("Data Integrity Check:")
            total_tokens = 0
            total_active = 0
            
            for chat_id, total, active in groups:
                print(f"  Group {chat_id}: {active}/{total} active tokens")
                total_tokens += total
                total_active += active
            
            print(f"  TOTAL: {total_active}/{total_tokens} active tokens in {len(groups)} groups")
            
            return len(groups) > 0 and total_tokens > 0
            
        except Exception as e:
            print(f"Error checking data integrity: {e}")
            return False

async def protect_data():
    """Main protection function"""
    print("DATA PROTECTION SYSTEM")
    print("=" * 30)
    
    protector = SimpleDataProtection()
    
    print("1. Creating database backup...")
    backup_file = await protector.create_backup()
    
    print("\n2. Exporting token information...")
    json_file = await protector.export_tokens_info()
    
    print("\n3. Verifying data integrity...")
    is_intact = await protector.verify_data_integrity()
    
    print("\n" + "=" * 30)
    print("PROTECTION SUMMARY:")
    print(f"  Database Backup: {'SUCCESS' if backup_file else 'FAILED'}")
    print(f"  Info Export: {'SUCCESS' if json_file else 'FAILED'}")
    print(f"  Data Integrity: {'GOOD' if is_intact else 'CORRUPTED'}")
    
    if backup_file and json_file and is_intact:
        print("\nYour token data is FULLY PROTECTED!")
    else:
        print("\nWARNING: Some protection steps failed!")
    
    return backup_file, json_file, is_intact

if __name__ == "__main__":
    asyncio.run(protect_data())
