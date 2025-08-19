"""Test script to validate bot functionality."""
import asyncio
import sqlite3
from database import Database
from solana_api import SolanaAPI

async def test_database_operations():
    """Test database operations."""
    print("🧪 Testing database operations...")
    
    # Test database initialization
    db = Database('test_tokens.db')
    await db.init_db()
    print("✅ Database initialized")
    
    # Test adding multiple tokens
    test_contracts = [
        "So11111111111111111111111111111111111111112",  # SOL
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    ]
    
    for i, contract in enumerate(test_contracts):
        try:
            result = await db.add_token(
                contract_address=contract,
                symbol=f"TEST{i+1}",
                name=f"Test Token {i+1}",
                initial_mcap=1000000.0,
                initial_price=1.0,
                chat_id=12345 + i,
                message_id=100 + i
            )
            print(f"✅ Added token {i+1}: {contract[:8]}...")
        except Exception as e:
            print(f"❌ Failed to add token {i+1}: {e}")
    
    # Test retrieving tokens
    tokens = await db.get_active_tokens()
    print(f"✅ Retrieved {len(tokens)} tokens from database")
    
    # Test updating token price
    if tokens:
        test_token = tokens[0]
        await db.update_token_price(
            contract_address=test_token['contract_address'],
            current_mcap=1500000.0,
            current_price=1.5
        )
        print("✅ Updated token price")
    
    print("✅ Database operations test completed\n")

async def test_api_functionality():
    """Test API functionality."""
    print("🧪 Testing API functionality...")
    
    async with SolanaAPI() as api:
        # Test with a known Solana token (SOL)
        sol_contract = "So11111111111111111111111111111111111111112"
        
        try:
            token_info = await api.get_token_info(sol_contract)
            if token_info:
                print(f"✅ API working - SOL info: {token_info['name']} (${token_info['market_cap']:,.2f})")
            else:
                print("❌ API returned no data for SOL")
        except Exception as e:
            print(f"❌ API test failed: {e}")
    
    print("✅ API functionality test completed\n")

async def test_multiple_token_handling():
    """Test handling multiple tokens simultaneously."""
    print("🧪 Testing multiple token handling...")
    
    # Simulate multiple tokens being tracked
    test_data = {
        "token1": {
            'name': 'Test Token 1',
            'symbol': 'TEST1',
            'initial_mcap': 1000000,
            'current_mcap': 1500000,
            'confirmed_scan_mcap': 1000000,
        },
        "token2": {
            'name': 'Test Token 2', 
            'symbol': 'TEST2',
            'initial_mcap': 500000,
            'current_mcap': 1000000,
            'confirmed_scan_mcap': 500000,
        },
        "token3": {
            'name': 'Test Token 3',
            'symbol': 'TEST3', 
            'initial_mcap': 2000000,
            'current_mcap': 1800000,
            'confirmed_scan_mcap': 2000000,
        }
    }
    
    # Test multiplier calculations
    for contract, data in test_data.items():
        multiplier = data['current_mcap'] / data['confirmed_scan_mcap']
        loss_percent = (multiplier - 1) * 100
        
        print(f"📊 {data['symbol']}: {multiplier:.2f}x ({loss_percent:+.1f}%)")
        
        # Check alerts that would be triggered
        triggered_alerts = []
        for mult in [2, 3, 5, 8, 10]:
            if multiplier >= mult:
                triggered_alerts.append(f"{mult}x")
        
        if loss_percent <= -50:
            triggered_alerts.append("LOSS -50%")
        
        if triggered_alerts:
            print(f"  🚨 Would trigger: {', '.join(triggered_alerts)}")
        else:
            print(f"  ✅ No alerts triggered")
    
    print("✅ Multiple token handling test completed\n")

def test_database_schema():
    """Test database schema integrity."""
    print("🧪 Testing database schema...")
    
    try:
        conn = sqlite3.connect('test_tokens.db')
        cursor = conn.cursor()
        
        # Check if all required columns exist
        cursor.execute("PRAGMA table_info(tokens)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'id', 'contract_address', 'symbol', 'name', 
            'initial_mcap', 'current_mcap', 'initial_price', 'current_price',
            'lowest_mcap', 'lowest_price', 'highest_mcap', 'highest_price',
            'chat_id', 'message_id', 'detected_at', 'last_updated',
            'is_active', 'platform', 'multipliers_alerted', 
            'loss_50_alerted', 'confirmed_scan_mcap', 'scan_confirmation_count'
        ]
        
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
        else:
            print("✅ All required columns present")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
    
    print("✅ Database schema test completed\n")

async def main():
    """Run all tests."""
    print("🚀 Starting bot functionality tests...\n")
    
    # Run tests
    test_database_schema()
    await test_database_operations()
    await test_api_functionality()
    await test_multiple_token_handling()
    
    print("🎉 All tests completed!")
    
    # Cleanup
    try:
        import os
        os.remove('test_tokens.db')
        print("🧹 Cleaned up test database")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())
