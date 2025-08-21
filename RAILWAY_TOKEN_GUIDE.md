🎯 GET CURRENT TOKENS FROM RAILWAY - STEP BY STEP
=================================================

📊 TARGET: The Hunted Group (-1002350881772)
🚂 SOURCE: Your live Railway deployment

🚀 EASIEST METHOD - Add /show Command:
=====================================

STEP 1: Copy this function to your Railway main.py
--------------------------------------------------

```python
async def show_hunted_tokens(update, context):
    """Show all tokens tracked in The Hunted group."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
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
        
        if not tokens:
            await update.message.reply_text("📊 No tokens currently tracked.")
            return
        
        active_tokens = [t for t in tokens if t[6]]
        
        message = f"🎯 **THE HUNTED TOKENS**\\n\\n"
        message += f"📊 Total: {len(tokens)} | Active: {len(active_tokens)}\\n\\n"
        
        for i, token in enumerate(active_tokens, 1):
            contract, symbol, name, initial_mcap, current_mcap, platform, is_active, detected_at = token
            
            performance = 0
            if initial_mcap and current_mcap and initial_mcap > 0:
                performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
            
            status = "🚀" if performance > 100 else "📈" if performance > 50 else "🟢" if performance > 0 else "🔴"
            
            message += f"{status} **{i}. {symbol or 'Unknown'}**\\n"
            if current_mcap:
                message += f"   💰 ${current_mcap:,.0f} ({performance:+.1f}%)\\n"
            message += f"   🏷️ {platform or 'Unknown'}\\n"
            message += f"   🔗 `{contract}`\\n\\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
```

STEP 2: Add this command handler
-------------------------------

Add this line with your other handlers in main.py:

```python
application.add_handler(CommandHandler("show", show_hunted_tokens))
```

STEP 3: Deploy to Railway
-------------------------

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Add /show command for token display"
   git push
   ```

2. Railway will auto-deploy your update

STEP 4: Get your tokens
-----------------------

1. Go to The Hunted group
2. Send: /show
3. Bot will display all tracked tokens with:
   - Current market caps
   - Performance percentages
   - Contract addresses
   - Platform information
   - Active status

📊 EXAMPLE OUTPUT:
==================

🎯 THE HUNTED TOKENS

📊 Total: 5 | Active: 4

🚀 1. MOONSHOT
   💰 $2,345,678 (+150.5%)
   🏷️ Pump.fun
   🔗 `ABC123...XYZ789`

📈 2. ROCKET
   💰 $1,234,567 (+75.2%)
   🏷️ Raydium
   🔗 `DEF456...UVW012`

🟢 3. PUMP
   💰 $567,890 (+25.3%)
   🏷️ DexScreener
   🔗 `GHI789...RST345`

🔴 4. DOWN
   💰 $234,567 (-15.8%)
   🏷️ Pump.fun
   🔗 `JKL012...MNO678`

🔄 ALTERNATIVE: Railway CLI Method
==================================

If you have Railway CLI installed:

```bash
railway login
railway connect your-project-name
railway run python -c "
import sqlite3
conn = sqlite3.connect('tokens.db')
cursor = conn.cursor()
cursor.execute('SELECT symbol, contract_address, current_mcap FROM tokens WHERE chat_id = -1002350881772 AND is_active = 1')
for symbol, address, mcap in cursor.fetchall():
    print(f'{symbol}: {address} - ${mcap:,.0f}' if mcap else f'{symbol}: {address}')
conn.close()
"
```

🎯 RECOMMENDED: Use the /show command method!
It's the fastest and easiest way to see your Railway tokens.
