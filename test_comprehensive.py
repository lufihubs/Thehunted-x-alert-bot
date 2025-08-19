"""Comprehensive test for bot restart and multiple token handling."""
import asyncio
import sqlite3
from database import Database
from token_tracker import TokenTracker
from main import SolanaAlertBot

async def test_restart_functionality():
    """Test bot restart with existing tokens."""
    print("🔄 Testing bot restart functionality...\n")
    
    # Setup test database with multiple tokens
    db_path = 'test_restart.db'
    
    # Create test database with tokens
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_address TEXT UNIQUE NOT NULL,
            symbol TEXT,
            name TEXT,
            initial_mcap REAL NOT NULL,
            current_mcap REAL,
            initial_price REAL NOT NULL,
            current_price REAL,
            lowest_mcap REAL DEFAULT NULL,
            lowest_price REAL DEFAULT NULL,
            highest_mcap REAL DEFAULT NULL,
            highest_price REAL DEFAULT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            platform TEXT,
            multipliers_alerted TEXT DEFAULT '[]',
            loss_50_alerted BOOLEAN DEFAULT FALSE,
            confirmed_scan_mcap REAL DEFAULT NULL,
            scan_confirmation_count INTEGER DEFAULT 0
        )
    ''')
    
    # Insert test tokens
    test_tokens = [
        ('So11111111111111111111111111111111111111112', 'SOL', 'Wrapped SOL', 1000000, 1500000, 1.0, 1.5, 1000000, 1.0, 1500000, 1.5, 12345, 100, '2025-08-19 08:00:00', '2025-08-19 08:00:00', True, 'birdeye', '[]', False, 1000000, 1),
        ('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'USDC', 'USD Coin', 500000, 1000000, 0.5, 1.0, 500000, 0.5, 1000000, 1.0, 12346, 101, '2025-08-19 08:00:00', '2025-08-19 08:00:00', True, 'dexscreener', '[]', False, 500000, 1),
        ('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', 'USDT', 'Tether USD', 2000000, 1000000, 2.0, 1.0, 1000000, 1.0, 2000000, 2.0, 12347, 102, '2025-08-19 08:00:00', '2025-08-19 08:00:00', True, 'pump.fun', '[]', False, 2000000, 1),
    ]
    
    for token in test_tokens:
        cursor.execute('''
            INSERT OR REPLACE INTO tokens 
            (contract_address, symbol, name, initial_mcap, current_mcap, initial_price, current_price,
             lowest_mcap, lowest_price, highest_mcap, highest_price, chat_id, message_id,
             detected_at, last_updated, is_active, platform, multipliers_alerted, loss_50_alerted,
             confirmed_scan_mcap, scan_confirmation_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', token)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created test database with {len(test_tokens)} tokens")
    
    # Test loading existing tokens (simulate bot restart)
    class MockBot:
        async def send_message(self, chat_id, text, parse_mode=None):
            print(f"📤 Mock message to {chat_id}: {text[:50]}...")
    
    mock_bot = MockBot()
    tracker = TokenTracker(mock_bot)
    
    # Override database path for testing
    import config
    original_db_path = config.Config.DATABASE_PATH
    config.Config.DATABASE_PATH = db_path
    
    try:
        # Load existing tokens (simulating restart)
        # Temporarily patch the database path in the tracker
        original_tracker_db_path = None
        
        # Create a database instance with our test path
        from database import Database
        test_db = Database(db_path)
        
        # Mock the Database instantiation in token_tracker
        import token_tracker
        original_database_init = token_tracker.Database
        
        def mock_database_init(path='tokens.db'):
            return Database(db_path)
        
        token_tracker.Database = mock_database_init
        
        await tracker._load_existing_tokens()
        
        # Restore original
        token_tracker.Database = original_database_init
        
        print(f"✅ Loaded {len(tracker.tracking_tokens)} tokens after restart")
        
        # Verify each token was loaded correctly
        for contract, token_data in tracker.tracking_tokens.items():
            print(f"📊 {token_data['symbol']}: {contract[:8]}... - {token_data['current_mcap']:,.0f} mcap")
        
        # Test tracking status
        status = tracker.get_tracking_status()
        print(f"📈 Tracking status: {status['total_tokens']} tokens, running: {status['is_running']}")
        
    finally:
        # Restore original database path
        config.Config.DATABASE_PATH = original_db_path
        
        # Cleanup
        import os
        try:
            os.remove(db_path)
            print("🧹 Cleaned up test database")
        except:
            pass
    
    print("✅ Restart functionality test completed\n")

async def test_duplicate_token_handling():
    """Test handling of duplicate tokens."""
    print("🔄 Testing duplicate token handling...\n")
    
    class MockBot:
        async def send_message(self, chat_id, text, parse_mode=None):
            print(f"📤 Mock message to {chat_id}: {text[:50]}...")
    
    mock_bot = MockBot()
    tracker = TokenTracker(mock_bot)
    
    # Test adding same token twice
    test_contract = "So11111111111111111111111111111111111111112"
    
    # Add to tracking_tokens manually to simulate existing token
    tracker.tracking_tokens[test_contract] = {
        'name': 'Wrapped SOL',
        'symbol': 'SOL',
        'initial_mcap': 1000000,
        'current_mcap': 1000000,
        'confirmed_scan_mcap': 1000000,
    }
    
    # Try to add the same token again
    try:
        result = await tracker.add_token(test_contract, 12345, 100)
        if not result:
            print("✅ Correctly rejected duplicate token")
        else:
            print("❌ Incorrectly accepted duplicate token")
    except Exception as e:
        print(f"❌ Error handling duplicate: {e}")
    
    print("✅ Duplicate token handling test completed\n")

async def test_multiple_alert_scenarios():
    """Test multiple alert scenarios."""
    print("🚨 Testing multiple alert scenarios...\n")
    
    class MockBot:
        def __init__(self):
            self.sent_messages = []
        
        async def send_message(self, chat_id, text, parse_mode=None):
            self.sent_messages.append({
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode
            })
            print(f"📤 Alert sent to {chat_id}: {text.split('*')[1] if '*' in text else text[:30]}...")
    
    mock_bot = MockBot()
    tracker = TokenTracker(mock_bot)
    
    # Simulate different alert scenarios
    test_scenarios = [
        {
            'name': 'High Gainer',
            'contract': 'HighGainer1111111111111111111111111111111111',
            'data': {
                'name': 'High Gainer Token',
                'symbol': 'HIGH',
                'initial_mcap': 100000,
                'current_mcap': 1000000,  # 10x gain
                'confirmed_scan_mcap': 100000,
                'chat_id': 12345,
                'message_id': 100,
                'loss_50_alerted': False
            }
        },
        {
            'name': 'Loss Token',
            'contract': 'LossToken1111111111111111111111111111111111',
            'data': {
                'name': 'Loss Token',
                'symbol': 'LOSS',
                'initial_mcap': 100000,
                'current_mcap': 40000,  # -60% loss
                'confirmed_scan_mcap': 100000,
                'chat_id': 12346,
                'message_id': 101,
                'loss_50_alerted': False
            }
        },
        {
            'name': 'Moderate Gainer',
            'contract': 'ModerateGainer111111111111111111111111111111',
            'data': {
                'name': 'Moderate Gainer',
                'symbol': 'MOD',
                'initial_mcap': 200000,
                'current_mcap': 600000,  # 3x gain
                'confirmed_scan_mcap': 200000,
                'chat_id': 12347,
                'message_id': 102,
                'loss_50_alerted': False
            }
        }
    ]
    
    # Setup tracking for each scenario
    for scenario in test_scenarios:
        contract = scenario['contract']
        tracker.tracking_tokens[contract] = scenario['data']
        tracker.sent_alerts[contract] = set()
    
    # Test multiplier alerts
    for contract, token_data in tracker.tracking_tokens.items():
        current_multiplier = token_data['current_mcap'] / token_data['confirmed_scan_mcap']
        print(f"\n📊 Testing {token_data['symbol']}: {current_multiplier:.2f}x")
        
        # Check multiplier alerts
        await tracker._check_multiplier_alerts(contract, token_data, current_multiplier)
        
        # Check loss alerts
        await tracker._check_loss_alerts(contract, token_data, current_multiplier)
    
    print(f"\n✅ Total alerts generated: {len(mock_bot.sent_messages)}")
    for i, msg in enumerate(mock_bot.sent_messages, 1):
        alert_type = "LOSS" if "LOSS ALERT" in msg['text'] else "GAIN"
        print(f"  {i}. {alert_type} alert to chat {msg['chat_id']}")
    
    print("✅ Multiple alert scenarios test completed\n")

async def test_contract_address_validation():
    """Test contract address validation."""
    print("🔍 Testing contract address validation...\n")
    
    test_addresses = [
        ("So11111111111111111111111111111111111111112", "Valid SOL address", True),
        ("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "Valid USDC address", True),
        ("InvalidAddress123", "Too short", False),
        ("So11111111111111111111111111111111111111112Extra", "Too long", False),
        ("0o11111111111111111111111111111111111111112", "Invalid characters", False),
        ("", "Empty string", False),
        ("So1111111111111111111111111111111111111111", "43 characters", False),
    ]
    
    import re
    contract_pattern = r'\b[1-9A-HJ-NP-Za-km-z]{44}\b'
    
    for address, description, expected in test_addresses:
        matches = re.findall(contract_pattern, address)
        is_valid = len(matches) > 0 and len(address) == 44
        
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} {description}: {address[:20]}... -> {is_valid}")
    
    print("✅ Contract address validation test completed\n")

async def main():
    """Run all comprehensive tests."""
    print("🧪 Starting comprehensive bot tests...\n")
    
    await test_restart_functionality()
    await test_duplicate_token_handling()
    await test_multiple_alert_scenarios()
    await test_contract_address_validation()
    
    print("🎉 All comprehensive tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
