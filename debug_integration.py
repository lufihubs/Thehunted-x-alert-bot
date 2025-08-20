#!/usr/bin/env python3
"""
Debug Cross-Group Alert Integration
Tests the _check_alerts_across_all_groups method specifically.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from token_tracker_enhanced import TokenTracker
import config

class IntegrationDebugBot:
    """Bot for debugging integration issues"""
    def __init__(self):
        self.alerts = []
    
    async def send_message(self, chat_id, text, parse_mode=None):
        self.alerts.append({
            'group': chat_id,
            'text': text,
            'type': 'multiplier' if 'MULTIPLIER' in text else 'loss' if 'LOSS' in text else 'rug' if 'RUG' in text else 'unknown'
        })
        print(f"📱 Alert to Group {chat_id}: {text[:60]}...")

async def debug_cross_group_integration():
    """Debug the cross-group alert integration"""
    print("🔍 Debugging Cross-Group Alert Integration")
    print("=" * 50)
    
    try:
        # Setup
        debug_bot = IntegrationDebugBot()
        tracker = TokenTracker(debug_bot)
        
        # Setup multiple groups with same token
        groups = [-1001111111111, -1001111111112, -1001111111113]
        test_token = "IntegrationTest123"
        initial_mcap = 2000000  # $2M
        loss_mcap = 600000     # $600K (-70% loss)
        
        print(f"📋 Setup:")
        print(f"   Token: {test_token}")
        print(f"   Groups: {groups}")
        print(f"   Initial: ${initial_mcap:,.0f}")
        print(f"   Loss Target: ${loss_mcap:,.0f} (-70%)")
        print()
        
        # Add token to all groups
        print("1️⃣ Setting up token in all groups...")
        for i, group_id in enumerate(groups, 1):
            tracker.tracking_tokens_by_group[group_id] = {
                test_token: {
                    'name': 'Integration Test Token',
                    'symbol': 'ITT',
                    'initial_price': 0.002,
                    'initial_mcap': initial_mcap,
                    'confirmed_scan_mcap': initial_mcap,
                    'current_price': 0.002,
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
        
        # Test the cross-group alert method directly
        print("\n2️⃣ Testing _check_alerts_across_all_groups...")
        
        try:
            await tracker._check_alerts_across_all_groups(test_token, loss_mcap, 0.0006)
            print(f"   ✅ Cross-group alert method completed")
        except Exception as e:
            print(f"   ❌ Error in cross-group method: {e}")
            import traceback
            traceback.print_exc()
        
        # Check results
        print(f"\n3️⃣ Results Analysis:")
        print(f"   📧 Total alerts sent: {len(debug_bot.alerts)}")
        
        # Group by type
        alert_types = {}
        for alert in debug_bot.alerts:
            alert_type = alert['type']
            if alert_type not in alert_types:
                alert_types[alert_type] = []
            alert_types[alert_type].append(alert)
        
        for alert_type, alerts in alert_types.items():
            print(f"   📊 {alert_type.title()} alerts: {len(alerts)}")
            
            # Check distribution across groups
            groups_with_alerts = set(alert['group'] for alert in alerts)
            print(f"      Groups: {len(groups_with_alerts)}/{len(groups)} received alerts")
            
            for group in groups:
                group_alerts = [a for a in alerts if a['group'] == group]
                status = "✅" if group_alerts else "❌"
                print(f"         {status} Group {group}: {len(group_alerts)} alert(s)")
        
        # Check token data after update
        print(f"\n4️⃣ Token Data Verification:")
        for i, group_id in enumerate(groups, 1):
            token_data = tracker.tracking_tokens_by_group[group_id][test_token]
            current_mcap = token_data['current_mcap']
            loss_pct = token_data.get('current_loss_percentage', 'N/A')
            print(f"   Group {i}: ${current_mcap:,.0f} (Loss: {loss_pct}%)")
        
        success = len(debug_bot.alerts) > 0 and len(set(alert['group'] for alert in debug_bot.alerts)) == len(groups)
        
        return success
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run integration debugging"""
    print("🔧 Cross-Group Alert Integration Debug")
    print("=" * 45)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    success = await debug_cross_group_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Cross-group alert integration is working!")
    else:
        print("❌ Cross-group alert integration has issues")
        print("💡 Check the debug output above for details")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
