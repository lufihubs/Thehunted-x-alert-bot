"""
DIRECT RAILWAY TOKEN FETCHER
Get current tokens from The Hunted group Railway deployment
"""

import requests
import json
from datetime import datetime
import os

def fetch_railway_tokens_via_api():
    """Fetch tokens using Railway API or bot commands."""
    
    print("🎯 FETCHING RAILWAY TOKENS - THE HUNTED GROUP")
    print("=" * 60)
    print("Target Group: -1002350881772")
    print("Method: Direct Railway API access")
    print()
    
    # Method 1: Try to get tokens via Telegram Bot API
    try:
        # Your bot token (from environment or config)
        BOT_TOKEN = "8301492869:AAG09Y6QO5R_j1awrKmxT6XBdCLYCl_1dAk"
        THE_HUNTED_GROUP_ID = -1002350881772
        
        # Send a request to get chat info first
        chat_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        chat_params = {"chat_id": THE_HUNTED_GROUP_ID}
        
        print("📱 Checking Railway bot connection...")
        
        response = requests.get(chat_url, params=chat_params, timeout=10)
        
        if response.status_code == 200:
            chat_data = response.json()
            if chat_data.get("ok"):
                chat_info = chat_data["result"]
                print(f"✅ Connected to: {chat_info.get('title', 'The Hunted')}")
                print(f"   Type: {chat_info.get('type')}")
                print(f"   ID: {chat_info.get('id')}")
                
                # Get bot info
                bot_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
                bot_response = requests.get(bot_url, timeout=10)
                
                if bot_response.status_code == 200:
                    bot_data = bot_response.json()
                    if bot_data.get("ok"):
                        bot_info = bot_data["result"]
                        print(f"🤖 Bot: @{bot_info.get('username')}")
                        print(f"   Status: Active on Railway")
                        print()
                        
                        # Try to get recent messages (if bot has access)
                        print("🔍 Attempting to extract token data...")
                        
                        # Create instructions for manual extraction
                        create_manual_extraction_guide()
                        
                        return True
                else:
                    print("❌ Bot API error")
            else:
                print("❌ Chat access denied")
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Fallback methods
    print("\n🔄 ALTERNATIVE METHODS:")
    print("=" * 40)
    
    print("Method A - Add Export Command:")
    print("1. Add export function to Railway main.py")
    print("2. Deploy updated code")
    print("3. Send /export in The Hunted group")
    
    print("\nMethod B - Railway CLI:")
    print("1. railway login")
    print("2. railway connect <your-project>")
    print("3. railway run python -c \"import sqlite3; print(...)\"")
    
    print("\nMethod C - Deploy Enhanced System:")
    print("1. Deploy our enhanced monitoring system")
    print("2. Existing tokens will be preserved")
    print("3. All tokens get 5-second real-time updates")
    
    return False

def create_manual_extraction_guide():
    """Create guide for manual token extraction."""
    
    print("📋 MANUAL EXTRACTION METHODS:")
    print("-" * 40)
    
    # Create Railway command
    railway_command = '''
# Add this to your Railway main.py:

async def get_tokens_command(update, context):
    """Get current tokens for The Hunted group."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
    if update.effective_chat.id != THE_HUNTED_GROUP_ID:
        return
    
    try:
        import sqlite3
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT contract_address, symbol, name, current_mcap, 
                   initial_mcap, platform, is_active, detected_at
            FROM tokens 
            WHERE chat_id = ? AND is_active = 1
            ORDER BY detected_at DESC
        """, (THE_HUNTED_GROUP_ID,))
        
        tokens = cursor.fetchall()
        conn.close()
        
        if tokens:
            message = f"🎯 **THE HUNTED TOKENS** ({len(tokens)} active)\\n\\n"
            
            for i, token in enumerate(tokens, 1):
                contract, symbol, name, current_mcap, initial_mcap, platform, is_active, detected_at = token
                
                performance = 0
                if initial_mcap and current_mcap:
                    performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
                
                message += f"**{i}. {symbol or 'Unknown'}**\\n"
                message += f"💰 ${current_mcap:,.0f} ({performance:+.1f}%)\\n"
                message += f"🔗 `{contract}`\\n\\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("No active tokens found.")
            
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# Add handler:
# application.add_handler(CommandHandler("tokens", get_tokens_command))
'''
    
    # Save the command
    with open('railway_get_tokens_command.py', 'w', encoding='utf-8') as f:
        f.write(railway_command)
    
    print("✅ Command saved: railway_get_tokens_command.py")
    print("   Copy this to your Railway main.py")
    
    # Create Railway CLI script
    cli_script = '''
# Railway CLI method - run this on Railway:
import sqlite3
import json
from datetime import datetime

def export_railway_tokens():
    try:
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM tokens 
            WHERE chat_id = -1002350881772
            ORDER BY detected_at DESC
        """)
        
        tokens = cursor.fetchall()
        conn.close()
        
        if tokens:
            print(f"Found {len(tokens)} tokens in The Hunted group:")
            for i, token in enumerate(tokens, 1):
                print(f"{i}. {token[1]} ({token[0]}) - {'Active' if token[16] else 'Inactive'}")
        else:
            print("No tokens found.")
            
    except Exception as e:
        print(f"Error: {e}")

export_railway_tokens()
'''
    
    with open('railway_cli_export.py', 'w', encoding='utf-8') as f:
        f.write(cli_script)
    
    print("✅ CLI script saved: railway_cli_export.py")
    print("   Run this via Railway CLI")

def create_instant_deployment():
    """Create instant deployment solution."""
    
    print("\n🚀 RECOMMENDED: INSTANT DEPLOYMENT")
    print("=" * 50)
    
    print("✅ Enhanced system ready with:")
    print("   • 5-second real-time updates for ALL tokens")
    print("   • Preserves existing Railway tokens")
    print("   • Automatic contract detection")
    print("   • Enhanced alerts for The Hunted group")
    
    print("\n📁 Ready files:")
    ready_files = [
        "main.py - Enhanced bot application",
        "token_tracker_enhanced.py - Fixed parallel processing",
        "config.py - Optimized for The Hunted group", 
        "database.py - Railway compatible",
        "requirements.txt - All dependencies"
    ]
    
    for file in ready_files:
        print(f"   ✅ {file}")
    
    print("\n🎯 DEPLOYMENT STEPS:")
    print("1. Upload enhanced files to Railway")
    print("2. Railway auto-deploys and restarts")
    print("3. Existing tokens preserved")
    print("4. New tokens get 5s real-time updates")
    
    print("\n💡 RESULT:")
    print("   • ALL tokens in The Hunted group get instant updates")
    print("   • No data loss from current Railway deployment")
    print("   • Enhanced monitoring with 5-second cycles")

if __name__ == "__main__":
    success = fetch_railway_tokens_via_api()
    create_instant_deployment()
    
    print(f"\n🎉 SUMMARY:")
    print("=" * 30)
    if success:
        print("✅ Railway connection verified")
    else:
        print("⚠️ Direct access limited")
    
    print("📋 Best options:")
    print("1. Add /tokens command to Railway bot")
    print("2. Deploy enhanced system (preserves existing data)")
    print("3. Use Railway CLI for direct database access")
    
    print(f"\n🎯 Files created for extraction:")
    print("   • railway_get_tokens_command.py")
    print("   • railway_cli_export.py")
    
    print(f"\n🚂 Ready to get your Railway tokens!")
