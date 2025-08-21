"""
RAILWAY TOKEN EXTRACTOR - Add this to your Railway main.py
This will create a /export command to get current tokens from The Hunted group
"""

# STEP 1: Add this import at the top of your Railway main.py
from telegram.ext import CommandHandler
import sqlite3
import json
from datetime import datetime

# STEP 2: Add this function to your Railway main.py

async def export_hunted_tokens(update, context):
    """Export current tokens from The Hunted group."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
    # Only work in The Hunted group or for admin users
    if update.effective_chat.id != THE_HUNTED_GROUP_ID:
        # Allow your admin user to export from anywhere
        admin_users = [7510364133]  # Replace with your Telegram user ID
        if update.effective_user.id not in admin_users:
            await update.message.reply_text("❌ This command only works in The Hunted group.")
            return
    
    try:
        # Connect to Railway database
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        # Get all tokens for The Hunted group
        query = """
            SELECT contract_address, symbol, name, initial_mcap, current_mcap,
                   initial_price, current_price, detected_at, last_updated,
                   platform, is_active, multipliers_alerted
            FROM tokens 
            WHERE chat_id = ?
            ORDER BY detected_at DESC
        """
        
        cursor.execute(query, (THE_HUNTED_GROUP_ID,))
        tokens = cursor.fetchall()
        conn.close()
        
        if not tokens:
            await update.message.reply_text("📊 No tokens currently tracked in The Hunted group.")
            return
        
        # Count active tokens
        active_tokens = [t for t in tokens if t[10]]  # is_active is index 10
        
        # Create summary message
        message = f"🎯 **THE HUNTED - CURRENT TOKENS**\\n\\n"
        message += f"📊 Total: {len(tokens)} tokens\\n"
        message += f"🟢 Active: {len(active_tokens)} tokens\\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S UTC')}\\n\\n"
        
        # Show each token
        for i, token in enumerate(tokens, 1):
            (contract, symbol, name, initial_mcap, current_mcap,
             initial_price, current_price, detected_at, last_updated,
             platform, is_active, multipliers_alerted) = token
            
            # Calculate performance
            performance = 0
            if initial_mcap and current_mcap and initial_mcap > 0:
                performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
            
            # Status icons
            if not is_active:
                status = "🔴 REMOVED"
            elif performance > 100:
                status = "🚀 MOON"
            elif performance > 50:
                status = "📈 PUMP"
            elif performance > 0:
                status = "🟢 UP"
            elif performance > -20:
                status = "🟡 DOWN"
            else:
                status = "📉 DUMP"
            
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
        
        # Send remaining message
        if message:
            await update.message.reply_text(message, parse_mode='Markdown')
        
        # Create JSON export
        export_data = {
            "group_id": THE_HUNTED_GROUP_ID,
            "group_name": "The Hunted",
            "export_time": datetime.now().isoformat(),
            "total_tokens": len(tokens),
            "active_tokens": len(active_tokens),
            "tokens": []
        }
        
        for token in tokens:
            export_data["tokens"].append({
                "contract_address": token[0],
                "symbol": token[1],
                "name": token[2],
                "initial_mcap": token[3],
                "current_mcap": token[4],
                "performance_percent": round(((token[4] - token[3]) / token[3] * 100) if token[3] and token[4] else 0, 2),
                "platform": token[9],
                "is_active": bool(token[10]),
                "detected_at": token[7],
                "last_updated": token[8]
            })
        
        # Save export file
        export_filename = f"hunted_tokens_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        await update.message.reply_text(f"💾 Full export saved as: `{export_filename}`", parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Export failed: {str(e)}")
        print(f"Export error: {e}")

# STEP 3: Add this line to your command handlers section in main.py:
# application.add_handler(CommandHandler("export", export_hunted_tokens))

print("""
🎯 RAILWAY TOKEN EXTRACTOR READY!
===============================================

TO GET CURRENT TOKENS FROM RAILWAY:

1. Copy the export_hunted_tokens function above
2. Add it to your Railway main.py
3. Add the command handler line at the bottom
4. Deploy to Railway
5. Go to The Hunted group and send: /export

This will show all current tokens being tracked!

🚀 Alternative: Deploy the enhanced system directly
   All existing tokens will be preserved and get 5s updates!
""")
