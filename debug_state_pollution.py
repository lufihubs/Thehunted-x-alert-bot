#!/usr/bin/env python3
"""
Debug State Pollution in Flow Test
Check if the multiplier alert phase affects loss alert phase.
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from token_tracker_enhanced import TokenTracker
import config

class StatePollutionBot:
    """Bot for debugging state pollution"""
    def __init__(self):
        self.phase_alerts = {'multiplier': [], 'loss': []}
        self.current_phase = 'multiplier'
    
    def set_phase(self, phase):
        self.current_phase = phase
    
    async def send_message(self, chat_id, text, parse_mode=None):
        alert_type = 'multiplier' if 'MULTIPLIER' in text else 'loss' if 'LOSS' in text else 'other'
        
        alert = {
            'group': chat_id,
            'text': text,
            'type': alert_type,
            'phase': self.current_phase
        }
        
        self.phase_alerts[self.current_phase].append(alert)
        print(f"📱 {alert_type.upper()} alert in {self.current_phase} phase → Group {chat_id}")

class StateMockAPI:
    """Mock API for state testing"""
    def __init__(self):
        self.responses = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def set_token_data(self, contract_address, market_cap, price):
        self.responses[contract_address] = {
            'market_cap': market_cap,
            'price': price,
            'symbol': 'STATE',
            'name': 'State Test Token'
        }
    
    async def get_token_info(self, contract_address):
        return self.responses.get(contract_address, {})

async def debug_state_pollution():
    """Debug if multiplier phase pollutes loss phase"""
    print("🔍 Debugging State Pollution Between Phases")
    print("=" * 55)
    
    try:
        # Setup
        test_bot = StatePollutionBot()
        tracker = TokenTracker(test_bot)
        mock_api = StateMockAPI()
        
        # Setup groups and token
        groups = [-1001111111111, -1001111111112, -1001111111113]
        test_token = "StatePollutionTest"
        initial_mcap = 10000000  # $10M
        
        print(f"📋 Setup:")
        print(f"   Token: {test_token}")
        print(f"   Groups: {len(groups)} groups")
        print(f"   Initial: ${initial_mcap:,.0f}")
        print()
        
        # Add token to all groups
        print("1️⃣ Setting up token in all groups...")
        for i, group_id in enumerate(groups, 1):
            tracker.tracking_tokens_by_group[group_id] = {
                test_token: {
                    'name': 'State Test Token',
                    'symbol': 'STATE',
                    'initial_price': 0.01,
                    'initial_mcap': initial_mcap,
                    'confirmed_scan_mcap': initial_mcap,
                    'current_price': 0.01,
                    'current_mcap': initial_mcap,
                    'highest_mcap': initial_mcap,
                    'lowest_mcap': initial_mcap,
                    'chat_id': group_id,
                    'message_id': i,
                    'last_updated': datetime.now(),
                    'current_loss_percentage': 0.0
                }
            }
            print(f"   ✅ Group {i}: Token added")
        
        # Patch API
        import token_tracker_enhanced
        original_api = token_tracker_enhanced.SolanaAPI
        token_tracker_enhanced.SolanaAPI = lambda: mock_api
        
        print("\n2️⃣ PHASE 1: Testing multiplier alerts...")
        test_bot.set_phase('multiplier')
        
        # Set 3x price
        multiplier_mcap = 30000000  # $30M (3x)
        mock_api.set_token_data(test_token, multiplier_mcap, 0.03)
        
        # Run monitoring for first group
        group_tokens = tracker.tracking_tokens_by_group[groups[0]]
        await tracker._check_group_tokens(groups[0], group_tokens)
        
        multiplier_alerts = test_bot.phase_alerts['multiplier']
        print(f"   📊 Multiplier alerts sent: {len(multiplier_alerts)}")
        
        # Check token state after multiplier phase
        print(f"\n   🔍 Token state after multiplier phase:")
        for i, group_id in enumerate(groups, 1):
            token_data = tracker.tracking_tokens_by_group[group_id][test_token]
            sent_alerts = token_data.get('loss_alerts_sent', '[]')
            print(f"      Group {i}: mcap=${token_data['current_mcap']:,.0f}, loss_alerts_sent={sent_alerts}")
        
        print("\n3️⃣ PHASE 2: Testing loss alerts...")
        test_bot.set_phase('loss')
        
        # Set major loss
        loss_mcap = 2000000  # $2M (-80% from original $10M)
        mock_api.set_token_data(test_token, loss_mcap, 0.002)
        
        # Check token state BEFORE loss phase
        print(f"   🔍 Token state BEFORE loss processing:")
        for i, group_id in enumerate(groups, 1):
            token_data = tracker.tracking_tokens_by_group[group_id][test_token]
            baseline = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
            current = token_data['current_mcap']
            loss_pct = ((current - baseline) / baseline) * 100 if baseline > 0 else 0
            sent_alerts = token_data.get('loss_alerts_sent', '[]')
            
            print(f"      Group {i}: baseline=${baseline:,.0f}, current=${current:,.0f}")
            print(f"               loss={loss_pct:.1f}%, sent_alerts={sent_alerts}")
        
        # Run monitoring for second group
        group_tokens = tracker.tracking_tokens_by_group[groups[1]]
        await tracker._check_group_tokens(groups[1], group_tokens)
        
        loss_alerts = test_bot.phase_alerts['loss']
        print(f"\n   📊 Loss alerts sent: {len(loss_alerts)}")
        
        # Check final token state
        print(f"\n   🔍 Token state AFTER loss processing:")
        for i, group_id in enumerate(groups, 1):
            token_data = tracker.tracking_tokens_by_group[group_id][test_token]
            baseline = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
            current = token_data['current_mcap']
            loss_pct = ((current - baseline) / baseline) * 100 if baseline > 0 else 0
            sent_alerts = token_data.get('loss_alerts_sent', '[]')
            
            print(f"      Group {i}: baseline=${baseline:,.0f}, current=${current:,.0f}")
            print(f"               loss={loss_pct:.1f}%, sent_alerts={sent_alerts}")
        
        # Restore API
        token_tracker_enhanced.SolanaAPI = original_api
        
        # Analysis
        print(f"\n📊 ANALYSIS:")
        print(f"   Multiplier phase alerts: {len(multiplier_alerts)}")
        print(f"   Loss phase alerts: {len(loss_alerts)}")
        
        if len(loss_alerts) == 0:
            print(f"   ❌ PROBLEM: No loss alerts in phase 2")
            print(f"   💡 Possible causes:")
            print(f"      - State pollution from phase 1")
            print(f"      - Incorrect baseline calculation")
            print(f"      - Alert cooldown interference")
            print(f"      - Shared alert state between groups")
        else:
            print(f"   ✅ Loss alerts working correctly")
        
        return len(loss_alerts) > 0
        
    except Exception as e:
        print(f"\n❌ STATE DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run state pollution debugging"""
    print("🔧 State Pollution Debug Session")
    print("=" * 40)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    success = await debug_state_pollution()
    
    print("\n" + "=" * 55)
    if success:
        print("✅ No state pollution - loss alerts work after multiplier alerts")
    else:
        print("❌ State pollution detected - multiplier phase affects loss phase")
        print("💡 Need to investigate alert state management")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
