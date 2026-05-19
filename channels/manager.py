"""
channels/manager.py
====================
OCTO Channel Manager — orchestrates all messaging channels.

Inspired by DeerFlow's app/channels/manager.py.
Provides a single entry point for the UI and agent to:
  - Start/stop channels
  - Route inbound messages to OCTO's agent
  - Send replies back to the correct platform
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

_CFG_PATH = Path(__file__).resolve().parent.parent / "config" / "gateway.json"


class ChannelManager:
    """
    Manages all active OCTO messaging channels.

    Usage::

        mgr = ChannelManager()
        mgr.on_message(lambda channel, user_id, text: agent.respond(text))
        mgr.start_all()
    """

    def __init__(self):
        self._channels: Dict[str, object] = {}
        self._handler: Optional[Callable[[str, str, str], None]] = None
        self._lock = threading.Lock()

    # ── Config ──────────────────────────────────────────────────────────

    def _load_cfg(self) -> Dict:
        if not _CFG_PATH.exists():
            return {}
        try:
            return json.loads(_CFG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    # ── Lifecycle ────────────────────────────────────────────────────────

    def on_message(self, handler: Callable[[str, str, str], None]) -> None:
        """Register global message handler: handler(channel, user_id, text)."""
        self._handler = handler

    def start_all(self) -> List[str]:
        """Start all configured channels. Returns list of started channel names."""
        cfg     = self._load_cfg()
        started = []
        for ch_name in ("telegram", "discord", "slack", "whatsapp"):
            ch_cfg = cfg.get(ch_name, {})
            if not ch_cfg.get("token") and not ch_cfg.get("url"):
                continue
            try:
                ch = self._make_channel(ch_name, ch_cfg)
                if ch:
                    ch.on_message(self._route)
                    ch.start()
                    with self._lock:
                        self._channels[ch_name] = ch
                    started.append(ch_name)
                    logger.info("[Gateway] Started channel: %s", ch_name)
            except Exception as e:
                logger.error("[Gateway] Failed to start %s: %s", ch_name, e)
        return started

    def stop_all(self) -> None:
        with self._lock:
            for ch in self._channels.values():
                try:
                    ch.stop()
                except Exception:
                    pass
            self._channels.clear()
        logger.info("[Gateway] All channels stopped")

    def start_channel(self, name: str) -> bool:
        """Start a single channel by name."""
        cfg    = self._load_cfg()
        ch_cfg = cfg.get(name, {})
        try:
            ch = self._make_channel(name, ch_cfg)
            if ch:
                ch.on_message(self._route)
                ch.start()
                with self._lock:
                    self._channels[name] = ch
                return True
        except Exception as e:
            logger.error("[Gateway] start_channel %s failed: %s", name, e)
        return False

    def stop_channel(self, name: str) -> None:
        with self._lock:
            ch = self._channels.pop(name, None)
        if ch:
            try:
                ch.stop()
            except Exception:
                pass

    # ── Routing ──────────────────────────────────────────────────────────

    def _route(self, channel: str, user_id: str, text: str) -> None:
        if self._handler:
            try:
                self._handler(channel, user_id, text)
            except Exception as e:
                logger.error("[Gateway] Route error: %s", e)

    def send(self, channel: str, user_id: str, text: str) -> None:
        """Send a reply on the specified channel."""
        with self._lock:
            ch = self._channels.get(channel)
        if ch:
            try:
                ch.send(user_id, text)
            except Exception as e:
                logger.error("[Gateway] Send error on %s: %s", channel, e)
        else:
            logger.warning("[Gateway] Channel '%s' not active", channel)

    # ── Status ────────────────────────────────────────────────────────────

    def status(self) -> Dict[str, bool]:
        with self._lock:
            return {name: ch.is_running for name, ch in self._channels.items()}

    # ── Factory ───────────────────────────────────────────────────────────

    def _make_channel(self, name: str, cfg: Dict):
        if name == "telegram":
            from .telegram_channel import TelegramChannel
            return TelegramChannel(cfg)
        if name == "discord":
            from .discord_channel import DiscordChannel
            return DiscordChannel(cfg)
        if name == "slack":
            from .slack_channel import SlackChannel
            return SlackChannel(cfg)
        if name == "whatsapp":
            from .whatsapp_channel import WhatsAppChannel
            return WhatsAppChannel(cfg)
        return None
