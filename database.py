import aiosqlite
import asyncio
import json
import shutil
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_dir = Path(db_path).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self) -> str:
        """Create a backup of the current database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"tokens_backup_{timestamp}.db"
            
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup_path)
                return str(backup_path)
            return ""
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""
    
    async def save_all_group_data(self) -> Dict:
        """Save all group data to ensure persistence across updates."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Save all group information
                groups_cursor = await db.execute('''
                    SELECT chat_id, chat_title, chat_type, settings, created_at, is_active
                    FROM groups WHERE is_active = 1
                ''')
                groups_data = await groups_cursor.fetchall()
                
                # Save all token information grouped by chat
                tokens_cursor = await db.execute('''
                    SELECT * FROM tokens WHERE is_active = 1
                    ORDER BY chat_id, detected_at
                ''')
                tokens_data = await tokens_cursor.fetchall()
                
                # Save all alert history
                alerts_cursor = await db.execute('''
                    SELECT * FROM alerts
                    ORDER BY chat_id, alerted_at DESC
                ''')
                alerts_data = await alerts_cursor.fetchall()
                
                # Organize data by chat_id for easy restoration
                grouped_data = {}
                
                # Process groups
                for group in groups_data:
                    chat_id = group[0]
                    grouped_data[chat_id] = {
                        'group_info': {
                            'chat_id': group[0],
                            'chat_title': group[1],
                            'chat_type': group[2],
                            'settings': json.loads(group[3]) if group[3] else {},
                            'created_at': group[4],
                            'is_active': group[5]
                        },
                        'tokens': [],
                        'alerts': []
                    }
                
                # Process tokens
                for token in tokens_data:
                    chat_id = token[12]  # chat_id is at index 12
                    if chat_id not in grouped_data:
                        grouped_data[chat_id] = {'group_info': {}, 'tokens': [], 'alerts': []}
                    
                    token_data = {
                        'id': token[0],
                        'contract_address': token[1],
                        'symbol': token[2],
                        'name': token[3],
                        'initial_mcap': token[4],
                        'current_mcap': token[5],
                        'initial_price': token[6],
                        'current_price': token[7],
                        'lowest_mcap': token[8],
                        'lowest_price': token[9],
                        'highest_mcap': token[10],
                        'highest_price': token[11],
                        'chat_id': token[12],
                        'group_id': token[13],
                        'message_id': token[14],
                        'detected_at': token[15],
                        'last_updated': token[16],
                        'is_active': token[17],
                        'platform': token[18],
                        'multipliers_alerted': json.loads(token[19]) if token[19] and token[19] != 'NULL' else [],
                        'loss_alerts_sent': json.loads(token[20]) if token[20] and token[20] != 'NULL' else [],
                        'confirmed_scan_mcap': token[21],
                        'scan_confirmation_count': token[22]
                    }
                    grouped_data[chat_id]['tokens'].append(token_data)
                
                # Process alerts
                for alert in alerts_data:
                    chat_id = alert[5]  # chat_id is at index 5
                    if chat_id in grouped_data:
                        alert_data = {
                            'id': alert[0],
                            'token_id': alert[1],
                            'alert_type': alert[2],
                            'multiplier': alert[3],
                            'alerted_at': alert[4],
                            'chat_id': alert[5],
                            'group_id': alert[6]
                        }
                        grouped_data[chat_id]['alerts'].append(alert_data)
                
                # Save to backup file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_data_path = self.backup_dir / f"all_group_data_{timestamp}.json"
                
                with open(backup_data_path, 'w') as f:
                    json.dump(grouped_data, f, indent=2, default=str)
                
                print(f"💾 All group data saved to: {backup_data_path}")
                return grouped_data
                
        except Exception as e:
            print(f"Error saving group data: {e}")
            return {}
    
    async def restore_group_data(self, backup_file: str) -> bool:
        """Restore group data from backup file."""
        try:
            with open(backup_file, 'r') as f:
                grouped_data = json.load(f)
            
            async with aiosqlite.connect(self.db_path) as db:
                for chat_id, data in grouped_data.items():
                    # Restore group info
                    if 'group_info' in data and data['group_info']:
                        group_info = data['group_info']
                        await db.execute('''
                            INSERT OR REPLACE INTO groups (chat_id, chat_title, chat_type, settings, is_active)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            group_info['chat_id'],
                            group_info.get('chat_title', f"Chat {chat_id}"),
                            group_info.get('chat_type', 'private'),
                            json.dumps(group_info.get('settings', {})),
                            group_info.get('is_active', True)
                        ))
                    
                    # Restore tokens
                    for token in data.get('tokens', []):
                        await db.execute('''
                            INSERT OR REPLACE INTO tokens 
                            (contract_address, symbol, name, initial_mcap, current_mcap,
                             initial_price, current_price, lowest_mcap, lowest_price,
                             highest_mcap, highest_price, chat_id, message_id,
                             detected_at, last_updated, is_active, platform,
                             multipliers_alerted, loss_alerts_sent, confirmed_scan_mcap,
                             scan_confirmation_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            token['contract_address'], token['symbol'], token['name'],
                            token['initial_mcap'], token['current_mcap'],
                            token['initial_price'], token['current_price'],
                            token['lowest_mcap'], token['lowest_price'],
                            token['highest_mcap'], token['highest_price'],
                            token['chat_id'], token.get('message_id'),
                            token.get('detected_at', datetime.now().isoformat()),
                            token.get('last_updated', datetime.now().isoformat()),
                            token.get('is_active', True), token.get('platform'),
                            json.dumps(token.get('multipliers_alerted', [])),
                            json.dumps(token.get('loss_alerts_sent', [])),
                            token.get('confirmed_scan_mcap'), token.get('scan_confirmation_count', 1)
                        ))
                
                await db.commit()
                print(f"✅ Successfully restored data for {len(grouped_data)} groups")
                return True
                
        except Exception as e:
            print(f"Error restoring group data: {e}")
            return False
    
    async def auto_save_on_update(self):
        """Automatically save data when updates are made."""
        backup_path = await self.create_backup()
        if backup_path:
            print(f"🔄 Auto-backup created: {backup_path}")
        
        # Save all group data
        await self.save_all_group_data()
        print("💾 All group data auto-saved")
        
    async def init_db(self):
        """Initialize the database with enhanced tables for group-specific tracking."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create groups table for group-specific settings
            await db.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY,
                    chat_id INTEGER UNIQUE NOT NULL,
                    chat_title TEXT,
                    chat_type TEXT,
                    settings TEXT DEFAULT '{}',  -- JSON settings for each group
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Enhanced tokens table with group-specific tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_address TEXT NOT NULL,
                    symbol TEXT,
                    name TEXT,
                    initial_mcap REAL NOT NULL,
                    current_mcap REAL,
                    initial_price REAL NOT NULL,
                    current_price REAL,
                    lowest_mcap REAL,
                    lowest_price REAL,
                    highest_mcap REAL,
                    highest_price REAL,
                    chat_id INTEGER NOT NULL,
                    group_id INTEGER,
                    message_id INTEGER,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    platform TEXT,
                    source_api TEXT DEFAULT 'dexscreener',
                    dex_name TEXT,
                    pair_address TEXT,
                    liquidity_usd REAL DEFAULT 0,
                    volume_24h REAL DEFAULT 0,
                    price_change_24h REAL DEFAULT 0,
                    multipliers_alerted TEXT DEFAULT '[]',
                    loss_alerts_sent TEXT DEFAULT '[]',
                    confirmed_scan_mcap REAL DEFAULT NULL,
                    scan_confirmation_count INTEGER DEFAULT 0,
                    user_notes TEXT,
                    FOREIGN KEY (group_id) REFERENCES groups (id),
                    UNIQUE(contract_address, chat_id)  -- Same token can be tracked in different groups
                )
            ''')
            
            # Migration: Add new columns if they don't exist
            new_columns = [
                ('group_id', 'INTEGER'),
                ('source_api', 'TEXT DEFAULT "dexscreener"'),
                ('dex_name', 'TEXT'),
                ('pair_address', 'TEXT'),
                ('liquidity_usd', 'REAL DEFAULT 0'),
                ('volume_24h', 'REAL DEFAULT 0'),
                ('price_change_24h', 'REAL DEFAULT 0'),
                ('user_notes', 'TEXT'),
                ('loss_alerts_sent', 'TEXT DEFAULT "[]"')
            ]
            
            for column_name, column_type in new_columns:
                try:
                    await db.execute(f'ALTER TABLE tokens ADD COLUMN {column_name} {column_type}')
                except aiosqlite.OperationalError:
                    # Column already exists
                    pass
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id INTEGER,
                    alert_type TEXT,
                    multiplier REAL,
                    alerted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    chat_id INTEGER,
                    group_id INTEGER,
                    FOREIGN KEY (token_id) REFERENCES tokens (id),
                    FOREIGN KEY (group_id) REFERENCES groups (id)
                )
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_contract_chat ON tokens(contract_address, chat_id)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_active ON tokens(is_active)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_chat ON tokens(chat_id)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_groups_chat ON groups(chat_id)
            ''')
            
            await db.commit()
    
    async def register_group(self, chat_id: int, chat_title: Optional[str] = None, chat_type: str = 'private') -> int:
        """Register a new group/chat for tracking."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT OR REPLACE INTO groups (chat_id, chat_title, chat_type)
                VALUES (?, ?, ?)
            ''', (chat_id, chat_title or f"Chat {chat_id}", chat_type))
            await db.commit()
            return cursor.lastrowid or 0
    
    async def get_group_settings(self, chat_id: int) -> Dict:
        """Get group-specific settings."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT settings FROM groups WHERE chat_id = ?
            ''', (chat_id,))
            row = await cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return {}
            return {}
    
    async def update_group_settings(self, chat_id: int, settings: Dict):
        """Update group-specific settings."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE groups SET settings = ? WHERE chat_id = ?
            ''', (json.dumps(settings), chat_id))
            await db.commit()
    
    async def add_token(self, contract_address: str, symbol: str, name: str, 
                       initial_mcap: float, initial_price: float, chat_id: int, 
                       message_id: Optional[int] = None, platform: Optional[str] = None,
                       source_api: str = 'dexscreener', dex_name: Optional[str] = None,
                       pair_address: Optional[str] = None, liquidity_usd: float = 0,
                       volume_24h: float = 0, price_change_24h: float = 0) -> int:
        """Add a new token to tracking with comprehensive data"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get or create group
            group_cursor = await db.execute('''
                SELECT id FROM groups WHERE chat_id = ?
            ''', (chat_id,))
            group_row = await group_cursor.fetchone()
            group_id = group_row[0] if group_row else None
            
            if not group_id:
                group_id = await self.register_group(chat_id)
            
            cursor = await db.execute('''
                INSERT OR REPLACE INTO tokens 
                (contract_address, symbol, name, initial_mcap, current_mcap, 
                 initial_price, current_price, lowest_mcap, lowest_price,
                 highest_mcap, highest_price, chat_id, group_id, message_id, platform,
                 source_api, dex_name, pair_address, liquidity_usd, volume_24h, price_change_24h,
                 confirmed_scan_mcap, scan_confirmation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (contract_address, symbol, name, initial_mcap, initial_mcap,
                  initial_price, initial_price, initial_mcap, initial_price,
                  initial_mcap, initial_price, chat_id, group_id, message_id, platform,
                  source_api, dex_name, pair_address, liquidity_usd, volume_24h, price_change_24h,
                  initial_mcap, 1))
            await db.commit()
            return cursor.lastrowid or 0
    
    async def update_token_price(self, contract_address: str, current_mcap: float, 
                                current_price: float):
        """Update token's current price and market cap across ALL groups, tracking highs and lows"""
        async with aiosqlite.connect(self.db_path) as db:
            # First, get all instances of this token across all groups
            cursor = await db.execute('''
                SELECT id, chat_id, lowest_mcap, lowest_price, highest_mcap, highest_price,
                       confirmed_scan_mcap, scan_confirmation_count
                FROM tokens WHERE contract_address = ? AND is_active = 1
            ''', (contract_address,))
            rows = await cursor.fetchall()
            
            if not rows:
                return  # No active tokens found
            
            updates_made = 0
            
            for row in rows:
                token_id, chat_id, lowest_mcap, lowest_price, highest_mcap, highest_price, confirmed_mcap, scan_count = row
                
                # Handle NULL values
                lowest_mcap = lowest_mcap if lowest_mcap is not None else current_mcap
                lowest_price = lowest_price if lowest_price is not None else current_price
                highest_mcap = highest_mcap if highest_mcap is not None else current_mcap
                highest_price = highest_price if highest_price is not None else current_price
                
                # Update lows
                new_lowest_mcap = min(lowest_mcap, current_mcap)
                new_lowest_price = min(lowest_price, current_price)
                
                # Update highs
                new_highest_mcap = max(highest_mcap, current_mcap)
                new_highest_price = max(highest_price, current_price)
                
                # Improve scan accuracy with multiple confirmations
                if scan_count is None or scan_count < 3:
                    new_confirmed_mcap = current_mcap
                    new_scan_count = (scan_count or 0) + 1
                else:
                    new_confirmed_mcap = confirmed_mcap or current_mcap
                    new_scan_count = scan_count
                
                # Update this specific token instance
                await db.execute('''
                    UPDATE tokens 
                    SET current_mcap = ?, current_price = ?, last_updated = CURRENT_TIMESTAMP,
                        lowest_mcap = ?, lowest_price = ?, highest_mcap = ?, highest_price = ?,
                        confirmed_scan_mcap = ?, scan_confirmation_count = ?
                    WHERE id = ?
                ''', (current_mcap, current_price, new_lowest_mcap, new_lowest_price,
                      new_highest_mcap, new_highest_price, new_confirmed_mcap, 
                      new_scan_count, token_id))
                
                updates_made += 1
            
            await db.commit()
            
            # Log the updates for verification
            if updates_made > 1:
                print(f"🔄 Updated token {contract_address[:8]}... across {updates_made} groups")
            elif updates_made == 1:
                print(f"🔄 Updated token {contract_address[:8]}... in 1 group")
    
    async def get_active_tokens(self) -> List[Dict]:
        """Get all active tokens for monitoring"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM tokens WHERE is_active = TRUE
            ''')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_token_by_address(self, contract_address: str) -> Optional[Dict]:
        """Get token by contract address"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT * FROM tokens WHERE contract_address = ?
            ''', (contract_address,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def add_alert(self, token_id: int, alert_type: str, chat_id: int, multiplier: Optional[float] = None):
        """Record an alert that was sent"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get group_id
            group_cursor = await db.execute('''
                SELECT id FROM groups WHERE chat_id = ?
            ''', (chat_id,))
            group_row = await group_cursor.fetchone()
            group_id = group_row[0] if group_row else None
            
            await db.execute('''
                INSERT INTO alerts (token_id, alert_type, multiplier, chat_id, group_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (token_id, alert_type, multiplier, chat_id, group_id))
            await db.commit()
    
    async def get_tokens_for_chat(self, chat_id: int, active_only: bool = True) -> List[Dict]:
        """Get all tokens tracked in a specific chat/group"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            where_clause = "WHERE t.chat_id = ?"
            params = [chat_id]
            
            if active_only:
                where_clause += " AND t.is_active = TRUE"
            
            cursor = await db.execute(f'''
                SELECT t.*, g.chat_title, g.chat_type
                FROM tokens t
                LEFT JOIN groups g ON t.group_id = g.id
                {where_clause}
                ORDER BY t.detected_at DESC
            ''', params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def remove_token(self, contract_address: str, chat_id: int) -> bool:
        """Remove a token from tracking for a specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                UPDATE tokens SET is_active = FALSE 
                WHERE contract_address = ? AND chat_id = ?
            ''', (contract_address, chat_id))
            await db.commit()
            
            # Auto-save after token removal
            if cursor.rowcount > 0:
                await self.auto_save_on_update()
                print(f"💾 Auto-saved after removing token {contract_address[:8]}... from chat {chat_id}")
            
            return cursor.rowcount > 0
    
    async def permanently_delete_token(self, contract_address: str, chat_id: int) -> bool:
        """Permanently delete a token from tracking for a specific chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                DELETE FROM tokens 
                WHERE contract_address = ? AND chat_id = ?
            ''', (contract_address, chat_id))
            await db.commit()
            
            # Auto-save after permanent deletion
            if cursor.rowcount > 0:
                await self.auto_save_on_update()
                print(f"💾 Auto-saved after permanently deleting token {contract_address[:8]}... from chat {chat_id}")
            
            return cursor.rowcount > 0
    
    async def get_token_stats(self, chat_id: int) -> Dict:
        """Get token tracking statistics for a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_tokens,
                    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_tokens,
                    COUNT(CASE WHEN current_mcap > initial_mcap THEN 1 END) as pumping_tokens,
                    COUNT(CASE WHEN current_mcap < initial_mcap THEN 1 END) as dumping_tokens,
                    AVG(current_mcap / initial_mcap) as avg_multiplier,
                    MAX(current_mcap / initial_mcap) as max_multiplier
                FROM tokens 
                WHERE chat_id = ?
            ''', (chat_id,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    'total_tokens': row[0] or 0,
                    'active_tokens': row[1] or 0,
                    'pumping_tokens': row[2] or 0,
                    'dumping_tokens': row[3] or 0,
                    'avg_multiplier': round(row[4] or 1.0, 2),
                    'max_multiplier': round(row[5] or 1.0, 2)
                }
            return {
                'total_tokens': 0,
                'active_tokens': 0,
                'pumping_tokens': 0,
                'dumping_tokens': 0,
                'avg_multiplier': 1.0,
                'max_multiplier': 1.0
            }
    
    async def search_tokens(self, chat_id: int, query: str) -> List[Dict]:
        """Search tokens by symbol, name, or contract address"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            search_pattern = f"%{query}%"
            cursor = await db.execute('''
                SELECT * FROM tokens 
                WHERE chat_id = ? AND is_active = TRUE 
                AND (symbol LIKE ? OR name LIKE ? OR contract_address LIKE ?)
                ORDER BY detected_at DESC
            ''', (chat_id, search_pattern, search_pattern, search_pattern))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_multipliers_alerted(self, contract_address: str, multipliers: List[float]):
        """Update the list of multipliers that have been alerted for a token"""
        multipliers_json = json.dumps(multipliers)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tokens 
                SET multipliers_alerted = ?
                WHERE contract_address = ?
            ''', (multipliers_json, contract_address))
            await db.commit()
    
    async def get_multipliers_alerted(self, contract_address: str) -> List[float]:
        """Get the list of multipliers already alerted for a token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT multipliers_alerted FROM tokens WHERE contract_address = ?
            ''', (contract_address,))
            row = await cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
            return []
    
    async def mark_loss_50_alerted(self, contract_address: str):
        """Mark that 50% loss alert has been sent for this token"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tokens SET loss_50_alerted = TRUE WHERE contract_address = ?
            ''', (contract_address,))
            await db.commit()
    
    async def is_loss_50_alerted(self, contract_address: str) -> bool:
        """Check if 50% loss alert has already been sent"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT loss_50_alerted FROM tokens WHERE contract_address = ?
            ''', (contract_address,))
            row = await cursor.fetchone()
            return bool(row[0]) if row and row[0] is not None else False
    
    async def get_confirmed_scan_mcap(self, contract_address: str) -> Optional[float]:
        """Get the confirmed scan market cap for a token"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT confirmed_scan_mcap, scan_confirmation_count FROM tokens WHERE contract_address = ?
            ''', (contract_address,))
            row = await cursor.fetchone()
            if row and row[1] and row[1] >= 2:  # At least 2 confirmations
                return row[0]
            return None
    
    async def deactivate_token(self, contract_address: str):
        """Deactivate a token (stop monitoring)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tokens SET is_active = FALSE WHERE contract_address = ?
            ''', (contract_address,))
            await db.commit()
    
    async def get_all_active_tokens_by_group(self) -> Dict[int, List[Dict]]:
        """Get all active tokens organized by group (chat_id) for multi-group support"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT t.*, g.chat_title, g.chat_type
                FROM tokens t
                LEFT JOIN groups g ON t.group_id = g.id
                WHERE t.is_active = TRUE
                ORDER BY t.chat_id, t.detected_at DESC
            ''')
            
            rows = await cursor.fetchall()
            tokens_by_group = {}
            
            for row in rows:
                token_dict = dict(row)
                chat_id = token_dict['chat_id']
                
                if chat_id not in tokens_by_group:
                    tokens_by_group[chat_id] = []
                tokens_by_group[chat_id].append(token_dict)
            
            return tokens_by_group
    
    async def auto_remove_rugged_tokens(self, threshold: float = -80.0) -> List[Dict]:
        """Auto-remove tokens that have dropped below the threshold"""
        removed_tokens = []
        
        async with aiosqlite.connect(self.db_path) as db:
            # Find tokens that should be auto-removed
            cursor = await db.execute('''
                SELECT id, contract_address, symbol, name, chat_id, 
                       initial_mcap, current_mcap, confirmed_scan_mcap
                FROM tokens 
                WHERE is_active = TRUE 
                AND current_mcap IS NOT NULL
                AND current_mcap > 0
                AND (
                    (confirmed_scan_mcap IS NOT NULL AND confirmed_scan_mcap > 0 AND 
                     (current_mcap - confirmed_scan_mcap) / confirmed_scan_mcap * 100 <= ?) OR
                    (confirmed_scan_mcap IS NULL AND initial_mcap > 0 AND 
                     (current_mcap - initial_mcap) / initial_mcap * 100 <= ?)
                )
            ''', (threshold, threshold))
            
            rugged_tokens = await cursor.fetchall()
            
            for token in rugged_tokens:
                token_id, contract_address, symbol, name, chat_id, initial_mcap, current_mcap, confirmed_mcap = token
                
                # Calculate actual loss percentage
                baseline = confirmed_mcap if confirmed_mcap and confirmed_mcap > 0 else initial_mcap
                loss_percentage = ((current_mcap - baseline) / baseline * 100) if baseline > 0 else -100
                
                # Mark token as inactive (auto-removed)
                await db.execute('''
                    UPDATE tokens 
                    SET is_active = FALSE, 
                        user_notes = COALESCE(user_notes, '') || ' [AUTO-REMOVED: ' || ? || '% loss]'
                    WHERE id = ?
                ''', (round(loss_percentage, 1), token_id))
                
                removed_tokens.append({
                    'contract_address': contract_address,
                    'symbol': symbol,
                    'name': name,
                    'chat_id': chat_id,
                    'loss_percentage': loss_percentage,
                    'current_mcap': current_mcap,
                    'baseline_mcap': baseline
                })
            
            await db.commit()
        
        return removed_tokens
    
    async def check_zero_liquidity_tokens(self) -> List[Dict]:
        """Find tokens with zero or very low liquidity for removal"""
        zero_liquidity_tokens = []
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT id, contract_address, symbol, name, chat_id, 
                       liquidity_usd, current_mcap
                FROM tokens 
                WHERE is_active = TRUE 
                AND (liquidity_usd IS NULL OR liquidity_usd < 100)
                AND current_mcap < 1000
            ''')
            
            rows = await cursor.fetchall()
            
            for row in rows:
                token_id, contract_address, symbol, name, chat_id, liquidity_usd, current_mcap = row
                
                # Mark as inactive due to zero liquidity
                await db.execute('''
                    UPDATE tokens 
                    SET is_active = FALSE, 
                        user_notes = COALESCE(user_notes, '') || ' [AUTO-REMOVED: Zero liquidity/Low mcap]'
                    WHERE id = ?
                ''', (token_id,))
                
                zero_liquidity_tokens.append({
                    'contract_address': contract_address,
                    'symbol': symbol,
                    'name': name,
                    'chat_id': chat_id,
                    'liquidity_usd': liquidity_usd or 0,
                    'current_mcap': current_mcap or 0
                })
            
            await db.commit()
        
        return zero_liquidity_tokens
    
    async def get_group_statistics(self, chat_id: int) -> Dict:
        """Get statistics for a specific group"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total tokens
            cursor = await db.execute('''
                SELECT COUNT(*) FROM tokens WHERE chat_id = ? AND is_active = TRUE
            ''', (chat_id,))
            result = await cursor.fetchone()
            total_active = result[0] if result else 0
            
            # Tokens with gains
            cursor = await db.execute('''
                SELECT COUNT(*) FROM tokens 
                WHERE chat_id = ? AND is_active = TRUE 
                AND current_mcap > COALESCE(confirmed_scan_mcap, initial_mcap)
            ''', (chat_id,))
            result = await cursor.fetchone()
            gaining_tokens = result[0] if result else 0
            
            # Tokens with losses
            cursor = await db.execute('''
                SELECT COUNT(*) FROM tokens 
                WHERE chat_id = ? AND is_active = TRUE 
                AND current_mcap < COALESCE(confirmed_scan_mcap, initial_mcap)
            ''', (chat_id,))
            result = await cursor.fetchone()
            losing_tokens = result[0] if result else 0
            
            # Total removed tokens
            cursor = await db.execute('''
                SELECT COUNT(*) FROM tokens WHERE chat_id = ? AND is_active = FALSE
            ''', (chat_id,))
            result = await cursor.fetchone()
            removed_tokens = result[0] if result else 0
            
            return {
                'total_active': total_active,
                'gaining_tokens': gaining_tokens,
                'losing_tokens': losing_tokens,
                'removed_tokens': removed_tokens,
                'chat_id': chat_id
            }
    
    async def update_loss_alerts_sent(self, contract_address: str, loss_thresholds: List[float]):
        """Update the loss alerts that have been sent for a token."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE tokens 
                SET loss_alerts_sent = ?
                WHERE contract_address = ?
            ''', (json.dumps(loss_thresholds), contract_address))
            await db.commit()
