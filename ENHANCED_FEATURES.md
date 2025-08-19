#  Enhanced Telegram Solana Alert Bot - Updated Features

##  **NEW FEATURES ADDED**

###  **Accurate Market Cap Capture**
- **Multiple Confirmations**: Takes 2-3 readings when first scanning a token for accuracy
- **Confirmed Scan Price**: Uses averaged initial readings as the baseline for alerts
- **High/Low Tracking**: Tracks the highest and lowest prices since scanning

###  **50% Loss Alert**
- **Risk Management**: Automatically alerts when token drops 50% or more from scan price
- **One-Time Alert**: Only sends the loss alert once per token to avoid spam
- **Clear Warning**: Includes risk management reminder in loss alerts

##  **Alert Types**

###  **Gain Alerts** (2x, 3x, 5x, 8x, 10x, 15x, 20x, 25x, 30x, 40x, 50x, 75x, 100x)
`
 **5x ALERT** 

 **TokenName (SYMBOL)**
 **5x** from scan!
 **+400.0%** gain

 **Market Cap:** .5M
 **Price:** .00012345
 **Scan Cap:** 

 **CA:** contract_address
 **Time:** 14:30:25 UTC

[Platform Links]
`

###  **Loss Alert** (-50% or more)
`
 **50% LOSS ALERT** 

 **TokenName (SYMBOL)**
 **-65.5%** from scan!
 **Down 50%+** from entry

 **Current Cap:** 
 **Current Price:** .00004321
 **Scan Cap:** 

 **CA:** contract_address
 **Time:** 14:30:25 UTC

 **Consider your risk management!**

[Platform Links]
`

##  **Improved Accuracy**

1. **Enhanced Scanning**: 
   - Takes multiple readings when first detecting a token
   - Uses averaged values for more accurate baseline
   - Confirms market cap over 2-3 checks

2. **Better Data Sources**:
   - Primary: Birdeye API (most comprehensive)
   - Secondary: pump.fun API (for new tokens)
   - Fallback: DexScreener API

3. **Platform Detection**:
   - Automatically identifies token source (pump.fun, Raydium, etc.)
   - Optimizes data fetching based on platform

##  **Enhanced Database**

New fields added for better tracking:
- confirmed_scan_mcap - Verified initial market cap
- lowest_mcap / highest_mcap - Price range tracking
- loss_50_alerted - Prevents duplicate loss alerts
- scan_confirmation_count - Accuracy counter

##  **Bot Commands Updated**

- /start - Welcome message with new features
- /help - Updated help including loss alerts
- /stats - Enhanced statistics with loss tracking
- /track <address> - Manual tracking with improved accuracy
- /stop <address> - Stop tracking any token

##  **Ready to Use!**

Your enhanced bot is now running with:
 **More accurate initial market cap detection**
 **50% loss risk management alerts**
 **Better data source reliability**
 **Enhanced tracking capabilities**

Just post contract addresses in your group and the bot will automatically track them with improved accuracy and send both gain and loss alerts! 
