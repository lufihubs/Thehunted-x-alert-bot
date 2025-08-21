# Add this export command to your Railway main.py to get current tokens

async def export_tokens_command(update, context):
    """Export current tokens for The Hunted group."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
    # Only work in The Hunted group
    if update.effective_chat.id != THE_HUNTED_GROUP_ID:
        return
    
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        query = """
            SELECT contract_address, symbol, name, initial_mcap, current_mcap, detected_at
            FROM tokens 
            WHERE chat_id = ? AND is_active = 1
            ORDER BY detected_at DESC
        """
        
        cursor.execute(query, (THE_HUNTED_GROUP_ID,))
        tokens = cursor.fetchall()
        conn.close()
        
        if tokens:
            message = f"📊 **THE HUNTED - CURRENT TOKENS**\n\n"
            message += f"🎯 Total Active: {len(tokens)}\n"
            message += f"⏰ Export: {datetime.now().strftime('%H:%M:%S')}\n\n"
            
            for i, token in enumerate(tokens, 1):
                contract, symbol, name, initial_mcap, current_mcap, detected_at = token
                
                performance = 0
                if initial_mcap and current_mcap and initial_mcap > 0:
                    performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
                
                status = "🟢" if performance > 0 else "🔴" if performance < -50 else "🟡"
                
                message += f"{status} **{i}. {symbol or 'Unknown'}**\n"
                if current_mcap:
                    message += f"   💰 ${current_mcap:,.0f} ({performance:+.1f}%)\n"
                message += f"   🔗 `{contract}`\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("📊 No tokens currently tracked.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Export failed: {str(e)}")

# Add this line to your command handlers section in main.py:
# application.add_handler(CommandHandler("export", export_tokens_command))
