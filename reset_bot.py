#!/usr/bin/env python3
"""
Bot Reset Tool - Clears webhook and resets bot state
"""

import asyncio
import httpx
from config import Config

async def reset_bot():
    """Reset the bot by clearing webhook and getting fresh updates"""
    print("🔄 Resetting bot webhook and clearing conflicts...")
    
    bot_token = Config.TELEGRAM_BOT_TOKEN
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Delete webhook
            print("1️⃣ Deleting webhook...")
            response = await client.post(f"{base_url}/deleteWebhook")
            if response.status_code == 200:
                print("   ✅ Webhook deleted successfully")
            else:
                print(f"   ⚠️  Webhook delete response: {response.status_code}")
            
            # 2. Set webhook to empty (force polling mode)
            print("2️⃣ Setting webhook to empty...")
            response = await client.post(f"{base_url}/setWebhook", json={"url": ""})
            if response.status_code == 200:
                print("   ✅ Webhook cleared successfully")
            else:
                print(f"   ⚠️  Webhook clear response: {response.status_code}")
            
            # 3. Get pending updates and clear them
            print("3️⃣ Clearing pending updates...")
            response = await client.post(f"{base_url}/getUpdates", json={
                "offset": -1,
                "limit": 1,
                "timeout": 0
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result"):
                    # Get the last update ID and set offset to clear all pending
                    last_update = data["result"][-1] if data["result"] else None
                    if last_update:
                        offset = last_update["update_id"] + 1
                        print(f"   🔄 Clearing updates from offset {offset}...")
                        
                        # Clear all pending updates
                        clear_response = await client.post(f"{base_url}/getUpdates", json={
                            "offset": offset,
                            "limit": 100,
                            "timeout": 0
                        })
                        
                        if clear_response.status_code == 200:
                            print("   ✅ Pending updates cleared")
                        else:
                            print(f"   ⚠️  Clear updates response: {clear_response.status_code}")
                    else:
                        print("   ✅ No pending updates to clear")
                else:
                    print("   ✅ No pending updates found")
            else:
                print(f"   ⚠️  Get updates response: {response.status_code}")
            
            # 4. Wait a moment for changes to propagate
            print("4️⃣ Waiting for changes to propagate...")
            await asyncio.sleep(3)
            
            # 5. Test bot connectivity
            print("5️⃣ Testing bot connectivity...")
            response = await client.post(f"{base_url}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    print(f"   ✅ Bot connected: @{bot_info.get('username', 'unknown')}")
                else:
                    print(f"   ❌ Bot test failed: {data}")
            else:
                print(f"   ❌ Bot connectivity test failed: {response.status_code}")
            
            print("\n🎉 Bot reset completed!")
            print("💡 You can now start the bot normally.")
            
        except Exception as e:
            print(f"❌ Error during bot reset: {e}")
            return False
    
    return True

if __name__ == "__main__":
    asyncio.run(reset_bot())
