"""
Railway Token Sync Command for "The Hunted" Group
Add this command to your Railway bot to extract current tokens
"""

import sqlite3
import json
from datetime import datetime

# Add this to your main.py on Railway to create a sync command

async def export_hunted_tokens_command(update, context):
    """Export current tokens for The Hunted group - Add this to your Railway bot."""
    
    THE_HUNTED_GROUP_ID = -1002350881772
    
    # Check if command is from The Hunted group
    if update.effective_chat.id != THE_HUNTED_GROUP_ID:
        return
    
    try:
        # Get tokens from Railway database
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT contract_address, symbol, name, initial_mcap, current_mcap, 
                   initial_price, current_price, detected_at, last_updated,
                   multipliers_alerted, loss_50_alerted, platform
            FROM tokens 
            WHERE chat_id = ? AND is_active = 1
            ORDER BY detected_at DESC
        ''', (THE_HUNTED_GROUP_ID,))
        
        tokens = cursor.fetchall()
        conn.close()
        
        # Create export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'group_id': THE_HUNTED_GROUP_ID,
            'group_name': 'The Hunted',
            'total_tokens': len(tokens),
            'tokens': []
        }
        
        # Process each token
        for token in tokens:
            contract, symbol, name, initial_mcap, current_mcap, initial_price, current_price, detected_at, last_updated, multipliers_alerted, loss_50_alerted, platform = token
            
            # Calculate performance
            performance = 0
            if initial_mcap and current_mcap and initial_mcap > 0:
                performance = ((current_mcap - initial_mcap) / initial_mcap) * 100
            
            token_data = {
                'contract_address': contract,
                'symbol': symbol,
                'name': name,
                'initial_mcap': initial_mcap,
                'current_mcap': current_mcap,
                'initial_price': initial_price,
                'current_price': current_price,
                'performance_pct': round(performance, 2),
                'detected_at': detected_at,
                'last_updated': last_updated,
                'multipliers_alerted': multipliers_alerted,
                'loss_50_alerted': bool(loss_50_alerted),
                'platform': platform
            }
            
            export_data['tokens'].append(token_data)
        
        # Send export as message
        if tokens:
            message = f"📊 **HUNTED GROUP TOKEN EXPORT**\\n\\n"
            message += f"🎯 Group: The Hunted\\n"
            message += f"📈 Total Tokens: {len(tokens)}\\n"
            message += f"⏰ Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
            
            for i, token_data in enumerate(export_data['tokens'], 1):
                symbol = token_data['symbol']
                performance = token_data['performance_pct']
                contract = token_data['contract_address']
                
                status = "🟢" if performance > 0 else "🔴" if performance < -50 else "🟡"
                
                message += f"{status} **{i}. {symbol}**\\n"
                message += f"   📊 Performance: {performance:+.1f}%\\n"
                message += f"   💰 MCap: ${token_data['current_mcap']:,.0f}\\n"
                message += f"   🔗 `{contract}`\\n\\n"
                
                # Telegram message limit
                if len(message) > 3500:
                    await update.message.reply_text(message, parse_mode='Markdown')
                    message = ""
            
            if message:
                await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("📊 No tokens currently tracked in The Hunted group.")
            
        # Also save to file (if Railway has file storage)
        filename = f"hunted_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        print(f"✅ Token export saved: {filename}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Export failed: {str(e)}")
        print(f"Export error: {e}")

# Add this command handler to your Railway bot:
# application.add_handler(CommandHandler("export_tokens", export_hunted_tokens_command))


def create_railway_sync_instructions():
    """Create instructions for syncing with Railway."""
    
    instructions = '''
# 🚂 RAILWAY TOKEN SYNC INSTRUCTIONS

## To get current tokens from your Railway bot:

### Method 1: Add Export Command (Recommended)
1. Add the `export_hunted_tokens_command` function to your Railway bot's main.py
2. Add this line to your command handlers:
   ```python
   application.add_handler(CommandHandler("export_tokens", export_hunted_tokens_command))
   ```
3. Deploy to Railway
4. In The Hunted group, send: `/export_tokens`
5. Bot will show all current tokens

### Method 2: Check Railway Logs
1. Go to Railway dashboard
2. Check your bot's logs
3. Look for token addition messages
4. Note contract addresses being tracked

### Method 3: Use Railway CLI (if available)
1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Connect to your project: `railway link`
4. Access database: `railway run sqlite3 tokens.db`
5. Query: `SELECT * FROM tokens WHERE chat_id = -1002350881772;`

### Method 4: Manual Re-sync (Easiest)
1. Deploy enhanced monitoring system
2. Add tokens again to The Hunted group
3. Bot will track them with new 5-second updates
4. Previous tokens will be re-detected if sent again

## Current Status:
- ✅ Enhanced monitoring system ready
- ✅ Bot has admin permissions in The Hunted group
- ✅ Railway deployment active
- ✅ Ready for real-time tracking improvements

## Next Steps:
1. Deploy enhanced system to Railway
2. All new tokens get 5-second real-time updates
3. All tokens in The Hunted group monitored simultaneously
4. Enhanced alert system active
'''
    
    return instructions

if __name__ == "__main__":
    instructions = create_railway_sync_instructions()
    print(instructions)
    
    # Save instructions
    with open('RAILWAY_SYNC_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    print("\\n📄 Instructions saved: RAILWAY_SYNC_INSTRUCTIONS.md")
    print("✅ Ready to sync with Railway deployment!")
