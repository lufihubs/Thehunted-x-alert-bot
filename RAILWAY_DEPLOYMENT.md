# 🚀 Railway Deployment Guide for Telegram Solana Alert Bot

## 📋 Pre-Deployment Checklist

✅ **Files Created:**
- `requirements.txt` - Python dependencies
- `Procfile` - Railway startup command
- `runtime.txt` - Python version specification  
- `railway.json` - Railway configuration
- `railway_start.py` - Production startup script
- `health_check.py` - Health monitoring endpoint
- `.gitignore` - Excludes sensitive/unnecessary files

## 🔧 Railway Setup Steps

### 1. **Create Railway Account & Project**
1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Connect your GitHub repository

### 2. **Configure Environment Variables**
In Railway dashboard, go to your project → Variables tab:

**Required:**
```
TELEGRAM_BOT_TOKEN=8301492869:AAE1sP4G54PqDQEIHs-9v49GCJ8rnz1aKqQ
```

**Optional (for better performance):**
```
BIRDEYE_API_KEY=your_birdeye_api_key
DEXSCREENER_API_KEY=your_dexscreener_api_key
DATABASE_PATH=/app/data/tokens.db
PORT=8000
```

### 3. **Enable Persistent Storage (Important!)**
1. In Railway dashboard → your service → Settings
2. Scroll to "Volumes" section
3. Click "Add Volume"
4. Mount path: `/app/data`
5. Size: `1GB` (sufficient for database)

### 4. **Deploy Settings**
Railway will auto-detect and use:
- `Procfile` for startup command
- `requirements.txt` for dependencies
- `runtime.txt` for Python version

## 🔄 Deployment Process

### **Automatic Deployment:**
1. Push your code to GitHub
2. Railway auto-deploys on every push to main branch
3. Monitor deployment in Railway dashboard

### **Manual Deployment:**
1. In Railway dashboard → Deployments
2. Click "Deploy Now"

## 📊 Monitoring Your Bot

### **Health Check:**
- URL: `https://your-app.railway.app/health`
- Returns bot status and timestamp
- Railway uses this for health monitoring

### **Logs:**
- Railway dashboard → your service → Logs
- Real-time log streaming
- Filter by severity level

### **Bot Status Commands:**
- `/status` - Check bot health in Telegram
- `/help` - View available commands

## ⚡ Performance Optimizations

### **Railway Features Used:**
- **Auto-scaling:** Handles traffic spikes
- **Health checks:** Automatic restart if unhealthy
- **Persistent volumes:** Database survives restarts
- **Environment variables:** Secure configuration

### **Bot Optimizations:**
- 15-second price monitoring intervals
- Multi-threshold loss alerts (-50%, -70%, -85%, -95%)
- Enhanced contract detection with punctuation
- Efficient database schema with SQLite

## 🛠️ Troubleshooting

### **Common Issues:**

**1. Bot not responding:**
- Check environment variables are set
- Verify Telegram bot token is correct
- Check logs for errors

**2. Database errors:**
- Ensure volume is mounted to `/app/data`
- Check database path in environment variables

**3. Memory/CPU issues:**
- Railway free tier: 512MB RAM, 1 vCPU
- Monitor resource usage in dashboard
- Consider upgrading plan for high-volume usage

**4. API rate limits:**
- Add BIRDEYE_API_KEY and DEXSCREENER_API_KEY
- These provide higher rate limits

### **Getting Help:**
- Railway logs: Real-time error monitoring
- Railway community: Discord support
- Bot logs: Detailed error messages

## 🎯 Post-Deployment Verification

### **Test Your Bot:**
1. **Start bot:** Send `/start` to your Telegram bot
2. **Add token:** Send a Solana contract address
3. **Check alerts:** Verify you receive price alerts
4. **Monitor logs:** Watch Railway dashboard logs

### **Expected Behavior:**
- Bot responds to commands instantly
- Price checks every 15 seconds
- Multi-level loss alerts (-50%, -70%, -85%, -95%)
- Enhanced contract detection (handles punctuation)
- Database persistence across restarts

## 🎉 Success Indicators

✅ **Deployment successful** - Railway shows "Active"  
✅ **Health check passing** - `/health` endpoint responds  
✅ **Bot responsive** - Telegram commands work  
✅ **Monitoring active** - Price checks running every 15s  
✅ **Alerts working** - Receiving loss notifications  

## 💡 Railway Benefits for Your Bot

- **24/7 uptime** - No more missed rug alerts
- **Auto-restart** - Bot recovers from crashes
- **Scalable** - Handles multiple users/tokens
- **Persistent data** - Token tracking survives restarts
- **Real-time logs** - Easy debugging and monitoring

Your bot is now ready for **continuous online operation** with **4x faster rug detection**! 🚀
