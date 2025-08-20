#!/usr/bin/env python3
"""
Debug Loss Alert Functionality
Tests loss alert logic to identify why alerts aren't being sent.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from token_tracker_enhanced import TokenTracker
import config

class DebugBot:
    """Debug bot that prints detailed info"""
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id, text, parse_mode=None):
        self.messages.append({'chat_id': chat_id, 'text': text})
        print(f"🔔 ALERT SENT to Group {chat_id}")
        print(f"   Message: {text[:100]}...")
        print()

async def debug_loss_alerts():
    """Debug the loss alert functionality"""
    print("🔍 Debugging Loss Alert Functionality")
    print("=" * 45)
    
    # Setup
    debug_bot = DebugBot()
    tracker = TokenTracker(debug_bot)
    
    test_group = -1001234567890
    test_token = "DebugToken123"
    initial_mcap = 1000000  # $1M
    new_mcap = 300000      # $300K (-70% loss)
    
    print(f"📋 Debug Setup:")
    print(f"   Token: {test_token}")
    print(f"   Group: {test_group}")
    print(f"   Initial: ${initial_mcap:,.0f}")
    print(f"   New: ${new_mcap:,.0f}")
    print(f"   Loss: {((new_mcap - initial_mcap) / initial_mcap) * 100:.1f}%")
    print(f"   Loss Thresholds: {config.Config.LOSS_THRESHOLDS}")
    print()
    
    # Setup token
    tracker.tracking_tokens_by_group[test_group] = {
        test_token: {
            'name': 'Debug Token',
            'symbol': 'DEBUG',
            'initial_price': 0.001,
            'initial_mcap': initial_mcap,
            'confirmed_scan_mcap': initial_mcap,
            'current_price': 0.0003,
            'current_mcap': new_mcap,
            'highest_mcap': initial_mcap,
            'lowest_mcap': new_mcap,
            'chat_id': test_group,
            'message_id': 1,
            'last_updated': datetime.now(),
            'current_loss_percentage': -70.0  # Pre-calculated
        }
    }
    
    print("1️⃣ Manually testing loss alert logic...")
    
    # Get token data
    token_data = tracker.tracking_tokens_by_group[test_group][test_token]
    
    # Calculate loss percentage
    baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
    current_mcap = token_data['current_mcap']
    loss_percentage = ((current_mcap - baseline_mcap) / baseline_mcap) * 100
    
    print(f"   📊 Calculated loss: {loss_percentage:.1f}%")
    print(f"   📊 Baseline: ${baseline_mcap:,.0f}")
    print(f"   📊 Current: ${current_mcap:,.0f}")
    
    # Check cooldown
    cooldown_check = tracker._is_alert_on_cooldown(test_token, test_group, 'loss')
    print(f"   ⏰ Alert on cooldown: {cooldown_check}")
    
    # Check which thresholds should trigger
    print(f"   🎯 Checking thresholds:")
    triggered_thresholds = []
    for threshold in config.Config.LOSS_THRESHOLDS:
        should_trigger = loss_percentage <= threshold
        print(f"      {threshold}%: {'✅ SHOULD TRIGGER' if should_trigger else '❌ No trigger'}")
        if should_trigger:
            triggered_thresholds.append(threshold)
    
    print(f"   📋 Should trigger: {triggered_thresholds}")
    
    # Check sent alerts
    sent_loss_alerts = token_data.get('loss_alerts_sent', '[]')
    print(f"   📝 Sent alerts JSON: {sent_loss_alerts}")
    
    try:
        import json
        sent_list = json.loads(sent_loss_alerts)
        print(f"   📝 Sent alerts parsed: {sent_list}")
    except Exception as e:
        print(f"   ❌ Error parsing sent alerts: {e}")
        sent_list = []
    
    print("\n2️⃣ Testing loss alert method directly...")
    
    # Call the loss alert method directly
    try:
        await tracker._check_loss_alerts_for_group(test_token, token_data, test_group)
        print(f"   ✅ Loss alert method completed")
    except Exception as e:
        print(f"   ❌ Error in loss alert method: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n3️⃣ Results:")
    print(f"   📧 Messages sent: {len(debug_bot.messages)}")
    
    for i, msg in enumerate(debug_bot.messages, 1):
        print(f"      {i}. Group {msg['chat_id']}: {msg['text'][:50]}...")
    
    if len(debug_bot.messages) == 0:
        print("   ❌ NO ALERTS SENT - Investigating why...")
        
        # Additional debugging
        print(f"\n🔍 Additional Debug Info:")
        print(f"   - Loss percentage: {loss_percentage}")
        print(f"   - Should trigger -30%: {loss_percentage <= -30}")
        print(f"   - Should trigger -50%: {loss_percentage <= -50}")
        print(f"   - Should trigger -70%: {loss_percentage <= -70}")
        print(f"   - Cooldown active: {cooldown_check}")
        print(f"   - Sent alerts: {sent_list}")
    
    return len(debug_bot.messages) > 0

async def main():
    """Run loss alert debugging"""
    print("🔧 Loss Alert Debug Session")
    print("=" * 35)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    success = await debug_loss_alerts()
    
    print("\n" + "=" * 45)
    if success:
        print("✅ Loss alerts are working!")
    else:
        print("❌ Loss alerts are NOT working - debug info above shows why")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
