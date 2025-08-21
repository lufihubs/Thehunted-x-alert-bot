
"""
PRODUCTION TOKEN TRACKER - 100 TOKEN CAPACITY
Enhanced parallel processing with safe Railway migration
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Set
import json

class EnhancedTokenTracker:
    def __init__(self):
        self.max_concurrent_tokens = 100
        self.batch_size = 20  # Process 20 tokens per batch for optimal performance
        self.update_interval = 5  # 5-second real-time updates
        self.tracking_tokens_by_group = {}
        self.is_running = False
        self.migration_completed = False
        
    async def safe_railway_migration(self):
        """Safely migrate existing Railway tokens to enhanced system."""
        try:
            logger.info("🔄 Starting safe Railway migration...")
            
            # Step 1: Backup existing data
            await self.backup_existing_tokens()
            
            # Step 2: Load existing tokens from Railway database
            existing_tokens = await self.load_railway_tokens()
            logger.info(f"📊 Found {len(existing_tokens)} existing tokens to migrate")
            
            # Step 3: Migrate to enhanced schema
            for token in existing_tokens:
                await self.migrate_single_token(token)
            
            # Step 4: Verify migration
            migrated_count = await self.verify_migration()
            logger.info(f"✅ Successfully migrated {migrated_count} tokens")
            
            self.migration_completed = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await self.rollback_migration()
            return False
    
    async def load_railway_tokens(self):
        """Load existing tokens from Railway database."""
        try:
            import sqlite3
            
            conn = sqlite3.connect('tokens.db')
            cursor = conn.cursor()
            
            # Get all active tokens from Railway
            cursor.execute("""
                SELECT contract_address, symbol, name, initial_mcap, current_mcap,
                       chat_id, platform, detected_at, last_updated
                FROM tokens 
                WHERE is_active = 1
            """)
            
            tokens = cursor.fetchall()
            conn.close()
            
            logger.info(f"📋 Loaded {len(tokens)} tokens from Railway database")
            return tokens
            
        except Exception as e:
            logger.error(f"Error loading Railway tokens: {e}")
            return []
    
    async def start_enhanced_monitoring(self):
        """Start enhanced monitoring with 100-token capacity."""
        
        if not self.migration_completed:
            migration_success = await self.safe_railway_migration()
            if not migration_success:
                logger.error("❌ Cannot start monitoring - migration failed")
                return
        
        self.is_running = True
        logger.info("🚀 Starting enhanced monitoring with 100-token capacity")
        
        while self.is_running:
            try:
                # Get ALL tokens across all groups
                all_tokens = await self.get_all_tracked_tokens()
                
                if len(all_tokens) > self.max_concurrent_tokens:
                    logger.warning(f"⚠️ Token limit reached: {len(all_tokens)}/{self.max_concurrent_tokens}")
                    all_tokens = all_tokens[:self.max_concurrent_tokens]
                
                # Process tokens in batches for optimal performance
                await self.process_tokens_in_batches(all_tokens)
                
                # Check alerts for all updated tokens
                await self.check_alerts_for_all_tokens()
                
                # Performance monitoring
                await self.log_performance_metrics(len(all_tokens))
                
                # Wait for next cycle
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in enhanced monitoring: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def process_tokens_in_batches(self, all_tokens: List):
        """Process tokens in optimized batches for 100+ token capacity."""
        
        total_tokens = len(all_tokens)
        logger.info(f"🔄 Processing {total_tokens} tokens in batches of {self.batch_size}")
        
        # Split tokens into batches
        batches = [all_tokens[i:i + self.batch_size] 
                  for i in range(0, len(all_tokens), self.batch_size)]
        
        start_time = datetime.now()
        
        # Process all batches concurrently
        batch_tasks = []
        for batch_num, batch in enumerate(batches, 1):
            task = self.process_token_batch(batch, batch_num)
            batch_tasks.append(task)
        
        # Execute all batches in parallel
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Calculate performance metrics
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        successful_batches = sum(1 for r in batch_results if r is True)
        successful_tokens = successful_batches * self.batch_size
        
        logger.info(f"⚡ Batch processing complete:")
        logger.info(f"   • Total time: {total_time:.2f}s")
        logger.info(f"   • Tokens updated: {successful_tokens}/{total_tokens}")
        logger.info(f"   • Average per token: {total_time/total_tokens:.2f}s")
        logger.info(f"   • Batches completed: {successful_batches}/{len(batches)}")
    
    async def process_token_batch(self, token_batch: List, batch_num: int):
        """Process a single batch of tokens concurrently."""
        try:
            logger.info(f"📦 Processing batch {batch_num} ({len(token_batch)} tokens)")
            
            # Create parallel tasks for this batch
            api = SolanaAPI()
            async with api:
                update_tasks = []
                for token_data in token_batch:
                    task = self.update_single_token_parallel(api, token_data)
                    update_tasks.append(task)
                
                # Execute batch concurrently
                results = await asyncio.gather(*update_tasks, return_exceptions=True)
                
                # Count successful updates
                successful_updates = sum(1 for r in results if r is True)
                logger.info(f"✅ Batch {batch_num}: {successful_updates}/{len(token_batch)} tokens updated")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Batch {batch_num} failed: {e}")
            return False
    
    async def update_single_token_parallel(self, api, token_data):
        """Update a single token with optimized parallel processing."""
        try:
            contract_address = token_data['contract_address']
            
            # Get latest price data
            latest_data = await api.get_token_info(contract_address)
            
            if latest_data and latest_data.get('market_cap', 0) > 0:
                # Update database
                await self.database.update_token_price(
                    contract_address, 
                    latest_data['market_cap'], 
                    latest_data['price']
                )
                
                # Update in-memory cache
                await self.update_token_cache(contract_address, latest_data)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating token {token_data.get('symbol', 'Unknown')}: {e}")
            return False
    
    async def get_all_tracked_tokens(self):
        """Get all tracked tokens across all groups."""
        all_tokens = []
        
        for chat_id, tokens in self.tracking_tokens_by_group.items():
            for contract_address, token_data in tokens.items():
                all_tokens.append({
                    'contract_address': contract_address,
                    'symbol': token_data['symbol'],
                    'chat_id': chat_id,
                    'token_data': token_data
                })
        
        return all_tokens
    
    async def log_performance_metrics(self, token_count: int):
        """Log system performance metrics."""
        import psutil
        
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent()
        
        logger.info(f"📊 Performance metrics:")
        logger.info(f"   • Tokens monitored: {token_count}/100")
        logger.info(f"   • Memory usage: {memory_mb:.1f}MB")
        logger.info(f"   • CPU usage: {cpu_percent:.1f}%")
        logger.info(f"   • Update interval: {self.update_interval}s")

# Usage
tracker = EnhancedTokenTracker()
