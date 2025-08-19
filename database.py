import aiosqlite
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def init_db(self):
        """Initialize the database with tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tokens table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_address TEXT UNIQUE NOT NULL,
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
                    message_id INTEGER,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    platform TEXT,
                    multipliers_alerted TEXT DEFAULT '[]',
                    loss_50_alerted BOOLEAN DEFAULT FALSE,
                    loss_alerts_sent TEXT DEFAULT '[]',  -- JSON array of loss percentages alerted
                    confirmed_scan_mcap REAL DEFAULT NULL,
                    scan_confirmation_count INTEGER DEFAULT 0
                )
            ''')
            
            # Add new column if it doesn't exist
            try:
                await db.execute('ALTER TABLE tokens ADD COLUMN loss_alerts_sent TEXT DEFAULT "[]"')
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
                    FOREIGN KEY (token_id) REFERENCES tokens (id)
                )
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_contract ON tokens(contract_address)
            ''')
            
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_active ON tokens(is_active)
            ''')
            
            await db.commit()
    
    async def add_token(self, contract_address: str, symbol: str, name: str, 
                       initial_mcap: float, initial_price: float, chat_id: int, 
                       message_id: int = None, platform: str = None) -> int:
        """Add a new token to tracking with initial market cap"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT OR REPLACE INTO tokens 
                (contract_address, symbol, name, initial_mcap, current_mcap, 
                 initial_price, current_price, lowest_mcap, lowest_price,
                 highest_mcap, highest_price, chat_id, message_id, platform,
                 confirmed_scan_mcap, scan_confirmation_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (contract_address, symbol, name, initial_mcap, initial_mcap,
                  initial_price, initial_price, initial_mcap, initial_price,
                  initial_mcap, initial_price, chat_id, message_id, platform,
                  initial_mcap, 1))
            await db.commit()
            return cursor.lastrowid
    
    async def update_token_price(self, contract_address: str, current_mcap: float, 
                                current_price: float):
        """Update token's current price and market cap, tracking highs and lows"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current token data
            cursor = await db.execute('''
                SELECT lowest_mcap, lowest_price, highest_mcap, highest_price,
                       confirmed_scan_mcap, scan_confirmation_count
                FROM tokens WHERE contract_address = ?
            ''', (contract_address,))
            row = await cursor.fetchone()
            
            if row:
                lowest_mcap, lowest_price, highest_mcap, highest_price, confirmed_mcap, scan_count = row
                
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
                
                await db.execute('''
                    UPDATE tokens 
                    SET current_mcap = ?, current_price = ?, last_updated = CURRENT_TIMESTAMP,
                        lowest_mcap = ?, lowest_price = ?, highest_mcap = ?, highest_price = ?,
                        confirmed_scan_mcap = ?, scan_confirmation_count = ?
                    WHERE contract_address = ?
                ''', (current_mcap, current_price, new_lowest_mcap, new_lowest_price,
                      new_highest_mcap, new_highest_price, new_confirmed_mcap, 
                      new_scan_count, contract_address))
                await db.commit()
    
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
    
    async def add_alert(self, token_id: int, alert_type: str, chat_id: int, multiplier: float = None):
        """Record an alert that was sent"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO alerts (token_id, alert_type, multiplier, chat_id)
                VALUES (?, ?, ?, ?)
            ''', (token_id, alert_type, multiplier, chat_id))
            await db.commit()
    
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
    
    async def get_token_stats(self) -> Dict:
        """Get database statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total_tokens,
                    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_tokens,
                    COUNT(DISTINCT chat_id) as unique_chats,
                    COUNT(CASE WHEN loss_50_alerted = TRUE THEN 1 END) as tokens_with_50_loss
                FROM tokens
            ''')
            row = await cursor.fetchone()
            return {
                'total_tokens': row[0] if row else 0,
                'active_tokens': row[1] if row else 0,
                'unique_chats': row[2] if row else 0,
                'tokens_with_50_loss': row[3] if row else 0
            }
