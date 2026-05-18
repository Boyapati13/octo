"""Shared helpers and styles for all OCTO pages."""
from __future__ import annotations
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QScrollArea, QTextEdit, QCheckBox,
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal

# ── Colour palette (mirrors ui.py C class) ────────────────────────────────────
BG       = "#00060a"
PANEL    = "#010d14"
PANEL2   = "#010f18"
BORDER   = "#0d3347"
BORDER_B = "#1a5c7a"
PRI      = "#00d4ff"
PRI_DIM  = "#007a99"
PRI_GHO  = "#001f2e"
ACC      = "#ff6b00"
ACC2     = "#ffcc00"
GREEN    = "#00ff88"
GREEN_D  = "#00aa55"
RED      = "#ff3355"
TEXT     = "#8ffcff"
TEXT_DIM = "#3a8a9a"
TEXT_MED = "#5ab8cc"
WHITE    = "#d8f8ff"
DARK     = "#000d14"


class OctoPage(QWidget):
    """Base class for all OCTO feature pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG};")

    # ── shared widget factories ───────────────────────────────────────────────
    @staticmethod
    def lbl(text: str, size: int = 8, bold: bool = False,
            color: str = TEXT, wrap: bool = False) -> QLabel:
        w = QLabel(text)
        w.setFont(QFont("Courier New", size,
                        QFont.Weight.Bold if bold else QFont.Weight.Normal))
        w.setStyleSheet(f"color: {color}; background: transparent;")
        w.setWordWrap(wrap)
        return w

    @staticmethod
    def sep() -> QFrame:
        s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
        s.setStyleSheet(f"color: {BORDER}; margin: 2px 0;")
        return s

    @staticmethod
    def field(ph: str = "", val: str = "", echo: bool = False,
              height: int = 30) -> QLineEdit:
        f = QLineEdit(val); f.setPlaceholderText(ph)
        f.setFont(QFont("Courier New", 9)); f.setFixedHeight(height)
        if echo: f.setEchoMode(QLineEdit.EchoMode.Password)
        f.setStyleSheet(f"""
            QLineEdit {{background:#000d14;color:{WHITE};
                border:1px solid {BORDER};border-radius:3px;padding:2px 8px;}}
            QLineEdit:focus {{border:1px solid {PRI};}}""")
        return f

    @staticmethod
    def btn(text: str, color: str = PRI, height: int = 30) -> QPushButton:
        b = QPushButton(text); b.setFixedHeight(height)
        b.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{background:transparent;color:{color};
                border:1px solid {color};border-radius:3px;padding:0 12px;}}
            QPushButton:hover {{background:{PRI_GHO};}}""")
        return b

    @staticmethod
    def card(title: str, color: str = PRI) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:4px;")
        lay = QVBoxLayout(w); lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(4)
        t = QLabel(title); t.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{color};background:transparent;border:none;")
        lay.addWidget(t)
        return w, lay

    @staticmethod
    def scrollable(inner_widget: QWidget) -> QScrollArea:
        sa = QScrollArea(); sa.setWidgetResizable(True)
        sa.setStyleSheet(f"""
            QScrollArea {{background:transparent;border:none;}}
            QScrollBar:vertical {{background:{PANEL};width:6px;border-radius:3px;}}
            QScrollBar::handle:vertical {{background:{BORDER_B};border-radius:3px;}}""")
        sa.setWidget(inner_widget)
        return sa

    def page_layout(self) -> QVBoxLayout:
        """Return a pre-configured VBoxLayout for the page with scroll."""
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner); lay.setContentsMargins(16, 12, 16, 12); lay.setSpacing(8)
        sa = self.scrollable(inner)
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)
        root.addWidget(sa)
        return lay
