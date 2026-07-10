import ccxt
import pandas as pd
import time
from datetime import datetime
import requests

# ================== تنظیمات ==================
SYMBOLS = ['XAUUSD', 'XAGUSD', 'BTCUSDT']
TIMEFRAMES = ['15m', '1h', '4h']

TELEGRAM_TOKEN = '8961298923:AAFbuiQm0peaGQ4gssD34G0shYeBjk2RaN8'
TELEGRAM_CHAT_ID = '111954131'

# ================== ارسال تلگرام ==================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# پیام شروع
send_telegram("✅ <b>رصد بازار شروع شد</b>\nنمادها: طلا، نقره، بیت‌کوین\nتایم‌فریم: 15m, 1h, 4h\nربات فعال است...")

print("Bot Started - پیام شروع ارسال شد")

# ================== بقیه کد (QM + SNR) ==================
exchange = ccxt.bybit()

while True:
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, tf, limit=150)
                df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # QM Detection (ساده)
                if len(df) > 40:
                    h = df['high'].values
                    l = df['low'].values
                    c = df['close'].iloc[-1]
                    for i in range(8, len(df)-10):
                        if h[i+2] > h[i] and l[i+5] < l[i+1] and h[i] > h[i-4]:
                            msg = f"<b>🚨 Bearish QM</b>\nSymbol: {symbol}\nTF: {tf}\nPrice: {c:.2f}"
                            send_telegram(msg)
                        if l[i+2] < l[i] and h[i+5] > h[i+1] and l[i] < l[i-4]:
                            msg = f"<b>🚨 Bullish QM</b>\nSymbol: {symbol}\nTF: {tf}\nPrice: {c:.2f}"
                            send_telegram(msg)
                
                # SNR Detection
                if len(df) > 30:
                    recent_high = df['high'].rolling(20).max().iloc[-1]
                    recent_low  = df['low'].rolling(20).min().iloc[-1]
                    price = df['close'].iloc[-1]
                    if abs(price - recent_high) / recent_high < 0.002:
                        send_telegram(f"<b>🔴 Near Resistance</b>\nSymbol: {symbol}\nPrice: {price:.2f}\nTF: {tf}")
                    elif abs(price - recent_low) / recent_low < 0.002:
                        send_telegram(f"<b>🟢 Near Support</b>\nSymbol: {symbol}\nPrice: {price:.2f}\nTF: {tf}")
                        
            except:
                pass
    
    time.sleep(120)
