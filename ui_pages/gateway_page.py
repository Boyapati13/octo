"""Gateway page — configure and launch OCTO messaging gateway on all platforms."""
from __future__ import annotations
import json
import socket
import threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFrame,
)
from PyQt6.QtGui import QFont
from .base import (
    OctoPage, PRI, PRI_DIM, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM,
    BORDER, BORDER_B, PANEL, PANEL2, WHITE, DARK,
)

# ── Platform catalogue — all have matching channel implementations ─────────────
_PLATFORMS = [
    {
        "id": "telegram", "name": "TELEGRAM", "icon": "✈", "color": "#2CA5E0",
        "fields": [
            ("token",         "Bot token  (from @BotFather)",       True),
            ("allowed_users", "Your Telegram user IDs  (comma-sep)", False),
        ],
        "hint": "Telegram → @BotFather → /newbot  |  Your ID: @userinfobot",
        "impl": "channels.telegram_channel",
    },
    {
        "id": "discord", "name": "DISCORD", "icon": "🎮", "color": "#5865F2",
        "fields": [
            ("token",         "Bot token  (discord.com/developers)",  True),
            ("allowed_users", "Your Discord user IDs  (comma-sep)",   False),
        ],
        "hint": "Developer Portal → New App → Bot → Reset Token  |  Enable Message Content Intent",
        "impl": "channels.discord_channel",
    },
    {
        "id": "slack", "name": "SLACK", "icon": "#", "color": "#4A154B",
        "fields": [
            ("token",         "Bot token  xoxb-…",                   True),
            ("api_key",       "App token  xapp-…  (Socket Mode)",    True),
            ("allowed_users", "Member IDs  (comma-sep)",             False),
        ],
        "hint": "api.slack.com/apps → OAuth: xoxb token  |  Settings → Socket Mode: xapp token",
        "impl": "channels.slack_channel",
    },
    {
        "id": "whatsapp", "name": "WHATSAPP", "icon": "📱", "color": "#25D366",
        "fields": [
            ("account_sid",   "Twilio Account SID  (optional)",      True),
            ("auth_token",    "Twilio Auth Token   (optional)",      True),
            ("allowed_users", "Phone numbers  (15551234567, no +)",  False),
        ],
        "hint": "Powered by whatsapp_channel.py — QR pairing via Twilio sandbox",
        "impl": "channels.whatsapp_channel",
    },
    {
        "id": "dingtalk", "name": "DINGTALK", "icon": "🔔", "color": "#FF6900",
        "fields": [
            ("webhook",       "Group webhook URL  (from DingTalk)",  True),
            ("secret",        "Signing secret  (optional)",          True),
        ],
        "hint": "DingTalk group → Settings → Robots → Add a robot → Webhook URL",
        "impl": "channels.dingtalk",
    },
    {
        "id": "feishu", "name": "FEISHU / LARK", "icon": "🕊", "color": "#00B96B",
        "fields": [
            ("app_id",        "App ID  (open.feishu.cn)",            True),
            ("app_secret",    "App Secret",                          True),
            ("allowed_users", "User open-IDs  (comma-sep)",          False),
        ],
        "hint": "Feishu Open Platform → Create App → Event Subscription",
        "impl": "channels.feishu",
    },
]


class GatewayPage(OctoPage):
    _status_sig = pyqtSignal(str)
    _state_sig  = pyqtSignal(bool)   # True = gateway running

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_sig.connect(self._on_status)
        self._state_sig.connect(self._on_gw_state)
        self._fields: dict[str, dict[str, QLineEdit]] = {}
        self._status_lbl: QLabel | None = None
        self._cfg = self._load_cfg()
        self._build()

        # Poll gateway port
        self._gw_timer = QTimer(self)
        self._gw_timer.timeout.connect(self._poll_gateway)
        self._gw_timer.start(5000)
        self._poll_gateway()

    # ── persistence ──────────────────────────────────────────────────────────
    def _load_cfg(self) -> dict:
        try:
            from memory.config_manager import load_gateway_config
            return load_gateway_config()
        except Exception:
            return {}

    def _save_cfg(self) -> dict:
        data: dict = {}
        for pid, flds in self._fields.items():
            vals = {k: f.text().strip() for k, f in flds.items() if f.text().strip()}
            if vals:
                vals["enabled"] = True
                data[pid] = vals
        try:
            from memory.config_manager import save_gateway_config
            save_gateway_config(data)
        except Exception as e:
            print(f"[OCTO] Gateway save error: {e}")
        return data

    # ── port polling ─────────────────────────────────────────────────────────
    def _poll_gateway(self):
        try:
            with socket.create_connection(("127.0.0.1", 2026), timeout=0.5):
                self._state_sig.emit(True)
        except OSError:
            self._state_sig.emit(False)

    def _on_gw_state(self, running: bool):
        if running:
            self._gw_status.setText("● ACTIVE  [127.0.0.1:2026]")
            self._gw_status.setStyleSheet(f"color:{GREEN};background:transparent;font-weight:bold;")
            self._gw_btn.setText("▪  GATEWAY RUNNING")
            self._gw_btn.setStyleSheet(f"""QPushButton{{background:transparent;color:{TEXT_DIM};
                border:1px solid {BORDER};border-radius:3px;padding:0 12px;}}""")
            self._gw_btn.setEnabled(False)
        else:
            self._gw_status.setText("○ OFFLINE")
            self._gw_status.setStyleSheet(f"color:{TEXT_DIM};background:transparent;")
            self._gw_btn.setText("▸  START GATEWAY")
            self._gw_btn.setStyleSheet(f"""QPushButton{{background:transparent;color:{GREEN};
                border:1px solid {GREEN_D};border-radius:3px;padding:0 12px;}}
                QPushButton:hover{{background:#001a0d;border-color:{GREEN};}}""")
            self._gw_btn.setEnabled(True)

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        lay = self.page_layout()

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  OCTO MESSAGING GATEWAY", 11, bold=True, color=PRI))
        hdr.addStretch()
        self._gw_status = self.lbl("○ CHECKING", 7, color=TEXT_DIM)
        hdr.addWidget(self._gw_status)

        self._gw_btn = QPushButton("▸  START GATEWAY")
        self._gw_btn.setFixedHeight(30)
        self._gw_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        self._gw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gw_btn.setStyleSheet(f"""QPushButton{{background:transparent;color:{GREEN};
            border:1px solid {GREEN_D};border-radius:3px;padding:0 12px;}}
            QPushButton:hover{{background:#001a0d;border-color:{GREEN};}}""")
        self._gw_btn.clicked.connect(self._start_gateway)
        hdr.addWidget(self._gw_btn)
        lay.addLayout(hdr)

        self._status_lbl = self.lbl(
            "Configure a messaging platform below, save, then click Start Gateway. "
            "The gateway runs on port 2026 — messages sent to your bot arrive here.",
            7, color=TEXT_DIM, wrap=True,
        )
        lay.addWidget(self._status_lbl)
        lay.addWidget(self.sep())

        # Platform cards
        for p in _PLATFORMS:
            lay.addWidget(self._platform_card(p))
            lay.addSpacing(4)

        lay.addWidget(self.sep())

        # Footer buttons
        footer = QHBoxLayout()
        save_b = self.btn("▸  SAVE ALL CHANNEL SETTINGS", color=PRI, height=34)
        save_b.clicked.connect(lambda: [self._save_cfg(),
                                        self._on_status("✓ Channel settings saved.")])
        footer.addStretch(); footer.addWidget(save_b)
        lay.addLayout(footer)
        lay.addStretch()

    def _platform_card(self, p: dict) -> QWidget:
        pid   = p["id"]
        saved = self._cfg.get(pid, {})
        has   = bool(saved)

        card = QWidget()
        card.setStyleSheet(f"""QWidget{{background:{PANEL};
            border:1px solid {"#1a5c7a" if has else BORDER};border-radius:6px;}}""")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 10, 14, 10)
        cl.setSpacing(6)

        # Card header
        ch = QHBoxLayout()
        icon_l = QLabel(p["icon"])
        icon_l.setFont(QFont("Segoe UI Emoji", 15))
        icon_l.setStyleSheet(f"color:{p['color']};background:transparent;border:none;")
        name_l = QLabel(p["name"])
        name_l.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        name_l.setStyleSheet(f"color:{p['color']};background:transparent;border:none;")
        impl_l = QLabel(p["impl"].split(".")[-1])
        impl_l.setFont(QFont("Courier New", 7))
        impl_l.setStyleSheet(f"color:{TEXT_DIM};background:transparent;border:none;")
        status_l = QLabel("● CONFIGURED" if has else "○ NOT SET")
        status_l.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        status_l.setStyleSheet(
            f"color:{GREEN if has else TEXT_DIM};background:transparent;border:none;"
        )
        ch.addWidget(icon_l)
        ch.addWidget(name_l)
        ch.addWidget(impl_l)
        ch.addStretch()
        ch.addWidget(status_l)
        cl.addLayout(ch)

        # Hint
        hint = QLabel(p["hint"])
        hint.setFont(QFont("Courier New", 7))
        hint.setStyleSheet(f"color:{TEXT_DIM};background:transparent;border:none;")
        hint.setWordWrap(True)
        cl.addWidget(hint)

        # Fields
        self._fields[pid] = {}
        for fname, fph, fecho in p["fields"]:
            fr = QHBoxLayout(); fr.setSpacing(6)
            fl = QLabel(fname)
            fl.setFixedWidth(130)
            fl.setFont(QFont("Courier New", 7))
            fl.setStyleSheet(f"color:{TEXT_MED};background:transparent;border:none;")
            ff = QLineEdit(str(saved.get(fname, "")))
            ff.setPlaceholderText(fph)
            ff.setFixedHeight(26)
            ff.setFont(QFont("Courier New", 8))
            if fecho:
                ff.setEchoMode(QLineEdit.EchoMode.Password)
            ff.setStyleSheet(f"""QLineEdit{{background:#000d14;color:{WHITE};
                border:1px solid {BORDER};border-radius:3px;padding:2px 6px;}}
                QLineEdit:focus{{border:1px solid {p['color']};}}""")
            fr.addWidget(fl); fr.addWidget(ff, stretch=1)
            cl.addLayout(fr)
            self._fields[pid][fname] = ff

        # WhatsApp extra: QR pair button
        if pid == "whatsapp":
            pair_b = QPushButton("📱  Pair WhatsApp via QR")
            pair_b.setFixedHeight(26)
            pair_b.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            pair_b.setCursor(Qt.CursorShape.PointingHandCursor)
            pair_b.setStyleSheet(f"""QPushButton{{background:transparent;color:{p['color']};
                border:1px solid {p['color']}55;border-radius:3px;padding:0 10px;}}
                QPushButton:hover{{background:#001a0d;}}""")
            pair_b.clicked.connect(self._pair_whatsapp)
            cl.addWidget(pair_b)

        return card

    # ── actions ───────────────────────────────────────────────────────────────
    def _on_status(self, msg: str):
        if self._status_lbl:
            self._status_lbl.setText(msg)

    def _start_gateway(self):
        cfg = self._save_cfg()
        self._gw_btn.setEnabled(False)
        self._on_status("Starting gateway threads…")

        def _run():
            try:
                from agent.hermes_bridge import start_gateway

                def on_msg(channel: str, user: str, text: str):
                    try:
                        from main import handle_gateway_message
                        handle_gateway_message(channel, user, text)
                    except Exception:
                        pass

                started = start_gateway(on_message=on_msg)
                if started:
                    self._status_sig.emit(f"✓ Gateway running: {', '.join(started)}")
                else:
                    self._status_sig.emit(
                        "Gateway started — no platforms configured with valid tokens yet."
                    )
            except Exception as e:
                self._status_sig.emit(f"Error: {e}")
            finally:
                self._gw_btn.setEnabled(True)

        threading.Thread(target=_run, daemon=True).start()

    def _pair_whatsapp(self):
        self._on_status("WhatsApp QR pairing — check the terminal for QR code.")
        try:
            from channels.whatsapp_channel import WhatsAppChannel  # type: ignore
            ch = WhatsAppChannel({})
            threading.Thread(target=ch.pair_qr, daemon=True).start()
        except Exception as e:
            self._on_status(f"WhatsApp pairing error: {e}")
