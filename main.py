import ccxt
import pandas as pd
import time
from datetime import datetime
import requests

# ================== تنظیمات ==================
SYMBOLS = ['XAUUSD', 'XAGUSD', 'BTCUSDT']
TIMEFRAMES = ['5m', '15m', '1h', '4h']

TELEGRAM_TOKEN = '8961298923:AAFbuiQm0peaGQ4gssD34G0shYeBjk2RaN8'
TELEGRAM_CHAT_ID = '111954131'

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

# پیام شروع
send_telegram("✅ <b>رصد بازار به سبک نورا شروع شد</b>\nنمادها: طلا، نقره، بیت‌کوین\nتایم‌فریم: 5m,15m,1h,4h")

exchange = ccxt.bybit()

while True:
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=100)
                df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','vol'])
                df['ts'] = pd.to_datetime(df['ts'], unit='ms')
                c = df['close'].iloc[-1]
                
                # Double Marubozu Detection (DMD)
                is_bull_dmd = (df['close'].iloc[-1] > df['open'].iloc[-1] and 
                               df['close'].iloc[-2] > df['open'].iloc[-2] and 
                               df['close'].iloc[-1] > df['open'].iloc[-1] * 1.001)
                is_bear_dmd = (df['close'].iloc[-1] < df['open'].iloc[-1] and 
                               df['close'].iloc[-2] < df['open'].iloc[-2] and 
                               df['close'].iloc[-1] < df['open'].iloc[-1] * 0.999)
                
                direction = "صعودی 🟢" if is_bull_dmd else "نزولی 🔴" if is_bear_dmd else "خنثی"
                
                # QM ساده
                if len(df) > 30:
                    h = df['high'].values
                    l = df['low'].values
                    for i in range(5, len(df)-8):
                        if h[i+2] > h[i] and l[i+5] < l[i+1]:
                            msg = f"<b>🚨 Bearish QM</b>\nنماد: {symbol}\nتایم‌فریم: {tf}\nجهت: {direction}\nقیمت: {c:.2f}"
                            if is_bull_dmd: msg += "\n⚠️ Double Marubozu صعودی وجود دارد"
                            send_telegram(msg)
                        if l[i+2] < l[i] and h[i+5] > h[i+1]:
                            msg = f"<b>🚨 Bullish QM</b>\nنماد: {symbol}\nتایم‌فریم: {tf}\nجهت: {direction}\nقیمت: {c:.2f}"
                            if is_bear_dmd: msg += "\n⚠️ Double Marubozu نزولی وجود دارد"
                            send_telegram(msg)
                
                # Danger Zone ساده (نزدیک highs/lows قوی)
                recent_high = df['high'].rolling(20).max().iloc[-1]
                recent_low = df['low'].rolling(20).min().iloc[-1]
                if abs(c - recent_high)/recent_high < 0.0015:
                    send_telegram(f"⚠️ <b>Danger Zone (Resistance)</b>\nنماد: {symbol}\nTF: {tf}\nقیمت نزدیک Resistance قوی")
                if abs(c - recent_low)/recent_low < 0.0015:
                    send_telegram(f"⚠️ <b>Danger Zone (Support)</b>\nنماد: {symbol}\nTF: {tf}\nقیمت نزدیک Support قوی")
                    
            except:
                pass
    
    time.sleep(90)  # چک سریع‌تر
