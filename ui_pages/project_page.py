"""
ui_pages/project_page.py
========================
OCTO Project Manager — store, activate and manage coding projects.

When a project is ACTIVE:
  • OCTO_PROJECT_ROOT env var is set → all file + terminal tools default to it
  • A system context blurb is injected into every OCTO turn
  • OCTO is granted: all files, CMD, PowerShell, security (admin) for that root
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

# ── resolve colours ───────────────────────────────────────────────────────────
try:
    from ui import C  # type: ignore
except Exception:
    class C:
        BG = "#000d14"; DARK = "#00070d"; PRI = "#00e5ff"; PRI_DIM = "#00607a"
        PRI_GHO = "#001a22"; ACC = "#ff6b35"; ACC2 = "#7c3aed"; GREEN = "#00ff88"
        GREEN_D = "#005533"; RED = "#ff3355"; TEXT = "#c8d8e0"; TEXT_MED = "#6b8fa0"
        TEXT_DIM = "#3a5060"; BORDER = "#1a2a35"; BORDER_A = "#203040"; BORDER_B = "#2a4050"
        PANEL2 = "#000f18"; WHITE = "#e8f4f8"

# ── config path ───────────────────────────────────────────────────────────────
_CFG = Path(__file__).resolve().parent.parent / "config" / "projects.json"


def _load_projects() -> list[dict]:
    try:
        return json.loads(_CFG.read_text(encoding="utf-8")) if _CFG.exists() else []
    except Exception:
        return []


def _save_projects(projects: list[dict]) -> None:
    _CFG.parent.mkdir(parents=True, exist_ok=True)
    _CFG.write_text(json.dumps(projects, indent=2), encoding="utf-8")


def get_active_project() -> dict | None:
    """Return the currently active project dict, or None."""
    for p in _load_projects():
        if p.get("active"):
            return p
    return None


def set_active_project(name: str | None) -> None:
    """Mark one project active (or clear active if name=None)."""
    projects = _load_projects()
    for p in projects:
        p["active"] = (p.get("name") == name)
    _save_projects(projects)
    # Inject into environment so sub-processes pick it up
    active = next((p for p in projects if p.get("active")), None)
    if active:
        os.environ["OCTO_PROJECT_ROOT"] = active.get("path", "")
        os.environ["OCTO_PROJECT_NAME"] = active.get("name", "")
    else:
        os.environ.pop("OCTO_PROJECT_ROOT", None)
        os.environ.pop("OCTO_PROJECT_NAME", None)


# ── project card ──────────────────────────────────────────────────────────────
class _ProjectCard(QWidget):
    activated = pyqtSignal(str)   # emits project name when activated
    removed   = pyqtSignal(str)   # emits project name when deleted

    def __init__(self, proj: dict, parent=None):
        super().__init__(parent)
        self._proj = proj
        self._build()

    def _build(self):
        name     = self._proj.get("name", "Unnamed")
        path     = self._proj.get("path", "")
        is_active= self._proj.get("active", False)
        desc     = self._proj.get("desc", "")
        border   = C.GREEN if is_active else C.BORDER_A

        self.setStyleSheet(
            f"background: {C.PANEL2}; border: 1px solid {border}; border-radius: 5px;"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(4)

        # Header row
        hrow = QHBoxLayout(); hrow.setSpacing(6)
        status_dot = QLabel("● ACTIVE" if is_active else "○")
        status_dot.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        status_dot.setStyleSheet(
            f"color: {C.GREEN if is_active else C.TEXT_DIM}; background: transparent; border: none;"
        )
        hrow.addWidget(status_dot)

        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {C.PRI if is_active else C.TEXT}; background: transparent; border: none;")
        hrow.addWidget(name_lbl, stretch=1)

        # Terminal button — opens CMD in project root
        term_btn = QPushButton("⊞ CMD")
        term_btn.setFixedHeight(22)
        term_btn.setFont(QFont("Courier New", 7))
        term_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        term_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C.ACC2};border:1px solid {C.BORDER};border-radius:3px;padding:0 6px;}}"
            f"QPushButton:hover{{border:1px solid {C.ACC2};}}"
        )
        term_btn.clicked.connect(lambda: self._open_terminal(path))
        hrow.addWidget(term_btn)

        # PowerShell button
        ps_btn = QPushButton("⊞ PS")
        ps_btn.setFixedHeight(22)
        ps_btn.setFont(QFont("Courier New", 7))
        ps_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ps_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C.ACC};border:1px solid {C.BORDER};border-radius:3px;padding:0 6px;}}"
            f"QPushButton:hover{{border:1px solid {C.ACC};}}"
        )
        ps_btn.clicked.connect(lambda: self._open_powershell(path))
        hrow.addWidget(ps_btn)

        lay.addLayout(hrow)

        # Path
        path_lbl = QLabel(f"📁  {path}")
        path_lbl.setFont(QFont("Courier New", 7))
        path_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent; border: none;")
        path_lbl.setWordWrap(True)
        lay.addWidget(path_lbl)

        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont("Courier New", 7))
            desc_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent; border: none;")
            desc_lbl.setWordWrap(True)
            lay.addWidget(desc_lbl)

        # Action row
        arow = QHBoxLayout(); arow.setSpacing(6)

        if not is_active:
            act_btn = QPushButton("▸  ACTIVATE PROJECT")
            act_btn.setFixedHeight(26)
            act_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(
                f"QPushButton{{background:transparent;color:{C.GREEN};"
                f"border:1px solid {C.GREEN_D};border-radius:3px;}}"
                f"QPushButton:hover{{background:#001a0d;border:1px solid {C.GREEN};}}"
            )
            act_btn.clicked.connect(lambda: self.activated.emit(self._proj["name"]))
            arow.addWidget(act_btn, stretch=1)
        else:
            deact_btn = QPushButton("◻  DEACTIVATE")
            deact_btn.setFixedHeight(26)
            deact_btn.setFont(QFont("Courier New", 8))
            deact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            deact_btn.setStyleSheet(
                f"QPushButton{{background:transparent;color:{C.TEXT_MED};"
                f"border:1px solid {C.BORDER};border-radius:3px;}}"
                f"QPushButton:hover{{color:{C.TEXT};border:1px solid {C.BORDER_B};}}"
            )
            deact_btn.clicked.connect(lambda: self.activated.emit(""))
            arow.addWidget(deact_btn, stretch=1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setFont(QFont("Courier New", 9))
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C.TEXT_DIM};"
            f"border:1px solid {C.BORDER};border-radius:3px;}}"
            f"QPushButton:hover{{color:{C.RED};border:1px solid {C.RED};}}"
        )
        del_btn.clicked.connect(lambda: self.removed.emit(self._proj["name"]))
        arow.addWidget(del_btn)

        lay.addLayout(arow)

    @staticmethod
    def _open_terminal(path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)  # opens explorer; below opens CMD
                subprocess.Popen(["cmd.exe", "/k", f"cd /d {path}"],
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception:
            pass

    @staticmethod
    def _open_powershell(path: str):
        try:
            if sys.platform == "win32":
                subprocess.Popen(
                    ["powershell.exe", "-NoExit", "-Command", f"Set-Location '{path}'"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
        except Exception:
            pass


# ── main page ─────────────────────────────────────────────────────────────────
class ProjectPage(QWidget):
    """Project Manager page — stores projects with full laptop access context."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C.BG};")
        self._build()
        self._refresh()

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        # Header
        hdr = QLabel("🗂  PROJECT MANAGER")
        hdr.setFont(QFont("Courier New", 13, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        root.addWidget(hdr)

        sub = QLabel(
            "Active project gives OCTO full access: all files · CMD · PowerShell · security"
        )
        sub.setFont(QFont("Courier New", 8))
        sub.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        root.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER};")
        root.addWidget(sep)

        # Active context banner
        self._active_banner = QLabel("")
        self._active_banner.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._active_banner.setStyleSheet(
            f"color: {C.GREEN}; background: {C.PANEL2}; border: 1px solid {C.GREEN_D};"
            f"border-radius: 4px; padding: 6px;"
        )
        self._active_banner.setWordWrap(True)
        self._active_banner.hide()
        root.addWidget(self._active_banner)

        # ADD PROJECT form
        form_box = QWidget()
        form_box.setStyleSheet(
            f"background: {C.PANEL2}; border: 1px solid {C.BORDER_A}; border-radius: 5px;"
        )
        form = QVBoxLayout(form_box)
        form.setContentsMargins(12, 10, 12, 10)
        form.setSpacing(6)

        form_hdr = QLabel("◈  ADD PROJECT")
        form_hdr.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        form_hdr.setStyleSheet(f"color: {C.ACC2}; background: transparent;")
        form.addWidget(form_hdr)

        # Name row
        name_row = QHBoxLayout(); name_row.setSpacing(6)
        name_lbl = QLabel("Name")
        name_lbl.setFixedWidth(60)
        name_lbl.setFont(QFont("Courier New", 8))
        name_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        self._name_f = QLineEdit()
        self._name_f.setPlaceholderText("e.g.  my-webapp")
        self._name_f.setFont(QFont("Courier New", 9))
        self._name_f.setFixedHeight(28)
        self._name_f.setStyleSheet(
            f"QLineEdit{{background:#000d12;color:{C.TEXT};"
            f"border:1px solid {C.BORDER};border-radius:3px;padding:2px 7px;}}"
            f"QLineEdit:focus{{border:1px solid {C.PRI};}}"
        )
        name_row.addWidget(name_lbl); name_row.addWidget(self._name_f, stretch=1)
        form.addLayout(name_row)

        # Path row
        path_row = QHBoxLayout(); path_row.setSpacing(6)
        path_lbl = QLabel("Path")
        path_lbl.setFixedWidth(60)
        path_lbl.setFont(QFont("Courier New", 8))
        path_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        self._path_f = QLineEdit()
        self._path_f.setPlaceholderText("C:\\Users\\You\\projects\\my-webapp")
        self._path_f.setFont(QFont("Courier New", 9))
        self._path_f.setFixedHeight(28)
        self._path_f.setStyleSheet(
            f"QLineEdit{{background:#000d12;color:{C.TEXT};"
            f"border:1px solid {C.BORDER};border-radius:3px;padding:2px 7px;}}"
            f"QLineEdit:focus{{border:1px solid {C.PRI};}}"
        )
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedHeight(28)
        browse_btn.setFont(QFont("Courier New", 8))
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(
            f"QPushButton{{background:#000d12;color:{C.ACC2};"
            f"border:1px solid {C.BORDER};border-radius:3px;padding:0 8px;}}"
            f"QPushButton:hover{{border:1px solid {C.ACC2};}}"
        )
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(path_lbl); path_row.addWidget(self._path_f, stretch=1)
        path_row.addWidget(browse_btn)
        form.addLayout(path_row)

        # Desc row
        desc_row = QHBoxLayout(); desc_row.setSpacing(6)
        desc_lbl = QLabel("Desc")
        desc_lbl.setFixedWidth(60)
        desc_lbl.setFont(QFont("Courier New", 8))
        desc_lbl.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        self._desc_f = QLineEdit()
        self._desc_f.setPlaceholderText("Short description (optional)")
        self._desc_f.setFont(QFont("Courier New", 9))
        self._desc_f.setFixedHeight(28)
        self._desc_f.setStyleSheet(
            f"QLineEdit{{background:#000d12;color:{C.TEXT};"
            f"border:1px solid {C.BORDER};border-radius:3px;padding:2px 7px;}}"
            f"QLineEdit:focus{{border:1px solid {C.PRI};}}"
        )
        desc_row.addWidget(desc_lbl); desc_row.addWidget(self._desc_f, stretch=1)
        form.addLayout(desc_row)

        add_btn = QPushButton("＋  ADD PROJECT")
        add_btn.setFixedHeight(30)
        add_btn.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C.PRI};"
            f"border:1px solid {C.PRI_DIM};border-radius:3px;}}"
            f"QPushButton:hover{{background:{C.PRI_GHO};border:1px solid {C.PRI};}}"
        )
        add_btn.clicked.connect(self._add_project)
        form.addWidget(add_btn)

        root.addWidget(form_box)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C.BORDER};")
        root.addWidget(sep2)

        # Project list
        list_hdr = QLabel("◈  STORED PROJECTS")
        list_hdr.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        list_hdr.setStyleSheet(f"color: {C.TEXT_MED}; background: transparent;")
        root.addWidget(list_hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self._card_container = QWidget()
        self._card_container.setStyleSheet("background:transparent;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_layout.setSpacing(6)
        self._card_layout.addStretch()
        scroll.setWidget(self._card_container)
        root.addWidget(scroll, stretch=1)

        # Access info bar
        info = QLabel(
            "🔒  FULL ACCESS:  files · directories · CMD · PowerShell · "
            "security · environment · registry (when project is active)"
        )
        info.setFont(QFont("Courier New", 7))
        info.setStyleSheet(
            f"color: {C.TEXT_DIM}; background: {C.PANEL2};"
            f"border: 1px solid {C.BORDER}; border-radius: 3px; padding: 5px;"
        )
        info.setWordWrap(True)
        root.addWidget(info)

    # ── actions ───────────────────────────────────────────────────────────────
    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select project root folder",
                                             str(Path.home()))
        if d:
            self._path_f.setText(d)
            if not self._name_f.text().strip():
                self._name_f.setText(Path(d).name)

    def _add_project(self):
        name = self._name_f.text().strip()
        path = self._path_f.text().strip()
        if not name or not path:
            return
        projects = _load_projects()
        # Update existing or append
        existing = next((p for p in projects if p["name"] == name), None)
        entry = {"name": name, "path": path, "desc": self._desc_f.text().strip(), "active": False}
        if existing:
            projects[projects.index(existing)] = {**existing, **entry}
        else:
            projects.append(entry)
        _save_projects(projects)
        self._name_f.clear(); self._path_f.clear(); self._desc_f.clear()
        self._refresh()

    def _activate(self, name: str):
        set_active_project(name if name else None)
        self._refresh()

    def _remove(self, name: str):
        projects = [p for p in _load_projects() if p["name"] != name]
        _save_projects(projects)
        if not name:
            os.environ.pop("OCTO_PROJECT_ROOT", None)
            os.environ.pop("OCTO_PROJECT_NAME", None)
        self._refresh()

    def _refresh(self):
        # Clear cards
        while self._card_layout.count() > 1:
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        projects = _load_projects()
        active = next((p for p in projects if p.get("active")), None)

        if active:
            self._active_banner.setText(
                f"▸ ACTIVE PROJECT: {active['name']}  |  {active['path']}\n"
                f"OCTO has full access: all files · CMD · PowerShell · security in this root"
            )
            self._active_banner.show()
            # Ensure env is synced
            os.environ["OCTO_PROJECT_ROOT"] = active.get("path", "")
            os.environ["OCTO_PROJECT_NAME"] = active.get("name", "")
        else:
            self._active_banner.hide()

        for proj in projects:
            card = _ProjectCard(proj)
            card.activated.connect(self._activate)
            card.removed.connect(self._remove)
            self._card_layout.insertWidget(self._card_layout.count() - 1, card)
