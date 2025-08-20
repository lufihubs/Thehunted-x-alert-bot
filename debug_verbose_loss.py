#!/usr/bin/env python3
"""
Debug Loss Alert with Detailed Logging
Add debug prints to understand exactly what's happening with loss alerts.
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

class VerboseTestBot:
    """Bot that provides verbose output"""
    def __init__(self):
        self.messages = []
    
    async def send_message(self, chat_id, text, parse_mode=None):
        self.messages.append({'group': chat_id, 'text': text})
        print(f"🚨 LOSS ALERT SENT to Group {chat_id}")
        print(f"   📝 {text[:80]}...")

# Monkey patch the loss alert method to add debug output
original_check_loss_alerts = TokenTracker._check_loss_alerts_for_group

async def debug_check_loss_alerts_for_group(self, contract_address: str, token_data: dict, chat_id: int):
    """Debug version of loss alert checking"""
    print(f"\n🔍 DEBUG: Checking loss alerts for {contract_address} in group {chat_id}")
    
    try:
        baseline_mcap = token_data.get('confirmed_scan_mcap') or token_data['initial_mcap']
        current_mcap = token_data['current_mcap']
        
        print(f"   📊 Baseline: ${baseline_mcap:,.0f}")
        print(f"   📊 Current: ${current_mcap:,.0f}")
        
        if baseline_mcap <= 0:
            print(f"   ❌ Baseline is {baseline_mcap}, skipping")
            return
        
        loss_percentage = ((current_mcap - baseline_mcap) / baseline_mcap) * 100
        print(f"   📉 Loss percentage: {loss_percentage:.1f}%")
        
        # Check alert cooldown
        cooldown = self._is_alert_on_cooldown(contract_address, chat_id, 'loss')
        print(f"   ⏰ On cooldown: {cooldown}")
        if cooldown:
            print(f"   ❌ Skipping due to cooldown")
            return
        
        # Load sent loss alerts
        try:
            sent_loss_alerts_str = token_data.get('loss_alerts_sent', '[]')
            sent_loss_alerts = json.loads(sent_loss_alerts_str)
            print(f"   📝 Sent alerts: {sent_loss_alerts}")
        except Exception as e:
            print(f"   ❌ Error parsing sent alerts: {e}")
            sent_loss_alerts = []
        
        # Check which loss alerts should be sent
        print(f"   🎯 Checking thresholds: {config.Config.LOSS_THRESHOLDS}")
        triggered = []
        
        for threshold in config.Config.LOSS_THRESHOLDS:
            should_trigger = loss_percentage <= threshold
            already_sent = threshold in sent_loss_alerts
            
            print(f"      {threshold}%: loss={loss_percentage:.1f} <= {threshold} = {should_trigger}, sent={already_sent}")
            
            if should_trigger and not already_sent:
                triggered.append(threshold)
                print(f"         ✅ WILL TRIGGER {threshold}% alert")
                
                # Send loss alert
                await self._send_loss_alert(
                    contract_address, token_data, chat_id, threshold, loss_percentage
                )
                
                # Mark as sent
                sent_loss_alerts.append(threshold)
                token_data['loss_alerts_sent'] = json.dumps(sent_loss_alerts)
                
                # Update database
                await self._update_loss_alerts_db(contract_address, sent_loss_alerts)
                
                # Set cooldown
                self._set_alert_cooldown(contract_address, chat_id, 'loss')
            elif already_sent:
                print(f"         ❌ Already sent {threshold}% alert")
            else:
                print(f"         ❌ {threshold}% not triggered")
        
        print(f"   📊 Total triggered: {len(triggered)} alerts")
        
    except Exception as e:
        print(f"   ❌ Error in loss alert checking: {e}")
        import traceback
        traceback.print_exc()

# Apply the monkey patch
TokenTracker._check_loss_alerts_for_group = debug_check_loss_alerts_for_group

async def test_loss_alert_debugging():
    """Test loss alerts with detailed debugging"""
    print("🔍 Loss Alert Debugging Session")
    print("=" * 45)
    
    try:
        # Setup
        test_bot = VerboseTestBot()
        tracker = TokenTracker(test_bot)
        
        # Simple test case
        test_group = -1001234567890
        test_token = "DebugLossToken"
        initial_mcap = 5000000   # $5M
        current_mcap = 1000000   # $1M (-80% loss)
        
        print(f"📋 Debug Setup:")
        print(f"   Token: {test_token}")
        print(f"   Group: {test_group}")
        print(f"   Initial: ${initial_mcap:,.0f}")
        print(f"   Current: ${current_mcap:,.0f}")
        print(f"   Expected Loss: {((current_mcap - initial_mcap) / initial_mcap) * 100:.1f}%")
        print()
        
        # Set up token data
        tracker.tracking_tokens_by_group[test_group] = {
            test_token: {
                'name': 'Debug Loss Token',
                'symbol': 'DLT',
                'initial_price': 0.005,
                'initial_mcap': initial_mcap,
                'confirmed_scan_mcap': initial_mcap,
                'current_price': 0.001,
                'current_mcap': current_mcap,
                'highest_mcap': initial_mcap,
                'lowest_mcap': current_mcap,
                'chat_id': test_group,
                'message_id': 1,
                'last_updated': datetime.now(),
                'current_loss_percentage': -80.0
            }
        }
        
        # Test the cross-group alert method
        print("🚀 Testing cross-group alert method...")
        await tracker._check_alerts_across_all_groups(test_token, current_mcap, 0.001)
        
        print(f"\n📊 Results:")
        print(f"   Messages sent: {len(test_bot.messages)}")
        
        for i, msg in enumerate(test_bot.messages, 1):
            print(f"   {i}. Group {msg['group']}: {msg['text'][:60]}...")
        
        return len(test_bot.messages) > 0
        
    except Exception as e:
        print(f"\n❌ DEBUG TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run debugging session"""
    print("🔧 Loss Alert Debug Session")
    print("=" * 35)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    success = await test_loss_alert_debugging()
    
    print("\n" + "=" * 45)
    if success:
        print("✅ Loss alerts are working!")
    else:
        print("❌ Loss alerts still have issues - check debug output above")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
