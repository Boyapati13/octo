"""Tools page — enable/disable OCTO capability toolsets."""
from __future__ import annotations
import subprocess, sys, threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtGui import QFont
from .base import OctoPage, PRI, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM, BORDER, PANEL, WHITE

_HERMES = Path(sys.executable).parent / "hermes.exe"

_TOOLSETS = [
    ("web",            "🔍", "Web Search & Scraping",        "DuckDuckGo, Exa, Tavily, web scraping"),
    ("browser",        "🌐", "Browser Automation",           "Navigate, click, fill forms, screenshot"),
    ("terminal",       "💻", "Terminal & Processes",         "Run commands, scripts, manage processes"),
    ("file",           "📁", "File Operations",              "Read, write, move, search files"),
    ("code_execution", "⚡", "Code Execution",               "Run Python, JS, bash in sandbox"),
    ("vision",         "👁",  "Vision / Image Analysis",      "Screenshot analysis, describe images"),
    ("memory",         "💾", "Memory",                       "Persistent user memory across sessions"),
    ("skills",         "📚", "Skills",                       "Install and run capability modules"),
    ("todo",           "📋", "Task Planning",                "Break goals into sub-tasks"),
    ("delegation",     "👥", "Task Delegation",              "Spawn sub-agents for parallel work"),
    ("cronjob",        "⏰", "Cron Jobs",                    "Create and manage scheduled tasks"),
    ("messaging",      "📨", "Cross-Platform Messaging",     "Send messages via Telegram, Slack, etc."),
    ("image_gen",      "🎨", "Image Generation",             "Generate images via AI (needs FAL key)"),
    ("tts",            "🔊", "Text-to-Speech",               "Convert text to audio files"),
    ("homeassistant",  "🏠", "Home Assistant",               "Control smart home (needs HA token)"),
]

_DEFAULT_ENABLED = {
    "terminal", "file", "code_execution", "memory",
    "todo", "skills", "delegation", "cronjob",
}


class ToolsPage(OctoPage):
    _refresh_sig = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._refresh_sig.connect(self._render)
        self._toggle_btns: dict[str, QPushButton] = {}
        self._enabled: set[str] = set(_DEFAULT_ENABLED)
        self._build()

    def _build(self):
        lay = self.page_layout()

        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  OCTO CAPABILITIES", 11, bold=True, color=PRI))
        hdr.addStretch()
        ref = self.btn("↺ Refresh Status", color=PRI, height=26)
        ref.clicked.connect(lambda: threading.Thread(target=self._load_status, daemon=True).start())
        hdr.addWidget(ref)
        lay.addLayout(hdr)
        lay.addWidget(self.lbl("Enable or disable tool categories for OCTO's extended agent.",
                               7, color=TEXT_DIM))
        lay.addWidget(self.sep())

        # Grid of tool cards (2 per row)
        grid_rows: list = []
        row: list = []
        for i, (tid, icon, name, desc) in enumerate(_TOOLSETS):
            card = self._tool_card(tid, icon, name, desc)
            row.append(card)
            if len(row) == 2:
                grid_rows.append(row); row = []
        if row:
            grid_rows.append(row)

        for rw in grid_rows:
            hr = QHBoxLayout(); hr.setSpacing(8)
            for card in rw:
                hr.addWidget(card, stretch=1)
            if len(rw) < 2:
                hr.addStretch(1)
            lay.addLayout(hr)

        lay.addWidget(self.sep())
        save_row = QHBoxLayout()
        save_b = self.btn("▸  SAVE TOOL CONFIG", color=PRI, height=32)
        save_b.clicked.connect(self._save)
        save_row.addStretch(); save_row.addWidget(save_b)
        lay.addLayout(save_row)
        lay.addStretch()

        threading.Thread(target=self._load_status, daemon=True).start()

    def _tool_card(self, tid: str, icon: str, name: str, desc: str) -> QWidget:
        enabled = tid in self._enabled
        card = QWidget()
        card.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:4px;")
        cl = QHBoxLayout(card); cl.setContentsMargins(10, 8, 10, 8); cl.setSpacing(8)

        icon_l = QLabel(icon); icon_l.setFont(QFont("Courier New", 14))
        icon_l.setStyleSheet(f"color:{ACC2};background:transparent;border:none;")
        icon_l.setFixedWidth(24)
        cl.addWidget(icon_l)

        info = QVBoxLayout(); info.setSpacing(1)
        info.addWidget(self.lbl(name, 8, bold=True, color=WHITE))
        info.addWidget(self.lbl(desc, 7, color=TEXT_DIM))
        cl.addLayout(info, stretch=1)

        tog = QPushButton("ON" if enabled else "OFF")
        tog.setFixedSize(44, 24)
        tog.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        tog.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_tog_style(tog, enabled)
        tog.clicked.connect(lambda _, t=tid, b=tog: self._toggle(t, b))
        cl.addWidget(tog)
        self._toggle_btns[tid] = tog
        return card

    def _update_tog_style(self, btn: QPushButton, on: bool):
        if on:
            btn.setText("ON")
            btn.setStyleSheet(f"""QPushButton{{background:{GREEN_D};color:#001a0a;
                border:none;border-radius:3px;font-weight:bold;}}""")
        else:
            btn.setText("OFF")
            btn.setStyleSheet(f"""QPushButton{{background:{PANEL};color:{TEXT_DIM};
                border:1px solid {BORDER};border-radius:3px;}}
                QPushButton:hover{{color:{PRI};border-color:{PRI};}}""")

    def _toggle(self, tid: str, btn: QPushButton):
        if tid in self._enabled:
            self._enabled.discard(tid)
            self._update_tog_style(btn, False)
        else:
            self._enabled.add(tid)
            self._update_tog_style(btn, True)

    def _load_status(self):
        try:
            r = subprocess.run([str(_HERMES), "tools", "list"],
                               capture_output=True, text=True, timeout=10)
            enabled = set()
            for line in r.stdout.splitlines():
                if "✓ enabled" in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if p == "enabled" and i + 1 < len(parts):
                            enabled.add(parts[i + 1])
            if enabled:
                self._enabled = enabled
                self._refresh_sig.emit(list(enabled))
        except Exception:
            pass

    def _render(self, enabled: list):
        self._enabled = set(enabled)
        for tid, btn in self._toggle_btns.items():
            self._update_tog_style(btn, tid in self._enabled)

    def _save(self):
        def _run():
            try:
                all_ids = {t[0] for t in _TOOLSETS}
                for tid in all_ids:
                    action = "enable" if tid in self._enabled else "disable"
                    subprocess.run([str(_HERMES), "tools", action, tid],
                                   capture_output=True, timeout=10)
                print("[OCTO] Tool config saved")
            except Exception as e:
                print(f"[OCTO] Tool save: {e}")
        threading.Thread(target=_run, daemon=True).start()
