#!/usr/bin/env python3
"""Check new group access and setup"""

import asyncio
import sys
from telegram import Bot

async def check_new_group():
    print('🔍 CHECKING NEW GROUP ACCESS')
    print('=' * 50)
    
    # Bot token from config
    bot_token = '8301492869:AAE1sP4G54PqDQEIHs-9v49GCJ8rnz1aKqQ'
    new_group_id = -1002350881772
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        
        print(f'🤖 Bot: @{bot_info.username}')
        print(f'🎯 Target Group: {new_group_id}')
        print()
        
        try:
            # Try to get group information
            chat = await bot.get_chat(new_group_id)
            
            print('✅ GROUP ACCESS CONFIRMED!')
            print('=' * 50)
            print(f'📛 Group Name: {getattr(chat, "title", "No Title")}')
            print(f'🏷️  Username: @{getattr(chat, "username", "None")}')
            print(f'👥 Type: {chat.type}')
            print(f'🆔 Group ID: {new_group_id}')
            
            # Check member count
            try:
                member_count = await bot.get_chat_member_count(new_group_id)
                print(f'👤 Members: {member_count}')
            except Exception as e:
                print(f'👤 Members: Cannot access count')
            
            # Check if bot is admin
            try:
                admins = await bot.get_chat_administrators(new_group_id)
                bot_is_admin = any(admin.user.id == bot_info.id for admin in admins)
                
                if bot_is_admin:
                    print('🛡️  Bot Status: ✅ ADMIN (Perfect!)')
                    
                    # Get bot's admin permissions
                    bot_admin = next((admin for admin in admins if admin.user.id == bot_info.id), None)
                    if bot_admin:
                        print('🔑 Bot has admin permissions')
                else:
                    print('🛡️  Bot Status: ⚠️  MEMBER (needs admin for full features)')
                    
            except Exception as admin_e:
                print(f'🛡️  Bot Status: Cannot verify admin status: {str(admin_e)[:50]}...')
            
            print()
            print('🎉 GROUP SETUP STATUS:')
            print('=' * 50)
            print('✅ Bot can access the group')
            print('✅ Group information retrieved successfully')
            if bot_is_admin:
                print('✅ Bot has admin permissions')
                print('✅ Ready for token tracking and alerts')
                print()
                print('🚀 NEXT STEPS:')
                print('1. Use /add CONTRACT_ADDRESS to start tracking tokens')
                print('2. Bot will provide real-time price updates')
                print('3. All alerts will be sent to this group')
                print('4. Cross-group synchronization is active')
            else:
                print('⚠️  Bot needs admin permissions for full functionality')
                
        except Exception as e:
            print(f'❌ Cannot access group {new_group_id}')
            print(f'Error: {str(e)}')
            print()
            print('🔧 TROUBLESHOOTING:')
            print('1. Make sure the bot is added to the group')
            print('2. Grant admin permissions to the bot')
            print('3. Ensure the group ID is correct')
        
    except Exception as e:
        print(f'❌ Error checking group: {e}')

if __name__ == "__main__":
    asyncio.run(check_new_group())
