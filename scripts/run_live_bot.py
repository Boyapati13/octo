#!/usr/bin/env python3
"""
Whale Suite & Robust Plateau — Hybrid Portfolio Automated Live Trading Bot
========================================================================
1. Evaluates Stock Indices and Metals (NAS100, XAUUSD+) on the M15 Pure Volume wick-absorption engine.
2. Evaluates Forex Majors (EURUSD+, GBPUSD+) on the H1 Robust RSI & EMA Plateau (Pass 244) engine.
3. Integrates Economic News Sentinel, 1% safe Lot Sizing, breakeven trailing, and 50% partials.
"""

import sys
import os
import time
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path
import MetaTrader5 as mt5

# Windows cp1252 terminals can't encode emoji — reconfigure stdout/stderr to UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from news_sentinel import NewsSentinel
from backtest_whale_engine import calc_poc_and_va

# === LOCAL HIGH-FIDELITY INDICATORS ==================================
def calculate_ema(prices, period):
    n = len(prices)
    ema = np.zeros(n)
    if n == 0: return ema
    ema[0] = prices[0]
    alpha = 2.0 / (period + 1.0)
    for i in range(1, n):
        ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i-1]
    return ema

def calculate_rsi(prices, period):
    n = len(prices)
    rsi = np.full(n, 50.0)
    if n <= period: return rsi
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        rsi[period] = 100.0
    else:
        rs = up / down
        rsi[period] = 100.0 - 100.0 / (1.0 + rs)
    for i in range(period + 1, n):
        delta = deltas[i - 1]
        upval = delta if delta > 0 else 0.0
        downval = -delta if delta < 0 else 0.0
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        if down == 0: rsi[i] = 100.0
        else: rsi[i] = 100.0 - 100.0 / (1.0 + up / down)
    return rsi

def calculate_atr(highs, lows, closes, period):
    n = len(closes)
    tr = np.zeros(n)
    if n == 0: return tr
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = np.zeros(n)
    atr[0] = tr[0]
    seed_len = min(period, n)
    atr[seed_len-1] = np.mean(tr[:seed_len])
    for i in range(seed_len, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr

class HybridTradingBot:
    def __init__(self, magic_number: int = 991206):
        self.magic_number = magic_number
        self.sentinel = NewsSentinel()
        self.risk_pct = 1.0  # Risk exactly 1.0% of active balance per trade
        
        # Portfolio Mappings
        self.forex_symbols = ["EURUSD+", "GBPUSD+"]
        self.volume_symbols = ["NAS100", "XAUUSD+"]
        self.all_symbols = self.forex_symbols + self.volume_symbols
        
        # Session configs for volume profiling
        self.sessions = {
            0: {"start": 0, "end": 8, "tol": 75, "lookback": 250, "bins": 40, "fvg_pct": 22.5, "name": "ASIA"},
            1: {"start": 8, "end": 16, "tol": 300, "lookback": 150, "bins": 30, "fvg_pct": 15.0, "name": "LONDON"},
            2: {"start": 13, "end": 21, "tol": 150, "lookback": 300, "bins": 45, "fvg_pct": 15.0, "name": "NY"}
        }
        
        self.state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_bot_state.json")
        self.load_state()

        # Load Telegram credentials from config/gateway.json
        self.tg_token = None
        self.tg_chat_id = None
        try:
            script_dir = Path(__file__).resolve().parent
            gateway_config_path = script_dir.parent / "config" / "gateway.json"
            if gateway_config_path.exists():
                with open(gateway_config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    tg_cfg = cfg.get("telegram", {})
                    if tg_cfg.get("enabled", False):
                        self.tg_token = tg_cfg.get("token")
                        self.tg_chat_id = tg_cfg.get("allowed_users")
                        print(f"[Bot] [Telegram] Enabled. Alerts will be sent to user '{self.tg_chat_id}'.")
            else:
                print(f"[Bot] [Telegram] gateway.json config not found at {gateway_config_path}")
        except Exception as e:
            print(f"[Bot] [Telegram] [ERROR] Failed to load Telegram config: {e}")

    def load_state(self):
        self.state = {}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.state = json.load(f)
            except Exception as e:
                print(f"[Bot] [ERROR] Failed to load state file: {e}")

    def save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            print(f"[Bot] [ERROR] Failed to save state file: {e}")

    def send_telegram_alert(self, message: str):
        """Sends a real-time trading alert directly to the user's Telegram."""
        if not self.tg_token or not self.tg_chat_id:
            return
        
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {
            "chat_id": self.tg_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            import urllib.request
            import json
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5.0) as response:
                pass
            print(f"[Bot] [Telegram] Alert successfully sent: {message[:60]}...")
        except Exception as e:
            print(f"[Bot] [Telegram] [ERROR] Failed to send alert: {e}")

    def execute_live_order(self, symbol: str, order_type: int, entry: float, sl: float, tp: float, lot: float):
        """Executes a live market order (BUY or SELL) on MetaTrader 5."""
        s_info = mt5.symbol_info(symbol)
        if s_info is None:
            return
            
        filling_type = mt5.ORDER_FILLING_FOK
        filling_flags = s_info.filling_mode
        if filling_flags & mt5.SYMBOL_FILLING_FOK:
            filling_type = mt5.ORDER_FILLING_FOK
        elif filling_flags & mt5.SYMBOL_FILLING_IOC:
            filling_type = mt5.ORDER_FILLING_IOC
        else:
            filling_type = mt5.ORDER_FILLING_RETURN

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": entry,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": self.magic_number,
            "comment": "Plateau Market Order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_type,
        }
        
        print(f"[Bot] Executing live MARKET order for {symbol} (Type={order_type}, Lot={lot:.2f}, Price={entry:.5f})...")
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"[Bot] [SUCCESS] Market order #{res.deal} executed successfully.")
            type_name = "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL"
            msg = f"🚀 *[NEW MARKET ORDER EXECUTED]*\n\n*Symbol:* `{symbol}`\n*Type:* `{type_name}`\n*Price:* `{entry:.5f}`\n*Stop Loss:* `{sl:.5f}`\n*Take Profit:* `{tp:.5f}`\n*Lot Size:* `{lot:.2f}`"
            self.send_telegram_alert(msg)
        else:
            err = res.retcode if res else "Unknown"
            print(f"[Bot] [ERROR] Market order failed. Code: {err}")

    def initialize_mt5(self) -> bool:
        if not mt5.initialize():
            print(f"[Bot] [ERROR] MT5 connection failed: {mt5.last_error()}")
            return False
        
        # Select all symbols
        for sym in self.all_symbols:
            mt5.symbol_select(sym, True)
            
        print("[Bot] [SUCCESS] Hybrid portfolio bot connected to live MT5 terminal.")
        return True

    def detect_broker_offset(self, symbol: str) -> int:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            server_time = tick.time
            utc_time = int(datetime.now(timezone.utc).timestamp())
            if abs(utc_time - server_time) > 3 * 3600:
                return 3
            return round((server_time - utc_time) / 3600.0)
        return 3

    def get_malta_hour(self, offset: int) -> int:
        utc_time = datetime.now(timezone.utc)
        malta_time = utc_time + timedelta(hours=2)
        return malta_time.hour

    def check_active_positions(self, symbol: str) -> bool:
        positions = mt5.positions_get(symbol=symbol, magic=self.magic_number)
        return len(positions) > 0 if positions is not None else False

    def check_pending_orders(self, symbol: str) -> bool:
        orders = mt5.orders_get(symbol=symbol, magic=self.magic_number)
        return len(orders) > 0 if orders is not None else False

    def calculate_lot_size(self, symbol: str, risk_amount: float, sl_dist_points: float) -> float:
        s_info = mt5.symbol_info(symbol)
        if s_info is None:
            return 0.01
        trade_size = s_info.trade_contract_size
        point = s_info.point
        sl_dist_price = sl_dist_points * point
        if sl_dist_price <= 0:
            return 0.01
        lot = risk_amount / (trade_size * sl_dist_price)
        lot = max(s_info.volume_min, min(s_info.volume_max, lot))
        step = s_info.volume_step
        lot = round(lot / step) * step
        return max(0.01, lot)

    def manage_active_positions(self):
        """Monitors active trades: takes 50% partial profit at 1:1 R:R and adjusts Stop Loss to breakeven."""
        positions = mt5.positions_get(magic=self.magic_number)
        if positions is None:
            return
            
        active_tickets = {str(p.ticket) for p in positions}
        state_tickets = list(self.state.keys())
        state_changed = False
        
        # Clean up tracked tickets that are no longer active
        for t_str in state_tickets:
            if t_str not in active_tickets:
                closed_data = self.state[t_str]
                symbol = closed_data["symbol"]
                print(f"[Bot] [INFO] Position #{t_str} has been closed by market. Removing from tracking state.")
                
                history_deal = ""
                try:
                    from_time = datetime.now() - timedelta(hours=1)
                    history = mt5.history_deals_get(from_date=from_time)
                    if history:
                        for d in history:
                            if d.position_id == int(t_str):
                                profit = d.profit
                                comment = d.comment
                                is_sl = "sl" in comment.lower() or (profit < 0)
                                is_tp = "tp" in comment.lower() or (profit > closed_data.get("initial_lot", 0.1) * 10)
                                status_msg = "🔴 Stop Loss Hit" if profit < 0 else "🟢 Take Profit Hit"
                                history_deal = f"\n*Status:* `{status_msg}`\n*PnL:* `${profit:.2f}`"
                                break
                except Exception as e:
                    print(f"[Bot] Failed to inspect closed position history: {e}")
                    
                msg = f"📉 *[TRADE CLOSED]*\n\n*Symbol:* `{symbol}`\n*Position:* `#{t_str}`{history_deal}"
                self.send_telegram_alert(msg)
                
                del self.state[t_str]
                state_changed = True
                
        # Audit each active position
        for p in positions:
            t_str = str(p.ticket)
            symbol = p.symbol
            s_info = mt5.symbol_info(symbol)
            if s_info is None:
                continue
                
            point = s_info.point
            current_price = p.price_current
            open_price = p.price_open
            
            if t_str not in self.state:
                self.state[t_str] = {
                    "symbol": symbol,
                    "entry_price": open_price,
                    "initial_sl": p.sl,
                    "initial_tp": p.tp,
                    "initial_lot": p.volume,
                    "partial_taken": False,
                    "sl_to_be": False
                }
                state_changed = True
                
            trade_data = self.state[t_str]
            initial_sl = trade_data["initial_sl"]
            
            if not initial_sl or initial_sl <= 0:
                continue
                
            sl_distance = abs(open_price - initial_sl)
            if sl_distance <= 0:
                continue
                
            is_buy = (p.type == mt5.POSITION_TYPE_BUY)
            profit_distance = (current_price - open_price) if is_buy else (open_price - current_price)
            
            # If price reaches 1:1 Risk-to-Reward ratio
            if profit_distance >= sl_distance:
                # 1. Adjust Stop Loss to Breakeven
                if not trade_data["sl_to_be"]:
                    new_sl = open_price
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": p.ticket,
                        "sl": new_sl,
                        "tp": p.tp,
                    }
                    print(f"[Bot] [INFO] Position #{p.ticket} ({symbol}) reached 1:1 R:R. Modifying SL to Breakeven...")
                    res = mt5.order_send(request)
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        trade_data["sl_to_be"] = True
                        state_changed = True
                        print(f"[Bot] [SUCCESS] SL successfully moved to Breakeven for #{p.ticket}.")
                        msg = f"🛡️ *[STOP LOSS TO BREAKEVEN]*\n\n*Symbol:* `{symbol}`\n*Position:* `#{p.ticket}`\n*New SL:* `{new_sl:.5f}` (Risk-free trade!)"
                        self.send_telegram_alert(msg)
                    else:
                        err = res.retcode if res else "Unknown"
                        print(f"[Bot] [ERROR] Failed to adjust SL to Breakeven: {err}")
                
                # 2. Take 50% Partial Profits
                if not trade_data["partial_taken"] and p.volume > s_info.volume_min:
                    half_vol = p.volume * 0.5
                    step = s_info.volume_step
                    half_vol = round(half_vol / step) * step
                    half_vol = max(s_info.volume_min, half_vol)
                    
                    if half_vol < p.volume:
                        close_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
                        close_price = s_info.bid if is_buy else s_info.ask
                        
                        filling_type = mt5.ORDER_FILLING_FOK
                        filling_flags = s_info.filling_mode
                        if filling_flags & mt5.SYMBOL_FILLING_FOK:
                            filling_type = mt5.ORDER_FILLING_FOK
                        elif filling_flags & mt5.SYMBOL_FILLING_IOC:
                            filling_type = mt5.ORDER_FILLING_IOC
                        else:
                            filling_type = mt5.ORDER_FILLING_RETURN

                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": half_vol,
                            "type": close_type,
                            "position": p.ticket,
                            "price": close_price,
                            "deviation": 20,
                            "magic": self.magic_number,
                            "comment": "Portfolio Partial Close",
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": filling_type,
                        }
                        
                        print(f"[Bot] [INFO] Position #{p.ticket} ({symbol}) reached 1:1 R:R. Closing 50% partial profit...")
                        res = mt5.order_send(request)
                        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                            trade_data["partial_taken"] = True
                            state_changed = True
                            print(f"[Bot] [SUCCESS] Closed 50% partial for #{p.ticket}.")
                            msg = f"💰 *[PARTIAL PROFIT CLOSED]*\n\n*Symbol:* `{symbol}`\n*Position:* `#{p.ticket}`\n*Closed Volume:* `{half_vol:.2f}` lots\n*Price:* `{close_price:.5f}`\n(50% profit banked!)"
                            self.send_telegram_alert(msg)
                        else:
                            err = res.retcode if res else "Unknown"
                            print(f"[Bot] [ERROR] Failed to close partial: {err}")
                            
        if state_changed:
            self.save_state()

    def manage_pending_limit_orders(self):
        """Auto-cancels pending volume matrix limit orders if the session has ended or price hit target TP first."""
        orders = mt5.orders_get(magic=self.magic_number)
        if orders is None:
            return
            
        for o in orders:
            symbol = o.symbol
            # Skip if this is a market order or not under volume engine
            if symbol not in self.volume_symbols:
                continue
                
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                continue
                
            current_price = tick.last if tick.last > 0 else tick.bid
            
            # Retrieve active session limits
            offset = self.detect_broker_offset(symbol)
            malta_hour = self.get_malta_hour(offset)
            
            active_s = None
            for s_idx, p in self.sessions.items():
                is_in = False
                if p["start"] <= p["end"]:
                    is_in = (malta_hour >= p["start"] and malta_hour < p["end"])
                else:
                    is_in = (malta_hour >= p["start"] or malta_hour < p["end"])
                if is_in:
                    active_s = p
                    break
                    
            cancel_order = False
            # Cancel if session ended
            if active_s is None:
                cancel_order = True
            else:
                # Cancel if price already hit Take Profit before execution
                is_buy_limit = (o.type == mt5.ORDER_TYPE_BUY_LIMIT)
                if is_buy_limit and current_price >= o.tp:
                    cancel_order = True
                elif not is_buy_limit and current_price <= o.tp:
                    cancel_order = True
                    
            if cancel_order:
                request = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": o.ticket,
                }
                print(f"[Bot] [INFO] Canceling orphaned volume limit order #{o.ticket} on {symbol} (Target hit or session closed)...")
                mt5.order_send(request)

    def evaluate_live_market(self):
        self.manage_active_positions()
        self.manage_pending_limit_orders()
        
        acc_info = mt5.account_info()
        if not acc_info:
            return
        balance = acc_info.balance
        risk_cash = balance * (self.risk_pct / 100.0)
        
        # === A. EVALUATE FOREX MAJOR (Robust H1 RSI & EMA Plateau) ==========
        for symbol in self.forex_symbols:
            if self.check_active_positions(symbol):
                continue
                
            # Check News Shield
            news = self.sentinel.check_risk_status(symbol)
            if news["status"] == "THREAT_DETECTED":
                continue
                
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
            if rates is None or len(rates) < 150:
                continue
                
            closes = np.array([float(x["close"]) for x in rates])
            highs = np.array([float(x["high"]) for x in rates])
            lows = np.array([float(x["low"]) for x in rates])
            
            s_info = mt5.symbol_info(symbol)
            point = s_info.point
            
            # Calculate Indicators
            ema25 = calculate_ema(closes, 25)
            ema135 = calculate_ema(closes, 135)
            rsi14 = calculate_rsi(closes, 14)
            atr14 = calculate_atr(highs, lows, closes, 14)
            
            # Checks completed bar 1 indices
            ema25_1 = ema25[-2]
            ema135_1 = ema135[-2]
            rsi_1 = rsi14[-2]
            rsi_2 = rsi14[-3]
            atr_1 = atr14[-2]
            
            buy_sig = (ema25_1 > ema135_1) and (rsi_2 <= 40.0 and rsi_1 > 40.0)
            sell_sig = (ema25_1 < ema135_1) and (rsi_2 >= 60.0 and rsi_1 < 60.0)
            
            # In live, check if we already traded this H1 bar time to prevent double entries
            last_bar_time = int(rates[-2]["time"])
            state_key = f"last_forex_bar_{symbol}"
            
            if state_key in self.state and self.state[state_key] == last_bar_time:
                # Already processed bar open
                continue
                
            if buy_sig or sell_sig:
                entry = s_info.ask if buy_sig else s_info.bid
                sl_dist_points = (4.0 * atr_1) / point
                
                if sl_dist_points > 0:
                    lot = self.calculate_lot_size(symbol, risk_cash, sl_dist_points)
                    sl = entry - (4.0 * atr_1) if buy_sig else entry + (4.0 * atr_1)
                    tp = entry + (5.0 * atr_1) if buy_sig else entry - (5.0 * atr_1)
                    
                    order_type = mt5.ORDER_TYPE_BUY if buy_sig else mt5.ORDER_TYPE_SELL
                    
                    # Execute Market Order
                    self.execute_live_order(symbol, order_type, entry, sl, tp, lot)
                    self.state[state_key] = last_bar_time
                    self.save_state()
                    
        # === B. EVALUATE STOCK INDEX / METAL (M15 Pure Volume Matrix) ======
        for symbol in self.volume_symbols:
            if self.check_active_positions(symbol) or self.check_pending_orders(symbol):
                continue
                
            # Check News Shield
            news = self.sentinel.check_risk_status(symbol)
            if news["status"] == "THREAT_DETECTED":
                continue
                
            # Copy rates
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 350)
            if rates is None or len(rates) < 310:
                continue
                
            sig_bar = rates[-2]  # bar 1 completed candle
            sig_time = datetime.fromtimestamp(int(sig_bar["time"]), tz=timezone.utc)
            
            offset = self.detect_broker_offset(symbol)
            sig_malta_hour = self.get_malta_hour(offset)
            
            # Find active session
            active_s = None
            active_s_idx = None
            for s_idx, p in self.sessions.items():
                is_in = False
                if p["start"] <= p["end"]:
                    is_in = (sig_malta_hour >= p["start"] and sig_malta_hour < p["end"])
                else:
                    is_in = (sig_malta_hour >= p["start"] or sig_malta_hour < p["end"])
                if is_in:
                    active_s = p
                    active_s_idx = s_idx
                    break
                    
            if active_s is None:
                continue
                
            # Fetch micro-timeframe M1 rates for the completed bar 1 (15 M1 bars)
            bar1_start = sig_time
            bar1_end = sig_time + timedelta(minutes=15)
            m1_rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, bar1_start, bar1_end)
            if m1_rates is None or len(m1_rates) == 0:
                continue
                
            s_info = mt5.symbol_info(symbol)
            point = s_info.point
            
            bodyMax = max(float(sig_bar["open"]), float(sig_bar["close"]))
            bodyMin = min(float(sig_bar["open"]), float(sig_bar["close"]))
            
            lower_wick_vol = 0.0
            upper_wick_vol = 0.0
            total_m1_vol = 0.0
            
            for r in m1_rates:
                m1_close = float(r["close"])
                m1_vol = float(r["tick_volume"])
                total_m1_vol += m1_vol
                if m1_close > bodyMax:
                    upper_wick_vol += m1_vol
                if m1_close < bodyMin:
                    lower_wick_vol += m1_vol
                    
            if total_m1_vol <= 0.0:
                total_m1_vol = 1.0
                
            lower_wick_vol_ratio = lower_wick_vol / total_m1_vol
            upper_wick_vol_ratio = upper_wick_vol / total_m1_vol
            wick_vol_concentration = (lower_wick_vol + upper_wick_vol) / total_m1_vol
            
            # VSA checks
            lowerWickVsaRejection = (lower_wick_vol_ratio >= 0.35)
            upperWickVsaRejection = (upper_wick_vol_ratio >= 0.35)
            institutionalAbsorption = (wick_vol_concentration >= 0.45)
            
            # Volume Spike Confirmation
            sum_vol = 0.0
            vol_cnt = 0
            for v in range(1, 11):
                sum_vol += float(rates[-2 - v]["tick_volume"])
                vol_cnt += 1
            avg_vol = sum_vol / vol_cnt if vol_cnt > 0 else 1.0
            isHighVolumeCandle = (float(sig_bar["tick_volume"]) >= avg_vol * 1.2)
            
            # Volume Profile
            lookback_rates = rates[-active_s["lookback"] - 1 : -1]
            closes = np.array([float(x["close"]) for x in lookback_rates])
            min_p = min(closes)
            max_p = max(closes)
            step = max(max_p - min_p, point * 10) / active_s["bins"]
            
            bins = np.zeros(active_s["bins"])
            for sc in lookback_rates:
                bn = int(np.floor((float(sc["close"]) - min_p) / step))
                bn = max(0, min(active_s["bins"] - 1, bn))
                bins[bn] += float(sc["tick_volume"])
                
            poc, vah, val, poc_bin = calc_poc_and_va(bins, active_s["bins"], min_p, step)
            
            # Proximity
            tol_price = active_s["tol"] * point
            lowNearValOrPoc = (abs(float(sig_bar["low"]) - val) <= tol_price) or (abs(float(sig_bar["low"]) - poc) <= tol_price)
            highNearVahOrPoc = (abs(float(sig_bar["high"]) - vah) <= tol_price) or (abs(float(sig_bar["high"]) - poc) <= tol_price)
            
            # PDH/PDL sweeps (completed daily bar 1)
            d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 1, 1)
            pdh = float(d1_rates[0]["high"]) if d1_rates is not None else float(sig_bar["high"])
            pdl = float(d1_rates[0]["low"]) if d1_rates is not None else float(sig_bar["low"])
            
            sweepsPdl = (abs(float(sig_bar["low"]) - pdl) <= tol_price)
            sweepsPdh = (abs(float(sig_bar["high"]) - pdh) <= tol_price)
            
            buy_sig = lowNearValOrPoc and sweepsPdl and lowerWickVsaRejection and institutionalAbsorption and isHighVolumeCandle
            sell_sig = highNearVahOrPoc and sweepsPdh and upperWickVsaRejection and institutionalAbsorption and isHighVolumeCandle
            
            # In live, check if we already placed order for this specific M15 bar
            last_m15_time = int(sig_bar["time"])
            state_key = f"last_m15_bar_{symbol}"
            
            if state_key in self.state and self.state[state_key] == last_m15_time:
                continue
                
            if buy_sig or sell_sig:
                if buy_sig:
                    lower_wick_size = bodyMin - float(sig_bar["low"])
                    entry_limit = bodyMin - (lower_wick_size * 0.50)
                    sl = float(sig_bar["low"]) - (20 * point)
                    tp = vah
                    sl_dist_points = (entry_limit - sl) / point
                    order_type = mt5.ORDER_TYPE_BUY_LIMIT
                else:
                    upper_wick_size = float(sig_bar["high"]) - bodyMax
                    entry_limit = bodyMax + (upper_wick_size * 0.50)
                    sl = float(sig_bar["high"]) + (20 * point)
                    tp = val
                    sl_dist_points = (sl - entry_limit) / point
                    order_type = mt5.ORDER_TYPE_SELL_LIMIT
                    
                if sl_dist_points > 0:
                    lot = self.calculate_lot_size(symbol, risk_amount = risk_cash, sl_dist_points = sl_dist_points)
                    
                    # Submit pending LIMIT order
                    # Dynamic filling type selection
                    filling_type = mt5.ORDER_FILLING_FOK
                    filling_flags = s_info.filling_mode
                    if filling_flags & mt5.SYMBOL_FILLING_FOK:
                        filling_type = mt5.ORDER_FILLING_FOK
                    elif filling_flags & mt5.SYMBOL_FILLING_IOC:
                        filling_type = mt5.ORDER_FILLING_IOC
                    else:
                        filling_type = mt5.ORDER_FILLING_RETURN

                    request = {
                        "action": mt5.TRADE_ACTION_LIMIT,
                        "symbol": symbol,
                        "volume": lot,
                        "type": order_type,
                        "price": entry_limit,
                        "sl": sl,
                        "tp": tp,
                        "deviation": 20,
                        "magic": self.magic_number,
                        "comment": "Pure Volume Limit",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": filling_type,
                    }
                    
                    print(f"[Bot] Placing live PENDING LIMIT order for {symbol} at wick 50% ({entry_limit:.5f})...")
                    res = mt5.order_send(request)
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"[Bot] [SUCCESS] Limit order #{res.order} submitted successfully.")
                        self.state[state_key] = last_m15_time
                        self.save_state()
                        
                        type_name = "BUY LIMIT" if order_type == mt5.ORDER_TYPE_BUY_LIMIT else "SELL LIMIT"
                        msg = f"🔔 *[NEW PENDING LIMIT ORDER]*\n\n*Symbol:* `{symbol}`\n*Type:* `{type_name}`\n*Entry Price:* `{entry_limit:.5f}`\n*Stop Loss:* `{sl:.5f}`\n*Take Profit:* `{tp:.5f}`\n*Lot Size:* `{lot:.2f}`"
                        self.send_telegram_alert(msg)
                    else:
                        err = res.retcode if res else "Unknown"
                        print(f"[Bot] [ERROR] Limit order failed. Code: {err}")

def main():
    print("=" * 60)
    print("   Whale Pure Volume & Robust H1 Plateau Bot Deployed")
    print("=" * 60)
    
    bot = HybridTradingBot()
    if bot.initialize_mt5():
        print("[Bot] Production loop started. Monitoring portfolio...")
        try:
            while True:
                bot.evaluate_live_market()
                print(f"[Bot] Cycle complete ({datetime.now().strftime('%H:%M:%S')}). Waiting 300 seconds...")
                time.sleep(300)
        except KeyboardInterrupt:
            print("[Bot] Exiting program clean via KeyboardInterrupt.")
        except Exception as e:
            print(f"[Bot] [ERROR] Exception in hybrid bot loop: {e}")
            
    mt5.shutdown()
    print("=" * 60)

if __name__ == "__main__":
    main()
