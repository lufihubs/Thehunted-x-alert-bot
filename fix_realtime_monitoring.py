"""
Fix for Real-Time Monitoring of ALL Tokens
This script fixes the issue where only the first token gets real-time updates.
"""

import asyncio
import sys
import logging
from datetime import datetime
sys.path.append('.')
from database import Database
from solana_api import SolanaAPI
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedTokenTracker:
    def __init__(self):
        self.database = Database(Config.DATABASE_PATH)
        self.api = SolanaAPI()
        self.tracking_tokens = {}  # contract -> token_data
        self.is_running = False
        
    async def load_all_active_tokens(self):
        """Load ALL active tokens from database regardless of group."""
        try:
            await self.database.init_db()
            
            # Get all active tokens from all groups
            import sqlite3
            conn = sqlite3.connect('tokens.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, symbol, name, 
                       initial_mcap, current_mcap, initial_price, current_price,
                       chat_id, is_active, last_updated
                FROM tokens 
                WHERE is_active = 1
                ORDER BY last_updated DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # Load into tracking dictionary
            self.tracking_tokens = {}
            for row in results:
                contract, symbol, name, initial_mcap, current_mcap, initial_price, current_price, chat_id, is_active, last_updated = row
                
                self.tracking_tokens[contract] = {
                    'contract_address': contract,
                    'symbol': symbol,
                    'name': name,
                    'initial_mcap': initial_mcap,
                    'current_mcap': current_mcap or initial_mcap,
                    'initial_price': initial_price,
                    'current_price': current_price or initial_price,
                    'chat_id': chat_id,
                    'last_updated': last_updated
                }
            
            logger.info(f"✅ Loaded {len(self.tracking_tokens)} active tokens for monitoring")
            return len(self.tracking_tokens)
            
        except Exception as e:
            logger.error(f"❌ Error loading tokens: {e}")
            return 0
    
    async def update_all_tokens_realtime(self):
        """Update ALL tokens with real-time data in parallel."""
        if not self.tracking_tokens:
            logger.warning("⚠️ No tokens loaded for monitoring")
            return
        
        logger.info(f"🔄 Starting real-time update for {len(self.tracking_tokens)} tokens...")
        
        # Create tasks for parallel processing
        update_tasks = []
        async with self.api:
            for contract_address, token_data in self.tracking_tokens.items():
                task = self.update_single_token(contract_address, token_data)
                update_tasks.append(task)
            
            # Execute all updates in parallel
            if update_tasks:
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                
                # Count successful updates
                successful = sum(1 for r in results if r is True)
                failed = len(results) - successful
                
                logger.info(f"✅ Update complete: {successful} successful, {failed} failed")
            else:
                logger.warning("⚠️ No update tasks created")
    
    async def update_single_token(self, contract_address: str, token_data: dict):
        """Update a single token with real-time price data."""
        try:
            # Get current token info from API
            current_info = await self.api.get_token_info(contract_address)
            
            if current_info and current_info.get('market_cap', 0) > 0:
                new_mcap = current_info['market_cap']
                new_price = current_info['price']
                
                # Calculate change
                old_mcap = token_data['current_mcap']
                if old_mcap > 0:
                    change_pct = ((new_mcap - old_mcap) / old_mcap) * 100
                    if abs(change_pct) > 1:  # Log significant changes
                        logger.info(f"📈 {token_data['symbol']}: {change_pct:+.2f}% (${old_mcap:,.0f} → ${new_mcap:,.0f})")
                
                # Update in-memory tracking
                token_data['current_mcap'] = new_mcap
                token_data['current_price'] = new_price
                token_data['last_updated'] = datetime.now().isoformat()
                
                # Update database immediately
                await self.database.update_token_price(contract_address, new_mcap, new_price)
                
                return True
            else:
                logger.warning(f"⚠️ No data for {token_data['symbol']} ({contract_address[:8]}...)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating {contract_address}: {e}")
            return False
    
    async def start_continuous_monitoring(self, duration_minutes=5):
        """Start continuous real-time monitoring for specified duration."""
        logger.info(f"🚀 Starting continuous monitoring for {duration_minutes} minutes...")
        
        # Load tokens
        token_count = await self.load_all_active_tokens()
        if token_count == 0:
            logger.error("❌ No tokens to monitor!")
            return
        
        # Monitor continuously
        start_time = datetime.now()
        cycles = 0
        
        while True:
            cycle_start = datetime.now()
            cycles += 1
            
            logger.info(f"🔄 Cycle {cycles}: Updating {len(self.tracking_tokens)} tokens...")
            
            # Update all tokens
            await self.update_all_tokens_realtime()
            
            # Check if we should continue
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
            if elapsed_minutes >= duration_minutes:
                logger.info(f"✅ Monitoring complete after {elapsed_minutes:.1f} minutes ({cycles} cycles)")
                break
            
            # Wait for next cycle (5 seconds)
            cycle_time = (datetime.now() - cycle_start).total_seconds()
            sleep_time = max(0, 5 - cycle_time)
            
            if sleep_time > 0:
                logger.info(f"⏱️ Cycle {cycles} took {cycle_time:.1f}s, sleeping {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)

async def test_fixed_monitoring():
    """Test the fixed monitoring system."""
    tracker = FixedTokenTracker()
    
    print("🧪 TESTING FIXED REAL-TIME MONITORING")
    print("=" * 50)
    
    # Test 1: Load tokens
    token_count = await tracker.load_all_active_tokens()
    print(f"📊 Loaded {token_count} tokens for testing")
    
    if token_count == 0:
        print("❌ No active tokens found!")
        return
    
    # Test 2: Single update cycle
    print("\\n🔄 Testing single update cycle...")
    await tracker.update_all_tokens_realtime()
    
    # Test 3: Continuous monitoring (short test)
    print("\\n🚀 Testing continuous monitoring (30 seconds)...")
    await tracker.start_continuous_monitoring(duration_minutes=0.5)
    
    print("\\n✅ Fixed monitoring test complete!")

if __name__ == "__main__":
    asyncio.run(test_fixed_monitoring())
