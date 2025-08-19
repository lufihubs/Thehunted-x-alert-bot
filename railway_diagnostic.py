#!/usr/bin/env python3
"""
Simple diagnostic script for Railway deployment
"""
import os
import sys
import traceback

def check_environment():
    """Check environment variables and basic setup"""
    print("🔍 Railway Deployment Diagnostics")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Check working directory
    print(f"📁 Working directory: {os.getcwd()}")
    
    # List files in current directory
    print(f"📂 Files in current directory:")
    try:
        for item in os.listdir('.'):
            print(f"   - {item}")
    except Exception as e:
        print(f"   Error listing files: {e}")
    
    # Check environment variables
    print(f"\n🔑 Environment Variables:")
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        print(f"   ✅ TELEGRAM_BOT_TOKEN: Set (length: {len(token)})")
    else:
        print(f"   ❌ TELEGRAM_BOT_TOKEN: Not set!")
    
    port = os.getenv('PORT', '8000')
    print(f"   📡 PORT: {port}")
    
    # Check if required files exist
    print(f"\n📋 Required Files:")
    required_files = ['main.py', 'railway_start.py', 'database.py', 'config.py']
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}: Found")
        else:
            print(f"   ❌ {file}: Missing!")
    
    # Test basic imports
    print(f"\n📦 Testing Imports:")
    try:
        import telegram
        print(f"   ✅ telegram: {telegram.__version__}")
    except ImportError as e:
        print(f"   ❌ telegram: {e}")
    
    try:
        import aiosqlite
        print(f"   ✅ aiosqlite: Found")
    except ImportError as e:
        print(f"   ❌ aiosqlite: {e}")
    
    try:
        import httpx
        print(f"   ✅ httpx: Found")
    except ImportError as e:
        print(f"   ❌ httpx: {e}")

def test_config():
    """Test configuration loading"""
    print(f"\n⚙️  Testing Configuration:")
    try:
        sys.path.append('.')
        from config import Config
        print(f"   ✅ Config imported successfully")
        
        # Test config values (without exposing sensitive data)
        if hasattr(Config, 'TELEGRAM_BOT_TOKEN'):
            if Config.TELEGRAM_BOT_TOKEN:
                print(f"   ✅ Bot token configured")
            else:
                print(f"   ❌ Bot token empty")
        
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        traceback.print_exc()

def main():
    """Main diagnostic function"""
    try:
        check_environment()
        test_config()
        
        print(f"\n🎯 Summary:")
        print(f"   If all checks pass, the issue might be in the application logic.")
        print(f"   If any checks fail, those need to be fixed first.")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
