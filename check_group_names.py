#!/usr/bin/env python3
"""Check group names where the bot is added"""

import asyncio
import sys
import sqlite3
from telegram import Bot

async def get_group_names():
    print('🏷️  GROUP NAMES AND DETAILS')
    print('=' * 50)
    
    # Bot token from config
    bot_token = '8301492869:AAE1sP4G54PqDQEIHs-9v49GCJ8rnz1aKqQ'
    
    try:
        # Initialize bot
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        
        print(f'🤖 Bot: @{bot_info.username}')
        print()
        
        # Get all groups from database
        conn = sqlite3.connect('tokens.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT chat_id
            FROM tokens 
            ORDER BY chat_id
        ''')
        
        group_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print('📋 ALL GROUPS WITH DETAILED INFORMATION:')
        print('=' * 50)
        
        active_groups = []
        inactive_groups = []
        
        for i, chat_id in enumerate(group_ids, 1):
            print(f'{i}. Group ID: {chat_id}')
            
            try:
                # Get chat information
                chat = await bot.get_chat(chat_id)
                
                # Get basic info
                chat_type = chat.type
                title = getattr(chat, 'title', 'No Title')
                username = getattr(chat, 'username', 'No Username')
                
                print(f'   📛 Name/Title: {title}')
                if username != 'No Username':
                    print(f'   🏷️  Username: @{username}')
                else:
                    print(f'   🏷️  Username: None')
                print(f'   👥 Type: {chat_type}')
                
                # Try to get member count for groups
                if chat_type in ['group', 'supergroup']:
                    try:
                        member_count = await bot.get_chat_member_count(chat_id)
                        print(f'   👤 Members: {member_count}')
                    except:
                        print(f'   👤 Members: Cannot access')
                
                # Check if bot is admin
                try:
                    admins = await bot.get_chat_administrators(chat_id)
                    bot_is_admin = any(admin.user.id == bot_info.id for admin in admins)
                    admin_status = '✅ ADMIN' if bot_is_admin else '👤 MEMBER'
                    print(f'   🛡️  Bot Status: {admin_status}')
                except:
                    print(f'   🛡️  Bot Status: Unknown')
                
                print(f'   ✅ Status: ACCESSIBLE')
                active_groups.append({
                    'id': chat_id,
                    'title': title,
                    'username': username,
                    'type': chat_type
                })
                
            except Exception as e:
                error_msg = str(e)
                print(f'   ❌ Status: INACCESSIBLE ({error_msg[:30]}...)')
                inactive_groups.append({
                    'id': chat_id,
                    'error': error_msg
                })
            
            print()
        
        # Summary
        print('📊 SUMMARY BY GROUP NAMES:')
        print('=' * 50)
        
        if active_groups:
            print('✅ ACCESSIBLE GROUPS:')
            for group in active_groups:
                title = group['title'] if group['title'] != 'No Title' else f'Group {group["id"]}'
                username_info = f' (@{group["username"]})' if group['username'] != 'No Username' else ''
                print(f'   • {title}{username_info}')
                print(f'     ID: {group["id"]} | Type: {group["type"]}')
            print()
        
        if inactive_groups:
            print('❌ INACCESSIBLE GROUPS:')
            for group in inactive_groups:
                print(f'   • Group {group["id"]}')
                print(f'     Error: {group["error"][:50]}...')
            print()
        
        print(f'🏢 Total Groups: {len(group_ids)}')
        print(f'✅ Accessible: {len(active_groups)}')
        print(f'❌ Inaccessible: {len(inactive_groups)}')
        
    except Exception as e:
        print(f'❌ Error getting group names: {e}')

if __name__ == "__main__":
    asyncio.run(get_group_names())
