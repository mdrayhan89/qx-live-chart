#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quotex Pro Trader — CLEAN CONSOLE VERSION
✅ Minimal console output - only essential messages
✅ Official PyQuotex Login + Hybrid Lazy Loading
✅ Candle loading starts AFTER chart is opened
✅ Loads 1m timeframe FIRST, then others gradually
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
# ⚙️ CONFIG: Console Verbosity Level
# ======================
# 0 = Silent (only errors)
# 1 = Minimal (essential status only) ← DEFAULT
# 2 = Verbose (debug info)
CONSOLE_LEVEL = 1

def log(msg: str, level: int = 1):
    """Print only if level <= CONSOLE_LEVEL"""
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
# Global State
# ======================
LAST_TICK_TIME = time.time()
ASSET_DISPLAY_MAP: Dict[str, str] = {}

# ✅ Assets Maps (Forex, Crypto, Commodities, Stocks, Indices)
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
CURRENT_ASSET = "AUD/CAD (OTC)"
CURRENT_TIMEFRAME = "1m"
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
# Helpers
# ======================
def is_websocket_connected() -> bool:
    try:
        if not CLIENT or not CLIENT.api:
            return False
        if hasattr(CLIENT.api, '_is_connected'):
            return bool(CLIENT.api._is_connected)
        if hasattr(CLIENT.api, 'websocket_client'):
            ws = CLIENT.api.websocket_client
            if hasattr(ws, 'wss') and hasattr(ws.wss, 'sock'):
                return ws.wss.sock is not None and getattr(ws.wss.sock, 'connected', False)
            if hasattr(ws, 'connected'):
                return bool(ws.connected)
        if hasattr(CLIENT.api, 'check_connect'):
            return CLIENT.api.check_connect()
        return True
    except Exception:
        return False

async def realtime_heartbeat():
    global CLIENT, CURRENT_ASSET
    while True:
        await asyncio.sleep(45)
        try:
            if CLIENT and CURRENT_ASSET and is_websocket_connected():
                log("💓 heartbeat ok", level=2)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ Heartbeat error: {e}")

async def market_activity_ping():
    global CLIENT, CURRENT_ASSET, CURRENT_TIMEFRAME
    while True:
        await asyncio.sleep(180)
        try:
            if not CLIENT or not CLIENT.api or CURRENT_ASSET is None:
                continue
            internal_asset = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET, "AUDCAD_otc")
            period_sec = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
            candles = await CLIENT.get_candles(
                asset=internal_asset,
                end_from_time=time.time(),
                offset=period_sec * 2,
                period=period_sec
            )
            log(f"📡 Market ping: {len(candles) if candles else 0} candles", level=2)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ Market ping failed: {str(e)[:80]}")

def price_sleep_watcher():
    global LAST_TICK_TIME, CLIENT, CURRENT_ASSET, ASYNC_LOOP, REALTIME_RUNNING
    while True:
        time.sleep(20)
        diff = time.time() - LAST_TICK_TIME
        if diff > 60:
            log(f"♻️ Stream idle {int(diff)}s — restarting", level=1)
            try:
                if CLIENT and CLIENT.api and CURRENT_ASSET and not REALTIME_RUNNING:
                    internal = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
                    if internal and is_websocket_connected():
                        period = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
                        future = asyncio.run_coroutine_threadsafe(
                            CLIENT.start_realtime_price(internal, period),
                            ASYNC_LOOP
                        )
                        future.result(timeout=10)
                        LAST_TICK_TIME = time.time()
            except Exception as e:
                if CONSOLE_LEVEL >= 2:
                    print(f"❌ Restart failed: {e}")

threading.Thread(target=price_sleep_watcher, daemon=True, name="PriceWatcher").start()

def safe_stop_realtime_price(asset: str):
    if CLIENT and CLIENT.api:
        try:
            future = asyncio.run_coroutine_threadsafe(
                CLIENT.stop_realtime_price(asset),
                ASYNC_LOOP
            )
            future.result(timeout=5)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ stop_realtime_price error: {e}")

def process_candle_data(raw_candles: List[dict], period: int) -> List[dict]:
    if not raw_candles:
        return []
    if raw_candles and not raw_candles[0].get("open"):
        try:
            return process_candles(raw_candles, period)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ process_candles failed: {e}")
    formatted = []
    for c in raw_candles:
        if not isinstance(c, dict):
            continue
        try:
            if not all(k in c for k in ("time", "open", "high", "low", "close")):
                continue
            candle_time = int(float(c["time"]))
            aligned_time = (candle_time // period) * period
            formatted.append({
                "time": aligned_time,
                "open": float(c["open"]), "high": float(c["high"]),
                "low": float(c["low"]), "close": float(c["close"])
            })
        except (ValueError, KeyError, TypeError):
            continue
    formatted.sort(key=lambda x: x["time"])
    return formatted

def update_candle(asset: str, frame: str, price: float, ts_sec: int):
    global CANDLES, CURRENT_CANDLE
    duration = TIMEFRAMES.get(frame, 60)
    candle_start = (ts_sec // duration) * duration
    curr = CURRENT_CANDLE.get(asset, {}).get(frame, {})
    if not curr or curr.get("time") != candle_start:
        if curr:
            if asset not in CANDLES:
                CANDLES[asset] = {}
            if frame not in CANDLES[asset]:
                CANDLES[asset][frame] = []
            CANDLES[asset][frame].append(curr.copy())
            if len(CANDLES[asset][frame]) > 200:
                CANDLES[asset][frame] = CANDLES[asset][frame][-200:]
        if asset not in CURRENT_CANDLE:
            CURRENT_CANDLE[asset] = {}
        CURRENT_CANDLE[asset][frame] = {
            "time": int(candle_start), "open": float(price), "high": float(price),
            "low": float(price), "close": float(price)
        }
    else:
        if price > curr["high"]: curr["high"] = float(price)
        if price < curr["low"]: curr["low"] = float(price)
        curr["close"] = float(price)

def send_to_ui(asset: str, timeframe: str):
    global CANDLES, CURRENT_CANDLE, SERVER_TIME_OFFSET
    all_candles = CANDLES.get(asset, {}).get(timeframe, []).copy()
    curr = CURRENT_CANDLE.get(asset, {}).get(timeframe)
    if curr:
        if all_candles and all_candles[-1]["time"] == curr["time"]:
            all_candles[-1] = curr
        else:
            all_candles.append(curr)
    all_candles.sort(key=lambda x: x["time"])
    payload = {
        "candles": [
            {"time": int(c["time"]), "open": float(c["open"]), "high": float(c["high"]),
             "low": float(c["low"]), "close": float(c["close"])} for c in all_candles
        ],
        "asset": asset, "timeframe": timeframe,
        "timeframe_seconds": TIMEFRAMES.get(timeframe, 60),
        "server_time": time.time() + SERVER_TIME_OFFSET,
        "last_candle_time": int(curr["time"]) if curr else 0
    }
    if UI_QUEUE.qsize() < 3:
        UI_QUEUE.put(payload)
        return True
    return False

# 🔥 Realtime price loop
async def realtime_price_loop(asset_display: str):
    global LAST_TICK_TIME, REALTIME_RUNNING
    if REALTIME_RUNNING:
        log(f"⚠️ Loop already running for {asset_display}", level=2)
        stop_realtime_loop()
        await asyncio.sleep(0.5)
    internal = DISPLAY_TO_INTERNAL.get(asset_display)
    if not internal or not CLIENT:
        return
    REALTIME_RUNNING = True
    log(f"🔄 realtime_price_loop started", level=2)
    while REALTIME_RUNNING:
        try:
            data = await CLIENT.get_realtime_price(internal)
            if data and len(data) > 0:
                latest = data[-1]
                price = float(latest.get("price", latest.get("close", 0)))
                timestamp = latest.get("time", time.time())
                if price > 0 and timestamp > 0:
                    ts_sec = int(float(timestamp))
                    LAST_TICK_TIME = time.time()
                    SERVER_TIME_OFFSET = timestamp - time.time()
                    for frame in TIMEFRAMES:
                        update_candle(asset_display, frame, price, ts_sec)
                    if send_to_ui(asset_display, CURRENT_TIMEFRAME):
                        if CONSOLE_LEVEL >= 2:
                            print(f"📤 Live: {price:.5f} @ {asset_display}/{CURRENT_TIMEFRAME}", end="\r")
            await asyncio.sleep(0.2)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ realtime_price_loop error: {e}")
            await asyncio.sleep(1)
    log(f"⏹️ realtime_price_loop stopped", level=2)

def stop_realtime_loop():
    global REALTIME_RUNNING
    REALTIME_RUNNING = False

# ======================
# Connection & Streaming — CLEAN VERSION
# ======================
async def load_timeframe_data(asset_display: str, tf_name: str, period_sec: int) -> List[dict]:
    global CANDLES
    if not CLIENT or not CLIENT.api:
        return []
    internal = DISPLAY_TO_INTERNAL.get(asset_display, "AUDCAD_otc")
    if not internal:
        return []
    try:
        log(f"📥 Loading {tf_name}...", level=2)
        hist_data = await CLIENT.get_candles(
            asset=internal, end_from_time=time.time(),
            offset=199 * period_sec, period=period_sec
        )
        loaded = process_candle_data(hist_data, period_sec)
        log(f"✅ {tf_name}: {len(loaded)} candles", level=2)
        if asset_display not in CANDLES:
            CANDLES[asset_display] = {}
        CANDLES[asset_display][tf_name] = loaded[-199:]
        return loaded[-199:]
    except Exception as e:
        if CONSOLE_LEVEL >= 2:
            print(f"⚠️ Failed to load {tf_name}: {e}")
        return []

# 🔥 Chart Open Handler
async def chart_opened_loader(asset_display: str):
    global CHART_OPENED, BACKGROUND_LOADER_TASK
    if CHART_OPENED:
        return
    CHART_OPENED = True
    log(f"📊 Chart opened — loading candles...", level=1)
    
    # Step 1: Load 1m first
    await load_timeframe_data(asset_display, "1m", TIMEFRAMES["1m"])
    send_to_ui(asset_display, "1m")
    
    # Step 2: Start realtime
    internal = DISPLAY_TO_INTERNAL.get(asset_display)
    if internal:
        for i in range(3):
            try:
                await CLIENT.start_realtime_price(internal, TIMEFRAMES["1m"])
                break
            except Exception as e:
                if CONSOLE_LEVEL >= 2:
                    print(f"⚠️ Retry {i+1}/3: {e}")
                await asyncio.sleep(2)
        asyncio.create_task(realtime_price_loop(asset_display))
        # Step 3: Background loader
        BACKGROUND_LOADER_TASK = asyncio.create_task(smart_background_loader(asset_display))

# 🔥 Smart Background Loader — CLEAN
async def smart_background_loader(asset_display: str):
    priority_order = ["5m", "15m", "30m", "1h", "10s", "30s", "2m", "3m", "10m", "4h", "5s", "15s"]
    for tf in priority_order:
        if CURRENT_ASSET != asset_display:
            break
        if tf == CURRENT_TIMEFRAME or tf in CANDLES.get(asset_display, {}):
            continue
        try:
            await load_timeframe_data(asset_display, tf, TIMEFRAMES[tf])
            await asyncio.sleep(2)  # Rate limit protection
        except asyncio.CancelledError:
            break
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ Background error {tf}: {e}")
            await asyncio.sleep(3)

# 🔥 Official PyQuotex Login — CLEAN
async def connect_with_retry(max_attempts: int = 5) -> Tuple[bool, str]:
    global CLIENT
    for attempt in range(1, max_attempts + 1):
        try:
            email, password = credentials()
            CLIENT = Quotex(email=email, password=password, host="qxbroker.com", lang="en")
            check, reason = await CLIENT.connect()
            if check:
                return True, reason
            session_file = Path("session.json")
            if session_file.exists():
                session_file.unlink()
            if attempt < max_attempts:
                await asyncio.sleep(2)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"❌ Attempt {attempt}: {e}")
            if attempt < max_attempts:
                await asyncio.sleep(2)
    return False, "Connection failed"

async def connect_to_quotex(email: str, password: str) -> Tuple[bool, str]:
    global CLIENT, ASSETS_LOADED, LOGIN_SUCCESS
    try:
        log("🔐 Connecting...", level=1)
        config_dir = Path.home() / ".pyquotex"
        config_dir.mkdir(parents=True, exist_ok=True)
        creds_file = config_dir / "credentials.json"
        with open(creds_file, 'w') as f:
            json.dump({"email": email, "password": password}, f)
        success, reason = await connect_with_retry(max_attempts=5)
        if not success:
            if creds_file.exists():
                creds_file.unlink()
            return False, reason
        await CLIENT.change_account("PRACTICE")
        await CLIENT.get_all_assets()
        ASSETS_LOADED = True
        asyncio.create_task(realtime_heartbeat())
        asyncio.create_task(market_activity_ping())
        LOGIN_SUCCESS = True
        log("✅ Login successful", level=1)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

async def start_streaming(asset_display: str):
    global CURRENT_ASSET, CANDLES, CURRENT_CANDLE, REALTIME_RUNNING, BACKGROUND_LOADER_TASK
    if REALTIME_RUNNING:
        stop_realtime_loop()
        await asyncio.sleep(0.5)
    if BACKGROUND_LOADER_TASK:
        BACKGROUND_LOADER_TASK.cancel()
        await asyncio.sleep(0.2)
    if not CLIENT or not CLIENT.api:
        return
    internal = DISPLAY_TO_INTERNAL.get(asset_display)
    if not internal:
        return
    if CURRENT_ASSET and CLIENT:
        old_internal = DISPLAY_TO_INTERNAL.get(CURRENT_ASSET)
        if old_internal:
            safe_stop_realtime_price(old_internal)
    CURRENT_ASSET = asset_display
    if asset_display not in CANDLES:
        CANDLES[asset_display] = {}
    if asset_display not in CURRENT_CANDLE:
        CURRENT_CANDLE[asset_display] = {}
    period_sec = TIMEFRAMES.get(CURRENT_TIMEFRAME, 60)
    await load_timeframe_data(asset_display, CURRENT_TIMEFRAME, period_sec)
    send_to_ui(CURRENT_ASSET, CURRENT_TIMEFRAME)
    await asyncio.sleep(1)
    subscription_success = False
    for i in range(3):
        try:
            await CLIENT.start_realtime_price(internal, period_sec)
            subscription_success = True
            break
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"⚠️ Retry {i+1}/3: {e}")
            await asyncio.sleep(2)
    if subscription_success:
        asyncio.create_task(realtime_price_loop(asset_display))
        BACKGROUND_LOADER_TASK = asyncio.create_task(smart_background_loader(asset_display))

# ======================
# Eel Functions
# ======================
@eel.expose
def login(email: str, password: str):
    def run():
        try:
            future = asyncio.run_coroutine_threadsafe(connect_to_quotex(email, password), ASYNC_LOOP)
            success, reason = future.result(timeout=60)
            if success:
                eel.onLoginSuccess()()
            else:
                eel.onLoginError(reason)()
        except Exception as e:
            eel.onLoginError(f"{type(e).__name__}: {str(e)}")()
    threading.Thread(target=run, daemon=True).start()

@eel.expose
def on_chart_opened():
    def run():
        try:
            if not LOGIN_SUCCESS:
                return
            future = asyncio.run_coroutine_threadsafe(chart_opened_loader(CURRENT_ASSET), ASYNC_LOOP)
            future.result(timeout=30)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"❌ Chart open error: {e}")
    threading.Thread(target=run, daemon=True).start()

@eel.expose
def change_asset(asset_display: str):
    def run():
        try:
            if not LOGIN_SUCCESS:
                time.sleep(2)
            future = asyncio.run_coroutine_threadsafe(start_streaming(asset_display), ASYNC_LOOP)
            future.result(timeout=15)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"❌ change_asset error: {e}")
    threading.Thread(target=run, daemon=True).start()

@eel.expose
def change_timeframe(tf: str):
    global CURRENT_TIMEFRAME
    if tf not in TIMEFRAMES:
        return
    CURRENT_TIMEFRAME = tf
    if tf in CANDLES.get(CURRENT_ASSET, {}):
        send_to_ui(CURRENT_ASSET, tf)
        return
    def load():
        try:
            future = asyncio.run_coroutine_threadsafe(
                load_timeframe_data(CURRENT_ASSET, tf, TIMEFRAMES[tf]), ASYNC_LOOP)
            future.result(timeout=15)
            send_to_ui(CURRENT_ASSET, tf)
        except Exception as e:
            if CONSOLE_LEVEL >= 2:
                print(f"❌ Load error {tf}: {e}")
    threading.Thread(target=load, daemon=True).start()

@eel.expose
def get_asset_categories():
    return ASSET_CATEGORIES

@eel.expose
def get_timeframes():
    return list(TIMEFRAMES.keys())

@eel.expose
def apply_candle_colors(colors: dict):
    global CANDLE_COLORS
    CANDLE_COLORS = colors
    eel.updateCandleColors(colors)()

@eel.expose
def get_candle_colors():
    return CANDLE_COLORS

@eel.expose
def get_connection_status():
    if CLIENT and CLIENT.api:
        return {
            "connected": is_websocket_connected(),
            "assets_loaded": ASSETS_LOADED,
            "current_asset": CURRENT_ASSET,
            "current_timeframe": CURRENT_TIMEFRAME,
            "login_success": LOGIN_SUCCESS,
            "realtime_running": REALTIME_RUNNING,
            "chart_opened": CHART_OPENED
        }
    return {"connected": False, "assets_loaded": False, "login_success": False}



# ======================
# HTML Template Writers - PLACEHOLDERS
# ======================
def write_login_html():
    with open("web/login.html", "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Login — QuotexChart</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="/eel.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #050814;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: 'Cormorant Garamond', serif;
  overflow: hidden;
  position: relative;
}

/* خلفية زخرفية باللون الأزرق */
body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(30, 58, 138, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
    repeating-linear-gradient(45deg, rgba(0,0,0,0.3) 0px, rgba(0,0,0,0.3) 1px, transparent 1px, transparent 11px),
    repeating-linear-gradient(-45deg, rgba(0,0,0,0.3) 0px, rgba(0,0,0,0.3) 1px, transparent 1px, transparent 11px),
    linear-gradient(180deg, #0a1020 0%, #050814 100%);
  z-index: -2;
}

/* الإطار الزخرفي */
.ornate-container {
  position: relative;
  padding: 20px;
  background: linear-gradient(135deg, rgba(30, 58, 138, 0.15) 0%, rgba(15, 23, 42, 0.2) 100%);
  border-radius: 4px;
}

/* الزخارف الزاوية باللون الأزرق الفضي */
.corner {
  position: absolute;
  width: 40px;
  height: 40px;
  border: 2px solid #3b82f6;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.corner-tl { top: 0; left: 0; border-right: 0; border-bottom: 0; }
.corner-tr { top: 0; right: 0; border-left: 0; border-bottom: 0; }
.corner-bl { bottom: 0; left: 0; border-right: 0; border-top: 0; }
.corner-br { bottom: 0; right: 0; border-left: 0; border-top: 0; }

.corner::after {
  content: '❧';
  position: absolute;
  color: #60a5fa;
  font-size: 16px;
  opacity: 0.9;
  text-shadow: 0 0 8px rgba(96, 165, 250, 0.6);
}

.corner-tl::after { top: -10px; left: -5px; }
.corner-tr::after { top: -10px; right: -5px; transform: scaleX(-1); }
.corner-bl::after { bottom: -10px; left: -5px; transform: scaleY(-1); }
.corner-br::after { bottom: -10px; right: -5px; transform: scale(-1, -1); }

/* البطاقة الرئيسية */
.card {
  width: 320px;
  background: linear-gradient(180deg, #0f172a 0%, #0a0f1d 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
  padding: 35px 30px;
  position: relative;
  box-shadow: 
    0 10px 40px rgba(0,0,0,0.8),
    inset 0 1px 0 rgba(255,255,255,0.05),
    0 0 0 1px rgba(0,0,0,0.5),
    0 0 30px rgba(30, 58, 138, 0.2);
}

/* خطوط زخرفية علوية وسفلية باللون الأزرق */
.card::before,
.card::after {
  content: '';
  position: absolute;
  left: 20px;
  right: 20px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
}

.card::before { top: 12px; }
.card::after { bottom: 12px; }

/* الشعار باللون الأزرق الفضي */
h2 {
  font-family: 'Cinzel', serif;
  color: #93c5fd;
  text-align: center;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 3px;
  margin-bottom: 8px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.8), 0 0 20px rgba(147, 197, 253, 0.3);
  position: relative;
}

h2::after {
  content: '◆';
  display: block;
  text-align: center;
  font-size: 8px;
  color: #3b82f6;
  margin-top: 8px;
  letter-spacing: normal;
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.8);
}

/* النص الفرعي */
.subtitle {
  text-align: center;
  font-size: 12px;
  color: #64748b;
  font-style: italic;
  margin-bottom: 28px;
  letter-spacing: 1px;
}

/* حقول الإدخال */
.inp-group {
  position: relative;
  margin-bottom: 18px;
}

.inp {
  width: 100%;
  padding: 12px 15px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 0;
  color: #bfdbfe;
  font-family: 'Cormorant Garamond', serif;
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
}

.inp:focus {
  border-color: #3b82f6;
  background: rgba(15, 23, 42, 0.8);
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
}

.inp::placeholder {
  color: #475569;
  font-style: italic;
}

/* خط زخرفي تحت الحقول */
.inp-group::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.4), transparent);
}

/* زر إظهار كلمة المرور */
.password-wrapper {
  position: relative;
}

.toggle-pass {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.toggle-pass:hover {
  opacity: 1;
}

.toggle-pass svg {
  width: 16px;
  height: 16px;
  fill: #3b82f6;
}

/* زر الدخول باللون الأزرق */
.btn {
  width: 100%;
  padding: 14px;
  margin-top: 25px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #3b82f6;
  color: #93c5fd;
  font-family: 'Cinzel', serif;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  text-transform: uppercase;
  box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(147, 197, 253, 0.1), transparent);
  transition: left 0.5s;
}

.btn:hover {
  background: linear-gradient(180deg, #1e293b 0%, #1e40af 100%);
  border-color: #60a5fa;
  box-shadow: 0 5px 25px rgba(59, 130, 246, 0.4);
  text-shadow: 0 0 8px rgba(147, 197, 253, 0.6);
  color: #bfdbfe;
}

.btn:hover::before {
  left: 100%;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Spinner */
.spinner {
  display: none;
  width: 24px;
  height: 24px;
  border: 2px solid rgba(59, 130, 246, 0.2);
  border-top: 2px solid #93c5fd;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 15px auto 0;
  box-shadow: 0 0 10px rgba(147, 197, 253, 0.3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* رسالة الخطأ */
.error {
  color: #f87171;
  text-align: center;
  margin-top: 12px;
  font-size: 12px;
  font-style: italic;
  min-height: 18px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}

/* زخرفة سفلية صغيرة */
.footer-ornament {
  text-align: center;
  margin-top: 20px;
  color: #334155;
  font-size: 10px;
  letter-spacing: 2px;
}

.footer-ornament span {
  color: #3b82f6;
  text-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
}

/* تأثيرات إضافية */
.glow {
  position: absolute;
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
  pointer-events: none;
  z-index: -1;
}

.glow-1 { top: -100px; left: -100px; }
.glow-2 { bottom: -100px; right: -100px; }

/* التذييل مع الاسم */
.footer {
  position: absolute;
  bottom: 20px;
  width: 100%;
  text-align: center;
  font-size: 11px;
  color: #475569;
  font-family: 'Cinzel', serif;
  letter-spacing: 1px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.8);
}

.footer b {
  color: #60a5fa;
  font-weight: 600;
}
</style>
<base target="_blank">
</head>
<body>

<div class="ornate-container">
  <div class="corner corner-tl"></div>
  <div class="corner corner-tr"></div>
  <div class="corner corner-bl"></div>
  <div class="corner corner-br"></div>
  
  <div class="card">
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>
    
    <h2>QuotexChart</h2>
    <div class="subtitle">~ Veritas et Tempus ~</div>
    
    <div class="inp-group">
      <input type="email" id="email" class="inp" placeholder="Email" required>
    </div>
    
    <div class="inp-group password-wrapper">
      <input type="password" id="password" class="inp" placeholder="Password" required>
      <span class="toggle-pass" onclick="togglePassword()">
        <svg id="eyeOpen" viewBox="0 0 24 24">
          <path d="M12 5C7 5 3.1 8 1.5 12c1.6 4 5.5 7 10.5 7s8.9-3 10.5-7C20.9 8 17 5 12 5zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>
        </svg>
        <svg id="eyeClosed" viewBox="0 0 24 24" style="display:none">
          <path d="M2 5.3 3.3 4l17 17-1.3 1.3-3.1-3.1C14.7 19.7 13.4 20 12 20 7 20 3.1 17 1.5 13c.7-1.7 1.8-3.2 3.2-4.4L2 5.3z"/>
        </svg>
      </span>
    </div>
    
    <button class="btn" onclick="login()">Enter</button>
    <div class="spinner" id="spinner"></div>
    <div class="error" id="error"></div>
    
    <div class="footer-ornament">
      <span>✦</span> ☙ <span>✦</span>
    </div>
  </div>
</div>

<div class="footer">
  Designed & Developed by <b>BADI SALAH</b> © 2026
</div>

<script>
async function login() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  if (!email || !password) {
    showError("Please enter your credentials");
    return;
  }
  showSpinner();
  try {
    await eel.login(email, password)();
  } catch {
    hideSpinner();
    showError("Connection failed");
  }
}

function togglePassword() {
  const pass = document.getElementById('password');
  const open = document.getElementById('eyeOpen');
  const closed = document.getElementById('eyeClosed');
  if (pass.type === "password") {
    pass.type = "text";
    open.style.display = "none";
    closed.style.display = "block";
  } else {
    pass.type = "password";
    open.style.display = "block";
    closed.style.display = "none";
  }
}

function showSpinner() {
  document.getElementById('spinner').style.display = 'block';
  document.querySelector('.btn').disabled = true;
  document.getElementById('error').textContent = '';
}

function hideSpinner() {
  document.getElementById('spinner').style.display = 'none';
  document.querySelector('.btn').disabled = false;
}

function showError(msg) {
  document.getElementById('error').textContent = msg;
}

document.addEventListener('keydown', e => {
  if (e.key === "Enter") login();
});

eel.expose(onLoginSuccess);
function onLoginSuccess() {
  window.location.href = 'chart.html';
}

eel.expose(onLoginError);
function onLoginError(reason) {
  hideSpinner();
  showError(reason || "Access denied");
}
</script>

</body>
</html>''')


def write_chart_html():
    with open("web/chart.html", "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quotex Pro Trader</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="/eel.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
:root { 
    --bg: #050814; 
    --panel: #0a0f1c; 
    --border: #1e3a8a; 
    --text: #bfdbfe; 
    --accent: #60a5fa;
    --gold: #d4af37;
    --silver: #94a3b8;
    --glow: rgba(96, 165, 250, 0.15);
}

html, body { 
    margin:0; 
    height:100%; 
    background: radial-gradient(circle at 20% 30%, rgba(30, 58, 138, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
                linear-gradient(180deg, #0a0f1c 0%, #050814 100%);
    color: var(--text); 
    font-family: 'Cormorant Garamond', serif;
    overflow:hidden; 
}

/* ✅ شريط الأدوات بالأسلوب العتيق */
#toolbar {
    height: 40px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 16px;
    background: linear-gradient(180deg, #0f172a 0%, #0a0f1c 100%);
    border-bottom: 1px solid rgba(59, 130, 246, 0.3);
    box-shadow: 0 2px 20px rgba(0, 0, 0, 0.5);
    font-family: 'Cinzel', serif;
    font-size: 11px;
    letter-spacing: 1px;
}

.btn {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.4);
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    font-size: 10px;
    font-family: 'Cinzel', serif;
    letter-spacing: 1px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
}

.btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(147, 197, 253, 0.1), transparent);
    transition: left 0.5s;
}

.btn:hover {
    background: linear-gradient(180deg, #1e293b 0%, #1e40af 100%);
    border-color: #60a5fa;
    color: #bfdbfe;
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
    transform: translateY(-1px);
}

.btn:hover::before {
    left: 100%;
}

.btn.active { 
    background: linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%);
    color: #fff; 
    border-color: #60a5fa;
    box-shadow: 0 0 12px rgba(96, 165, 250, 0.4);
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

/* ✅ أيقونات SVG باللون الأزرق الفضي */
.icon-chart, .icon-clock, .icon-settings, .icon-close { 
    width: 14px; 
    height: 14px; 
    stroke: #60a5fa;
    filter: drop-shadow(0 0 2px rgba(96, 165, 250, 0.5));
}

/* ✅ عنوان الأصل بالذهبي */
#currentAsset {
    color: var(--gold);
    text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    font-weight: 600;
    letter-spacing: 1px;
    margin-right: auto;
    font-size: 12px;
}

/* ✅ Modal بالأسلوب العتيق الأزرق */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(5, 8, 20, 0.85);
    backdrop-filter: blur(8px);
    z-index: 1000;
    display: none;
    justify-content: center;
    align-items: center;
}

.modal-card {
    background: linear-gradient(180deg, #0f172a 0%, #0a0f1c 100%);
    border: 1px solid rgba(59, 130, 246, 0.4);
    border-radius: 8px;
    box-shadow: 0 0 40px rgba(30, 58, 138, 0.3), 0 10px 40px rgba(0, 0, 0, 0.6);
    width: 480px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
}

/* زخارف Modal */
.modal-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 20px;
    right: 20px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #3b82f6, transparent);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: rgba(30, 58, 138, 0.15);
    border-bottom: 1px solid rgba(59, 130, 246, 0.2);
}

.modal-title {
    font-family: 'Cinzel', serif;
    font-size: 13px;
    font-weight: 600;
    color: #60a5fa;
    letter-spacing: 2px;
    text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
}

.modal-close {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 50%;
    transition: all 0.3s ease;
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
    background: rgba(15, 23, 42, 0.5);
}

.modal-close:hover {
    background: rgba(59, 130, 246, 0.2);
    transform: rotate(90deg);
    border-color: #60a5fa;
    box-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
}

.modal-search {
    padding: 16px 24px;
    border-bottom: 1px solid rgba(59, 130, 246, 0.15);
}

.modal-search-input {
    width: 100%;
    padding: 10px 14px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    color: #bfdbfe;
    font-family: 'Cormorant Garamond', serif;
    font-size: 13px;
    outline: none;
    transition: all 0.3s ease;
}

.modal-search-input:focus {
    border-color: #60a5fa;
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    background: rgba(15, 23, 42, 0.8);
}

.modal-search-input::placeholder {
    color: #475569;
    font-style: italic;
}

.modal-content {
    overflow-y: auto;
    flex: 1;
    padding: 16px;
}

/* ✅ تصنيفات الأصول */
.modal-category {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(30, 58, 138, 0.12);
    font-family: 'Cinzel', serif;
    font-weight: 600;
    font-size: 10px;
    color: #60a5fa;
    border-radius: 4px;
    margin-bottom: 8px;
    margin-top: 12px;
    border-left: 3px solid #3b82f6;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.modal-category:first-child {
    margin-top: 0;
}

/* ✅ عناصر الأصول */
.modal-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.3s ease;
    font-size: 12px;
    color: #93c5fd;
    margin-bottom: 6px;
    border: 1px solid transparent;
    font-family: 'Cormorant Garamond', serif;
}

.modal-item:hover {
    background: rgba(59, 130, 246, 0.12);
    color: #bfdbfe;
    transform: translateX(4px);
    border-color: rgba(59, 130, 246, 0.3);
    box-shadow: 0 2px 8px rgba(30, 58, 138, 0.2);
}

.modal-item.active {
    background: rgba(59, 130, 246, 0.2);
    color: #fff;
    font-weight: 600;
    border-color: rgba(96, 165, 250, 0.5);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
}

.modal-item.active::after {
    content: "✦";
    font-size: 12px;
    color: #d4af37;
    text-shadow: 0 0 5px rgba(212, 175, 55, 0.5);
}

/* ✅ Timeframes Grid */
.tf-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    padding: 16px;
}

.tf-btn {
    padding: 12px;
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    cursor: pointer;
    text-align: center;
    font-size: 11px;
    color: #93c5fd;
    font-family: 'Cinzel', serif;
    letter-spacing: 1px;
    transition: all 0.3s ease;
}

.tf-btn:hover {
    background: linear-gradient(180deg, #1e293b 0%, #1e40af 100%);
    border-color: rgba(96, 165, 250, 0.6);
    color: #bfdbfe;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
}

.tf-btn.active {
    background: linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%);
    border-color: #60a5fa;
    color: #fff;
    font-weight: 600;
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
}

/* ✅ Settings Panel بالأسلوب العتيق */
#settings-panel {
    position: absolute;
    top: 45px;
    right: 16px;
    background: linear-gradient(180deg, #0f172a 0%, #0a0f1c 100%);
    border: 1px solid rgba(59, 130, 246, 0.4);
    border-radius: 8px;
    padding: 20px;
    width: 280px;
    z-index: 200;
    display: none;
    font-family: 'Cormorant Garamond', serif;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(30, 58, 138, 0.2);
}

.settings-section {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(59, 130, 246, 0.15);
}

.settings-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.settings-title {
    font-family: 'Cinzel', serif;
    font-size: 11px;
    font-weight: 600;
    color: #60a5fa;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    border-left: 2px solid #3b82f6;
    padding-left: 8px;
}

.setting-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 8px 0;
}

.setting-row label {
    font-size: 11px;
    color: #93c5fd;
}

/* ✅ Color Inputs مزخرفة */
.setting-row input[type="color"] {
    width: 36px;
    height: 24px;
    border: 1px solid rgba(59, 130, 246, 0.4);
    background: #0f172a;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
}

.settings-btns {
    display: flex;
    gap: 10px;
    margin-top: 16px;
}

.settings-btns button {
    flex: 1;
    padding: 8px;
    font-size: 10px;
    font-family: 'Cinzel', serif;
    letter-spacing: 1px;
    border: 1px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    text-transform: uppercase;
}

.apply-btn { 
    background: linear-gradient(180deg, #1e40af 0%, #1e3a8a 100%);
    color: #fff;
    border-color: rgba(96, 165, 250, 0.5);
}

.apply-btn:hover {
    background: linear-gradient(180deg, #2563eb 0%, #1e40af 100%);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    transform: translateY(-1px);
}

.cancel-btn { 
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    color: #94a3b8;
    border-color: rgba(59, 130, 246, 0.3);
}

.cancel-btn:hover {
    background: linear-gradient(180deg, #334155 0%, #1e293b 100%);
    color: #bfdbfe;
    border-color: rgba(96, 165, 250, 0.5);
}

/* ✅ Scrollbar مزخرف */
.modal-content::-webkit-scrollbar {
    width: 6px;
}

.modal-content::-webkit-scrollbar-track {
    background: rgba(30, 58, 138, 0.1);
    border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.4);
    border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
    background: rgba(96, 165, 250, 0.6);
}

#chart { 
    height: calc(100% - 40px); 
    position: relative; 
}

/* ✅ علامة العد التنازلي الذهبية */
.countdown-label {
    color: #d4af37 !important;
    font-family: 'Cinzel', serif !important;
}
</style>
</head>
<body>
<div id="toolbar">
<div class="btn" id="assetsBtn">
    <svg class="icon-chart" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 3v18h18"/>
        <path d="M18 17V9"/>
        <path d="M13 17V5"/>
        <path d="M8 17v-3"/>
    </svg>
    Assets
</div>
<div class="btn" id="timeframesBtn">
    <svg class="icon-clock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
    </svg>
    Timeframes
</div>
<div id="currentAsset">AUD/CAD (OTC)</div>
<div id="currentTimeframe" class="btn active">1m</div>
<div class="btn" id="settingsBtn">
    <svg class="icon-settings" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
</div>
</div>

<div id="assetsModal" class="modal-overlay">
    <div class="modal-card">
        <div class="modal-header">
            <div class="modal-title">Select Asset</div>
            <div class="modal-close" onclick="closeAssetsModal()">
                <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </div>
        </div>
        <div class="modal-search">
            <input type="text" id="modalAssetSearch" class="modal-search-input" placeholder="Search assets..." autocomplete="off">
        </div>
        <div class="modal-content" id="assetsModalContent"></div>
    </div>
</div>

<div id="timeframesModal" class="modal-overlay">
    <div class="modal-card" style="width: 300px;">
        <div class="modal-header">
            <div class="modal-title">Select Timeframe</div>
            <div class="modal-close" onclick="closeTimeframesModal()">
                <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </div>
        </div>
        <div class="tf-grid" id="timeframesModalContent"></div>
    </div>
</div>

<div id="settings-panel">
    <div class="settings-section">
        <div class="settings-title">Candle Colors</div>
        <div class="setting-row">
            <label>Bull Body (Gold):</label>
            <input type="color" id="upColor" value="#d4af37">
        </div>
        <div class="setting-row">
            <label>Bull Border:</label>
            <input type="color" id="borderUpColor" value="#d4af37">
        </div>
        <div class="setting-row">
            <label>Bull Wick:</label>
            <input type="color" id="wickUpColor" value="#d4af37">
        </div>
        <div class="setting-row">
            <label>Bear Body (Silver):</label>
            <input type="color" id="downColor" value="#64748b">
        </div>
        <div class="setting-row">
            <label>Bear Border:</label>
            <input type="color" id="borderDownColor" value="#64748b">
        </div>
        <div class="setting-row">
            <label>Bear Wick:</label>
            <input type="color" id="wickDownColor" value="#64748b">
        </div>
    </div>

    <div class="settings-section">
        <div class="settings-title">Chart Appearance</div>
        <div class="setting-row">
            <label>Background:</label>
            <input type="color" id="chartBgColor" value="#0a0f1c">
        </div>
        <div class="setting-row">
            <label>Grid Lines:</label>
            <input type="color" id="gridColor" value="#1e293b">
        </div>
        <div class="setting-row">
            <label>Text Color:</label>
            <input type="color" id="textColor" value="#bfdbfe">
        </div>
    </div>

    <div class="settings-btns">
        <button class="apply-btn" onclick="applySettings()">Apply</button>
        <button class="cancel-btn" onclick="closeSettings()">Cancel</button>
    </div>
</div>

<div id="chart"></div>
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
<script>
let currentAsset = "AUD/CAD (OTC)";
let currentTimeframe = "1m";
let timeframeSeconds = 60;
let serverTimeOffset = 0;
let isFirstLoad = true;
let currentCandles = [];
let allCategories = null;
let needsFullRedraw = false;
let isUserInteracting = false;

let countdownLabel = null;
let lastCandleTime = 0;
let countdownAnimationId = null;

// ✅ إعدادات الألوان الفاخرة (ذهبي/فضي)
let chartColors = {
    background: '#0a0f1c',
    grid: '#1e293b',
    text: '#bfdbfe'
};

const chart = LightweightCharts.createChart(document.getElementById('chart'), {
layout: {
background: { color: chartColors.background },
textColor: chartColors.text,
fontFamily: "'Cormorant Garamond', serif"
},
grid: {
vertLines: { color: chartColors.grid, style: LightweightCharts.LineStyle.SparseDotted },
horzLines: { color: chartColors.grid, style: LightweightCharts.LineStyle.SparseDotted }
},
crosshair: { 
    mode: LightweightCharts.CrosshairMode.Normal,
    vertLine: {
        color: 'rgba(96, 165, 250, 0.5)',
        width: 1,
        style: LightweightCharts.LineStyle.Solid,
        labelBackgroundColor: '#1e40af'
    },
    horzLine: {
        color: 'rgba(96, 165, 250, 0.5)',
        width: 1,
        style: LightweightCharts.LineStyle.Solid,
        labelBackgroundColor: '#1e40af'
    }
},
handleScroll: { mouseWheel: true, pressedMouseMove: true },
handleScale: { axisPressedMouseMove: true, mouseWheel: false },
rightPriceScale: {
visible: true,
borderColor: 'rgba(59, 130, 246, 0.3)',
textColor: '#93c5fd',
entireTextOnly: false,
minimumWidth: 70,
scaleMargins: {
top: 0.15,
bottom: 0.15
}
},
timeScale: {
visible: true,
borderColor: 'rgba(59, 130, 246, 0.3)',
timeVisible: true,
secondsVisible: true,
minBarSpacing: 4,
maxBarSpacing: 15,
fixLeftEdge: false,
fixRightEdge: false,
borderVisible: true
}
});

// ✅ شموع ذهبية/فضية افتراضية
let candleSeries = chart.addCandlestickSeries({
upColor: '#d4af37',
downColor: '#64748b',
borderUpColor: '#d4af37',
borderDownColor: '#64748b',
wickUpColor: '#d4af37',
wickDownColor: '#64748b',
borderVisible: true,
priceFormat: {
type: 'price',
precision: 5,
minMove: 0.00001
},
lastValueVisible: false,
priceLineVisible: false
});

chart.subscribeCrosshairMove(() => {
    isUserInteracting = true;
});

chart.timeScale().subscribeVisibleTimeRangeChange(() => {
    isUserInteracting = true;
});

let interactionResetTimer = null;
function resetInteraction() {
    isUserInteracting = false;
}

const chartContainer = document.getElementById('chart');

chartContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const timeScale = chart.timeScale();
    const logicalRange = timeScale.getVisibleLogicalRange();
    if (!logicalRange) return;

    const rect = chartContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const ratio = mouseX / rect.width;
    const rangeSize = logicalRange.to - logicalRange.from;
    const intensity = Math.min(Math.abs(e.deltaY), 100) / 100;
    const zoomFactor = e.deltaY > 0 
        ? 1 + 0.15 * intensity
        : 1 - 0.15 * intensity;
    
    const newRange = rangeSize * zoomFactor;
    const center = logicalRange.from + rangeSize * ratio;
    const newFrom = center - newRange * ratio;
    const newTo = center + newRange * (1 - ratio);

    timeScale.setVisibleLogicalRange({
        from: newFrom,
        to: newTo
    });

    clearTimeout(interactionResetTimer);
    interactionResetTimer = setTimeout(resetInteraction, 300);

}, { passive: false });

function createCountdownLabel(candle) {
    const candleEndTime = candle.time + timeframeSeconds;

    if (countdownLabel) {
        candleSeries.removePriceLine(countdownLabel);
    }
    if (countdownAnimationId) {
        cancelAnimationFrame(countdownAnimationId);
    }

    countdownLabel = candleSeries.createPriceLine({
        price: candle.close,
        color: '#d4af37',
        lineWidth: 0,
        axisLabelVisible: true,
        title: '⏱ --:--',
    });

    countdownLabel.candleEndTime = candleEndTime;
    animateCountdown();
}

function animateCountdown() {
    if (!countdownLabel || currentCandles.length === 0) return;

    const now = Date.now() / 1000;
    let remaining = Math.max(0, Math.floor(countdownLabel.candleEndTime - now));
    
    const mins = Math.floor(remaining / 60).toString().padStart(2, '0');
    const secs = (remaining % 60).toString().padStart(2, '0');

    const lastPrice = currentCandles[currentCandles.length - 1].close;

    countdownLabel.applyOptions({
        price: lastPrice,
        title: `⏱ ${mins}:${secs}`
    });

    countdownAnimationId = requestAnimationFrame(animateCountdown);
}

function openAssetsModal() {
    renderAssetsModal();
    document.getElementById('assetsModal').style.display = 'flex';
    document.getElementById('modalAssetSearch').focus();
}

function closeAssetsModal() {
    document.getElementById('assetsModal').style.display = 'none';
}

function openTimeframesModal() {
    renderTimeframesModal();
    document.getElementById('timeframesModal').style.display = 'flex';
}

function closeTimeframesModal() {
    document.getElementById('timeframesModal').style.display = 'none';
}

document.getElementById('assetsModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeAssetsModal();
});

document.getElementById('timeframesModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeTimeframesModal();
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAssetsModal();
        closeTimeframesModal();
        closeSettings();
    }
});

function renderAssetsModal(searchTerm = '') {
    const content = document.getElementById('assetsModalContent');
    let html = '';
    const term = searchTerm.toLowerCase();
    
    for (const [category, assets] of Object.entries(allCategories)) {
        const filteredAssets = assets.filter(asset => asset.toLowerCase().includes(term));
        if (filteredAssets.length > 0) {
            html += `<div class="modal-category">${category}</div>`;
            filteredAssets.forEach(asset => {
                const isActive = asset === currentAsset;
                html += `<div class="modal-item ${isActive ? 'active' : ''}" onclick="selectAsset('${asset}')">${asset}</div>`;
            });
        }
    }
    
    if (!html && searchTerm) {
        html = '<div style="padding: 30px; text-align: center; color: #475569; font-size: 13px; font-style: italic;">No matching assets found</div>';
    }
    
    content.innerHTML = html;
}

function selectAsset(asset) {
    currentAsset = asset;
    needsFullRedraw = true;
    document.getElementById('currentAsset').textContent = currentAsset;
    eel.change_asset(currentAsset)();
    closeAssetsModal();
    isFirstLoad = true;
}

function renderTimeframesModal() {
    const content = document.getElementById('timeframesModalContent');
    const tfs = ["5s", "10s", "15s", "30s", "1m", "2m", "3m", "5m", "10m", "15m", "30m", "1h", "4h"];
    
    let html = '';
    tfs.forEach(tf => {
        const isActive = tf === currentTimeframe;
        html += `<div class="tf-btn ${isActive ? 'active' : ''}" onclick="selectTimeframe('${tf}')">${tf}</div>`;
    });
    
    content.innerHTML = html;
}

function selectTimeframe(tf) {
    currentTimeframe = tf;
    needsFullRedraw = true;
    timeframeSeconds = {
        "5s":5,"10s":10,"15s":15,"30s":30,
        "1m":60,"2m":120,"3m":180,"5m":300,
        "10m":600,"15m":900,"30m":1800,
        "1h":3600,"4h":14400
    }[currentTimeframe];
    
    const tfBtn = document.getElementById('currentTimeframe');
    tfBtn.textContent = currentTimeframe;
    
    eel.change_timeframe(currentTimeframe)();
    closeTimeframesModal();
    isFirstLoad = true;
}

document.getElementById('settingsBtn').addEventListener('click', () => {
    const panel = document.getElementById('settings-panel');
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        eel.get_candle_colors()(function(colors) {
            document.getElementById('upColor').value = colors.upColor;
            document.getElementById('downColor').value = colors.downColor;
            document.getElementById('borderUpColor').value = colors.borderUpColor;
            document.getElementById('borderDownColor').value = colors.borderDownColor;
            document.getElementById('wickUpColor').value = colors.wickUpColor;
            document.getElementById('wickDownColor').value = colors.wickDownColor;
            
            document.getElementById('chartBgColor').value = chartColors.background;
            document.getElementById('gridColor').value = chartColors.grid;
            document.getElementById('textColor').value = chartColors.text;
            
            panel.style.display = 'block';
        });
    }
});

function applySettings() {
    const candleColors = {
        upColor: document.getElementById('upColor').value,
        downColor: document.getElementById('downColor').value,
        borderUpColor: document.getElementById('borderUpColor').value,
        borderDownColor: document.getElementById('borderDownColor').value,
        wickUpColor: document.getElementById('wickUpColor').value,
        wickDownColor: document.getElementById('wickDownColor').value
    };
    
    chartColors.background = document.getElementById('chartBgColor').value;
    chartColors.grid = document.getElementById('gridColor').value;
    chartColors.text = document.getElementById('textColor').value;
    
    chart.applyOptions({
        layout: {
            background: { color: chartColors.background },
            textColor: chartColors.text
        },
        grid: {
            vertLines: { color: chartColors.grid },
            horzLines: { color: chartColors.grid }
        },
        rightPriceScale: {
            borderColor: chartColors.grid,
            textColor: chartColors.text
        },
        timeScale: {
            borderColor: chartColors.grid
        }
    });
    
    needsFullRedraw = true;
    eel.apply_candle_colors(candleColors)();
    closeSettings();
}

function closeSettings() {
    document.getElementById('settings-panel').style.display = 'none';
}

eel.expose(updateCandleColors);
function updateCandleColors(colors) {
    chart.removeSeries(candleSeries);
    candleSeries = chart.addCandlestickSeries({
        upColor: colors.upColor,
        downColor: colors.downColor,
        borderUpColor: colors.borderUpColor,
        borderDownColor: colors.borderDownColor,
        wickUpColor: colors.wickUpColor,
        wickDownColor: colors.wickDownColor,
        borderVisible: true,
        priceFormat: {
            type: 'price',
            precision: 5,
            minMove: 0.00001
        },
        lastValueVisible: false,
        priceLineVisible: false
    });
    needsFullRedraw = true;
}

eel.get_asset_categories()(function(categories) {
    allCategories = categories;
    document.getElementById('assetsBtn').addEventListener('click', openAssetsModal);
    document.getElementById('timeframesBtn').addEventListener('click', openTimeframesModal);
});

document.getElementById('modalAssetSearch').addEventListener('input', (e) => {
    renderAssetsModal(e.target.value);
});

eel.get_timeframes()(function(tfs) {
});

eel.expose(updateChart);
function updateChart(data) {
    const candles = data.candles;
    currentCandles = candles;
    document.getElementById('currentAsset').textContent = data.asset;
    currentTimeframe = data.timeframe;
    timeframeSeconds = data.timeframe_seconds || 60;
    serverTimeOffset = (data.server_time || 0) - (Date.now() / 1000);

    const lastCandle = candles[candles.length - 1];
    const shouldUpdateCountdown = lastCandle && lastCandle.time !== lastCandleTime;

    if (isFirstLoad && data.candles && data.candles.length > 1) {
        candleSeries.setData(data.candles);
        
        if (lastCandle) {
            createCountdownLabel(lastCandle);
            lastCandleTime = lastCandle.time;
        }
        
        chart.timeScale().fitContent();
        isFirstLoad = false;
        return;
    }

    if (needsFullRedraw) {
        candleSeries.setData(candles);
        
        if (lastCandle) {
            createCountdownLabel(lastCandle);
            lastCandleTime = lastCandle.time;
        }
        
        chart.timeScale().fitContent();
        needsFullRedraw = false;
        return;
    }

    if (candles.length > 0 && isUserInteracting) {
        candleSeries.update(lastCandle);
        
        if (shouldUpdateCountdown) {
            createCountdownLabel(lastCandle);
            lastCandleTime = lastCandle.time;
        }
        return;
    }

    if (isFirstLoad && candles.length >= 150) {
        candleSeries.setData(candles);
        
        if (lastCandle) {
            createCountdownLabel(lastCandle);
            lastCandleTime = lastCandle.time;
        }
        
        chart.timeScale().fitContent();
        requestAnimationFrame(() => {
            chart.resize(
                document.getElementById('chart').clientWidth,
                document.getElementById('chart').clientHeight
            );
        });
        isFirstLoad = false;
    } else if (candles.length > 0) {
        candleSeries.update(lastCandle);
        
        if (shouldUpdateCountdown) {
            createCountdownLabel(lastCandle);
            lastCandleTime = lastCandle.time;
        }
    }
}

window.addEventListener('resize', () => {
    chart.resize(window.innerWidth, window.innerHeight - 40);
});

eel.change_asset(currentAsset)();
</script>
</body>
</html>''')

# ======================
# Main
# ======================
if __name__ == '__main__':
    os.makedirs("web", exist_ok=True)
    write_login_html()
    write_chart_html()
    
    if CONSOLE_LEVEL >= 1:
        print("🚀 Quotex Pro Trader — Clean Console Mode")
        print("✅ Minimal output | Hybrid Lazy Loading | Official Login")
    
    eel.init('web')
    
    # ✅ CHANGE FOR RENDER HOSTING:
    # Render binds the application to a dynamic port via environment variables.
    # 'mode=None' ensures that it acts strictly as a web server without trying to open a local desktop browser.
    port = int(os.environ.get("PORT", 8080))
    eel.start('login.html', host='0.0.0.0', port=port, mode=None)
