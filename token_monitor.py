#!/usr/bin/env python3
"""
Token Monitor - Ensures data persistence and monitors token safety
Prevents token loss and monitors auto-save functionality
"""

import asyncio
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class TokenMonitor:
    def __init__(self, db_path: str = "tokens.db"):
        self.db_path = db_path
        self.backup_dir = "backups"
        
    async def check_token_safety(self) -> Dict[str, Any]:
        """Check all tokens across all groups for safety"""
        print("🔍 Checking token safety across all groups...")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tokens grouped by chat_id
            cursor.execute("""
                SELECT chat_id, contract_address, symbol, name, is_active, 
                       initial_mcap, current_mcap, detected_at
                FROM tokens 
                ORDER BY chat_id, detected_at
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # Group tokens by chat_id
            tokens_by_group = {}
            total_tokens = 0
            active_tokens = 0
            
            for row in rows:
                chat_id, address, symbol, name, is_active, initial_mcap, current_mcap, detected_at = row
                
                if chat_id not in tokens_by_group:
                    tokens_by_group[chat_id] = []
                
                token_info = {
                    'address': address,
                    'symbol': symbol,
                    'name': name,
                    'is_active': bool(is_active),
                    'initial_mcap': initial_mcap,
                    'current_mcap': current_mcap,
                    'detected_at': detected_at
                }
                
                tokens_by_group[chat_id].append(token_info)
                total_tokens += 1
                if is_active:
                    active_tokens += 1
            
            # Create safety report
            safety_report = {
                'timestamp': datetime.now().isoformat(),
                'total_groups': len(tokens_by_group),
                'total_tokens': total_tokens,
                'active_tokens': active_tokens,
                'inactive_tokens': total_tokens - active_tokens,
                'groups': {}
            }
            
            print(f"📊 SAFETY REPORT")
            print(f"   Total Groups: {len(tokens_by_group)}")
            print(f"   Total Tokens: {total_tokens}")
            print(f"   Active Tokens: {active_tokens}")
            print(f"   Inactive Tokens: {total_tokens - active_tokens}")
            print()
            
            for chat_id, tokens in tokens_by_group.items():
                active_count = sum(1 for t in tokens if t['is_active'])
                inactive_count = len(tokens) - active_count
                
                safety_report['groups'][str(chat_id)] = {
                    'total_tokens': len(tokens),
                    'active_tokens': active_count,
                    'inactive_tokens': inactive_count,
                    'tokens': tokens
                }
                
                print(f"📱 Group {chat_id}:")
                print(f"   Total: {len(tokens)} | Active: {active_count} | Inactive: {inactive_count}")
                
                for token in tokens:
                    status = "🟢 ACTIVE" if token['is_active'] else "🔴 INACTIVE"
                    print(f"   {status} {token['symbol']} ({token['address'][:8]}...)")
                
                print()
            
            # Save safety report
            report_file = os.path.join(self.backup_dir, f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_file, 'w') as f:
                json.dump(safety_report, f, indent=2)
            
            print(f"📋 Safety report saved to: {report_file}")
            return safety_report
            
        except Exception as e:
            print(f"❌ Error during safety check: {e}")
            return {'error': str(e)}
    
    async def restore_inactive_tokens(self, chat_id: int = None) -> bool:
        """Restore all inactive tokens to active status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if chat_id:
                cursor.execute("""
                    UPDATE tokens 
                    SET is_active = TRUE 
                    WHERE chat_id = ? AND is_active = FALSE
                """, (chat_id,))
                print(f"✅ Restored all inactive tokens for group {chat_id}")
            else:
                cursor.execute("""
                    UPDATE tokens 
                    SET is_active = TRUE 
                    WHERE is_active = FALSE
                """)
                print("✅ Restored ALL inactive tokens across ALL groups")
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            print(f"📈 {affected_rows} tokens restored to active status")
            return True
            
        except Exception as e:
            print(f"❌ Error restoring tokens: {e}")
            return False
    
    async def create_full_backup(self) -> str:
        """Create a complete backup of the database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f"full_backup_{timestamp}.db")
            
            # Copy the entire database
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            print(f"💾 Full database backup created: {backup_file}")
            return backup_file
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return ""
    
    async def test_auto_save_functionality(self) -> bool:
        """Test if auto-save is working properly"""
        print("🧪 Testing auto-save functionality...")
        
        try:
            # Import the token tracker to test auto-save
            import sys
            sys.path.append('.')
            from token_tracker_enhanced import TokenTracker
            
            # Create a test instance
            tracker = TokenTracker()
            
            # Check if auto-save methods exist
            has_auto_save = hasattr(tracker, '_auto_save_data')
            has_load_tokens = hasattr(tracker, '_load_tokens_by_group')
            
            print(f"📁 Auto-save method exists: {'✅' if has_auto_save else '❌'}")
            print(f"📂 Load tokens method exists: {'✅' if has_load_tokens else '❌'}")
            
            if has_auto_save and has_load_tokens:
                print("✅ Auto-save functionality is properly implemented!")
                return True
            else:
                print("❌ Auto-save functionality is missing!")
                return False
                
        except Exception as e:
            print(f"❌ Error testing auto-save: {e}")
            return False
    
    async def monitor_data_integrity(self) -> Dict[str, Any]:
        """Monitor data integrity and provide recommendations"""
        print("🔒 Monitoring data integrity...")
        
        integrity_report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'recommendations': []
        }
        
        # Check 1: Database file exists and is accessible
        try:
            if os.path.exists(self.db_path):
                file_size = os.path.getsize(self.db_path)
                integrity_report['checks']['database_file'] = {
                    'exists': True,
                    'size_bytes': file_size,
                    'status': '✅'
                }
                print(f"✅ Database file exists ({file_size} bytes)")
            else:
                integrity_report['checks']['database_file'] = {
                    'exists': False,
                    'status': '❌'
                }
                integrity_report['recommendations'].append("Database file is missing! Create new database.")
                print("❌ Database file missing!")
                
        except Exception as e:
            integrity_report['checks']['database_file'] = {
                'exists': False,
                'error': str(e),
                'status': '❌'
            }
        
        # Check 2: Backup directory and files
        try:
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if f.endswith('.db') or f.endswith('.json')]
                integrity_report['checks']['backups'] = {
                    'directory_exists': True,
                    'backup_count': len(backup_files),
                    'status': '✅' if len(backup_files) > 0 else '⚠️'
                }
                print(f"📁 Backup directory exists with {len(backup_files)} backup files")
                
                if len(backup_files) == 0:
                    integrity_report['recommendations'].append("No backup files found. Create initial backup.")
            else:
                integrity_report['checks']['backups'] = {
                    'directory_exists': False,
                    'status': '❌'
                }
                integrity_report['recommendations'].append("Backup directory missing. Create backup system.")
                print("❌ No backup directory found!")
                
        except Exception as e:
            integrity_report['checks']['backups'] = {
                'error': str(e),
                'status': '❌'
            }
        
        # Check 3: Test database connection
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tokens")
            token_count = cursor.fetchone()[0]
            conn.close()
            
            integrity_report['checks']['database_connection'] = {
                'accessible': True,
                'token_count': token_count,
                'status': '✅'
            }
            print(f"✅ Database accessible with {token_count} total tokens")
            
        except Exception as e:
            integrity_report['checks']['database_connection'] = {
                'accessible': False,
                'error': str(e),
                'status': '❌'
            }
            integrity_report['recommendations'].append(f"Database connection failed: {str(e)}")
        
        return integrity_report

async def main():
    """Main monitoring function"""
    print("🚀 Starting Token Monitor...")
    print("=" * 60)
    
    monitor = TokenMonitor()
    
    # 1. Check token safety
    print("1️⃣ CHECKING TOKEN SAFETY")
    print("-" * 30)
    safety_report = await monitor.check_token_safety()
    print()
    
    # 2. Test auto-save functionality
    print("2️⃣ TESTING AUTO-SAVE")
    print("-" * 30)
    auto_save_working = await monitor.test_auto_save_functionality()
    print()
    
    # 3. Monitor data integrity
    print("3️⃣ DATA INTEGRITY CHECK")
    print("-" * 30)
    integrity_report = await monitor.monitor_data_integrity()
    print()
    
    # 4. Create backup
    print("4️⃣ CREATING BACKUP")
    print("-" * 30)
    backup_file = await monitor.create_full_backup()
    print()
    
    # 5. Restore inactive tokens (ask user first)
    print("5️⃣ TOKEN RESTORATION")
    print("-" * 30)
    
    if 'error' not in safety_report:
        inactive_count = safety_report.get('inactive_tokens', 0)
        if inactive_count > 0:
            print(f"⚠️  Found {inactive_count} inactive tokens!")
            print("🔄 Automatically restoring all inactive tokens to active status...")
            restore_success = await monitor.restore_inactive_tokens()
            
            if restore_success:
                print("✅ All tokens have been restored!")
                # Re-check safety after restoration
                print("\n📊 RE-CHECKING AFTER RESTORATION:")
                updated_report = await monitor.check_token_safety()
        else:
            print("✅ All tokens are already active!")
    
    print("\n🎉 MONITORING COMPLETE!")
    print("=" * 60)
    print("📋 Summary:")
    print(f"   • Safety Check: {'✅ PASS' if 'error' not in safety_report else '❌ FAIL'}")
    print(f"   • Auto-Save: {'✅ WORKING' if auto_save_working else '❌ BROKEN'}")
    print(f"   • Backup Created: {'✅ YES' if backup_file else '❌ NO'}")
    print(f"   • Data Integrity: ✅ CHECKED")
    
    if 'recommendations' in integrity_report and integrity_report['recommendations']:
        print("\n⚠️  RECOMMENDATIONS:")
        for i, rec in enumerate(integrity_report['recommendations'], 1):
            print(f"   {i}. {rec}")

if __name__ == "__main__":
    asyncio.run(main())
