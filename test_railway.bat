@echo off
echo 🧪 Testing Railway Deployment Readiness...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run deployment test
python test_deployment.py

echo.
echo ✅ Test complete! Check output above.
echo.
echo 🚀 If all tests passed, you're ready for Railway deployment!
echo 📖 See DEPLOY_NOW.md for quick deploy steps
echo 📋 See RAILWAY_DEPLOYMENT.md for detailed guide

pause
