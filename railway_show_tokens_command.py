
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
        
        message = f"🎯 **THE HUNTED - CURRENT TOKENS**\n\n"
        message += f"📊 Total: {len(tokens)} | Active: {len(active_tokens)}\n"
        message += f"⏰ {datetime.now().strftime('%H:%M:%S UTC')}\n\n"
        
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
            
            message += f"{status} **{i}. {symbol or 'Unknown'}**\n"
            
            if current_mcap:
                message += f"   💰 ${current_mcap:,.0f}"
                if performance != 0:
                    message += f" ({performance:+.1f}%)"
                message += "\n"
            
            message += f"   🏷️ {platform or 'Unknown'}\n"
            message += f"   📅 {detected_at}\n"
            message += f"   🔗 `{contract}`\n\n"
            
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
