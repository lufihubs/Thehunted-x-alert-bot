🎯 HOW TO GET CURRENT TOKENS FROM RAILWAY - THE HUNTED GROUP
===============================================================

📊 TARGET: The Hunted Group (-1002350881772)
🤖 YOUR RAILWAY BOT: Live and running

🚀 EASIEST METHOD - Add Export Command:
======================================

STEP 1: Copy this function to your Railway main.py:

```python
async def get_hunted_tokens(update, context):
    """Get current tokens from The Hunted group."""
    
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
                   platform, is_active, detected_at
            FROM tokens 
            WHERE chat_id = ?
            ORDER BY detected_at DESC
        """, (THE_HUNTED_GROUP_ID,))
        
        tokens = cursor.fetchall()
        conn.close()
        
        if tokens:
            message = f"🎯 **THE HUNTED TOKENS**\n\n"
            message += f"📊 Total: {len(tokens)} tokens\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            active_count = 0
            for token in tokens:
                contract, symbol, name, initial_mcap, current_mcap, platform, is_active, detected_at = token
                
                if not is_active:
                    continue
                    
                active_count += 1
                
                # Calculate performance
                performance = 0
                if initial_mcap and current_mcap and initial_mcap > 0:
                    performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
                
                status = "🟢" if performance > 0 else "🔴" if performance < -20 else "🟡"
                
                message += f"{status} **{active_count}. {symbol or 'Unknown'}**\n"
                if current_mcap:
                    message += f"   💰 ${current_mcap:,.0f} ({performance:+.1f}%)\n"
                message += f"   🏷️ {platform or 'Unknown'}\n"
                message += f"   🔗 `{contract}`\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("📊 No tokens found in The Hunted group.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
```

STEP 2: Add this command handler:

```python
# Add this line with your other command handlers:
application.add_handler(CommandHandler("tokens", get_hunted_tokens))
```

STEP 3: Deploy to Railway
- Commit and push your changes
- Railway will automatically deploy

STEP 4: Get your tokens
- Go to The Hunted group 
- Send: /tokens
- Bot will show all current tracked tokens!

🔄 ALTERNATIVE METHODS:
======================

Method B - Railway CLI:
```bash
railway login
railway connect your-project-name
railway run python -c "
import sqlite3
conn = sqlite3.connect('tokens.db')
cursor = conn.cursor()
cursor.execute('SELECT contract_address, symbol, current_mcap FROM tokens WHERE chat_id = -1002350881772 AND is_active = 1')
for token in cursor.fetchall():
    print(f'{token[1]}: {token[0]} - ${token[2]:,.0f}' if token[2] else f'{token[1]}: {token[0]}')
conn.close()
"
```

Method C - Deploy Enhanced System:
- Deploy our enhanced monitoring system
- All existing tokens preserved automatically
- Get 5-second real-time updates for ALL tokens

🎯 RECOMMENDED: Use Method A (/tokens command)
It's the fastest way to see your current Railway tokens!

📊 What you'll see:
- All tokens currently tracked in The Hunted group
- Current market caps and performance
- Contract addresses
- Platform information
- Active/inactive status

🚀 After getting current tokens, you can deploy the enhanced system for:
- 5-second real-time updates (instead of 30 seconds)
- Parallel processing for ALL tokens
- Enhanced alerts and monitoring
