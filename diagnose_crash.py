#!/usr/bin/env python3
"""
Quick Railway crash diagnostic tool
"""
import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def diagnose_crash():
    """Diagnose potential crash causes"""
    print("🔍 Railway Crash Diagnostic")
    print("=" * 40)
    
    issues_found = []
    
    # Test 1: Check environment variables
    print("1. Environment Variables...")
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        issues_found.append("❌ TELEGRAM_BOT_TOKEN not set")
        print("   ❌ TELEGRAM_BOT_TOKEN missing")
    else:
        print("   ✅ TELEGRAM_BOT_TOKEN configured")
    
    # Test 2: Check imports
    print("\n2. Import Test...")
    try:
        from config import Config
        from database import Database
        from main import SolanaAlertBot
        from health_check import HealthCheckServer
        print("   ✅ All imports successful")
    except Exception as e:
        issues_found.append(f"❌ Import error: {e}")
        print(f"   ❌ Import failed: {e}")
    
    # Test 3: Check database initialization
    print("\n3. Database Test...")
    try:
        from database import Database
        db_path = os.getenv('DATABASE_PATH', 'tokens.db')
        db = Database(db_path)
        await db.init_db()
        print("   ✅ Database initialization successful")
    except Exception as e:
        issues_found.append(f"❌ Database error: {e}")
        print(f"   ❌ Database failed: {e}")
    
    # Test 4: Check bot token validation
    print("\n4. Bot Token Test...")
    try:
        from config import Config
        if Config.validate():
            print("   ✅ Configuration validation passed")
        else:
            issues_found.append("❌ Configuration validation failed")
            print("   ❌ Configuration validation failed")
    except Exception as e:
        issues_found.append(f"❌ Config error: {e}")
        print(f"   ❌ Config test failed: {e}")
    
    # Test 5: Check health server
    print("\n5. Health Server Test...")
    try:
        from health_check import HealthCheckServer
        port = int(os.getenv('PORT', 8000))
        health_server = HealthCheckServer(port=port)
        print(f"   ✅ Health server can start on port {port}")
    except Exception as e:
        issues_found.append(f"❌ Health server error: {e}")
        print(f"   ❌ Health server failed: {e}")
    
    # Summary
    print("\n" + "=" * 40)
    if issues_found:
        print("🚨 ISSUES FOUND:")
        for issue in issues_found:
            print(f"   {issue}")
        
        print("\n🔧 LIKELY FIXES:")
        if "TELEGRAM_BOT_TOKEN" in str(issues_found):
            print("   1. Set TELEGRAM_BOT_TOKEN in Railway environment variables")
        if "Import error" in str(issues_found):
            print("   2. Check Railway build logs for dependency installation")
        if "Database error" in str(issues_found):
            print("   3. Check Railway volume is mounted at /app/data")
        if "PORT" in str(issues_found):
            print("   4. Railway should auto-set PORT environment variable")
    else:
        print("✅ No obvious issues found")
        print("Check Railway logs for runtime errors")
    
    print("\n📋 Quick Railway Checklist:")
    print("   □ TELEGRAM_BOT_TOKEN environment variable set")
    print("   □ Volume mounted at /app/data (1GB)")
    print("   □ Python 3.11+ detected in build")
    print("   □ requirements.txt dependencies installed")
    print("   □ railway_start.py as start command")

if __name__ == "__main__":
    asyncio.run(diagnose_crash())
