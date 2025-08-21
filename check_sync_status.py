#!/usr/bin/env python3
"""Check cross-group sync potential"""

import sqlite3

print('🔄 CROSS-GROUP SYNCHRONIZATION STATUS')
print('=' * 50)

try:
    conn = sqlite3.connect('tokens.db')
    cursor = conn.cursor()
    
    # Get all active tokens from other groups
    cursor.execute('''
        SELECT contract_address, symbol, name, current_mcap, chat_id
        FROM tokens 
        WHERE is_active = 1 AND chat_id != -1002350881772
        ORDER BY symbol
    ''')
    
    existing_tokens = cursor.fetchall()
    conn.close()
    
    new_group_id = -1002350881772
    
    print(f'🎯 Target Group: "The Hunted" ({new_group_id})')
    print(f'📊 Active tokens in other groups: {len(existing_tokens)}')
    print()
    
    if existing_tokens:
        print('🔄 TOKENS THAT WILL SYNC TO "THE HUNTED":')
        print('=' * 50)
        print('When you add any of these tokens to "The Hunted",')
        print('they will benefit from existing cross-group monitoring:')
        print()
        
        for i, (address, symbol, name, mcap, source_group) in enumerate(existing_tokens, 1):
            mcap_display = f'${mcap:,.0f}' if mcap else 'Unknown'
            print(f'{i}. {symbol} ({name})')
            print(f'   💰 Current MCAP: {mcap_display}')
            print(f'   📍 Currently tracked in group: {source_group}')
            print(f'   🏷️  Contract: {address[:8]}...{address[-8:]}')
            print()
        
        print('💡 BENEFIT OF CROSS-GROUP SYNC:')
        print('• Real-time price data already being collected')
        print('• Historical data available immediately') 
        print('• Alerts will be sent to ALL groups tracking each token')
        print('• No delay in monitoring when you add these tokens')
        
    else:
        print('📝 NO EXISTING TOKENS TO SYNC')
        print('• "The Hunted" will be the first group to track tokens')
        print('• Any tokens you add will become available for other groups')
        print('• Cross-group sync will activate when multiple groups track same tokens')
    
    print()
    print('🚀 READY TO START TRACKING!')
    print('Use /add CONTRACT_ADDRESS in "The Hunted" to begin!')
    
except Exception as e:
    print(f'❌ Error checking sync status: {e}')
