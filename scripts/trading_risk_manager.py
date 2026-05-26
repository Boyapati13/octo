"""
TradingRiskManager — TimesFM G4 Gate for Octo HybridTradingBot
==============================================================
Reads the cached TimesFM signal and applies one of four configurable gate
modes before any trade is placed.  No model inference happens here — the
signal is written by timesfm_forecaster.py on a 5-minute loop.

GATE_MODE values (set in live_bot_config.json or env var GATE_MODE):
  "BLOCK"   — hard block if TFM is confident in the opposite direction
  "SOFT"    — allow trade but halve the lot size when TFM disagrees
  "WARN"    — send Telegram warning but place the full trade
  "OFF"     — disable TFM gate entirely (EA behaves as original)

Per-asset timeframe overrides are also configurable so you can test
H1 vs H4 on forex and H1 vs M15 on volume symbols.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

# ── Config ────────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).resolve().parent

# Signal files — written by timesfm_forecaster.py
_MT5_COMMON_FILES = Path(os.environ.get("APPDATA", "")) / \
    "MetaQuotes" / "Terminal" / "Common" / "Files"

# Gate modes: BLOCK | SOFT | WARN | OFF
GateMode = Literal["BLOCK", "SOFT", "WARN", "OFF"]

# Default per-asset timeframe to use for forecasting
DEFAULT_TF_MAP: dict[str, str] = {
    # Forex H1 engine symbols
    "EURUSD+": "H1",
    "GBPUSD+": "H1",
    # Volume / metal symbols
    "NAS100":  "H1",
    "XAUUSD+": "H1",
    "XAUEUR+": "H1",
    "BTCUSD":  "H1",
    "CL-OIL":  "H1",
}


class TradingRiskManager:
    """
    Evaluates a proposed trade against the TimesFM directional forecast and
    returns a gate decision according to the configured mode.

    Usage:
        rm = TradingRiskManager(gate_mode="SOFT", min_confidence=0.65)
        gate = rm.evaluate("EURUSD+", "BUY")
        if gate["allow"]:
            lot = base_lot * gate["lot_mult"]
            execute_order(..., lot)
    """

    def __init__(
        self,
        gate_mode: GateMode = "SOFT",
        min_confidence: float = 0.65,
        max_signal_age_seconds: int = 600,
        tf_map: Optional[dict] = None,
    ):
        self.gate_mode   = gate_mode.upper()
        self.min_conf    = min_confidence
        self.max_age     = max_signal_age_seconds
        self.tf_map      = tf_map or DEFAULT_TF_MAP
        self._cache: dict[str, dict] = {}   # in-memory signal cache
        self.load_config()  # Load saved settings if available

    # ── Configuration Persistence ─────────────────────────────────────────────

    def load_config(self):
        """Loads configuration from live_bot_config.json if it exists."""
        config_path = _SCRIPT_DIR.parent / "config" / "live_bot_config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                if "gate_mode" in data:
                    self.gate_mode = data["gate_mode"].upper()
                if "min_confidence" in data:
                    self.min_conf = float(data["min_confidence"])
                if "max_signal_age_seconds" in data:
                    self.max_age = int(data["max_signal_age_seconds"])
                if "tf_map" in data:
                    self.tf_map = data["tf_map"]
            except Exception as e:
                print(f"[RiskMgr] [ERROR] Failed to load config from {config_path}: {e}")

    def save_config(self):
        """Saves current configuration to live_bot_config.json."""
        config_path = _SCRIPT_DIR.parent / "config" / "live_bot_config.json"
        try:
            data = {
                "gate_mode": self.gate_mode,
                "min_confidence": self.min_conf,
                "max_signal_age_seconds": self.max_age,
                "tf_map": self.tf_map
            }
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[RiskMgr] [ERROR] Failed to save config to {config_path}: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(self, symbol: str, direction: str) -> dict:
        """
        Evaluate whether to allow/modify a proposed trade.

        Returns dict:
          allow     : bool   — whether to place the trade
          lot_mult  : float  — multiply base lot by this (1.0 = full, 0.5 = half)
          bias      : str    — "BULL" | "BEAR" | "NEUTRAL"
          confidence: float  — 0.0–1.0
          mode      : str    — gate mode used
          reason    : str    — human-readable explanation
          telegram_tag: str  — emoji tag for Telegram alert
        """
        self.load_config()  # Dynamic hot-reload of config!
        direction = direction.upper()

        if self.gate_mode == "OFF":
            return self._allow(direction, "NEUTRAL", 0.0, "G4 gate is OFF")

        signal = self._read_signal(symbol)

        if signal is None:
            # No signal file — fail open (allow trade, no block)
            return self._allow(direction, "NEUTRAL", 0.0,
                               "No TFM signal file — gate open")

        bias       = signal.get("bias", "NEUTRAL").upper()
        confidence = float(signal.get("confidence", 0.0))
        pct_change = float(signal.get("pct_change", 0.0))

        # Determine if TFM conflicts with the proposed direction
        conflicts = (
            (direction == "BUY"  and bias == "BEAR") or
            (direction == "SELL" and bias == "BULL")
        )
        aligns = (
            (direction == "BUY"  and bias == "BULL") or
            (direction == "SELL" and bias == "BEAR")
        )

        high_conf = confidence >= self.min_conf

        if not conflicts or not high_conf:
            # No meaningful conflict — allow full trade
            tag = "✅" if aligns else "➖"
            reason = (f"TFM {bias} {confidence*100:.0f}% "
                      f"{'ALIGNED' if aligns else 'NEUTRAL — gate open'}")
            return self._allow(direction, bias, confidence, reason, tag)

        # ── Conflict detected ──────────────────────────────────────────────
        reason = (f"TFM says {bias} {confidence*100:.0f}% "
                  f"but signal is {direction}")

        if self.gate_mode == "BLOCK":
            return self._block(direction, bias, confidence, reason)

        elif self.gate_mode == "SOFT":
            return self._soft(direction, bias, confidence, reason)

        else:  # WARN
            return self._warn(direction, bias, confidence, reason)

    def set_mode(self, mode: GateMode):
        """Hot-swap gate mode and save config."""
        self.gate_mode = mode.upper()
        self.save_config()
        print(f"[RiskMgr] Gate mode changed to {self.gate_mode} and config saved.")

    def get_forecast_summary(self, symbol: str) -> str:
        """Returns a human-readable one-liner for OCTO / Telegram."""
        sig = self._read_signal(symbol)
        if sig is None:
            return f"{symbol}: No forecast available (signal file missing)"
        bias = sig.get("bias", "NEUTRAL")
        conf = float(sig.get("confidence", 0.0)) * 100
        pct  = float(sig.get("pct_change", 0.0))
        tf   = sig.get("timeframe", "?")
        end  = sig.get("expected_end_price", 0.0)
        arrow = "⬆️" if bias == "BULL" else ("⬇️" if bias == "BEAR" else "➡️")
        return (f"{arrow} *{symbol}* [{tf}] → `{bias}` "
                f"{conf:.0f}% conf | Δ`{pct:+.3f}%` | Target `{end:.5f}`")

    def get_all_summaries(self, symbols: list[str]) -> str:
        """Multi-symbol summary for OCTO voice response."""
        lines = [self.get_forecast_summary(s) for s in symbols]
        return "\n".join(lines)

    # ── Signal file reader ────────────────────────────────────────────────────

    def _read_signal(self, symbol: str) -> Optional[dict]:
        """
        Read the cached TimesFM signal for a symbol.
        Looks in MT5 Common Files first, then the script directory.
        Returns None if file is missing, stale, or has an error.
        """
        # Build file path (portfolio mode writes per-symbol portfolio file)
        portfolio_path = self._signal_path("portfolio")
        symbol_path    = self._signal_path(symbol)

        data = None

        # Try portfolio file first (written by --portfolio mode)
        if portfolio_path.exists():
            try:
                all_sigs = json.loads(portfolio_path.read_text(encoding="utf-8"))
                # Portfolio file is a dict keyed by symbol
                if isinstance(all_sigs, dict) and symbol in all_sigs:
                    data = all_sigs[symbol]
                elif isinstance(all_sigs, list):
                    data = next((s for s in all_sigs if s.get("symbol") == symbol), None)
            except Exception:
                pass

        # Fall back to per-symbol file
        if data is None and symbol_path.exists():
            try:
                data = json.loads(symbol_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Fall back to the single timesfm_signal.json
        if data is None:
            single_path = self._signal_path(None)
            if single_path.exists():
                try:
                    d = json.loads(single_path.read_text(encoding="utf-8"))
                    if d.get("symbol", "").upper() == symbol.upper():
                        data = d
                except Exception:
                    pass

        if data is None:
            return None

        # Stale check
        ts = data.get("generated_at", "")
        if ts:
            try:
                # Parse ISO-8601 with or without timezone
                ts_clean = ts[:19].replace("T", " ")
                sig_time = datetime.strptime(ts_clean, "%Y-%m-%d %H:%M:%S")
                sig_time = sig_time.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - sig_time).total_seconds()
                if age > self.max_age:
                    print(f"[RiskMgr] {symbol} signal stale ({age:.0f}s) — gate open")
                    return None
            except Exception:
                pass  # can't parse timestamp, allow through

        # Error check
        if data.get("error"):
            return None

        return data

    def _signal_path(self, symbol: Optional[str]) -> Path:
        """Determine signal file path, preferring MT5 common files."""
        base = _MT5_COMMON_FILES if _MT5_COMMON_FILES.exists() else _SCRIPT_DIR
        if symbol is None:
            return base / "timesfm_signal.json"
        if symbol == "portfolio":
            return base / "timesfm_portfolio_signals.json"
        safe = symbol.replace("+", "plus").replace("/", "_")
        return base / f"timesfm_{safe}.json"

    # ── Gate helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _allow(direction, bias, conf, reason, tag="✅") -> dict:
        return {
            "allow": True, "lot_mult": 1.0,
            "bias": bias, "confidence": conf,
            "mode": "ALLOW", "reason": reason,
            "telegram_tag": tag,
        }

    @staticmethod
    def _block(direction, bias, conf, reason) -> dict:
        return {
            "allow": False, "lot_mult": 0.0,
            "bias": bias, "confidence": conf,
            "mode": "BLOCK", "reason": f"BLOCKED — {reason}",
            "telegram_tag": "🚫",
        }

    @staticmethod
    def _soft(direction, bias, conf, reason) -> dict:
        return {
            "allow": True, "lot_mult": 0.5,
            "bias": bias, "confidence": conf,
            "mode": "SOFT", "reason": f"SOFT — {reason}",
            "telegram_tag": "⚠️",
        }

    @staticmethod
    def _warn(direction, bias, conf, reason) -> dict:
        return {
            "allow": True, "lot_mult": 1.0,
            "bias": bias, "confidence": conf,
            "mode": "WARN", "reason": f"WARN — {reason}",
            "telegram_tag": "⚠️",
        }
