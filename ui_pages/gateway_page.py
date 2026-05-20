"""Gateway page — configure and launch OCTO messaging on all platforms."""
from __future__ import annotations
import json
import threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QFont
from .base import OctoPage, PRI, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM, BORDER, PANEL, WHITE, DARK

_PLATFORMS = [
    {
        "id": "telegram", "name": "TELEGRAM", "icon": "✈", "color": "#2CA5E0",
        "fields": [
            ("token",         "Bot token  (from @BotFather)",         True),
            ("allowed_users", "Your user IDs  (comma-separated)",     False),
        ],
        "hint": "Telegram → @BotFather → /newbot  |  Your ID: @userinfobot",
    },
    {
        "id": "discord", "name": "DISCORD", "icon": "🎮", "color": "#5865F2",
        "fields": [
            ("token",         "Bot token  (discord.com/developers)",  True),
            ("allowed_users", "Your Discord user IDs",                False),
        ],
        "hint": "Developer Portal → New App → Bot → Reset Token  |  Enable Message Content Intent",
    },
    {
        "id": "slack", "name": "SLACK", "icon": "#", "color": "#4A154B",
        "fields": [
            ("token",         "Bot token  xoxb-…",                    True),
            ("api_key",       "App token  xapp-…",                    True),
            ("allowed_users", "Member IDs  (comma-separated)",        False),
        ],
        "hint": "api.slack.com/apps → OAuth: xoxb token  |  Settings → Socket Mode: xapp token",
    },
    {
        "id": "whatsapp", "name": "WHATSAPP", "icon": "📱", "color": "#25D366",
        "fields": [
            ("allowed_users", "Phone numbers  (15551234567, no +)",   False),
        ],
        "hint": "Uses QR pairing — click 'Pair WhatsApp' button below",
    },
    {
        "id": "signal", "name": "SIGNAL", "icon": "🔒", "color": "#3A76F0",
        "fields": [
            ("http_url",      "signal-cli URL  (http://127.0.0.1:8080)", False),
            ("account",       "Your phone number  (+1234567890)",         False),
            ("allowed_users", "Allowed numbers  (+1234567890,…)",         False),
        ],
        "hint": "Needs signal-cli + Java 17 running as daemon",
    },
]


class GatewayPage(OctoPage):
    _status_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_sig.connect(self._on_status)
        self._fields: dict[str, dict[str, QLineEdit]] = {}
        self._status_lbl: QLabel | None = None
        self._cfg = self._load_cfg()
        self._build()

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

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        lay = self.page_layout()
        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  OCTO GATEWAY", 11, bold=True, color=PRI))
        hdr.addStretch()

        # Gateway status indicator
        self._gw_status = self.lbl("○ STOPPED", 7, color=TEXT_DIM)
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
            "Configure a platform below and click Start Gateway.", 7, color=TEXT_DIM)
        lay.addWidget(self._status_lbl)
        lay.addWidget(self.sep())

        for p in _PLATFORMS:
            lay.addWidget(self._platform_card(p))
            lay.addSpacing(4)

        lay.addWidget(self.sep())
        save_row = QHBoxLayout()
        save_b = self.btn("▸  SAVE ALL SETTINGS", color=PRI, height=34)
        save_b.clicked.connect(lambda: [self._save_cfg(),
                                        self._on_status("✓ Settings saved.")])
        save_row.addStretch(); save_row.addWidget(save_b)
        lay.addLayout(save_row)
        lay.addStretch()

    def _platform_card(self, p: dict) -> QWidget:
        pid   = p["id"]
        saved = self._cfg.get(pid, {})
        has   = bool(saved)

        card = QWidget()
        card.setStyleSheet(f"""QWidget{{background:{PANEL};
            border:1px solid {"#1a5c7a" if has else BORDER};border-radius:5px;}}""")
        cl = QVBoxLayout(card); cl.setContentsMargins(14, 10, 14, 10); cl.setSpacing(6)

        ch = QHBoxLayout()
        icon_lbl = QLabel(p["icon"])
        icon_lbl.setFont(QFont("Courier New", 14))
        icon_lbl.setStyleSheet(f"color:{p['color']};background:transparent;border:none;")
        name_lbl = QLabel(p["name"])
        name_lbl.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color:{p['color']};background:transparent;border:none;")
        status_lbl = QLabel("● CONFIGURED" if has else "○ NOT SET")
        status_lbl.setFont(QFont("Courier New", 7))
        status_lbl.setStyleSheet(f"color:{GREEN if has else TEXT_DIM};background:transparent;border:none;")
        ch.addWidget(icon_lbl); ch.addWidget(name_lbl); ch.addStretch(); ch.addWidget(status_lbl)
        cl.addLayout(ch)

        hint = QLabel(p["hint"])
        hint.setFont(QFont("Courier New", 7))
        hint.setStyleSheet(f"color:{TEXT_DIM};background:transparent;border:none;")
        hint.setWordWrap(True)
        cl.addWidget(hint)

        self._fields[pid] = {}
        for fname, fph, fecho in p["fields"]:
            fr = QHBoxLayout(); fr.setSpacing(6)
            fl = QLabel(fname); fl.setFixedWidth(100)
            fl.setFont(QFont("Courier New", 7))
            fl.setStyleSheet(f"color:{TEXT_MED};background:transparent;border:none;")
            ff = QLineEdit(str(saved.get(fname, "")))
            ff.setPlaceholderText(fph); ff.setFixedHeight(26)
            ff.setFont(QFont("Courier New", 8))
            if fecho:
                ff.setEchoMode(QLineEdit.EchoMode.Password)
            ff.setStyleSheet(f"""QLineEdit{{background:#000d14;color:{WHITE};
                border:1px solid {BORDER};border-radius:3px;padding:2px 6px;}}
                QLineEdit:focus{{border:1px solid {PRI};}}""")
            fr.addWidget(fl); fr.addWidget(ff, stretch=1)
            cl.addLayout(fr)
            self._fields[pid][fname] = ff

        if pid == "whatsapp":
            pair_b = self.btn("📱  Pair WhatsApp (QR Code)", color=p["color"], height=26)
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
        self._on_status("Starting gateway…")

        def _run():
            try:
                from agent.hermes_bridge import start_gateway

                def on_msg(channel: str, user: str, text: str):
                    # Forward inbound messages to the OCTO voice loop handler
                    try:
                        from main import handle_gateway_message
                        handle_gateway_message(channel, user, text)
                    except Exception:
                        pass

                started = start_gateway(on_message=on_msg)
                if started:
                    self._status_sig.emit(f"✓ Gateway running: {', '.join(started)}")
                    self._gw_status.setText("● RUNNING")
                    self._gw_status.setStyleSheet(f"color:{GREEN};background:transparent;")
                else:
                    self._status_sig.emit("Gateway started (no platforms configured with valid tokens).")
            except Exception as e:
                self._status_sig.emit(f"Error: {e}")
            finally:
                self._gw_btn.setEnabled(True)

        threading.Thread(target=_run, daemon=True).start()

    def _pair_whatsapp(self):
        self._on_status("WhatsApp QR pairing — check the terminal window.")
        try:
            from channels.whatsapp import WhatsAppChannel  # type: ignore
            ch = WhatsAppChannel()
            threading.Thread(target=ch.pair_qr, daemon=True).start()
        except Exception as e:
            self._on_status(f"WhatsApp pairing error: {e}")
