"""MCP page — connect any MCP server for extended OCTO capabilities."""
from __future__ import annotations
import json
import subprocess
import sys
import threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit,
)
from PyQt6.QtGui import QFont
from .base import OctoPage, PRI, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM, BORDER, PANEL, WHITE

_HERMES = Path(sys.executable).parent / "hermes.exe"

_POPULAR_MCP = [
    ("filesystem",  "npx -y @modelcontextprotocol/server-filesystem",  "Local file system access"),
    ("github",      "npx -y @modelcontextprotocol/server-github",       "GitHub repos, issues, PRs"),
    ("postgres",    "npx -y @modelcontextprotocol/server-postgres",     "PostgreSQL database queries"),
    ("brave-search","npx -y @modelcontextprotocol/server-brave-search", "Web search via Brave"),
    ("puppeteer",   "npx -y @modelcontextprotocol/server-puppeteer",    "Browser automation"),
    ("memory",      "npx -y @modelcontextprotocol/server-memory",       "Persistent knowledge graph"),
    ("slack",       "npx -y @modelcontextprotocol/server-slack",        "Slack workspace integration"),
    ("google-maps", "npx -y @modelcontextprotocol/server-google-maps",  "Maps & location data"),
]


class McpPage(OctoPage):
    _refresh_sig = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._refresh_sig.connect(self._render_servers)
        self._servers: list = []
        self._build()

    def _build(self):
        lay = self.page_layout()

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  MCP INTEGRATION", 11, bold=True, color=PRI))
        hdr.addStretch()
        ref = self.btn("↺ Refresh", color=PRI, height=26)
        ref.clicked.connect(lambda: threading.Thread(target=self._load, daemon=True).start())
        hdr.addWidget(ref)
        lay.addLayout(hdr)
        lay.addWidget(self.lbl(
            "Connect any MCP (Model Context Protocol) server to extend OCTO with custom tools and data sources.",
            7, color=TEXT_DIM, wrap=True))
        lay.addWidget(self.sep())

        # ── Add server form ──
        lay.addWidget(self.lbl("ADD MCP SERVER", 8, bold=True, color=ACC2))

        name_row = QHBoxLayout(); name_row.setSpacing(6)
        n_lbl = QLabel("Name"); n_lbl.setFixedWidth(70)
        n_lbl.setFont(QFont("Courier New", 7))
        n_lbl.setStyleSheet(f"color:{TEXT_MED};background:transparent;")
        self._name_f = self.field("e.g. my-database", height=28)
        name_row.addWidget(n_lbl); name_row.addWidget(self._name_f, stretch=1)
        lay.addLayout(name_row)

        # Mode: command or URL
        mode_row = QHBoxLayout(); mode_row.setSpacing(6)
        cmd_lbl = QLabel("Command"); cmd_lbl.setFixedWidth(70)
        cmd_lbl.setFont(QFont("Courier New", 7))
        cmd_lbl.setStyleSheet(f"color:{TEXT_MED};background:transparent;")
        self._cmd_f = self.field("npx -y @modelcontextprotocol/server-filesystem /path",
                                  height=28)
        mode_row.addWidget(cmd_lbl); mode_row.addWidget(self._cmd_f, stretch=1)
        lay.addLayout(mode_row)

        url_row = QHBoxLayout(); url_row.setSpacing(6)
        url_lbl = QLabel("OR  URL"); url_lbl.setFixedWidth(70)
        url_lbl.setFont(QFont("Courier New", 7))
        url_lbl.setStyleSheet(f"color:{TEXT_DIM};background:transparent;")
        self._url_f = self.field("https://mcp.example.com/sse  (SSE endpoint)", height=28)
        url_row.addWidget(url_lbl); url_row.addWidget(self._url_f, stretch=1)
        lay.addLayout(url_row)

        add_row = QHBoxLayout()
        add_b = self.btn("+ Connect Server", color=GREEN, height=30)
        add_b.clicked.connect(self._add_server)
        self._add_msg = self.lbl("", 7, color=GREEN)
        add_row.addWidget(add_b); add_row.addWidget(self._add_msg, stretch=1)
        lay.addLayout(add_row)
        lay.addWidget(self.sep())

        # ── Quick install popular servers ──
        lay.addWidget(self.lbl("POPULAR MCP SERVERS", 8, bold=True, color=TEXT_MED))
        lay.addWidget(self.lbl("Click to auto-configure  (requires Node.js / npx)",
                               7, color=TEXT_DIM))

        for name, cmd, desc in _POPULAR_MCP:
            card = self._quick_card(name, cmd, desc)
            lay.addWidget(card)

        lay.addWidget(self.sep())

        # ── Connected servers ──
        lay.addWidget(self.lbl("CONNECTED SERVERS", 8, bold=True, color=PRI))
        self._servers_layout = QVBoxLayout(); self._servers_layout.setSpacing(4)
        lay.addLayout(self._servers_layout)
        lay.addStretch()

        threading.Thread(target=self._load, daemon=True).start()

    def _quick_card(self, name: str, cmd: str, desc: str) -> QWidget:
        card = QWidget()
        card.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:4px;")
        cl = QHBoxLayout(card); cl.setContentsMargins(10,6,10,6); cl.setSpacing(8)

        info = QVBoxLayout(); info.setSpacing(1)
        info.addWidget(self.lbl(name, 8, bold=True, color=ACC2))
        info.addWidget(self.lbl(desc, 7, color=TEXT_DIM))
        cl.addLayout(info, stretch=1)

        add_b = self.btn("+ Add", color=PRI, height=24)
        add_b.clicked.connect(lambda _, n=name, c=cmd: self._quick_add(n, c))
        cl.addWidget(add_b)
        return card

    def _load(self):
        try:
            r = subprocess.run([str(_HERMES), "mcp", "list"],
                               capture_output=True, text=True, timeout=10)
            servers: list = []
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line and not line.startswith("No MCP") and "Add one with" not in line:
                    servers.append({"name": line})
            self._servers = servers
            self._refresh_sig.emit(servers)
        except Exception:
            self._refresh_sig.emit([])

    def _render_servers(self, servers: list):
        while self._servers_layout.count():
            item = self._servers_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not servers:
            self._servers_layout.addWidget(
                self.lbl("No MCP servers connected yet.", 8, color=TEXT_DIM))
            return

        for s in servers:
            name = s.get("name", "unknown")
            card = QWidget()
            card.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:3px;")
            cl = QHBoxLayout(card); cl.setContentsMargins(10,6,10,6); cl.setSpacing(8)
            cl.addWidget(self.lbl("●", 10, color=GREEN))
            cl.addWidget(self.lbl(name, 9, bold=True, color=WHITE), stretch=1)
            rm = self.btn("✕ Remove", color=RED, height=24)
            rm.clicked.connect(lambda _, n=name: self._remove(n))
            cl.addWidget(rm)
            self._servers_layout.addWidget(card)

    def _add_server(self):
        name = self._name_f.text().strip()
        cmd  = self._cmd_f.text().strip()
        url  = self._url_f.text().strip()
        if not name:
            self._add_msg.setText("Name is required.")
            return
        if not cmd and not url:
            self._add_msg.setText("Command or URL is required.")
            return

        def _run():
            try:
                if url:
                    args = [str(_HERMES), "mcp", "add", name, "--url", url]
                else:
                    parts = cmd.split()
                    args = [str(_HERMES), "mcp", "add", name, "--command", parts[0]]
                    if len(parts) > 1:
                        args += ["--args"] + parts[1:]
                r = subprocess.run(args, capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    self._add_msg.setText(f"Connected: {name}")
                    self._name_f.clear(); self._cmd_f.clear(); self._url_f.clear()
                else:
                    self._add_msg.setText(r.stderr.strip()[:60] or "Failed.")
                self._load()
            except Exception as e:
                self._add_msg.setText(str(e)[:60])

        self._add_msg.setText("Connecting…")
        threading.Thread(target=_run, daemon=True).start()

    def _quick_add(self, name: str, cmd: str):
        self._name_f.setText(name)
        self._cmd_f.setText(cmd)
        self._url_f.clear()

    def _remove(self, name: str):
        def _run():
            try:
                subprocess.run([str(_HERMES), "mcp", "remove", name],
                               capture_output=True, timeout=10)
                self._load()
            except Exception as e:
                print(f"[OCTO] MCP remove: {e}")
        threading.Thread(target=_run, daemon=True).start()
