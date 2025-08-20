#!/usr/bin/env python3
"""
Data Recovery Tool - Ensures tokens never get lost
Creates automated backups and provides recovery options
"""

import asyncio
import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any

class DataRecoveryTool:
    def __init__(self, db_path: str = "tokens.db"):
        self.db_path = db_path
        self.backup_dir = "backups"
        self.recovery_dir = "recovery"
        
        # Ensure directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.recovery_dir, exist_ok=True)
    
    async def create_scheduled_backup(self) -> str:
        """Create a timestamped backup of the current database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"scheduled_backup_{timestamp}.db")
            
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_file)
                print(f"📦 Scheduled backup created: {backup_file}")
                
                # Also create a JSON export for human readability
                await self._export_to_json(backup_file.replace('.db', '.json'))
                
                return backup_file
            else:
                print("❌ Source database not found!")
                return ""
                
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return ""
    
    async def _export_to_json(self, json_file: str):
        """Export database to JSON format for easy recovery"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tokens
            cursor.execute("""
                SELECT chat_id, contract_address, symbol, name, initial_mcap, 
                       current_mcap, initial_price, current_price, is_active,
                       detected_at, last_updated, platform
                FROM tokens 
                ORDER BY chat_id, detected_at
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Organize by group
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_tokens': len(rows),
                'groups': {}
            }
            
            for row in rows:
                (chat_id, address, symbol, name, initial_mcap, current_mcap, 
                 initial_price, current_price, is_active, detected_at, 
                 last_updated, platform) = row
                
                if str(chat_id) not in export_data['groups']:
                    export_data['groups'][str(chat_id)] = []
                
                token_data = {
                    'contract_address': address,
                    'symbol': symbol,
                    'name': name,
                    'initial_mcap': initial_mcap,
                    'current_mcap': current_mcap,
                    'initial_price': initial_price,
                    'current_price': current_price,
                    'is_active': bool(is_active),
                    'detected_at': detected_at,
                    'last_updated': last_updated,
                    'platform': platform
                }
                
                export_data['groups'][str(chat_id)].append(token_data)
            
            with open(json_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"📄 JSON export created: {json_file}")
            
        except Exception as e:
            print(f"❌ Error exporting to JSON: {e}")
    
    async def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files"""
        backups = []
        
        try:
            if os.path.exists(self.backup_dir):
                for filename in os.listdir(self.backup_dir):
                    if filename.endswith('.db'):
                        filepath = os.path.join(self.backup_dir, filename)
                        file_stat = os.stat(filepath)
                        
                        backup_info = {
                            'filename': filename,
                            'filepath': filepath,
                            'size_bytes': file_stat.st_size,
                            'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'type': 'database'
                        }
                        backups.append(backup_info)
                    
                    elif filename.endswith('.json'):
                        filepath = os.path.join(self.backup_dir, filename)
                        file_stat = os.stat(filepath)
                        
                        backup_info = {
                            'filename': filename,
                            'filepath': filepath,
                            'size_bytes': file_stat.st_size,
                            'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'type': 'json_export'
                        }
                        backups.append(backup_info)
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x['modified_time'], reverse=True)
            
            print(f"📁 Found {len(backups)} backup files:")
            for i, backup in enumerate(backups, 1):
                print(f"   {i}. {backup['filename']} ({backup['size_bytes']} bytes) - {backup['modified_time']}")
            
            return backups
            
        except Exception as e:
            print(f"❌ Error listing backups: {e}")
            return []
    
    async def restore_from_backup(self, backup_file: str) -> bool:
        """Restore database from a backup file"""
        try:
            if not os.path.exists(backup_file):
                print(f"❌ Backup file not found: {backup_file}")
                return False
            
            # Create a backup of current database before restoring
            if os.path.exists(self.db_path):
                current_backup = f"{self.db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, current_backup)
                print(f"📦 Current database backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_file, self.db_path)
            print(f"✅ Database restored from: {backup_file}")
            
            # Verify the restoration
            await self._verify_restored_database()
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring from backup: {e}")
            return False
    
    async def _verify_restored_database(self):
        """Verify the restored database is valid"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count tokens by group
            cursor.execute("""
                SELECT chat_id, COUNT(*) as token_count, 
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_count
                FROM tokens 
                GROUP BY chat_id
                ORDER BY chat_id
            """)
            
            groups = cursor.fetchall()
            conn.close()
            
            print("✅ Database restoration verified:")
            total_tokens = 0
            total_active = 0
            
            for chat_id, token_count, active_count in groups:
                print(f"   Group {chat_id}: {active_count}/{token_count} active tokens")
                total_tokens += token_count
                total_active += active_count
            
            print(f"📊 Total: {total_active}/{total_tokens} active tokens across {len(groups)} groups")
            
        except Exception as e:
            print(f"❌ Error verifying restored database: {e}")
    
    async def emergency_recovery(self) -> bool:
        """Emergency recovery from the most recent backup"""
        print("🚨 EMERGENCY RECOVERY INITIATED")
        print("Attempting to restore from the most recent backup...")
        
        try:
            backups = await self.list_available_backups()
            
            if not backups:
                print("❌ No backups available for emergency recovery!")
                return False
            
            # Find the most recent database backup
            db_backups = [b for b in backups if b['type'] == 'database']
            
            if not db_backups:
                print("❌ No database backups available!")
                return False
            
            most_recent = db_backups[0]  # Already sorted by newest first
            print(f"🔄 Restoring from: {most_recent['filename']}")
            
            success = await self.restore_from_backup(most_recent['filepath'])
            
            if success:
                print("🎉 EMERGENCY RECOVERY SUCCESSFUL!")
                return True
            else:
                print("❌ EMERGENCY RECOVERY FAILED!")
                return False
                
        except Exception as e:
            print(f"❌ Error during emergency recovery: {e}")
            return False

    async def setup_automated_protection(self):
        """Set up automated protection system"""
        print("🛡️ Setting up automated data protection...")
        
        # Create initial backup
        await self.create_scheduled_backup()
        
        # Create a protection script that runs automatically
        protection_script = f"""#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append('{os.path.dirname(os.path.abspath(__file__))}')

from data_recovery import DataRecoveryTool

async def automated_backup():
    recovery_tool = DataRecoveryTool()
    await recovery_tool.create_scheduled_backup()
    print("✅ Automated backup completed")

if __name__ == "__main__":
    asyncio.run(automated_backup())
"""
        
        script_path = os.path.join(self.recovery_dir, "automated_backup.py")
        with open(script_path, 'w') as f:
            f.write(protection_script)
        
        print(f"📄 Automated backup script created: {script_path}")
        print("💡 You can run this script periodically or set up a cron job/task scheduler")
        
        # Create a Windows batch file for easy execution
        batch_content = f"""@echo off
cd /d "{os.path.dirname(os.path.abspath(__file__))}"
python automated_backup.py
pause
"""
        
        batch_path = os.path.join(self.recovery_dir, "run_backup.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        print(f"📄 Windows batch file created: {batch_path}")
        print("✅ Automated protection system setup complete!")

async def main():
    """Main recovery tool interface"""
    print("🔧 DATA RECOVERY TOOL")
    print("=" * 40)
    
    recovery_tool = DataRecoveryTool()
    
    print("1️⃣ Creating current backup...")
    backup_file = await recovery_tool.create_scheduled_backup()
    
    print("\n2️⃣ Listing available backups...")
    backups = await recovery_tool.list_available_backups()
    
    print("\n3️⃣ Setting up automated protection...")
    await recovery_tool.setup_automated_protection()
    
    print("\n🎉 Data Recovery Tool Setup Complete!")
    print("📋 Available commands:")
    print("   • Current backup created")
    print("   • All backups listed")
    print("   • Automated protection configured")
    print("   • Emergency recovery ready")
    
    print("\n💡 Your data is now fully protected!")

if __name__ == "__main__":
    asyncio.run(main())
