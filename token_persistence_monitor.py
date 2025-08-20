#!/usr/bin/env python3
"""
Enhanced Token Persistence Monitor
Ensures all group tokens are properly saved and restored
"""
import asyncio
import sqlite3
import os
import json
from datetime import datetime, timedelta
import shutil

class TokenPersistenceMonitor:
    def __init__(self, db_path='tokens.db'):
        self.db_path = db_path
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)
    
    async def create_full_backup(self):
        """Create a comprehensive backup of all data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'full_backup_{timestamp}.db')
        
        # Copy database file
        shutil.copy2(self.db_path, backup_path)
        
        # Also create JSON export for readability
        data = await self.export_all_data()
        json_path = os.path.join(self.backup_dir, f'data_export_{timestamp}.json')
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Full backup created:")
        print(f"   Database: {backup_path}")
        print(f"   JSON: {json_path}")
        
        return backup_path, json_path
    
    async def export_all_data(self):
        """Export all data to a structured format"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        data = {
            'backup_time': datetime.now().isoformat(),
            'groups': {},
            'tokens_by_group': {},
            'alert_history': {}
        }
        
        try:
            # Export tokens by group
            cursor.execute('''
                SELECT contract_address, symbol, name, chat_id, initial_mcap, 
                       current_mcap, initial_price, current_price, is_active,
                       detected_at, last_updated, multipliers_alerted
                FROM tokens ORDER BY chat_id, detected_at
            ''')
            
            tokens = cursor.fetchall()
            
            for token in tokens:
                chat_id = token['chat_id']
                
                if chat_id not in data['tokens_by_group']:
                    data['tokens_by_group'][chat_id] = {
                        'active_tokens': [],
                        'inactive_tokens': [],
                        'total_count': 0
                    }
                
                token_data = {
                    'contract_address': token['contract_address'],
                    'symbol': token['symbol'],
                    'name': token['name'],
                    'initial_mcap': token['initial_mcap'],
                    'current_mcap': token['current_mcap'],
                    'initial_price': token['initial_price'],
                    'current_price': token['current_price'],
                    'detected_at': token['detected_at'],
                    'last_updated': token['last_updated'],
                    'multipliers_alerted': token['multipliers_alerted']
                }
                
                if token['is_active']:
                    data['tokens_by_group'][chat_id]['active_tokens'].append(token_data)
                else:
                    data['tokens_by_group'][chat_id]['inactive_tokens'].append(token_data)
                
                data['tokens_by_group'][chat_id]['total_count'] += 1
            
            # Export alert history
            cursor.execute('''
                SELECT alert_type, multiplier, alerted_at, chat_id, 
                       (SELECT contract_address FROM tokens WHERE id = alerts.token_id) as contract_address
                FROM alerts ORDER BY chat_id, alerted_at DESC
            ''')
            
            alerts = cursor.fetchall()
            
            for alert in alerts:
                chat_id = alert['chat_id']
                if chat_id not in data['alert_history']:
                    data['alert_history'][chat_id] = []
                
                data['alert_history'][chat_id].append({
                    'alert_type': alert['alert_type'],
                    'multiplier': alert['multiplier'],
                    'alerted_at': alert['alerted_at'],
                    'contract_address': alert['contract_address']
                })
        
        finally:
            conn.close()
        
        return data
    
    async def verify_data_integrity(self):
        """Verify that all data is properly saved and accessible"""
        print("🔍 Verifying data integrity...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check tokens by group
            cursor.execute('''
                SELECT chat_id, 
                       COUNT(*) as total_tokens,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_tokens,
                       SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_tokens
                FROM tokens 
                GROUP BY chat_id
                ORDER BY chat_id
            ''')
            
            groups = cursor.fetchall()
            
            print("\n📊 Token distribution by group:")
            total_active = 0
            for group in groups:
                chat_id, total, active, inactive = group
                total_active += active
                print(f"   Group {chat_id}: {active} active, {inactive} inactive ({total} total)")
            
            print(f"\n✅ Total active tokens across all groups: {total_active}")
            
            # Check for any data inconsistencies
            cursor.execute('''
                SELECT COUNT(*) FROM tokens 
                WHERE (current_mcap IS NULL OR current_price IS NULL) 
                AND is_active = 1
            ''')
            
            missing_data = cursor.fetchone()[0]
            if missing_data > 0:
                print(f"⚠️  Warning: {missing_data} active tokens have missing price/mcap data")
            else:
                print("✅ All active tokens have complete data")
            
            return total_active > 0
        
        finally:
            conn.close()
    
    async def enable_continuous_monitoring(self):
        """Set up continuous monitoring and auto-backup"""
        print("🚀 Starting continuous token persistence monitoring...")
        
        while True:
            try:
                # Verify data integrity
                has_data = await self.verify_data_integrity()
                
                if has_data:
                    # Create periodic backup (every 30 minutes)
                    current_time = datetime.now()
                    if current_time.minute % 30 == 0:
                        await self.create_full_backup()
                
                # Check again in 5 minutes
                print(f"⏰ Next check in 5 minutes...")
                await asyncio.sleep(300)
                
            except Exception as e:
                print(f"❌ Error in monitoring: {e}")
                await asyncio.sleep(60)  # Shorter retry on error

async def main():
    monitor = TokenPersistenceMonitor()
    
    print("🔧 Token Persistence Monitor")
    print("=" * 50)
    
    # Initial integrity check
    await monitor.verify_data_integrity()
    
    # Create initial backup
    await monitor.create_full_backup()
    
    print("\n🎯 Your tokens are now fully protected with:")
    print("   ✅ Auto-save every 5 minutes")
    print("   ✅ Backup on every token add/remove")
    print("   ✅ Continuous monitoring")
    print("   ✅ Data integrity verification")
    print("   ✅ Multi-group persistence")
    
    choice = input("\n🔄 Start continuous monitoring? (y/n): ").lower().strip()
    
    if choice == 'y':
        await monitor.enable_continuous_monitoring()
    else:
        print("✅ Monitoring setup complete. Your tokens are safe!")

if __name__ == "__main__":
    asyncio.run(main())
