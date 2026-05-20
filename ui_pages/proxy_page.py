"""Proxy page — configure and monitor the embedded Model Routing Proxy (free-claude-code)."""
from __future__ import annotations
import socket
import threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtGui import QFont
from .base import OctoPage, PRI, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM, BORDER, PANEL, WHITE, DARK

_PROXY_PROVIDERS = [
    ("anthropic_auth_token",  "Anthropic Auth Token  (optional, direct route)", True),
    ("openrouter_api_key",    "OpenRouter API Key  (optional)", True),
    ("deepseek_api_key",      "DeepSeek API Key  (Sonnet-tier backup)", True),
    ("kimi_api_key",          "Kimi API Key  (Moonshot Opus-tier)", True),
    ("nvidia_nim_api_key",    "NVIDIA NIM API Key  (Opus-tier routing)", True),
    ("fireworks_api_key",     "Fireworks AI API Key  (Opus-tier backup)", True),
    ("zai_api_key",           "Z.ai API Key", True),
    ("wafer_api_key",         "Wafer API Key  (Sonnet-tier)", True),
]


class ProxyPage(OctoPage):
    _status_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_sig.connect(self._on_status)
        self._fields: dict[str, QLineEdit] = {}
        self._status_lbl: QLabel | None = None
        self._cfg = self._load_cfg()
        self._build()

        # Port status monitor timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_proxy_port)
        self._timer.start(3000)
        self._check_proxy_port()

    # ── persistence ──────────────────────────────────────────────────────────
    def _load_cfg(self) -> dict:
        try:
            from memory.config_manager import load_proxy_keys
            return load_proxy_keys()
        except Exception:
            return {}

    def _save_cfg(self) -> dict:
        keys = {k: f.text().strip() for k, f in self._fields.items()}
        try:
            from memory.config_manager import save_proxy_keys, sync_proxy_env
            save_proxy_keys(keys)
            sync_proxy_env()
        except Exception as e:
            print(f"[OCTO] Proxy keys save error: {e}")
        return keys

    # ── status port check ─────────────────────────────────────────────────────
    def _check_proxy_port(self):
        # Check if port 8082 is listening
        is_up = False
        try:
            with socket.create_connection(("127.0.0.1", 8082), timeout=0.5):
                is_up = True
        except OSError:
            pass

        if is_up:
            self._proxy_status.setText("● ACTIVE  [PORT 8082]")
            self._proxy_status.setStyleSheet(f"color:{GREEN};background:transparent;font-weight:bold;")
        else:
            self._proxy_status.setText("○ INACTIVE")
            self._proxy_status.setStyleSheet(f"color:{TEXT_DIM};background:transparent;")

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        lay = self.page_layout()
        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  MODEL ROUTING PROXY", 11, bold=True, color=PRI))
        hdr.addStretch()

        # Proxy service status
        self._proxy_status = self.lbl("○ CHECKING", 7, color=TEXT_DIM)
        hdr.addWidget(self._proxy_status)
        lay.addLayout(hdr)

        self._status_lbl = self.lbl(
            "Configure model backends below. The embedded Free-Claude-Code routing proxy automatically picks the best model tier.",
            7, color=TEXT_DIM, wrap=True
        )
        lay.addWidget(self._status_lbl)
        lay.addWidget(self.sep())

        # ── Routing Tiers Card ──
        tc, tl = self.card("ROUTING TIERS", color=ACC2)
        tiers = [
            (PRI,   "Opus   (Pro/Ultra)",   "NVIDIA NIM · Kimi (Moonshot) · Fireworks"),
            (ACC2,  "Sonnet (Standard)",     "DeepSeek · Wafer · OpenRouter · Anthropic"),
            (GREEN, "Haiku  (Flash)",        "Local Ollama · llama.cpp · LM Studio"),
        ]
        for col, tier, backends in tiers:
            row = QHBoxLayout(); row.setSpacing(8)
            row.addWidget(self.lbl(f"{tier:18}", 8, bold=True, color=col))
            row.addWidget(self.lbl(backends, 7, color=TEXT_MED), stretch=1)
            tl.addLayout(row)
        lay.addWidget(tc)
        lay.addSpacing(6)

        # ── Keys Configuration Card ──
        kc, kl = self.card("API KEYS (synced to ~/.fcc/.env)", color=PRI)
        for key_name, label_text, is_password in _PROXY_PROVIDERS:
            saved_val = self._cfg.get(key_name, "")
            row = QHBoxLayout(); row.setSpacing(6)
            lbl = QLabel(label_text); lbl.setFixedWidth(260)
            lbl.setFont(QFont("Courier New", 7))
            lbl.setStyleSheet(f"color:{TEXT_MED};background:transparent;border:none;")
            f = QLineEdit(saved_val)
            f.setPlaceholderText("Leave blank if unused")
            f.setFixedHeight(26)
            f.setFont(QFont("Courier New", 8))
            if is_password:
                f.setEchoMode(QLineEdit.EchoMode.Password)
            f.setStyleSheet(f"""QLineEdit{{background:#000d14;color:{WHITE};
                border:1px solid {BORDER};border-radius:3px;padding:2px 6px;}}
                QLineEdit:focus{{border:1px solid {PRI};}}""")
            row.addWidget(lbl); row.addWidget(f, stretch=1)
            kl.addLayout(row)
            self._fields[key_name] = f
        lay.addWidget(kc)

        lay.addWidget(self.sep())
        save_row = QHBoxLayout()
        save_b = self.btn("▸  SAVE & SYNC PROXY KEYS", color=PRI, height=34)
        save_b.clicked.connect(lambda: [self._save_cfg(),
                                        self._on_status("✓ Proxy keys saved and synced.")])
        save_row.addStretch(); save_row.addWidget(save_b)
        lay.addLayout(save_row)
        lay.addStretch()

    # ── actions ───────────────────────────────────────────────────────────────
    def _on_status(self, msg: str):
        if self._status_lbl:
            self._status_lbl.setText(msg)
