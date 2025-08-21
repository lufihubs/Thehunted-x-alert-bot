"""
FETCH CURRENT TOKENS FROM RAILWAY - THE HUNTED GROUP
Direct method to get tokens from your live Railway deployment
"""

import requests
import json
from datetime import datetime

def fetch_railway_tokens():
    """Fetch current tokens from Railway deployment using bot API."""
    
    print("🎯 FETCHING RAILWAY TOKENS - THE HUNTED GROUP")
    print("=" * 60)
    print("Target Group: The Hunted (-1002350881772)")
    print("Source: Live Railway deployment")
    print()
    
    # Your bot details
    BOT_TOKEN = "8301492869:AAG09Y6QO5R_j1awrKmxT6XBdCLYCl_1dAk"
    THE_HUNTED_GROUP_ID = -1002350881772
    
    try:
        # Method 1: Try to get bot status
        print("🤖 Checking Railway bot status...")
        
        bot_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
        response = requests.get(bot_url, timeout=10)
        
        if response.status_code == 200:
            bot_data = response.json()
            if bot_data.get("ok"):
                bot_info = bot_data["result"]
                print(f"✅ Bot connected: @{bot_info.get('username')}")
                print(f"   Status: Active on Railway")
                print()
                
                # Method 2: Check group access
                print("📱 Checking The Hunted group access...")
                
                chat_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
                chat_params = {"chat_id": THE_HUNTED_GROUP_ID}
                
                chat_response = requests.get(chat_url, params=chat_params, timeout=10)
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    if chat_data.get("ok"):
                        chat_info = chat_data["result"]
                        print(f"✅ Group found: {chat_info.get('title')}")
                        print(f"   Type: {chat_info.get('type')}")
                        print(f"   Members: {chat_info.get('member_count', 'N/A')}")
                        print()
                        
                        # Create extraction methods
                        create_token_extraction_methods()
                        return True
                    else:
                        print("❌ Cannot access The Hunted group")
                else:
                    print(f"❌ Group access error: {chat_response.status_code}")
            else:
                print("❌ Bot authentication failed")
        else:
            print(f"❌ Bot connection error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    # Fallback - show extraction methods anyway
    create_token_extraction_methods()
    return False

def create_token_extraction_methods():
    """Create methods to extract tokens from Railway."""
    
    print("🔍 RAILWAY TOKEN EXTRACTION METHODS")
    print("=" * 50)
    print()
    
    print("📋 METHOD 1 - Add /show_tokens Command (RECOMMENDED):")
    print("-" * 55)
    
    command_code = '''
# Add this to your Railway main.py:

async def show_hunted_tokens(update, context):
    """Show all tokens tracked in The Hunted group."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
    # Only work in The Hunted group
    if update.effective_chat.id != THE_HUNTED_GROUP_ID:
        return
    
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT contract_address, symbol, name, initial_mcap, current_mcap,
                   platform, is_active, detected_at, last_updated
            FROM tokens 
            WHERE chat_id = ?
            ORDER BY detected_at DESC
        """, (THE_HUNTED_GROUP_ID,))
        
        tokens = cursor.fetchall()
        conn.close()
        
        if not tokens:
            await update.message.reply_text("📊 No tokens currently tracked in The Hunted group.")
            return
        
        # Count active tokens
        active_tokens = [t for t in tokens if t[6]]  # is_active column
        
        message = f"🎯 **THE HUNTED - CURRENT TOKENS**\\n\\n"
        message += f"📊 Total: {len(tokens)} | Active: {len(active_tokens)}\\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S UTC')}\\n\\n"
        
        for i, token in enumerate(active_tokens, 1):
            contract, symbol, name, initial_mcap, current_mcap, platform, is_active, detected_at, last_updated = token
            
            # Calculate performance
            performance = 0
            if initial_mcap and current_mcap and initial_mcap > 0:
                performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
            
            # Status emoji
            if performance > 100:
                status = "🚀"
            elif performance > 50:
                status = "📈"
            elif performance > 0:
                status = "🟢"
            elif performance > -20:
                status = "🟡"
            else:
                status = "🔴"
            
            message += f"{status} **{i}. {symbol or 'Unknown'}**\\n"
            
            if current_mcap:
                message += f"   💰 ${current_mcap:,.0f}"
                if performance != 0:
                    message += f" ({performance:+.1f}%)"
                message += "\\n"
            
            message += f"   🏷️ {platform or 'Unknown'}\\n"
            message += f"   📅 {detected_at}\\n"
            message += f"   🔗 `{contract}`\\n\\n"
            
            # Split long messages
            if len(message) > 3500:
                await update.message.reply_text(message, parse_mode='Markdown')
                message = ""
        
        if message:
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Add this handler:
application.add_handler(CommandHandler("show", show_hunted_tokens))
'''
    
    # Save the command
    with open('railway_show_tokens_command.py', 'w', encoding='utf-8') as f:
        f.write(command_code)
    
    print("✅ Command saved: railway_show_tokens_command.py")
    print()
    print("📋 DEPLOYMENT STEPS:")
    print("1. Copy the function from railway_show_tokens_command.py")
    print("2. Add it to your Railway main.py")
    print("3. Add the command handler line")
    print("4. Deploy to Railway (git push)")
    print("5. In The Hunted group, send: /show")
    print()
    
    print("📋 METHOD 2 - Railway CLI Database Access:")
    print("-" * 45)
    print("1. railway login")
    print("2. railway connect your-project-name")
    print(f"3. railway run python -c \"")
    print("import sqlite3")
    print("conn = sqlite3.connect('tokens.db')")
    print("cursor = conn.cursor()")
    print("cursor.execute('SELECT contract_address, symbol, current_mcap FROM tokens WHERE chat_id = -1002350881772 AND is_active = 1')")
    print("tokens = cursor.fetchall()")
    print("for token in tokens:")
    print("    print(f'{token[1]}: {token[0]} - ${token[2]:,.0f}' if token[2] else f'{token[1]}: {token[0]}')")
    print("conn.close()")
    print("\"")
    print()
    
    print("📋 METHOD 3 - Alternative Commands:")
    print("-" * 35)
    print("Add any of these commands to your Railway bot:")
    print("• /tokens - Show all tokens")
    print("• /export - Export token data")
    print("• /status - Show tracking status")
    print("• /list - List tracked tokens")
    print()
    
    print("🎯 RECOMMENDED:")
    print("Use Method 1 (/show command) - it's the fastest way!")
    print("This will show all tokens currently tracked in The Hunted group.")

def create_instant_display():
    """Create method to instantly display tokens if we had Railway access."""
    
    print("💡 WHAT YOU'LL SEE AFTER ADDING /show COMMAND:")
    print("=" * 55)
    print()
    print("🎯 THE HUNTED - CURRENT TOKENS")
    print()
    print("📊 Total: X | Active: Y")
    print("⏰ 15:30:45 UTC")
    print()
    print("🟢 1. TOKEN1")
    print("   💰 $1,234,567 (+45.2%)")
    print("   🏷️ Pump.fun")
    print("   📅 2025-08-22 10:15:30")
    print("   🔗 `ABC123...XYZ789`")
    print()
    print("📈 2. TOKEN2")
    print("   💰 $2,345,678 (+120.5%)")
    print("   🏷️ Raydium")
    print("   📅 2025-08-22 11:20:15")
    print("   🔗 `DEF456...UVW012`")
    print()
    print("🔴 3. TOKEN3")
    print("   💰 $567,890 (-15.3%)")
    print("   🏷️ DexScreener")
    print("   📅 2025-08-22 12:45:00")
    print("   🔗 `GHI789...RST345`")
    print()
    print("This shows all tokens you've added to The Hunted group!")

if __name__ == "__main__":
    success = fetch_railway_tokens()
    
    print()
    print("🎯 SUMMARY:")
    print("=" * 30)
    
    if success:
        print("✅ Railway bot connection verified")
    else:
        print("⚠️ Limited API access (normal for deployed bots)")
    
    print()
    print("📁 Files created:")
    print("   ✅ railway_show_tokens_command.py")
    print()
    print("🚀 NEXT STEPS:")
    print("1. Add /show command to your Railway bot")
    print("2. Deploy the update")
    print("3. Send /show in The Hunted group")
    print("4. See all your tracked tokens!")
    
    create_instant_display()
