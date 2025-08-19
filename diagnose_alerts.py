#!/usr/bin/env python3
"""
Diagnostic script to check why alerts aren't working
"""

import asyncio
import logging
from datetime import datetime
from database import Database
from token_tracker import TokenTracker
from solana_api import SolanaAPI

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockBot:
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id, text, parse_mode=None):
        self.messages.append({
            'chat_id': chat_id,
            'text': text,
            'timestamp': datetime.now()
        })
        print(f"🚨 ALERT WOULD BE SENT to {chat_id}:")
        print(f"   {text[:100]}...")
        return True

async def diagnose_alert_system():
    print("🔧 ALERT SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    # Initialize components
    db = Database('tokens.db')
    await db.init_db()
    
    # Get all active tokens
    tokens = await db.get_active_tokens()
    print(f"📊 Found {len(tokens)} active tokens")
    
    if not tokens:
        print("❌ No active tokens found!")
        return
    
    # Initialize API and mock bot
    api = SolanaAPI()
    mock_bot = MockBot()
    tracker = TokenTracker(mock_bot)
    
    # Load tokens into tracker
    await tracker._load_existing_tokens()
    print(f"📋 Tracker loaded {len(tracker.tracking_tokens)} tokens")
    
    for i, token in enumerate(tokens, 1):
        print(f"\n--- CHECKING TOKEN {i}: {token['symbol']} ---")
        contract = token['contract_address']
        
        # Check if token is in tracker
        if contract not in tracker.tracking_tokens:
            print(f"❌ Token {contract} not in tracker!")
            continue
        
        print(f"✅ Token found in tracker")
        
        # Get current price from API
        print("🌐 Fetching current price from API...")
        current_info = await api.get_token_info(contract)
        
        if not current_info:
            print("❌ Could not fetch current token info from API")
            continue
        
        print(f"💰 Current API Price: ${current_info.get('price', 'N/A')}")
        print(f"💰 Current API MCap: ${current_info.get('market_cap', 'N/A'):,.0f}")
        
        # Check token data in tracker
        token_data = tracker.tracking_tokens[contract]
        confirmed_mcap = token_data.get('confirmed_scan_mcap')
        
        print(f"🔍 Confirmed Scan MCap: ${confirmed_mcap:,.0f}" if confirmed_mcap else "❌ No confirmed scan mcap")
        
        if confirmed_mcap and confirmed_mcap > 0:
            current_multiplier = current_info['market_cap'] / confirmed_mcap
            print(f"📈 Current Multiplier: {current_multiplier:.2f}x")
            
            # Check what alerts should trigger
            should_alerts = []
            for mult in [2, 3, 5, 8, 10]:
                if current_multiplier >= mult:
                    should_alerts.append(f"{mult}x")
            
            should_loss = current_multiplier <= 0.5
            if should_loss:
                should_alerts.append("-50%")
            
            print(f"🚨 Should trigger alerts: {should_alerts}")
            
            # Check what alerts have been sent
            sent_alerts = tracker.sent_alerts.get(contract, set())
            print(f"📤 Already sent alerts: {sent_alerts}")
            
            # Manually trigger alert check
            print("🧪 Testing alert logic...")
            initial_count = len(mock_bot.messages)
            
            # Test multiplier alerts
            await tracker._check_multiplier_alerts(contract, token_data, current_multiplier)
            
            # Test loss alerts  
            await tracker._check_loss_alerts(contract, token_data, current_multiplier)
            
            new_alerts = len(mock_bot.messages) - initial_count
            print(f"✅ {new_alerts} alerts would be sent")
            
        else:
            print("❌ Cannot calculate multiplier - no confirmed scan mcap")
    
    print(f"\n📊 SUMMARY:")
    print(f"Total alerts that would be sent: {len(mock_bot.messages)}")
    
    if len(mock_bot.messages) == 0:
        print("\n🤔 NO ALERTS TRIGGERED - POSSIBLE REASONS:")
        print("1. Tokens haven't moved enough to trigger alerts")
        print("2. Alerts have already been sent (check sent_alerts)")
        print("3. confirmed_scan_mcap is missing or zero")
        print("4. Token tracker isn't running in live bot")
        print("5. API not returning valid price data")
    
    await api.close()

if __name__ == "__main__":
    asyncio.run(diagnose_alert_system())
