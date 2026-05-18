"""Skills page — browse and install OCTO capability modules."""
from __future__ import annotations
import subprocess, sys, threading
from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont
from .base import OctoPage, PRI, ACC2, GREEN, GREEN_D, RED, TEXT_MED, TEXT_DIM, BORDER, PANEL, WHITE

_HERMES = Path(sys.executable).parent / "hermes.exe"


class SkillsPage(OctoPage):
    _refresh_sig = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._refresh_sig.connect(self._render)
        self._build()

    def _build(self):
        lay = self.page_layout()

        hdr = QHBoxLayout()
        hdr.addWidget(self.lbl("◈  OCTO CAPABILITIES HUB", 11, bold=True, color=PRI))
        hdr.addStretch()
        ref = self.btn("↺ Refresh", color=PRI, height=26)
        ref.clicked.connect(lambda: threading.Thread(target=self._load, daemon=True).start())
        hdr.addWidget(ref)
        lay.addLayout(hdr)
        lay.addWidget(self.lbl(
            "Install capability modules — procedural memory that teaches OCTO new skills.",
            7, color=TEXT_DIM, wrap=True))
        lay.addWidget(self.sep())

        # ── search + install by name ──
        lay.addWidget(self.lbl("INSTALL BY NAME", 8, bold=True, color=ACC2))
        inst_row = QHBoxLayout(); inst_row.setSpacing(6)
        self._skill_f = self.field("e.g. github, docker, aws, kubernetes", height=30)
        inst_b = self.btn("Install", color=GREEN, height=30)
        inst_b.clicked.connect(self._install)
        self._inst_msg = self.lbl("", 7, color=GREEN)
        inst_row.addWidget(self._skill_f, stretch=1)
        inst_row.addWidget(inst_b)
        lay.addLayout(inst_row)
        lay.addWidget(self._inst_msg)

        browse_b = self.btn("🔍  Browse Skills Hub (opens terminal)", color=PRI, height=28)
        browse_b.clicked.connect(self._browse_hub)
        lay.addWidget(browse_b)
        lay.addWidget(self.sep())

        # ── installed list ──
        lay.addWidget(self.lbl("INSTALLED CAPABILITIES", 8, bold=True, color=PRI))
        self._inst_layout = QVBoxLayout(); self._inst_layout.setSpacing(4)
        lay.addLayout(self._inst_layout)
        lay.addStretch()

        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            r = subprocess.run([str(_HERMES), "skills", "list"],
                               capture_output=True, text=True, timeout=15)
            installed: list = []
            for line in r.stdout.strip().splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("┌") and not stripped.startswith("└") \
                   and not stripped.startswith("├") and not stripped.startswith("│ Name") \
                   and "─" not in stripped:
                    parts = [p.strip() for p in stripped.split("│") if p.strip()]
                    if parts and len(parts) >= 2:
                        installed.append({"name": parts[0], "status": parts[-1]})
            self._refresh_sig.emit(installed, [])
        except Exception:
            self._refresh_sig.emit([], [])

    def _render(self, installed: list, _ignored):
        while self._inst_layout.count():
            item = self._inst_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not installed:
            self._inst_layout.addWidget(
                self.lbl("No capability modules installed. Use 'Install by Name' above or browse the hub.",
                         8, color=TEXT_DIM, wrap=True))
            return

        for s in installed:
            name   = s.get("name", "")
            status = s.get("status", "")
            card   = QWidget()
            card.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:3px;")
            cl = QHBoxLayout(card); cl.setContentsMargins(10,6,10,6); cl.setSpacing(8)
            cl.addWidget(self.lbl("📚", 10))
            cl.addWidget(self.lbl(name, 9, bold=True, color=ACC2), stretch=1)
            cl.addWidget(self.lbl(status, 7, color=GREEN if "enabled" in status else TEXT_DIM))
            rm = self.btn("✕", color=RED, height=22)
            rm.clicked.connect(lambda _, n=name: self._uninstall(n))
            cl.addWidget(rm)
            self._inst_layout.addWidget(card)

    def _install(self):
        name = self._skill_f.text().strip()
        if not name:
            return
        def _run():
            try:
                r = subprocess.run([str(_HERMES), "skills", "install", name, "--yes"],
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0:
                    self._inst_msg.setText(f"Installed: {name}")
                    self._skill_f.clear()
                else:
                    self._inst_msg.setText(r.stderr.strip()[:60] or "Not found.")
                self._load()
            except Exception as e:
                self._inst_msg.setText(str(e)[:60])
        self._inst_msg.setText(f"Installing {name}…")
        threading.Thread(target=_run, daemon=True).start()

    def _uninstall(self, name: str):
        def _run():
            try:
                subprocess.run([str(_HERMES), "skills", "uninstall", name, "--yes"],
                               capture_output=True, timeout=30)
                self._load()
            except Exception as e:
                print(f"[OCTO] Skill uninstall: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def _browse_hub(self):
        try:
            subprocess.Popen([str(_HERMES), "skills", "browse"],
                             creationflags=0x00000010)
        except Exception as e:
            print(f"[OCTO] Skills browse: {e}")
