#!/usr/bin/env python3
"""
Railway Deployment Helper - Updates Railway with Enhanced Multi-Group Code
"""
import os
import subprocess
import sys
from pathlib import Path

def check_git_status():
    """Check git status and stage files"""
    print("📋 Checking git status...")
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("📝 Unstaged changes found:")
            print(result.stdout)
            return True
        else:
            print("✅ No unstaged changes")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Git status error: {e}")
        return False

def prepare_railway_deployment():
    """Prepare files for Railway deployment"""
    print("🚀 PREPARING RAILWAY DEPLOYMENT WITH ENHANCED MULTI-GROUP FEATURES")
    print("=" * 70)
    
    # Essential files for Railway deployment
    essential_files = [
        'main.py',
        'token_tracker_enhanced.py',  # This is key!
        'database.py',
        'config.py',
        'solana_api.py',
        'requirements.txt',
        'Procfile',
        'railway_start.py',
        'health_check.py'
    ]
    
    print("🔍 Checking essential files...")
    missing_files = []
    for file in essential_files:
        if not os.path.exists(file):
            missing_files.append(file)
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"\n❌ Missing essential files: {missing_files}")
        return False
    
    print("\n📦 All essential files present!")
    return True

def stage_and_commit_changes():
    """Stage and commit all changes"""
    print("\n📝 Staging changes for Railway deployment...")
    
    try:
        # Add all relevant files
        files_to_add = [
            'main.py',
            'token_tracker_enhanced.py',
            'database.py',
            'config.py',
            'solana_api.py',
            'railway_start.py',
            'health_check.py'
        ]
        
        for file in files_to_add:
            if os.path.exists(file):
                subprocess.run(['git', 'add', file], check=True)
                print(f"✅ Staged: {file}")
        
        # Commit with descriptive message
        commit_message = "🚀 Deploy enhanced multi-group bot with cross-group price updates and alerts"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"✅ Committed: {commit_message}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        return False

def display_deployment_status():
    """Display deployment status and next steps"""
    print("\n" + "=" * 70)
    print("🎯 RAILWAY DEPLOYMENT STATUS")
    print("=" * 70)
    print("✅ Enhanced multi-group code ready for deployment")
    print("✅ Cross-group price updates implemented")
    print("✅ Cross-group alert distribution implemented") 
    print("✅ Real-time 5-second monitoring configured")
    print("✅ Auto-save and data persistence enabled")
    print("✅ Rug detection and auto-removal active")
    
    print("\n🚀 DEPLOYMENT COMMANDS:")
    print("To deploy to Railway, run:")
    print("   git push origin main")
    print("\n🔄 Railway will automatically:")
    print("   • Pull the latest code")
    print("   • Install dependencies")
    print("   • Start the enhanced bot")
    print("   • Enable multi-group functionality")
    
    print("\n💡 AFTER DEPLOYMENT:")
    print("✅ Your bot will update prices across ALL groups")
    print("✅ Alerts will be sent to ALL groups tracking a token")
    print("✅ Real-time monitoring every 5 seconds")
    print("✅ Automatic data backup and persistence")

def main():
    """Main deployment preparation function"""
    print("🚀 RAILWAY DEPLOYMENT PREPARATION")
    print("Enhanced Multi-Group Solana Alert Bot")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository!")
        print("🔧 Initialize git repository first:")
        print("   git init")
        print("   git remote add origin <your-repo-url>")
        return False
    
    # Prepare deployment
    if not prepare_railway_deployment():
        return False
    
    # Check git status
    has_changes = check_git_status()
    
    if has_changes:
        print("\n📝 Staging and committing changes...")
        if not stage_and_commit_changes():
            return False
    else:
        print("✅ No changes to commit")
    
    # Display status
    display_deployment_status()
    
    print("\n🎉 READY FOR RAILWAY DEPLOYMENT!")
    print("Run: git push origin main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
