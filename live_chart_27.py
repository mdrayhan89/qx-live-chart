#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quotex Pro Trader — Automated Login & URL Parameter Version (Fixed)
✅ Bypasses HTML login completely using hardcoded credentials
✅ Reads URL parameters (?Pair=USDPHP_otc&timeframe=1) automatically
✅ Fully optimized for Render Cloud Deployment without start() argument bugs
"""
import asyncio
import threading
import time
import json
import os
import sys
import eel
import certifi
from pathlib import Path
from queue import Queue
from typing import Optional, Dict, List, Tuple

# ✅ SSL Setup
cert_path = certifi.where()
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = cert_path

try:
    from pyquotex.stable_api import Quotex
    from pyquotex.utils.processor import process_candles
    from pyquotex.config import credentials
except ImportError as e:
    print(f"\n❌ Error: Missing dependency - {e}")
    print("Run: pip install git+https://github.com/cleitonleonel/pyquotex.git@master\n")
    sys.exit(1)

# ======================
# ⚙️ CONFIG: Credentials & Console Verbosity
# ======================
CONSOLE_LEVEL = 1
QUOTEX_EMAIL = "trrayhanislam786@gmail.com"
QUOTEX_PASSWORD = "Mdrayhan@655"

def log(msg: str, level: int = 1):
    if level <= CONSOLE_LEVEL:
        print(msg)

# ======================
# Async Loop Manager
# ======================
ASYNC_LOOP = asyncio.new_event_loop()

def start_async_loop():
    asyncio.set_event_loop(ASYNC_LOOP)
    ASYNC_LOOP.run_forever()

threading.Thread(target=start_async_loop, daemon=True, name="AsyncLoop").start()

# ======================
# UI Update Queue
# ======================
UI_QUEUE = Queue()

def ui_loop():
    while True:
        try:
            payload = UI_QUEUE.get()
            if payload is None:
                break
            eel.updateChart(payload)()
            UI_QUEUE.task_done()
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"[UI Loop Error]: {e}")

threading.Thread(target=ui_loop, daemon=True, name="UIUpdater").start()

# ======================
# Global State & Asset Maps
# ======================
LAST_TICK_TIME = time.time()
ASSET_DISPLAY_MAP: Dict[str, str] = {}

forex_assets = {
    "AUDCAD": "AUD/CAD", "AUDCAD_otc": "AUD/CAD (OTC)", "AUDCHF": "AUD/CHF", "AUDCHF_otc": "AUD/CHF (OTC)",
    "AUDJPY": "AUD/JPY", "AUDJPY_otc": "AUD/JPY (OTC)", "AUDNZD_otc": "AUD/NZD (OTC)", "AUDUSD": "AUD/USD",
    "AUDUSD_otc": "AUD/USD (OTC)", "CADJPY": "CAD/JPY", "CADJPY_otc": "CAD/JPY (OTC)", "CADCHF_otc": "CAD/CHF (OTC)",
    "CHFJPY": "CHF/JPY", "CHFJPY_otc": "CHF/JPY (OTC)", "EURAUD": "EUR/AUD", "EURAUD_otc": "EUR/AUD (OTC)",
    "EURCAD": "EUR/CAD", "EURCAD_otc": "EUR/CAD (OTC)", "EURCHF": "EUR/CHF", "EURCHF_otc": "EUR/CHF (OTC)",
    "EURGBP": "EUR/GBP", "EURGBP_otc": "EUR/GBP (OTC)", "EURJPY": "EUR/JPY", "EURJPY_otc": "EUR/JPY (OTC)",
    "EURNZD_otc": "EUR/NZD (OTC)", "EURSGD_otc": "EUR/SGD (OTC)", "EURUSD": "EUR/USD", "EURUSD_otc": "EUR/USD (OTC)",
    "GBPAUD": "GBP/AUD", "GBPAUD_otc": "GBP/AUD (OTC)", "GBPCAD": "GBP/CAD", "GBPCAD_otc": "GBP/CAD (OTC)",
    "GBPCHF": "GBP/CHF", "GBPCHF_otc": "GBP/CHF (OTC)", "GBPJPY": "GBP/JPY", "GBPJPY_otc": "GBP/JPY (OTC)",
    "GBPNZD_otc": "GBP/NZD (OTC)", "GBPUSD": "GBP/USD", "GBPUSD_otc": "GBP/USD (OTC)", "NZDCAD_otc": "NZD/CAD (OTC)",
    "NZDCHF_otc": "NZD/CHF (OTC)", "NZDJPY_otc": "NZD/JPY (OTC)", "NZDUSD_otc": "NZD/USD (OTC)", "USDCAD": "USD/CAD",
    "USDCAD_otc": "USD/CAD (OTC)", "USDCHF": "USD/CHF", "USDCHF_otc": "USD/CHF (OTC)", "USDJPY": "USD/JPY",
    "USDJPY_otc": "USD/JPY (OTC)", "USDARS_otc": "USD/ARS (OTC)", "USDBDT_otc": "USD/BDT (OTC)", "USDCOP_otc": "USD/COP (OTC)",
    "USDDZD_otc": "USD/DZD (OTC)", "USDEGP_otc": "USD/EGP (OTC)", "USDIDR_otc": "USD/IDR (OTC)", "USDINR_otc": "USD/INR (OTC)",
    "USDMXN_otc": "USD/MXN (OTC)", "USDNGN_otc": "USD/NGN (OTC)", "USDPHP_otc": "USD/PHP (OTC)", "USDPKR_otc": "USD/PKR (OTC)",
    "USDTRY_otc": "USD/TRY (OTC)", "USDZAR_otc": "USD/ZAR (OTC)",
}
ASSET_DISPLAY_MAP.update(forex_assets)

crypto_assets = {
    "ADAUSD_otc": "Cardano (OTC)", "APTUSD_otc": "Aptos (OTC)", "ARBUSD_otc": "Arbitrum (OTC)", "ATOUSD_otc": "ATO (OTC)",
    "AVAUSD_otc": "Avalanche (OTC)", "AXSUSD_otc": "Axie Infinity (OTC)", "BCHUSD_otc": "Bitcoin Cash (OTC)",
    "BNBUSD_otc": "Binance Coin (OTC)", "BONUSD_otc": "Bonk (OTC)", "BTCUSD_otc": "Bitcoin (OTC)", "DASUSD_otc": "Dash (OTC)",
    "DOGUSD_otc": "Dogecoin (OTC)", "DOTUSD_otc": "Polkadot (OTC)", "ETCUSD_otc": "Ethereum Classic (OTC)",
    "ETHUSD_otc": "Ethereum (OTC)", "FLOUSD_otc": "Floki (OTC)", "GALUSD_otc": "Gala (OTC)", "HMSUSD_otc": "Hamster Kombat (OTC)",
    "LINUSD_otc": "Chainlink (OTC)", "LTCUSD_otc": "Litecoin (OTC)", "MELUSD_otc": "Melania Meme (OTC)",
    "SHIBUSD_otc": "Shiba Inu (OTC)", "SOLUSD_otc": "Solana (OTC)", "TIAUSD_otc": "Celestia (OTC)", "TONUSD_otc": "Toncoin (OTC)",
    "TRUUSD_otc": "TrueFi (OTC)", "TRXUSD_otc": "TRON (OTC)", "WIFUSD_otc": "Dogwifhat (OTC)", "XRPUSD_otc": "Ripple (OTC)",
    "ZECUSD_otc": "Zcash (OTC)",
}
ASSET_DISPLAY_MAP.update(crypto_assets)

commodities_assets = {
    "XAUUSD": "Gold", "XAUUSD_otc": "Gold (OTC)", "XAGUSD": "Silver", "XAGUSD_otc": "Silver (OTC)",
    "UKBrent_otc": "UK Brent (OTC)", "USCrude_otc": "US Crude (OTC)",
}
ASSET_DISPLAY_MAP.update(commodities_assets)

stocks_assets = {
    "AXP_otc": "American Express (OTC)", "BA_otc": "Boeing Company (OTC)", "FB_otc": "Facebook (OTC)",
    "INTC_otc": "Intel (OTC)", "JNJ_otc": "Johnson & Johnson (OTC)", "MCD_otc": "McDonald's (OTC)",
    "MSFT_otc": "Microsoft (OTC)", "PFE_otc": "Pfizer Inc (OTC)", "PEPUSD_otc": "PepsiCo (OTC)",
}
ASSET_DISPLAY_MAP.update(stocks_assets)

indices_assets = {
    "DJIUSD": "Dow Jones", "NDXUSD": "NASDAQ 100", "F40EUR": "CAC 40", "FTSGBP": "FTSE 100",
    "HSIHKD": "Hong Kong 50", "IBXEUR": "IBEX 35", "JPXJPY": "Nikkei 225", "CHIA50": "China A50",
    "STXEUR": "EURO STOXX 50",
}
ASSET_DISPLAY_MAP.update(indices_assets)

DISPLAY_TO_INTERNAL = {v: k for k, v in ASSET_DISPLAY_MAP.items()}
ASSET_CATEGORIES = {
    "💱 Forex": list(forex_assets.values()),
    "₿ Crypto": list(crypto_assets.values()),
    "🛢️ Commodities": list(commodities_assets.values()),
    "🏦 Stocks": list(stocks_assets.values()),
    "📊 Indices": list(indices_assets.values()),
}
TIMEFRAMES = {
    "5s": 5, "10s": 10, "15s": 15, "30s": 30,
    "1m": 60, "2m": 120, "3m": 180, "5m": 300,
    "10m": 600, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400
}

CLIENT: Optional[Quotex] = None
CURRENT_ASSET = "USD/PHP (OTC)"  # Default Asset
CURRENT_TIMEFRAME = "1m"          # Default Timeframe
CANDLES: Dict[str, Dict[str, List[dict]]] = {}
CURRENT_CANDLE: Dict[str, Dict[str, dict]] = {}
SERVER_TIME_OFFSET = 0
CANDLE_COLORS = {
    "upColor": "#00C510", "downColor": "#ff0000",
    "borderUpColor": "#00C510", "borderDownColor": "#ff0000",
    "wickUpColor": "#00C510", "wickDownColor": "#ff0000"
}
ASSETS_LOADED = False
LOGIN_SUCCESS = False
REALTIME_RUNNING = False
CHART_OPENED = False
BACKGROUND_LOADER_TASK = None

# ======================
# Core Logic & Watchers
# ======================
def is_websocket_connected() -> bool:
    try:
        if not CLIENT or not CLIENT.api: return False
        if hasattr(CLIENT.api, '_is_connected'): return bool(CLIENT.api._is_connected)
        if hasattr(CLIENT.api, 'websocket_client'):
            ws = CLIENT.api.websocket_client
            if hasattr(ws, 'wss') and hasattr(ws.wss, 'sock'):
                return ws.wss.sock is not None and getattr(ws.wss.sock, 'connected', False)
        return True
    except Exception:
        return False

async def realtime_heartbeat():
    while True:
        await asyncio.sleep(45)
        if CLIENT and CURRENT_ASSET and is_websocket_connected():
            log("💓 heartbeat ok", level=2)

async def market_activity_ping():
    while True:
        await asyncio.sleep(180)
        try:
            if not CLIENT or not CLIENT.api or CURRENT_ASSET is None: continue
            internal_asset = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET, "USDPHP_otc")
            period_sec = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
            candles = await CLIENT.get_candles(asset=internal_asset, end_from_time=time.time(), offset=period_sec * 2, period=period_sec)
            log(f"📡 Market ping: {len(candles) if candles else 0} candles", level=2)
        except Exception as e:
            log(f"⚠️ Market ping failed: {str(e)[:80]}", level=2)

def price_sleep_watcher():
    global LAST_TICK_TIME, REALTIME_RUNNING
    while True:
        time.sleep(20)
        diff = time.time() - LAST_TICK_TIME
        if diff > 60 and CLIENT and CLIENT.api and CURRENT_ASSET and not REALTIME_RUNNING:
            log(f"♻️ Stream idle {int(diff)}s — restarting", level=1)
            try:
                internal = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
                if internal and is_websocket_connected():
                    period = TIMEFRAMES.get(CURRENT_TIMRAME, 60)
                    asyncio.run_coroutine_threadsafe(CLIENT.start_realtime_price(internal, period), ASYNC_LOOP).result(timeout=10)
                    LAST_TICK_TIME = time.time()
            except Exception as e:
                log(f"❌ Restart failed: {e}", level=2)

threading.Thread(target=price_sleep_watcher, daemon=True, name="PriceWatcher").start()

def process_candle_data(raw_candles: List[dict], period: int) -> List[dict]:
    if not raw_candles: return []
    if raw_candles and not raw_candles[0].get("open"):
        try: return process_candles(raw_candles, period)
        except Exception: pass
    formatted = []
    for c in raw_candles:
        if not isinstance(c, dict): continue
        try:
            if not all(k in c for k in ("time", "open", "high", "low", "close")): continue
            formatted.append({
                "time": (int(float(c["time"])) // period) * period,
                "open": float(c["open"]), "high": float(c["high"]), "low": float(c["low"]), "close": float(c["close"])
            })
        except Exception: continue
    formatted.sort(key=lambda x: x["time"])
    return formatted

def update_candle(asset: str, frame: str, price: float, ts_sec: int):
    global CANDLES, CURRENT_CANDLE
    duration = TIMEFRAMES.get(frame, 60)
    candle_start = (ts_sec // duration) * duration
    curr = CURRENT_CANDLE.get(asset, {}).get(frame, {})
    if not curr or curr.get("time") != candle_start:
        if curr:
            if asset not in CANDLES: CANDLES[asset] = {}
            if frame not in CANDLES[asset]: CANDLES[asset][frame] = []
            CANDLES[asset][frame].append(curr.copy())
            if len(CANDLES[asset][frame]) > 200: CANDLES[asset][frame] = CANDLES[asset][frame][-200:]
        if asset not in CURRENT_CANDLE: CURRENT_CANDLE[asset] = {}
        CURRENT_CANDLE[asset][frame] = {"time": int(candle_start), "open": float(price), "high": float(price), "low": float(price), "close": float(price)}
    else:
        if price > curr["high"]: curr["high"] = float(price)
        if price < curr["low"]: curr["low"] = float(price)
        curr["close"] = float(price)

def send_to_ui(asset: str, timeframe: str):
    global CANDLES, CURRENT_CANDLE, SERVER_TIME_OFFSET
    all_candles = CANDLES.get(asset, {}).get(timeframe, []).copy()
    curr = CURRENT_CANDLE.get(asset, {}).get(timeframe)
    if curr:
        if all_candles and all_candles[-1]["time"] == curr["time"]: all_candles[-1] = curr
        else: all_candles.append(curr)
    all_candles.sort(key=lambda x: x["time"])
    payload = {
        "candles": all_candles, "asset": asset, "timeframe": timeframe,
        "timeframe_seconds": TIMEFRAMES.get(timeframe, 60),
        "server_time": time.time() + SERVER_TIME_OFFSET,
        "last_candle_time": int(curr["time"]) if curr else 0
    }
    if UI_QUEUE.qsize() < 3:
        UI_QUEUE.put(payload)
        return True
    return False

async def realtime_price_loop(asset_display: str):
    global LAST_TICK_TIME, REALTIME_RUNNING
    internal = DISPLAY_TO_INTERNAL.get(asset_display)
    if not internal or not CLIENT: return
    REALTIME_RUNNING = True
    while REALTIME_RUNNING:
        try:
            data = await CLIENT.get_realtime_price(internal)
            if data:
                latest = data[-1]
                price = float(latest.get("price", latest.get("close", 0)))
                timestamp = latest.get("time", time.time())
                if price > 0 and timestamp > 0:
                    ts_sec = int(float(timestamp))
                    LAST_TICK_TIME = time.time()
                    SERVER_TIME_OFFSET = timestamp - time.time()
                    for frame in TIMEFRAMES:
                        update_candle(asset_display, frame, price, ts_sec)
                    send_to_ui(asset_display, CURRENT_TIMEFRAME)
            await asyncio.sleep(0.2)
        except Exception:
            await asyncio.sleep(1)

async def load_timeframe_data(asset_display: str, tf_name: str, period_sec: int) -> List[dict]:
    global CANDLES
    if not CLIENT or not CLIENT.api: return []
    internal = DISPLAY_TO_INTERNAL.get(asset_display, "USDPHP_otc")
    try:
        hist_data = await CLIENT.get_candles(asset=internal, end_from_time=time.time(), offset=199 * period_sec, period=period_sec)
        loaded = process_candle_data(hist_data, period_sec)
        if asset_display not in CANDLES: CANDLES[asset_display] = {}
        CANDLES[asset_display][tf_name] = loaded[-199:]
        return loaded[-199:]
    except Exception:
        return []

async def smart_background_loader(asset_display: str):
    priority_order = ["5m", "15m", "30m", "1h", "10s", "30s", "2m", "3m", "10m", "4h", "5s", "15s"]
    for tf in priority_order:
        if CURRENT_ASSET != asset_display: break
        if tf == CURRENT_TIMEFRAME or tf in CANDLES.get(asset_display, {}): continue
        try:
            await load_timeframe_data(asset_display, tf, TIMEFRAMES[tf])
            await asyncio.sleep(1.5)
        except asyncio.CancelledError: break
        except Exception: pass

async def start_streaming(asset_display: str):
    global CURRENT_ASSET, REALTIME_RUNNING, BACKGROUND_LOADER_TASK
    if REALTIME_RUNNING: REALTIME_RUNNING = False; await asyncio.sleep(0.3)
    if BACKGROUND_LOADER_TASK: BACKGROUND_LOADER_TASK.cancel()
    if not CLIENT or not CLIENT.api: return
    
    internal = DISPLAY_TO_INTERNAL.get(asset_display)
    if not internal: return
    
    CURRENT_ASSET = asset_display
    period_sec = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
    await load_timeframe_data(asset_display, CURRENT_TIMEFRAME, period_sec)
    send_to_ui(CURRENT_ASSET, CURRENT_TIMEFRAME)
    
    try: await CLIENT.start_realtime_price(internal, period_sec)
    except Exception: pass
    
    asyncio.create_task(realtime_price_loop(asset_display))
    BACKGROUND_LOADER_TASK = asyncio.create_task(smart_background_loader(asset_display))

# ======================
# Automated Background Login
# ======================
async def connect_to_quotex_automated():
    global CLIENT, ASSETS_LOADED, LOGIN_SUCCESS
    log("🔐 Initiating Automatic Quotex Login...", level=1)
    for attempt in range(1, 6):
        try:
            CLIENT = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, host="qxbroker.com", lang="en")
            check, reason = await CLIENT.connect()
            if check:
                await CLIENT.change_account("PRACTICE")
                await CLIENT.get_all_assets()
                ASSETS_LOADED = True
                LOGIN_SUCCESS = True
                asyncio.create_task(realtime_heartbeat())
                asyncio.create_task(market_activity_ping())
                log("✅ Quotex Auto Login Successful!", level=1)
                return
            log(f"⚠️ Login attempt {attempt} failed: {reason}. Retrying...", level=1)
            await asyncio.sleep(3)
        except Exception as e:
            log(f"❌ Error during auto-login attempt {attempt}: {e}", level=1)
            await asyncio.sleep(3)

def run_auto_login():
    future = asyncio.run_coroutine_threadsafe(connect_to_quotex_automated(), ASYNC_LOOP)
    try: future.result(timeout=60)
    except Exception as e: print(f"Auto login thread error: {e}")

threading.Thread(target=run_auto_login, daemon=True, name="AutoLoginThread").start()

# ======================
# Eel Exposed Functions & URL Processing
# ======================
@eel.expose
def process_url_parameters(pair_param: Optional[str], tf_param: Optional[str]):
    """Processes parameters passed from browser URL query strings"""
    global CURRENT_TIMEFRAME, CURRENT_ASSET
    
    # URL Format parsing logic
    if not pair_param: pair_param = "USDPHP_otc"
    if not tf_param or tf_param == "1": tf_param = "1m"
    elif tf_param.isdigit(): tf_param = f"{tf_param}m"
    
    # Internal code to display name handling
    display_name = ASSET_DISPLAY_MAP.get(pair_param, pair_param)
    if display_name not in DISPLAY_TO_INTERNAL and pair_param in DISPLAY_TO_INTERNAL:
        display_name = pair_param
        
    if tf_param in TIMEFRAMES:
        CURRENT_TIMEFRAME = tf_param
        
    log(f"📥 URL Request -> Asset: {display_name} | Timeframe: {CURRENT_TIMEFRAME}", level=1)
    
    def run():
        # Wait until backend authentication is done
        while not LOGIN_SUCCESS:
            time.sleep(0.5)
        future = asyncio.run_coroutine_threadsafe(start_streaming(display_name), ASYNC_LOOP)
        future.result(timeout=20)
        
    threading.Thread(target=run, daemon=True).start()

@eel.expose
def change_asset(asset_display: str):
    threading.Thread(target=lambda: asyncio.run_coroutine_threadsafe(start_streaming(asset_display), ASYNC_LOOP).result(), daemon=True).start()

@eel.expose
def change_timeframe(tf: str):
    global CURRENT_TIMEFRAME
    if tf not in TIMEFRAMES: return
    CURRENT_TIMEFRAME = tf
    if tf in CANDLES.get(CURRENT_ASSET, {}):
        send_to_ui(CURRENT_ASSET, tf)
    else:
        threading.Thread(target=lambda: [asyncio.run_coroutine_threadsafe(load_timeframe_data(CURRENT_ASSET, tf, TIMEFRAMES[tf]), ASYNC_LOOP).result(), send_to_ui(CURRENT_ASSET, tf)], daemon=True).start()

@eel.expose
def get_asset_categories(): return ASSET_CATEGORIES
@eel.expose
def get_timeframes(): return list(TIMEFRAMES.keys())
@eel.expose
def get_candle_colors(): return CANDLE_COLORS
@eel.expose
def get_connection_status():
    return {"connected": is_websocket_connected(), "assets_loaded": ASSETS_LOADED, "current_asset": CURRENT_ASSET, "current_timeframe": CURRENT_TIMEFRAME, "login_success": LOGIN_SUCCESS}

# ======================
# Dynamic HTML Generator
# ======================
def write_chart_html():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Quotex Live Pro Chart</title>
    <script src="/eel.js"></script>
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { margin: 0; background-color: #0c0d14; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow: hidden; }
        #header { height: 50px; background: #131722; display: flex; align-items: center; padding: 0 20px; border-bottom: 1px solid #2a2e39; justify-content: space-between; }
        .brand { font-weight: bold; color: #00c510; font-size: 18px; }
        .status-box { font-size: 13px; background: #1e222d; padding: 5px 12px; border-radius: 4px; border: 1px solid #2a2e39; }
        #chart-container { width: 100vw; height: calc(100vh - 50px); }
        #loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; background: rgba(19,23,34,0.9); padding: 20px; border-radius: 8px; border: 1px solid #2a2e39; z-index: 99; }
    </style>
</head>
<body>
    <div id="loading">🔐 Connecting & Authenticating Background Session...</div>
    <div id="header">
        <div class="brand">📈 QUOTEX LIVE CHART</div>
        <div id="asset-info" style="font-weight: 600;">Loading Asset...</div>
        <div class="status-box" id="status">Status: Synchronizing...</div>
    </div>
    <div id="chart-container"></div>

    <script>
        let chart, candlestickSeries;
        
        function initChart() {
            const container = document.getElementById('chart-container');
            chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: { backgroundColor: '#0c0d14', textColor: '#d1d4dc' },
                grid: { vertLines: { color: '#1f222e' }, horzLines: { color: '#1f222e' } },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                rightPriceScale: { borderColor: '#2a2e39' },
                timeScale: { borderColor: '#2a2e39', timeVisible: true, secondsVisible: true }
            });
            candlestickSeries = chart.addCandlestickSeries({
                upColor: '#00C510', downColor: '#ff0000',
                borderUpColor: '#00C510', borderDownColor: '#ff0000',
                wickUpColor: '#00C510', wickDownColor: '#ff0000'
            });
            
            window.addEventListener('resize', () => {
                chart.resize(container.clientWidth, container.clientHeight);
            });
        }

        eel.expose(updateChart);
        function updateChart(data) {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('asset-info').innerText = `${data.asset} (${data.timeframe})`;
            document.getElementById('status').innerHTML = `<span style="color:#00c510">● Live Connected</span>`;
            
            if (data.candles && data.candles.length > 0) {
                candlestickSeries.setData(data.candles);
            }
        }

        window.addEventListener('DOMContentLoaded', () => {
            initChart();
            
            const urlParams = new URLSearchParams(window.location.search);
            const pair = urlParams.get('Pair');      
            const timeframe = urlParams.get('timeframe'); 
            
            function checkLoginAndLoad() {
                eel.get_connection_status()(status => {
                    if (status.login_success) {
                        document.getElementById('loading').innerText = "📊 Loading Market Candles...";
                        eel.process_url_parameters(pair, timeframe);
                    } else {
                        setTimeout(checkLoginAndLoad, 1000);
                    }
                });
            }
            checkLoginAndLoad();
        });
    </script>
</body>
</html>"""
    with open("web/chart.html", "w", encoding="utf-8") as f:
        f.write(html_content)

# ======================
# Application Bootstrap
# ======================
if __name__ == '__main__':
    os.makedirs("web", exist_ok=True)
    write_chart_html()
    
    eel.init('web')
    port = int(os.environ.get("PORT", 8080))
    
    # 🛠️ FIXED: Removed 'page=' keyword to prevent TypeError on cloud instance
    eel.start('chart.html', host='0.0.0.0', port=port, mode=None)
