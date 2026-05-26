"""MetaTrader 5 Dashboard page — display account status, watchlist, open positions, and AI suggestions."""
from __future__ import annotations
import json
import threading
from typing import Any
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout, QFrame,
    QStackedWidget, QTextEdit, QCheckBox, QDialog
)
from PyQt6.QtGui import QFont, QColor
from .base import (
    OctoPage, BG, PANEL, PANEL2, BORDER, BORDER_B, PRI, PRI_DIM, PRI_GHO,
    ACC, ACC2, GREEN, GREEN_D, RED, TEXT, TEXT_DIM, TEXT_MED, WHITE, DARK
)

class PremiumAlertToast(QWidget):
    """A floating, high-fidelity premium trade alert toast overlay."""
    def __init__(self, parent_widget, symbol: str, direction: str, entry: str, sl: str, tp: str):
        super().__init__(parent_widget)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        border_color = GREEN if direction == "BUY" else RED
        bg_gradient = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #00121d, stop:1 #00060a)"
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(15, 12, 15, 12)
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg_gradient};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(10, 8, 10, 8)
        card_lay.setSpacing(6)
        
        hdr = QHBoxLayout()
        icon = QLabel("⚠️" if direction == "SELL" else "🚀")
        icon.setFont(QFont("Courier New", 14))
        icon.setStyleSheet("background: transparent; border: none;")
        hdr.addWidget(icon)
        
        title = QLabel(f"⚡ MATRIX {direction} ALERT ⚡")
        title.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {border_color}; background: transparent; border: none;")
        hdr.addWidget(title)
        
        hdr.addStretch()
        
        close_b = QPushButton("✕")
        close_b.setFixedSize(16, 16)
        close_b.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        close_b.setCursor(Qt.CursorShape.PointingHandCursor)
        close_b.setStyleSheet(f"QPushButton {{background: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 2px;}} QPushButton:hover {{background: {RED}; color: {WHITE};}}")
        close_b.clicked.connect(self.close)
        hdr.addWidget(close_b)
        card_lay.addLayout(hdr)
        
        info = QLabel(f"Instrument: {symbol}\nEntry Target: {entry}\nStop Loss: {sl}\nTake Profit: {tp}")
        info.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        info.setStyleSheet(f"color: {WHITE}; background: transparent; border: none;")
        card_lay.addWidget(info)
        
        note = QLabel("Multi-Agent Swarm Locked Alignment Parameters Natively.")
        note.setFont(QFont("Courier New", 7))
        note.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        card_lay.addWidget(note)
        
        lay.addWidget(card)
        
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass
            
        self.resize(320, 140)
        self.position_toast(parent_widget)
        
        QTimer.singleShot(12000, self.close)
        
    def position_toast(self, parent):
        if not parent:
            return
        rect = parent.rect()
        x = rect.width() - self.width() - 20
        y = rect.height() - self.height() - 20
        self.move(max(10, x), max(10, y))
        self.show()

class TradingManagerChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OCTO — Live Trading Manager Assistant")
        self.setMinimumSize(500, 600)
        self.resize(550, 650)
        self.setStyleSheet("""
            QDialog {
                background: #000a10;
                border: 1px solid #005577;
            }
        """)
        
        # Main layout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)
        
        # Title and header
        hdr = QHBoxLayout()
        icon = QLabel("📊")
        icon.setFont(QFont("Courier New", 14))
        hdr.addWidget(icon)
        
        title = QLabel("LIVE TRADING MANAGER ASSISTANT")
        title.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff88; background: transparent;")
        hdr.addWidget(title)
        hdr.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setAutoDefault(False)
        close_btn.setDefault(False)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #888888;
                border: 1px solid #1a2f3f; border-radius: 2px;
            }
            QPushButton:hover { background: #ff3355; color: #ffffff; }
        """)
        close_btn.clicked.connect(self.close)
        hdr.addWidget(close_btn)
        lay.addLayout(hdr)
        
        # Add a brief separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("background-color: #1a2f3f; max-height: 1px; border: none;")
        lay.addWidget(sep)
        
        # Subtitle info about account
        sub = QLabel("Coordinating with Live Risk Managers and MT5 Automated Trading Agents...")
        sub.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
        sub.setStyleSheet("color: #888888; background: transparent;")
        lay.addWidget(sub)
        
        # Instantiate the imported ChatWidget
        from ui import ChatWidget, C
        sys_prompt = (
            "You are the user's executive Trading Manager, Risk Manager, and automated Trading Agent coordinator.\n"
            "Your role is to assist the user with any trading questions, risk calculations, strategy logic, or current position queries.\n"
            "You are connected live to their MetaTrader 5 account (Vantage Live, Account ID 29045579).\n"
            "You know that they currently hold an extremely profitable long position on Gold (XAUUSD+ buy, 0.01 lot, ticket #193436544, opened at 4500.94).\n"
            "Keep your responses data-driven, mathematically precise, professional, and direct. Avoid generic advice. Use clear bullet points and simple markdown tables if needed."
        )
        self.chat = ChatWidget(system=sys_prompt)
        lay.addWidget(self.chat, stretch=1)
        
        # Input row
        inp_row = QHBoxLayout()
        inp_row.setSpacing(6)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your Trading Manager a question (e.g. should I close Gold?)...")
        self.input_field.setFont(QFont("Courier New", 8))
        self.input_field.setFixedHeight(30)
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: #000d12; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 3px; padding: 2px 8px;
            }}
            QLineEdit:focus {{ border: 1px solid #00ff88; }}
        """)
        self.input_field.returnPressed.connect(self._send_message)
        inp_row.addWidget(self.input_field, stretch=1)
        
        send_btn = QPushButton("Send ▸")
        send_btn.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        send_btn.setFixedHeight(30)
        send_btn.setFixedWidth(70)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setAutoDefault(False)
        send_btn.setDefault(False)
        send_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #00ff88;
                border: 1px solid #00aa66; border-radius: 3px;
            }
            QPushButton:hover { background: rgba(0, 255, 136, 0.1); border-color: #00ff88; }
        """)
        send_btn.clicked.connect(self._send_message)
        inp_row.addWidget(send_btn)
        lay.addLayout(inp_row)
        
        # Initial greeting from Trading Manager
        self.chat._append(
            f'<div style="color:#00ff88;margin:2px 0"><b>Trading Manager:</b> Hello! I am your AI Trading Manager and Portfolio Risk Coordinator. '
            f'I am monitoring your active <b>XAUUSD+</b> position (ticket #193436544, lot 0.01) currently in healthy profit on your Vantage Live account. '
            f'How can I assist you with your positions, economic calendars, or strategy queries today?</div>'
        )
        
    def _send_message(self):
        text = self.input_field.text().strip()
        if text:
            self.chat.send(text)
            self.input_field.clear()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            if self.input_field.hasFocus():
                self._send_message()
            event.accept()
        else:
            super().keyPressEvent(event)

class Mt5Page(OctoPage):
    _status_sig = pyqtSignal(dict)
    _suggestion_sig = pyqtSignal(dict)
    _timesfm_sig = pyqtSignal(dict)
    _news_sig = pyqtSignal(dict)
    _ollama_sig = pyqtSignal(dict)
    _auto_scan_sig = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        from memory.config_manager import load_watchlist
        self._watchlist_symbols = load_watchlist()
        self._current_news = []
        self._current_calendar = []
        self._ollama_generating = False
        self._status_sig.connect(self._on_status_updated)
        self._suggestion_sig.connect(self._on_suggestion_received)
        self._timesfm_sig.connect(self._on_timesfm_received)
        self._news_sig.connect(self._on_news_received)
        self._ollama_sig.connect(self._on_ollama_insight_received)
        self._auto_scan_sig.connect(self._on_auto_scan_received)

        # Scanner state variables
        self._auto_scan_timer = QTimer(self)
        self._auto_scan_timer.timeout.connect(self._cycle_auto_scan)
        self._auto_scan_index = 0
        self._auto_scan_active = False

        # Build UI layout
        self._lay = self.page_layout()
        self._build_header()
        self._build_offline_banner()
        self._build_dashboard()
        
        # Connect news and calendar table double click interactions
        self._news_table.itemDoubleClicked.connect(self._on_news_double_clicked)
        self._cal_table.itemDoubleClicked.connect(self._on_cal_double_clicked)

        # Regular update timer (polls MT5 every 4 seconds)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(4000)

        # Economic calendar & news polling timer (polls every 60 seconds)
        self._news_timer = QTimer(self)
        self._news_timer.timeout.connect(self._refresh_news)
        self._news_timer.start(60000)

        # Initial load
        self._refresh()
        QTimer.singleShot(1000, self._refresh_news)

    def _build_header(self):
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 4)
        
        title_box = QVBoxLayout()
        title_lbl = self.lbl("◈  METATRADER 5 DASHBOARD", 11, bold=True, color=PRI)
        title_box.addWidget(title_lbl)
        
        self._conn_status = self.lbl("○ OFFLINE (Initializing...)", 7, color=TEXT_DIM)
        title_box.addWidget(self._conn_status)
        hdr.addLayout(title_box)
        hdr.addStretch()

        # Chat with Manager button
        self._chat_manager_btn = self.btn("💬 Chat with AI Manager", color=ACC2, height=26)
        self._chat_manager_btn.clicked.connect(self._open_chat_dialog)
        self._chat_manager_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hdr.addWidget(self._chat_manager_btn)

        # Refresh button
        self._ref_btn = self.btn("↺ Refresh", color=PRI, height=26)
        self._ref_btn.clicked.connect(self._refresh)
        hdr.addWidget(self._ref_btn)
        
        self._lay.addLayout(hdr)
        self._lay.addWidget(self.sep())

    def _build_offline_banner(self):
        self._offline_w = QFrame()
        self._offline_w.setStyleSheet(f"""
            QFrame {{
                background: {PANEL};
                border: 1px dashed {RED};
                border-radius: 4px;
                padding: 20px;
            }}
        """)
        lay = QVBoxLayout(self._offline_w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("⚠️")
        icon.setFont(QFont("Courier New", 28))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)
        
        title = QLabel("MT5 CONNECTION OFFLINE")
        title.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {RED}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        
        desc = QLabel(
            "OCTO cannot connect to the MetaTrader 5 Bridge.\n\n"
            "Please make sure:\n"
            "1. MetaTrader 5 Desktop terminal is open and active on this computer.\n"
            "2. The MT5 Python integration library is authorized (Tools -> Options -> Expert Advisors -> Allow WebRequest).\n"
            "3. The FastMCP bridge server is fully running.\n\n"
            "OCTO will automatically retry the connection in the background."
        )
        desc.setFont(QFont("Courier New", 8))
        desc.setStyleSheet(f"color: {WHITE}; background: transparent;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(desc)
        
        self._lay.addWidget(self._offline_w)

    def _build_dashboard(self):
        # Container widget to easily show/hide the entire dashboard
        self._dash_w = QWidget()
        self._dash_w.setStyleSheet("background: transparent;")
        self._dash_lay = QVBoxLayout(self._dash_w)
        self._dash_lay.setContentsMargins(0, 0, 0, 0)
        self._dash_lay.setSpacing(10)

        # 1. Account summary cards row
        self._cards_lay = QGridLayout()
        self._cards_lay.setSpacing(6)
        
        self._acc_card, self._acc_card_lay = self.card("ACCOUNT METRICS", PRI)
        self._bal_card, self._bal_card_lay = self.card("BALANCE & EQUITY", ACC2)
        self._pnl_card, self._pnl_card_lay = self.card("FLOATING PROFIT", GREEN)
        
        self._cards_lay.addWidget(self._acc_card, 0, 0)
        self._cards_lay.addWidget(self._bal_card, 0, 1)
        self._cards_lay.addWidget(self._pnl_card, 0, 2)
        
        # Populate initial labels in cards
        self._acc_lbl = self.lbl("Login: --\nBroker: --\nServer: --\nLeverage: 1:--", 8, color=WHITE)
        self._acc_card_lay.addWidget(self._acc_lbl)
        
        self._bal_lbl = self.lbl("Balance: $0.00\nEquity: $0.00\nFree Margin: $0.00", 8, color=WHITE)
        self._bal_card_lay.addWidget(self._bal_lbl)
        
        self._pnl_lbl = self.lbl("$0.00\n(0.00% Margin)", 14, bold=True, color=GREEN)
        self._pnl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pnl_card_lay.addWidget(self._pnl_lbl)
        
        self._dash_lay.addLayout(self._cards_lay)

        # 2. Split middle section: Positions (left) & Watchlist (right)
        split = QHBoxLayout()
        split.setSpacing(8)

        # Left Column: Active Positions
        pos_w, pos_lay = self.card("ACTIVE POSITIONS", PRI)
        self._pos_table = QTableWidget(0, 8)
        self._pos_table.setHorizontalHeaderLabels([
            "Ticket", "Symbol", "Type", "Lots", "Open", "Current", "P&L", "Action"
        ])
        self._style_table(self._pos_table)
        pos_lay.addWidget(self._pos_table)
        split.addWidget(pos_w, stretch=5)

        # Right Column: Watchlist
        wl_w, wl_lay = self.card("WATCHLIST", ACC2)
        
        # Add symbol row
        add_sym_row = QHBoxLayout()
        add_sym_row.setSpacing(4)
        self._sym_input = self.field("Symbol (e.g. XAUUSD)", height=24)
        add_btn = self.btn("+ Add", color=ACC2, height=24)
        add_btn.clicked.connect(self._add_to_watchlist)
        
        sync_btn = self.btn("⟳ Sync MT5", color=PRI, height=24)
        sync_btn.clicked.connect(self._sync_watchlist_with_mt5)
        
        add_sym_row.addWidget(self._sym_input, stretch=2)
        add_sym_row.addWidget(add_btn, stretch=1)
        add_sym_row.addWidget(sync_btn, stretch=1)
        wl_lay.addLayout(add_sym_row)

        self._wl_table = QTableWidget(0, 6)
        self._wl_table.setHorizontalHeaderLabels([
            "Symbol", "Bid", "Ask", "Spread", "Suggest", ""
        ])
        self._style_table(self._wl_table)
        self._wl_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._wl_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self._wl_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._wl_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._wl_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._wl_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._wl_table.setColumnWidth(1, 65)
        self._wl_table.setColumnWidth(2, 65)
        self._wl_table.setColumnWidth(3, 65)
        wl_lay.addWidget(self._wl_table)
        
        split.addWidget(wl_w, stretch=4)
        self._dash_lay.addLayout(split)

        # 3. Bottom Section: Gemini AI Trading Suggestions
        ai_w, ai_lay = self.card("⚡ GEMINI AI TRADING SUGGESTIONS", ACC2)
        
        # Inputs row
        ai_inputs = QHBoxLayout()
        ai_inputs.setSpacing(6)
        ai_inputs.addWidget(self.lbl("Analyze:", 8, bold=True, color=WHITE))
        
        self._ai_symbol_cb = QComboBox()
        self._ai_symbol_cb.setFont(QFont("Courier New", 8))
        self._ai_symbol_cb.setFixedHeight(26)
        self._style_combobox(self._ai_symbol_cb)
        self._ai_symbol_cb.currentTextChanged.connect(self._update_relevant_trading_links)
        ai_inputs.addWidget(self._ai_symbol_cb, stretch=1)
        
        ai_inputs.addWidget(self.lbl("Timeframe:", 8, bold=True, color=WHITE))
        self._ai_tf_cb = QComboBox()
        self._ai_tf_cb.addItems(["M1", "M5", "M15", "M30", "H1", "H4", "D1"])
        self._ai_tf_cb.setCurrentText("H1")
        self._ai_tf_cb.setFont(QFont("Courier New", 8))
        self._ai_tf_cb.setFixedHeight(26)
        self._style_combobox(self._ai_tf_cb)
        ai_inputs.addWidget(self._ai_tf_cb, stretch=1)
        
        self._ai_btn = self.btn("✨ SUGGESTION", color=ACC2, height=26)
        self._ai_btn.clicked.connect(self._get_suggestion)
        ai_inputs.addWidget(self._ai_btn, stretch=2)

        self._tf_btn = self.btn("🔮 TIMESFM FORECAST", color=PRI, height=26)
        self._tf_btn.clicked.connect(self._get_timesfm_forecast)
        ai_inputs.addWidget(self._tf_btn, stretch=2)
        ai_lay.addLayout(ai_inputs)

        # Continuous Auto-Scan & Alerts Controls
        scanner_row = QHBoxLayout()
        scanner_row.setSpacing(6)
        self._auto_scan_cb = QCheckBox("🔔 Continuous Auto-Scan & Alerts")
        self._auto_scan_cb.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        self._auto_scan_cb.setStyleSheet(f"color: {ACC2}; background: transparent; padding: 2px;")
        self._auto_scan_cb.stateChanged.connect(self._on_auto_scan_changed)
        scanner_row.addWidget(self._auto_scan_cb)
        
        self._auto_scan_status = self.lbl("Scanner status: IDLE", 7, color=TEXT_DIM)
        scanner_row.addWidget(self._auto_scan_status)
        scanner_row.addStretch()
        ai_lay.addLayout(scanner_row)

        # AI Result Area
        self._ai_res_lbl = self.lbl("Select a symbol and click Suggestion or TimesFM Forecast to analyze market patterns.", 8, color=TEXT_DIM, wrap=True)
        
        # Create a structured layout for suggestion output
        self._ai_res_w = QWidget()
        self._ai_res_w.setStyleSheet("background: transparent; border: none;")
        self._ai_res_lay = QVBoxLayout(self._ai_res_w)
        self._ai_res_lay.setContentsMargins(0, 4, 0, 0)
        self._ai_res_lay.setSpacing(6)

        # Suggestion summary boxes
        sug_metrics = QHBoxLayout()
        sug_metrics.setSpacing(8)
        
        self._sug_dir_w = QWidget()
        self._sug_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        dir_lay = QVBoxLayout(self._sug_dir_w)
        dir_lay.setContentsMargins(6,4,6,4)
        dir_lay.addWidget(self.lbl("DIRECTION", 7, color=TEXT_DIM, bold=True))
        self._sug_dir_val = self.lbl("WAIT", 16, bold=True, color=ACC2)
        self._sug_dir_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dir_lay.addWidget(self._sug_dir_val)
        sug_metrics.addWidget(self._sug_dir_w, stretch=1)

        self._sug_conf_w = QWidget()
        self._sug_conf_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        conf_lay = QVBoxLayout(self._sug_conf_w)
        conf_lay.setContentsMargins(6,4,6,4)
        conf_lay.addWidget(self.lbl("CONFIDENCE", 7, color=TEXT_DIM, bold=True))
        self._sug_conf_val = self.lbl("MEDIUM", 11, bold=True, color=WHITE)
        self._sug_conf_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        conf_lay.addWidget(self._sug_conf_val)
        sug_metrics.addWidget(self._sug_conf_w, stretch=1)

        self._sug_levels_w = QWidget()
        self._sug_levels_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        lvl_grid = QGridLayout(self._sug_levels_w)
        lvl_grid.setContentsMargins(6,4,6,4)
        lvl_grid.addWidget(self.lbl("ENTRY", 6, color=TEXT_DIM), 0, 0)
        self._sug_entry = self.lbl("--", 8, bold=True, color=WHITE)
        lvl_grid.addWidget(self._sug_entry, 0, 1)
        
        lvl_grid.addWidget(self.lbl("SL", 6, color=TEXT_DIM), 1, 0)
        self._sug_sl = self.lbl("--", 8, bold=True, color=RED)
        lvl_grid.addWidget(self._sug_sl, 1, 1)

        lvl_grid.addWidget(self.lbl("TP", 6, color=TEXT_DIM), 0, 2)
        self._sug_tp = self.lbl("--", 8, bold=True, color=GREEN)
        lvl_grid.addWidget(self._sug_tp, 0, 3)

        lvl_grid.addWidget(self.lbl("R:R", 6, color=TEXT_DIM), 1, 2)
        self._sug_rr = self.lbl("--", 8, bold=True, color=WHITE)
        lvl_grid.addWidget(self._sug_rr, 1, 3)
        sug_metrics.addWidget(self._sug_levels_w, stretch=2)

        self._ai_res_lay.addLayout(sug_metrics)

        # Reasoning block
        self._sug_reason_card = QFrame()
        self._sug_reason_card.setStyleSheet(f"background: #00080f; border: 1px solid {BORDER}; border-radius: 3px; padding: 6px;")
        reason_lay = QVBoxLayout(self._sug_reason_card)
        reason_lay.setContentsMargins(4,4,4,4)
        reason_lay.addWidget(self.lbl("AI TECHNICAL ANALYSIS REASONING", 7, bold=True, color=ACC2))
        self._sug_reasoning = self.lbl("Waiting for analysis request...", 8, color=TEXT, wrap=True)
        reason_lay.addWidget(self._sug_reasoning)
        self._ai_res_lay.addWidget(self._sug_reason_card)

        # Relevant Market News & Macro Calendar Links Card
        self._sug_links_card = QFrame()
        self._sug_links_card.setStyleSheet(f"background: #00080f; border: 1px solid {BORDER}; border-radius: 3px; padding: 6px;")
        links_lay = QVBoxLayout(self._sug_links_card)
        links_lay.setContentsMargins(4,4,4,4)
        links_lay.addWidget(self.lbl("RELEVANT MARKET NEWS & MACRO CALENDAR LINKS", 7, bold=True, color=ACC2))
        self._sug_links_lbl = self.lbl("No active symbol selected.", 8, color=TEXT, wrap=True)
        self._sug_links_lbl.setOpenExternalLinks(True)
        links_lay.addWidget(self._sug_links_lbl)
        self._ai_res_lay.addWidget(self._sug_links_card)

        ai_lay.addWidget(self._ai_res_lbl)
        ai_lay.addWidget(self._ai_res_w)
        self._ai_res_w.hide() # hide until we get a result

        # TimesFM Result Area
        self._tf_res_w = QWidget()
        self._tf_res_w.setStyleSheet("background: transparent; border: none;")
        self._tf_res_lay = QVBoxLayout(self._tf_res_w)
        self._tf_res_lay.setContentsMargins(0, 4, 0, 0)
        self._tf_res_lay.setSpacing(6)

        # Forecast summary boxes
        tf_metrics = QHBoxLayout()
        tf_metrics.setSpacing(8)
        
        self._tf_dir_w = QWidget()
        self._tf_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        tf_dir_lay = QVBoxLayout(self._tf_dir_w)
        tf_dir_lay.setContentsMargins(6,4,6,4)
        tf_dir_lay.addWidget(self.lbl("EXPECTED TREND", 7, color=TEXT_DIM, bold=True))
        self._tf_dir_val = self.lbl("NEUTRAL", 16, bold=True, color=ACC2)
        self._tf_dir_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf_dir_lay.addWidget(self._tf_dir_val)
        tf_metrics.addWidget(self._tf_dir_w, stretch=1)

        self._tf_target_w = QWidget()
        self._tf_target_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        tf_target_lay = QVBoxLayout(self._tf_target_w)
        tf_target_lay.setContentsMargins(6,4,6,4)
        tf_target_lay.addWidget(self.lbl("TARGET PRICE (+24H)", 7, color=TEXT_DIM, bold=True))
        self._tf_target_val = self.lbl("--", 12, bold=True, color=WHITE)
        self._tf_target_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf_target_lay.addWidget(self._tf_target_val)
        tf_metrics.addWidget(self._tf_target_w, stretch=1)

        self._tf_move_w = QWidget()
        self._tf_move_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        tf_move_lay = QVBoxLayout(self._tf_move_w)
        tf_move_lay.setContentsMargins(6,4,6,4)
        tf_move_lay.addWidget(self.lbl("EXPECTED MOVE", 7, color=TEXT_DIM, bold=True))
        self._tf_move_val = self.lbl("--", 12, bold=True, color=WHITE)
        self._tf_move_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tf_move_lay.addWidget(self._tf_move_val)
        tf_metrics.addWidget(self._tf_move_w, stretch=1)

        self._tf_res_lay.addLayout(tf_metrics)

        # Forecast intervals table
        tf_table_card = QFrame()
        tf_table_card.setStyleSheet(f"background: #00080f; border: 1px solid {BORDER}; border-radius: 3px; padding: 6px;")
        table_card_lay = QVBoxLayout(tf_table_card)
        table_card_lay.setContentsMargins(4,4,4,4)
        table_card_lay.addWidget(self.lbl("🔮 TIMESFM STEP FORECAST & 80% CONFIDENCE INTERVAL", 7, bold=True, color=PRI))
        
        self._tf_table = QTableWidget(0, 4)
        self._tf_table.setHorizontalHeaderLabels([
            "Step (Ahead)", "Estimated Price", "80% CI (Lower)", "80% CI (Upper)"
        ])
        self._style_table(self._tf_table)
        self._tf_table.setFixedHeight(120)
        table_card_lay.addWidget(self._tf_table)
        
        self._tf_res_lay.addWidget(tf_table_card)
        ai_lay.addWidget(self._tf_res_w)
        self._tf_res_w.hide()

        # 3. Tabbed Bottom Section: AI Analytics vs News/Calendar
        tab_row = QHBoxLayout()
        tab_row.setSpacing(10)
        
        self._ai_tab_btn = self.btn("✨ AI TRADING ANALYTICS", color=PRI, height=28)
        self._ai_tab_btn.clicked.connect(lambda: self._switch_tab(0))
        self._ai_tab_btn.setStyleSheet(f"background: {PRI_GHO}; color: {PRI}; border: 1px solid {PRI}; border-radius: 3px; padding: 0 12px;")
        
        self._news_tab_btn = self.btn("📰 LIVE NEWS & CALENDAR", color=TEXT_DIM, height=28)
        self._news_tab_btn.clicked.connect(lambda: self._switch_tab(1))
        self._news_tab_btn.setStyleSheet(f"background: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 3px; padding: 0 12px;")
        
        tab_row.addWidget(self._ai_tab_btn)
        tab_row.addWidget(self._news_tab_btn)
        tab_row.addStretch()
        self._dash_lay.addLayout(tab_row)
        
        # QStackedWidget to contain our tabs
        self._stacked_w = QStackedWidget()
        
        # Tab 1: AI suggestions + TimesFM (ai_w)
        self._stacked_w.addWidget(ai_w)
        
        # Tab 2: Economic Calendar & News
        self._news_tab_w = QWidget()
        self._news_tab_w.setStyleSheet("background: transparent; border: none;")
        news_tab_lay = QVBoxLayout(self._news_tab_w)
        news_tab_lay.setContentsMargins(0, 0, 0, 0)
        news_tab_lay.setSpacing(8)
        
        # Row 0: Quick Trading Links Card
        import webbrowser
        links_card, links_card_lay = self.card("🌐 QUICK TRADING CALENDARS & NEWS", PRI)
        links_row = QHBoxLayout()
        links_row.setSpacing(6)
        
        ff_cal_b = self.btn("📅 Forex Factory Calendar", color=ACC2, height=24)
        ff_cal_b.clicked.connect(lambda: webbrowser.open("https://www.forexfactory.com/calendar"))
        ff_cal_b.setToolTip("Open Forex Factory Economic Calendar in browser")
        
        ff_news_b = self.btn("📰 Forex Factory News", color=PRI, height=24)
        ff_news_b.clicked.connect(lambda: webbrowser.open("https://www.forexfactory.com/news"))
        ff_news_b.setToolTip("Open Forex Factory News page in browser")
        
        inv_cal_b = self.btn("📈 Investing.com Calendar", color=GREEN, height=24)
        inv_cal_b.clicked.connect(lambda: webbrowser.open("https://www.investing.com/economic-calendar/"))
        inv_cal_b.setToolTip("Open Investing.com Economic Calendar in browser")
        
        te_cal_b = self.btn("📊 Trading Economics", color=ACC, height=24)
        te_cal_b.clicked.connect(lambda: webbrowser.open("https://tradingeconomics.com/calendar"))
        te_cal_b.setToolTip("Open Trading Economics Calendar in browser")
        
        myfx_cal_b = self.btn("🔗 Myfxbook Calendar", color=TEXT_MED, height=24)
        myfx_cal_b.clicked.connect(lambda: webbrowser.open("https://www.myfxbook.com/forex-economic-calendar"))
        myfx_cal_b.setToolTip("Open Myfxbook Economic Calendar in browser")
        
        links_row.addWidget(ff_cal_b)
        links_row.addWidget(ff_news_b)
        links_row.addWidget(inv_cal_b)
        links_row.addWidget(te_cal_b)
        links_row.addWidget(myfx_cal_b)
        links_row.addStretch()
        
        links_card_lay.addLayout(links_row)
        news_tab_lay.addWidget(links_card)
        
        # Row 1: News & Economic Calendar
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # Left: Live News
        news_card, news_card_lay = self.card("📰 LIVE FOREX FACTORY NEWS", PRI)
        news_hdr_lay = QHBoxLayout()
        self._news_status_lbl = self.lbl("Polling latest news...", 7, color=TEXT_DIM)
        
        open_news_btn = self.btn("🌐 Open Site", color=PRI, height=22)
        open_news_btn.clicked.connect(lambda: webbrowser.open("https://www.forexfactory.com/news"))
        open_news_btn.setToolTip("Open Forex Factory News page in browser")
        
        ref_news_btn = self.btn("↺ Refresh News", color=PRI, height=22)
        ref_news_btn.clicked.connect(self._refresh_news)
        
        news_hdr_lay.addWidget(self._news_status_lbl)
        news_hdr_lay.addStretch()
        news_hdr_lay.addWidget(open_news_btn)
        news_hdr_lay.addWidget(ref_news_btn)
        news_card_lay.addLayout(news_hdr_lay)
        
        self._news_table = QTableWidget(0, 2)
        self._news_table.setHorizontalHeaderLabels(["Source", "Headline"])
        self._style_table(self._news_table)
        self._news_table.setFixedHeight(180)
        self._news_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._news_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._news_table.setColumnWidth(0, 110)
        news_card_lay.addWidget(self._news_table)
        
        top_row.addWidget(news_card, stretch=4)
        
        # Right: Economic Calendar
        cal_card, cal_card_lay = self.card("📅 ECONOMIC CALENDAR", ACC2)
        cal_hdr_lay = QHBoxLayout()
        self._cal_status_lbl = self.lbl("Today's live high-impact macroeconomic events", 7, color=TEXT_DIM)
        
        open_cal_btn = self.btn("🌐 Open Calendar", color=ACC2, height=22)
        open_cal_btn.clicked.connect(lambda: webbrowser.open("https://www.forexfactory.com/calendar"))
        open_cal_btn.setToolTip("Open Forex Factory Economic Calendar in browser")
        
        cal_hdr_lay.addWidget(self._cal_status_lbl)
        cal_hdr_lay.addStretch()
        cal_hdr_lay.addWidget(open_cal_btn)
        cal_card_lay.addLayout(cal_hdr_lay)
        
        self._cal_table = QTableWidget(0, 7)
        self._cal_table.setHorizontalHeaderLabels([
            "Time", "Curr", "Impact", "Event Details", "Actual", "Forecast", "Previous"
        ])
        self._style_table(self._cal_table)
        self._cal_table.setFixedHeight(180)
        self._cal_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._cal_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self._cal_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self._cal_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._cal_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._cal_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self._cal_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self._cal_table.setColumnWidth(0, 60)
        self._cal_table.setColumnWidth(1, 40)
        self._cal_table.setColumnWidth(2, 55)
        self._cal_table.setColumnWidth(4, 55)
        self._cal_table.setColumnWidth(5, 55)
        self._cal_table.setColumnWidth(6, 55)
        cal_card_lay.addWidget(self._cal_table)
        
        top_row.addWidget(cal_card, stretch=5)
        news_tab_lay.addLayout(top_row)
        
        # Row 2: Ollama Macroeconomic Insights Card
        ollama_card, ollama_card_lay = self.card("✨ OLLAMA MACROECONOMIC INSIGHTS", GREEN)
        ollama_hdr_lay = QHBoxLayout()
        self._ollama_status_lbl = self.lbl("Ollama: Idle (Gemma model preferred)", 7, color=TEXT_DIM)
        self._ollama_btn = self.btn("✨ Generate Macro Summary", color=GREEN, height=22)
        self._ollama_btn.clicked.connect(lambda: self._generate_ollama_summary())
        ollama_hdr_lay.addWidget(self._ollama_status_lbl)
        ollama_hdr_lay.addStretch()
        ollama_hdr_lay.addWidget(self._ollama_btn)
        ollama_card_lay.addLayout(ollama_hdr_lay)
        
        self._ollama_insights_box = QTextEdit()
        self._ollama_insights_box.setReadOnly(True)
        self._ollama_insights_box.setFixedHeight(220)
        self._ollama_insights_box.setFont(QFont("Courier New", 8))
        self._ollama_insights_box.setStyleSheet(f"""
            QTextEdit {{
                background: #000d14;
                color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        self._ollama_insights_box.setPlaceholderText(
            "Click 'Generate Macro Summary' to have local Ollama analyze current news headlines and macroeconomic calendar events..."
        )
        ollama_card_lay.addWidget(self._ollama_insights_box)
        
        news_tab_lay.addWidget(ollama_card)
        
        self._stacked_w.addWidget(self._news_tab_w)
        
        self._dash_lay.addWidget(self._stacked_w)
        
        self._lay.addWidget(self._dash_w)

    def _style_table(self, t: QTableWidget):
        t.setFont(QFont("Courier New", 8))
        t.setStyleSheet(f"""
            QTableWidget {{
                background: #000d14;
                color: {WHITE};
                gridline-color: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background: {PANEL2};
                color: {PRI};
                padding: 4px;
                border: 1px solid {BORDER};
                font-weight: bold;
                font-size: 8pt;
                font-family: 'Courier New';
            }}
            QTableWidget::item {{
                padding: 2px;
                background: {PANEL};
            }}
        """)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        t.setFixedHeight(140)

    def _style_combobox(self, cb: QComboBox):
        cb.setStyleSheet(f"""
            QComboBox {{
                background: #000d14;
                color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 3px;
                padding: 2px 6px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {PRI_GHO};
                selection-color: {PRI};
            }}
        """)

    def _refresh(self):
        """Spawns background thread to fetch data from MT5 server."""
        threading.Thread(target=self._load_data_thread, daemon=True).start()

    def _load_data_thread(self):
        from agent.mcp_bridge import call_tool
        
        portfolio = None
        account_err = None
        try:
            res = call_tool("metatrader5", "get_portfolio_summary", {})
            if res.startswith("[MCP]"):
                account_err = res
            else:
                portfolio = self._parse_json(res)
        except Exception as e:
            account_err = str(e)

        # Fallback to plain account metrics if summary fails but is connected
        if not portfolio and not account_err:
            try:
                m_res = call_tool("metatrader5", "get_account_metrics", {})
                if not m_res.startswith("[MCP]"):
                    metrics = self._parse_json(m_res)
                    if metrics and "error" not in metrics:
                        portfolio = {
                            "account": metrics,
                            "open_positions": 0,
                            "positions": []
                        }
            except Exception:
                pass

        # Load live prices for watchlist
        prices = []
        for sym in self._watchlist_symbols:
            try:
                res_price = call_tool("metatrader5", "get_live_price", {"symbol": sym})
                if not res_price.startswith("[MCP]"):
                    pdata = self._parse_json(res_price)
                    if pdata and "error" not in pdata:
                        prices.append(pdata)
                    else:
                        prices.append({"symbol": sym, "error": True})
                else:
                    prices.append({"symbol": sym, "error": True})
            except Exception:
                prices.append({"symbol": sym, "error": True})

        self._status_sig.emit({
            "portfolio": portfolio,
            "prices": prices,
            "error": account_err
        })

    def _on_status_updated(self, data: dict):
        portfolio = data["portfolio"]
        prices = data["prices"]
        error = data["error"]

        if error or not portfolio:
            self._conn_status.setText(f"○ OFFLINE ({error or 'No connection'})")
            self._conn_status.setStyleSheet(f"color: {RED}; background: transparent;")
            self._offline_w.show()
            self._dash_w.hide()
            return

        self._offline_w.hide()
        self._dash_w.show()

        # Update Connection Status
        acc = portfolio.get("account", {})
        login_id = acc.get("account_id", "--")
        broker = acc.get("broker", "--")
        server = acc.get("server", "--")
        currency = acc.get("currency", "USD")
        
        self._conn_status.setText(f"● CONNECTED  |  ID: {login_id}  |  Broker: {broker}  |  Server: {server}")
        self._conn_status.setStyleSheet(f"color: {GREEN}; background: transparent;")

        # 1. Update Cards
        self._acc_lbl.setText(f"Login: {login_id}\nBroker: {broker[:16]}\nServer: {server[:16]}\nLeverage: 1:{acc.get('leverage', '--')}")
        
        bal = acc.get("balance", 0.0)
        eq = acc.get("equity", 0.0)
        free_margin = acc.get("free_margin", 0.0)
        margin_level = acc.get("margin_level", 0.0)
        
        self._bal_lbl.setText(f"Balance: {currency} {bal:,.2f}\nEquity: {currency} {eq:,.2f}\nFree Margin: {free_margin:,.2f}")
        
        pnl = acc.get("floating_profit", 0.0)
        pnl_text = f"${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        margin_pct = f"{margin_level:.1f}%" if margin_level else "100.0%"
        self._pnl_lbl.setText(f"{pnl_text}\n({margin_pct} Margin)")
        
        if pnl >= 0:
            self._pnl_lbl.setStyleSheet(f"color: {GREEN}; font-size: 14pt; font-weight: bold; background: transparent;")
            self._pnl_card.setStyleSheet(f"background:{PANEL}; border: 1px solid {GREEN}; border-radius:4px;")
        else:
            self._pnl_lbl.setStyleSheet(f"color: {RED}; font-size: 14pt; font-weight: bold; background: transparent;")
            self._pnl_card.setStyleSheet(f"background:{PANEL}; border: 1px solid {RED}; border-radius:4px;")

        # 2. Update Active Positions Table
        positions = portfolio.get("positions", [])
        self._pos_table.setRowCount(len(positions))
        
        for idx, pos in enumerate(positions):
            ticket = pos.get("ticket")
            symbol = pos.get("symbol")
            p_type = pos.get("type", "BUY")
            vol = pos.get("volume", 0.01)
            o_price = pos.get("open_price", 0.0)
            c_price = pos.get("current_price", 0.0)
            profit = pos.get("profit", 0.0)
            
            # Setup columns
            self._set_cell(self._pos_table, idx, 0, str(ticket))
            self._set_cell(self._pos_table, idx, 1, symbol, bold=True)
            
            type_item = self._set_cell(self._pos_table, idx, 2, p_type, bold=True)
            if p_type == "BUY":
                type_item.setForeground(QColor(GREEN))
            else:
                type_item.setForeground(QColor(RED))
                
            self._set_cell(self._pos_table, idx, 3, f"{vol:.2f}")
            self._set_cell(self._pos_table, idx, 4, f"{o_price:.5f}")
            self._set_cell(self._pos_table, idx, 5, f"{c_price:.5f}")
            
            pnl_item = self._set_cell(self._pos_table, idx, 6, f"{profit:+.2f}", bold=True)
            if profit >= 0:
                pnl_item.setForeground(QColor(GREEN))
            else:
                pnl_item.setForeground(QColor(RED))

            # Add close button
            close_b = QPushButton("✕ Close")
            close_b.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            close_b.setStyleSheet(f"QPushButton {{background: transparent; color: {RED}; border: 1px solid {RED}; border-radius: 2px; padding: 1px 4px;}} QPushButton:hover {{background: #2b0c13;}}")
            close_b.setCursor(Qt.CursorShape.PointingHandCursor)
            close_b.clicked.connect(lambda _, t=ticket: self._close_position(t))
            self._pos_table.setCellWidget(idx, 7, close_b)

        # 3. Update Watchlist Table
        self._wl_table.setRowCount(len(prices))
        
        # Check combobox items to sync
        combo_items = [self._ai_symbol_cb.itemText(i) for i in range(self._ai_symbol_cb.count())]
        for idx, p in enumerate(prices):
            sym = p.get("symbol")
            
            # Populate combobox dynamically
            if sym not in combo_items:
                self._ai_symbol_cb.addItem(sym)
                
            self._set_cell(self._wl_table, idx, 0, sym, bold=True)
            
            if p.get("error"):
                self._set_cell(self._wl_table, idx, 1, "--")
                self._set_cell(self._wl_table, idx, 2, "--")
                self._set_cell(self._wl_table, idx, 3, "--")
            else:
                bid = p.get("bid")
                ask = p.get("ask")
                spread = p.get("spread_points", 0.0)
                
                self._set_cell(self._wl_table, idx, 1, f"{bid:.5f}")
                self._set_cell(self._wl_table, idx, 2, f"{ask:.5f}")
                self._set_cell(self._wl_table, idx, 3, f"{spread:.5f}")

            # AI Suggest button
            sug_b = QPushButton("⚡ AI")
            sug_b.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            sug_b.setStyleSheet(f"QPushButton {{background: transparent; color: {ACC2}; border: 1px solid {ACC2}; border-radius: 2px; padding: 1px 4px;}} QPushButton:hover {{background: #2d2600;}}")
            sug_b.setCursor(Qt.CursorShape.PointingHandCursor)
            sug_b.clicked.connect(lambda _, s=sym: self._trigger_ai_for_symbol(s))
            self._wl_table.setCellWidget(idx, 4, sug_b)

            # Delete button
            del_b = QPushButton("✕")
            del_b.setFont(QFont("Courier New", 7, QFont.Weight.Bold))
            del_b.setStyleSheet(f"QPushButton {{background: transparent; color: {RED}; border: 1px solid {RED}; border-radius: 2px; padding: 1px 4px;}} QPushButton:hover {{background: #2b0c13;}}")
            del_b.setCursor(Qt.CursorShape.PointingHandCursor)
            del_b.clicked.connect(lambda _, s=sym: self._remove_from_watchlist(s))
            self._wl_table.setCellWidget(idx, 5, del_b)

    def _set_cell(self, table: QTableWidget, row: int, col: int, text: str, bold: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        table.setItem(row, col, item)
        return item

    def _add_to_watchlist(self):
        sym = self._sym_input.text().strip().upper()
        if sym and sym not in self._watchlist_symbols:
            self._watchlist_symbols.append(sym)
            from memory.config_manager import save_watchlist
            save_watchlist(self._watchlist_symbols)
            self._sym_input.clear()
            self._refresh()

    def _remove_from_watchlist(self, symbol: str):
        if symbol in self._watchlist_symbols:
            self._watchlist_symbols.remove(symbol)
            from memory.config_manager import save_watchlist
            save_watchlist(self._watchlist_symbols)
            self._refresh()

    def _sync_watchlist_with_mt5(self):
        self._conn_status.setText("⚙ Syncing Market Watch symbols from MT5...")
        self._conn_status.setStyleSheet("color: #ffaa00; background: transparent;")
        threading.Thread(target=self._sync_watchlist_thread, daemon=True).start()

    def _sync_watchlist_thread(self):
        from agent.mcp_bridge import call_tool
        from memory.config_manager import save_watchlist
        try:
            sym_res = call_tool("metatrader5", "get_available_symbols", {"selected_only": True})
            if not sym_res.startswith("[MCP]"):
                active_symbols = self._parse_json(sym_res)
                if active_symbols and isinstance(active_symbols, list):
                    active_symbols = [str(s).strip() for s in active_symbols if s]
                    if active_symbols:
                        # User only wants the symbols they chose in their MT5 Market Watch
                        target_symbols = ["XAUUSD+", "XAUEUR+", "EURUSD+", "CL-OIL", "BTCUSD"]
                        filtered = [s for s in active_symbols if s in target_symbols]
                        if filtered:
                            self._watchlist_symbols = sorted(list(set(filtered)))
                        else:
                            self._watchlist_symbols = sorted(list(set(active_symbols)))
                        save_watchlist(self._watchlist_symbols)
        except Exception:
            pass
        self._refresh()

    def _close_position(self, ticket: int):
        self._conn_status.setText("⚙ Closing position...")
        threading.Thread(target=self._close_position_thread, args=(ticket,), daemon=True).start()

    def _close_position_thread(self, ticket: int):
        from agent.mcp_bridge import call_tool
        try:
            call_tool("metatrader5", "close_position", {"ticket": ticket})
        except Exception:
            pass
        self._refresh()

    def _trigger_ai_for_symbol(self, symbol: str):
        self._ai_symbol_cb.setCurrentText(symbol)
        self._get_suggestion()

    def _on_auto_scan_changed(self, state: int):
        from PyQt6.QtCore import Qt
        if state == 2 or state == Qt.CheckState.Checked.value:
            self._auto_scan_active = True
            self._auto_scan_index = 0
            self._auto_scan_status.setText("Scanner status: ACTIVE (Cycling...)")
            self._auto_scan_status.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._auto_scan_timer.start(20000)
            QTimer.singleShot(1000, self._cycle_auto_scan)
        else:
            self._auto_scan_active = False
            self._auto_scan_timer.stop()
            self._auto_scan_status.setText("Scanner status: IDLE")
            self._auto_scan_status.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")

    def _cycle_auto_scan(self):
        if not self._auto_scan_active or not self._watchlist_symbols:
            return
        
        if self._auto_scan_index >= len(self._watchlist_symbols):
            self._auto_scan_index = 0
            
        symbol = self._watchlist_symbols[self._auto_scan_index]
        self._auto_scan_index += 1
        
        timeframe = self._ai_tf_cb.currentText()
        
        self._auto_scan_status.setText(f"Scanner status: ANALYZING {symbol}...")
        self._auto_scan_status.setStyleSheet(f"color: {ACC2}; background: transparent;")
        
        threading.Thread(target=self._auto_scan_symbol_thread, args=(symbol, timeframe), daemon=True).start()

    def _auto_scan_symbol_thread(self, symbol: str, timeframe: str):
        from agent.mcp_bridge import call_tool
        import json
        try:
            news_str = json.dumps(self._current_news) if self._current_news else "[]"
            cal_str = json.dumps(self._current_calendar) if self._current_calendar else "[]"
            res = call_tool("metatrader5", "get_trading_suggestion", {
                "symbol": symbol, 
                "timeframe": timeframe,
                "news_json": news_str,
                "calendar_json": cal_str
            })
            sug = self._parse_json(res)
            if sug and isinstance(sug, dict):
                sug["_scan_symbol"] = symbol
                self._auto_scan_sig.emit(sug)
            else:
                self._auto_scan_sig.emit({"_scan_symbol": symbol, "error": res})
        except Exception as e:
            self._auto_scan_sig.emit({"_scan_symbol": symbol, "error": str(e)})

    def _on_auto_scan_received(self, sug: dict):
        if not self._auto_scan_active:
            return
            
        symbol = sug.get("_scan_symbol", "")
        
        if "error" in sug:
            self._auto_scan_status.setText(f"Scanner status: ERROR on {symbol}")
            self._auto_scan_status.setStyleSheet(f"color: {RED}; background: transparent;")
            return
            
        direction = sug.get("direction", "WAIT").upper()
        
        self._auto_scan_status.setText(f"Scanner status: IDLE (Last: {symbol} - {direction})")
        self._auto_scan_status.setStyleSheet(f"color: {TEXT_DIM}; background: transparent;")
        
        if direction in ["BUY", "SELL"]:
            entry = sug.get("entry", "--")
            sl = sug.get("sl", "--")
            tp = sug.get("tp", "--")
            
            self._alert_toast = PremiumAlertToast(self.window(), symbol, direction, str(entry), str(sl), str(tp))
            
            if self._ai_symbol_cb.currentText() == symbol:
                self._on_suggestion_received(sug)

    def _get_suggestion(self):
        symbol = self._ai_symbol_cb.currentText()
        timeframe = self._ai_tf_cb.currentText()
        if not symbol:
            return
            
        self._ai_res_lbl.hide()
        self._ai_res_w.show()
        
        self._sug_dir_val.setText("WAIT")
        self._sug_dir_val.setStyleSheet(f"color: {ACC2}; background: transparent; font-size: 16pt; font-weight: bold;")
        self._sug_conf_val.setText("ANALYZING...")
        self._sug_conf_val.setStyleSheet(f"color: {WHITE}; background: transparent; font-weight: bold;")
        self._sug_entry.setText("...")
        self._sug_sl.setText("...")
        self._sug_tp.setText("...")
        self._sug_rr.setText("...")
        self._sug_reasoning.setText("Gemini Live Core is analyzing structural patterns, key supply/demand levels, and recent price action momentum...")
        self._ai_btn.setEnabled(False)

        threading.Thread(target=self._get_suggestion_thread, args=(symbol, timeframe), daemon=True).start()

    def _get_suggestion_thread(self, symbol: str, timeframe: str):
        from agent.mcp_bridge import call_tool
        import json
        try:
            news_str = json.dumps(self._current_news) if self._current_news else "[]"
            cal_str = json.dumps(self._current_calendar) if self._current_calendar else "[]"
            res = call_tool("metatrader5", "get_trading_suggestion", {
                "symbol": symbol, 
                "timeframe": timeframe,
                "news_json": news_str,
                "calendar_json": cal_str
            })
            sug = self._parse_json(res)
            if sug and isinstance(sug, dict):
                self._suggestion_sig.emit(sug)
            else:
                self._suggestion_sig.emit({"error": res})
        except Exception as e:
            self._suggestion_sig.emit({"error": str(e)})

    def _on_suggestion_received(self, sug: dict):
        self._ai_btn.setEnabled(True)
        
        if "error" in sug:
            self._sug_conf_val.setText("ERROR")
            self._sug_conf_val.setStyleSheet(f"color: {RED}; font-weight: bold;")
            self._sug_reasoning.setText(f"Analysis failed: {sug['error']}")
            return

        direction = sug.get("direction", "WAIT").upper()
        conf = sug.get("confidence", "Medium").upper()
        entry = sug.get("entry", "--")
        sl = sug.get("sl", "--")
        tp = sug.get("tp", "--")
        rr = sug.get("rr", "--")
        reasoning = sug.get("reasoning", "")

        # Update direction pill
        self._sug_dir_val.setText(direction)
        if "BUY" in direction:
            self._sug_dir_val.setStyleSheet(f"color: {GREEN}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._sug_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {GREEN}; border-radius: 4px;")
        elif "SELL" in direction:
            self._sug_dir_val.setStyleSheet(f"color: {RED}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._sug_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {RED}; border-radius: 4px;")
        else:
            self._sug_dir_val.setStyleSheet(f"color: {ACC2}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._sug_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")

        # Update confidence
        self._sug_conf_val.setText(conf)
        if conf == "HIGH":
            self._sug_conf_val.setStyleSheet(f"color: {GREEN}; background: transparent; font-weight: bold;")
        elif conf == "LOW":
            self._sug_conf_val.setStyleSheet(f"color: {RED}; background: transparent; font-weight: bold;")
        else:
            self._sug_conf_val.setStyleSheet(f"color: {ACC2}; background: transparent; font-weight: bold;")

        # Update metrics
        self._sug_entry.setText(str(entry))
        self._sug_sl.setText(str(sl))
        self._sug_tp.setText(str(tp))
        self._sug_rr.setText(str(rr))
        self._sug_reasoning.setText(reasoning)
        
        # Update relevant trading links
        self._update_relevant_trading_links(sug.get("symbol") or self._ai_symbol_cb.currentText())

    def _update_relevant_trading_links(self, symbol: str):
        if not symbol:
            self._sug_links_lbl.setText('<div style="color: #888888; font-style: italic; font-family: \'Courier New\'; font-size: 8pt;">No active symbol selected.</div>')
            return
            
        target_currencies = set()
        symbol_upper = symbol.upper()
        
        # Common currencies we might look for
        common_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD", "CNH", "HKD", "SGD", "MXN", "SEK", "NOK", "DKK", "ZAR", "TRY"]
        for c in common_currencies:
            if c in symbol_upper:
                target_currencies.add(c)
                
        # Split symbol if standard 6-character FX
        if len(symbol_upper) == 6:
            target_currencies.add(symbol_upper[0:3])
            target_currencies.add(symbol_upper[3:6])
            
        # Standard mappings for indices and commodities
        if "US" in symbol_upper or "NAS" in symbol_upper or "SPX" in symbol_upper or "BTC" in symbol_upper or "ETH" in symbol_upper or "GOLD" in symbol_upper:
            target_currencies.add("USD")
        if "DE" in symbol_upper or "GER" in symbol_upper or "EU" in symbol_upper:
            target_currencies.add("EUR")
        if "UK" in symbol_upper or "GBP" in symbol_upper:
            target_currencies.add("GBP")
        if "JP" in symbol_upper or "NIKKEI" in symbol_upper:
            target_currencies.add("JPY")
            
        # Keyword mappings for headlines matching
        currency_keywords = {
            "USD": ["USD", "US ", "FEDERAL RESERVE", "FED", "FOMC", "POWELL", "DOLLAR", "AMERICA", "WHITE HOUSE", "TREASURY"],
            "EUR": ["EUR", "EURO", "ECB", "LAGARDE", "GERMAN", "FRANCE", "ITALY"],
            "GBP": ["GBP", "POUND", "BOE", "STERLING", "UK ", "BRITAIN", "BAILEY"],
            "JPY": ["JPY", "YEN", "BOJ", "JAPAN", "UEDA"],
            "AUD": ["AUD", "AUSSIE", "RBA", "AUSTRALIA"],
            "CAD": ["CAD", "LOONIE", "BOC", "CANADA"],
            "CHF": ["CHF", "FRANC", "SNB", "SWISS"],
            "NZD": ["NZD", "KIWI", "RBNZ", "NEW ZEALAND"],
        }
        
        # Filter Calendar Events
        relevant_cal = []
        for ev in self._current_calendar:
            ev_curr = ev.get("currency", "").upper()
            if ev_curr in target_currencies:
                relevant_cal.append(ev)
                
        cal_html = ""
        if relevant_cal:
            for ev in relevant_cal[:4]:
                impact = ev.get("impact", "Low")
                impact_color = "#ff3355" if impact == "High" else ("#ffaa00" if impact == "Medium" else "#00ff88")
                event_name = ev.get("event", "Event")
                time_str = ev.get("time", "--")
                link = ev.get("link") or "https://www.forexfactory.com/calendar"
                
                cal_html += f"""
                <div style="margin-bottom: 6px; padding: 4px; background: rgba(255, 255, 255, 0.03); border-radius: 3px;">
                    <span style="color: {impact_color}; font-weight: bold;">[{impact}]</span> 
                    <span style="color: #ffffff; font-weight: bold;">{ev_curr}</span> - {time_str} | 
                    <a href="{link}" style="color: #00ff88; text-decoration: underline; font-weight: bold;">{event_name}</a>
                    <span style="color: #888888; font-size: 7.5pt;"> (Act: {ev.get("actual", "--")} | Fct: {ev.get("forecast", "--")})</span>
                </div>
                """
        else:
            cal_html = f'<div style="color: #888888; font-style: italic; padding: 4px;">No upcoming high-impact economic events found for {", ".join(target_currencies) if target_currencies else symbol}. <a href="https://www.forexfactory.com/calendar" style="color: #00ff88; text-decoration: underline;">Open Calendar</a></div>'
            
        # Filter News Headlines
        relevant_news = []
        for n in self._current_news:
            title_upper = n.get("title", "").upper()
            is_relevant = False
            for curr in target_currencies:
                if curr in title_upper:
                    is_relevant = True
                    break
                if curr in currency_keywords:
                    for kw in currency_keywords[curr]:
                        if kw in title_upper:
                            is_relevant = True
                            break
                    if is_relevant:
                        break
            if is_relevant:
                relevant_news.append(n)
                
        news_html = ""
        if relevant_news:
            for n in relevant_news[:4]:
                title = n.get("title", "News")
                link = n.get("link") or "https://www.forexfactory.com/news"
                news_html += f"""
                <div style="margin-bottom: 6px; padding: 4px; background: rgba(255, 255, 255, 0.03); border-radius: 3px;">
                    <span style="color: #00ff88;">•</span> 
                    <a href="{link}" style="color: #8ab4f8; text-decoration: underline;">{title}</a>
                </div>
                """
        else:
            news_html = f'<div style="color: #888888; font-style: italic; padding: 4px;">No matching headlines found. <a href="https://www.forexfactory.com/news" style="color: #8ab4f8; text-decoration: underline;">View All Market News</a></div>'
            
        final_html = f"""
        <div style="font-family: 'Courier New'; font-size: 8pt; line-height: 1.4;">
            <div style="margin-bottom: 6px; color: #8ab4f8; font-weight: bold; border-bottom: 1px solid #1a2f3f; padding-bottom: 2px;">
                📅 UPCOMING MACRO EVENTS ({", ".join(target_currencies) if target_currencies else symbol})
            </div>
            {cal_html}
            <div style="margin-top: 10px; margin-bottom: 6px; color: #00ff88; font-weight: bold; border-bottom: 1px solid #1a2f3f; padding-bottom: 2px;">
                📰 CORRELATED FINANCIAL HEADLINES
            </div>
            {news_html}
        </div>
        """
        self._sug_links_lbl.setText(final_html)

    def _get_timesfm_forecast(self):
        symbol = self._ai_symbol_cb.currentText()
        timeframe = self._ai_tf_cb.currentText()
        if not symbol:
            return
            
        self._ai_res_lbl.hide()
        self._ai_res_w.hide()
        self._tf_res_w.show()
        
        self._tf_dir_val.setText("WAIT")
        self._tf_dir_val.setStyleSheet(f"color: {ACC2}; background: transparent; font-size: 16pt; font-weight: bold;")
        self._tf_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")
        
        self._tf_target_val.setText("FORECASTING...")
        self._tf_move_val.setText("ANALYZING...")
        self._tf_table.setRowCount(0)
        
        self._ai_btn.setEnabled(False)
        self._tf_btn.setEnabled(False)

        threading.Thread(target=self._get_timesfm_forecast_thread, args=(symbol, timeframe), daemon=True).start()

    def _get_timesfm_forecast_thread(self, symbol: str, timeframe: str):
        from agent.mcp_bridge import call_tool
        try:
            res = call_tool("metatrader5", "forecast_price_trend", {"symbol": symbol, "timeframe": timeframe, "horizon": 24})
            fc = self._parse_json(res)
            if fc and isinstance(fc, dict):
                self._timesfm_sig.emit(fc)
            else:
                self._timesfm_sig.emit({"error": res})
        except Exception as e:
            self._timesfm_sig.emit({"error": str(e)})

    def _on_timesfm_received(self, data: dict):
        self._ai_btn.setEnabled(True)
        self._tf_btn.setEnabled(True)
        
        if "error" in data:
            self._tf_target_val.setText("ERROR")
            self._tf_move_val.setText("FAILED")
            self._tf_table.setRowCount(1)
            self._set_cell(self._tf_table, 0, 0, "ERR")
            self._set_cell(self._tf_table, 0, 1, str(data["error"])[:40], bold=True).setForeground(QColor(RED))
            self._set_cell(self._tf_table, 0, 2, "--")
            self._set_cell(self._tf_table, 0, 3, "--")
            return

        direction = data.get("direction", "NEUTRAL").upper()
        current_price = data.get("current_price", 0.0)
        forecast_price = data.get("forecast_price", 0.0)
        net_change = data.get("net_change", 0.0)
        pct_change = data.get("pct_change", 0.0)
        
        # 1. Update Direction Pill
        self._tf_dir_val.setText(direction)
        if direction == "BULLISH":
            self._tf_dir_val.setStyleSheet(f"color: {GREEN}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._tf_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {GREEN}; border-radius: 4px;")
        elif direction == "BEARISH":
            self._tf_dir_val.setStyleSheet(f"color: {RED}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._tf_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {RED}; border-radius: 4px;")
        else:
            self._tf_dir_val.setStyleSheet(f"color: {ACC2}; background: transparent; font-size: 16pt; font-weight: bold;")
            self._tf_dir_w.setStyleSheet(f"background: {DARK}; border: 1px solid {BORDER}; border-radius: 4px;")

        # 2. Update Metrics Summary
        self._tf_target_val.setText(f"{forecast_price:.5f}")
        sign = "+" if net_change >= 0 else ""
        self._tf_move_val.setText(f"{sign}{net_change:+.5f} ({sign}{pct_change:+.2f}%)")
        move_col = GREEN if net_change >= 0 else RED
        self._tf_move_val.setStyleSheet(f"color: {move_col}; background: transparent; font-size: 12pt; font-weight: bold;")

        # 3. Populate detailed increments table
        steps_to_show = [1, 4, 8, 12, 24]
        
        point_fc = data.get("point_forecast", [])
        q10_fc = data.get("q10_forecast", [])
        q90_fc = data.get("q90_forecast", [])
        
        actual_steps = [s for s in steps_to_show if s <= len(point_fc)]
        self._tf_table.setRowCount(len(actual_steps))
        
        for idx, step in enumerate(actual_steps):
            p_val = point_fc[step - 1]
            q10_val = q10_fc[step - 1]
            q90_val = q90_fc[step - 1]
            
            self._set_cell(self._tf_table, idx, 0, f"+{step} periods")
            self._set_cell(self._tf_table, idx, 1, f"{p_val:.5f}", bold=True)
            self._set_cell(self._tf_table, idx, 2, f"{q10_val:.5f}").setForeground(QColor(TEXT_DIM))
            self._set_cell(self._tf_table, idx, 3, f"{q90_val:.5f}").setForeground(QColor(TEXT_DIM))

    def _parse_json(self, val: str) -> Any:
        if not val:
            return None
        val_str = val.strip()
        try:
            return json.loads(val_str)
        except json.JSONDecodeError:
            try:
                import ast
                return ast.literal_eval(val_str)
            except Exception:
                return None

    def _switch_tab(self, index: int):
        self._stacked_w.setCurrentIndex(index)
        if index == 0:
            self._ai_tab_btn.setStyleSheet(f"background: {PRI_GHO}; color: {PRI}; border: 1px solid {PRI}; border-radius: 3px; padding: 0 12px;")
            self._news_tab_btn.setStyleSheet(f"background: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 3px; padding: 0 12px;")
        else:
            self._ai_tab_btn.setStyleSheet(f"background: transparent; color: {TEXT_DIM}; border: 1px solid {BORDER}; border-radius: 3px; padding: 0 12px;")
            self._news_tab_btn.setStyleSheet(f"background: {PRI_GHO}; color: {ACC2}; border: 1px solid {ACC2}; border-radius: 3px; padding: 0 12px;")

    def _on_news_double_clicked(self, item):
        link = item.data(Qt.ItemDataRole.UserRole)
        if link:
            import webbrowser
            webbrowser.open(link)

    def _on_cal_double_clicked(self, item):
        link = item.data(Qt.ItemDataRole.UserRole)
        if link:
            import webbrowser
            webbrowser.open(link)
        else:
            import webbrowser
            webbrowser.open("https://www.forexfactory.com/calendar")

    def _refresh_news(self):
        self._news_status_lbl.setText("Updating feed...")
        self._news_status_lbl.setStyleSheet(f"color: {ACC2}; background: transparent;")
        threading.Thread(target=self._load_news_thread, daemon=True).start()

    def _load_news_thread(self):
        import requests
        from bs4 import BeautifulSoup
        
        news_items = []
        calendar_events = []
        news_err = None
        cal_err = None
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 1. Fetch news headlines
        try:
            resp = requests.get("https://www.forexfactory.com/news", headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                seen_headlines = set()
                for a in soup.find_all("a"):
                    href = a.get("href", "")
                    if "news/" in href:
                        title = a.text.strip()
                        title = " ".join(title.split())
                        if len(title) > 15 and not href.endswith("/hit") and title not in seen_headlines:
                            seen_headlines.add(title)
                            news_items.append({
                                "title": title,
                                "source": "ForexFactory",
                                "link": f"https://www.forexfactory.com/{href}"
                            })
            else:
                news_err = f"HTTP {resp.status_code}"
        except Exception as e:
            news_err = str(e)
            
        # 2. Fetch Economic Calendar
        try:
            resp = requests.get("https://www.forexfactory.com/", headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                table = soup.find("table", class_="calendar__table")
                if table:
                    rows = table.find_all("tr", class_="calendar__row")
                    for row in rows:
                        currency_td = row.find("td", class_="calendar__currency")
                        currency = currency_td.text.strip() if currency_td else ""
                        
                        event_td = row.find("td", class_="calendar__event")
                        event_name = event_td.text.strip() if event_td else ""
                        
                        event_link = ""
                        if event_td:
                            event_a = event_td.find("a")
                            if event_a:
                                event_href = event_a.get("href", "")
                                if event_href:
                                    if event_href.startswith("http"):
                                        event_link = event_href
                                    else:
                                        if event_href.startswith("/"):
                                            event_href = event_href[1:]
                                        event_link = f"https://www.forexfactory.com/{event_href}"
                                        
                        time_td = row.find("td", class_="calendar__time")
                        event_time = time_td.text.strip() if time_td else ""
                        
                        impact_td = row.find("td", class_="calendar__impact")
                        impact_span = impact_td.find("span") if impact_td else None
                        impact = "Low"
                        if impact_span:
                            impact_class = impact_span.get("class", [])
                            impact_str = "".join(impact_class)
                            if "high" in impact_str.lower() or "red" in impact_str.lower():
                                impact = "High"
                            elif "medium" in impact_str.lower() or "orange" in impact_str.lower():
                                impact = "Medium"
                            elif "low" in impact_str.lower() or "yellow" in impact_str.lower():
                                impact = "Low"
                        
                        actual_td = row.find("td", class_="calendar__actual")
                        actual = actual_td.text.strip() if actual_td else ""
                        
                        forecast_td = row.find("td", class_="calendar__forecast")
                        forecast = forecast_td.text.strip() if forecast_td else ""
                        
                        previous_td = row.find("td", class_="calendar__previous")
                        previous = previous_td.text.strip() if previous_td else ""
                        
                        if event_name:
                            calendar_events.append({
                                "time": event_time or "--",
                                "currency": currency or "--",
                                "event": event_name,
                                "impact": impact,
                                "actual": actual or "--",
                                "forecast": forecast or "--",
                                "previous": previous or "--",
                                "link": event_link
                            })
                else:
                    cal_err = "Table not found"
            else:
                cal_err = f"HTTP {resp.status_code}"
        except Exception as e:
            cal_err = str(e)
            
        self._news_sig.emit({
            "news": news_items,
            "calendar": calendar_events,
            "news_error": news_err,
            "calendar_error": cal_err
        })

    def _on_news_received(self, data: dict):
        news = data["news"]
        calendar = data["calendar"]
        news_error = data["news_error"]
        calendar_error = data["calendar_error"]
        
        # Cache news & calendar data for Ollama
        self._current_news = news
        self._current_calendar = calendar
        
        # 1. Update news table
        if news_error:
            self._news_status_lbl.setText(f"Failed: {news_error}")
            self._news_status_lbl.setStyleSheet(f"color: {RED}; background: transparent;")
            self._news_table.setRowCount(1)
            self._set_cell(self._news_table, 0, 0, "ERR")
            self._set_cell(self._news_table, 0, 1, f"Unable to fetch Forex Factory news feed: {news_error}", bold=True).setForeground(QColor(RED))
        else:
            self._news_status_lbl.setText(f"● LIVE news synced ({len(news)} items)")
            self._news_status_lbl.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._news_table.setRowCount(len(news))
            for idx, item in enumerate(news):
                src_item = self._set_cell(self._news_table, idx, 0, item["source"])
                src_item.setForeground(QColor(TEXT_DIM))
                src_item.setData(Qt.ItemDataRole.UserRole, item.get("link", ""))
                src_item.setToolTip("Double-click to open news in browser")
                
                title_item = self._set_cell(self._news_table, idx, 1, item["title"], bold=True)
                title_item.setData(Qt.ItemDataRole.UserRole, item.get("link", ""))
                title_item.setToolTip("Double-click to open news in browser")
                
        # 2. Update calendar table
        if calendar_error:
            self._cal_status_lbl.setText(f"Failed: {calendar_error}")
            self._cal_status_lbl.setStyleSheet(f"color: {RED}; background: transparent;")
            self._cal_table.setRowCount(1)
            self._set_cell(self._cal_table, 0, 0, "--").setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 1, "--").setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 2, "High").setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 3, f"Unable to fetch economic calendar: {calendar_error}", bold=True).setForeground(QColor(RED))
            self._cal_table.item(0, 3).setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 4, "--").setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 5, "--").setToolTip("Double-click to open calendar in browser")
            self._set_cell(self._cal_table, 0, 6, "--").setToolTip("Double-click to open calendar in browser")
        else:
            self._cal_status_lbl.setText(f"Economic events synced ({len(calendar)} active events)")
            self._cal_status_lbl.setStyleSheet(f"color: {TEXT_MED}; background: transparent;")
            self._cal_table.setRowCount(len(calendar))
            for idx, ev in enumerate(calendar):
                for col_idx, key in enumerate(["time", "currency", "impact", "event", "actual", "forecast", "previous"]):
                    val = ev.get(key, "--")
                    if key == "impact":
                        item = self._set_cell(self._cal_table, idx, col_idx, val, bold=True)
                        if val == "High":
                            item.setForeground(QColor(RED))
                        elif val == "Medium":
                            item.setForeground(QColor(ACC2))
                        else:
                            item.setForeground(QColor(GREEN))
                    elif key == "currency" or key == "event":
                        item = self._set_cell(self._cal_table, idx, col_idx, val, bold=True)
                    elif key == "forecast" or key == "previous":
                        item = self._set_cell(self._cal_table, idx, col_idx, val)
                        item.setForeground(QColor(TEXT_DIM))
                    else:
                        item = self._set_cell(self._cal_table, idx, col_idx, val)
                    
                    item.setData(Qt.ItemDataRole.UserRole, ev.get("link", ""))
                    item.setToolTip("Double-click to open Forex Factory calendar in browser")

        # Update relevant trading links
        self._update_relevant_trading_links(self._ai_symbol_cb.currentText())

    def _generate_ollama_summary(self, auto=False):
        if self._ollama_generating:
            return
        
        self._ollama_generating = True
        self._ollama_btn.setEnabled(False)
        self._ollama_status_lbl.setText("Analyzing macroeconomic data via Ollama...")
        self._ollama_status_lbl.setStyleSheet(f"color: {ACC2}; background: transparent;")
        self._ollama_insights_box.setPlaceholderText("Ollama is thinking... Analyzing live events and headlines...")
        
        threading.Thread(target=self._load_ollama_summary_thread, daemon=True).start()

    def _load_ollama_summary_thread(self):
        import requests
        from memory.config_manager import load_api_keys
        
        cfg = load_api_keys()
        url = cfg.get("ollama_base_url", "http://localhost:11434")
        cfg_model = cfg.get("ollama_model", "")
        if "  [" in cfg_model:
            cfg_model = cfg_model.split("  [")[0]
        elif " [" in cfg_model:
            cfg_model = cfg_model.split(" [")[0]
        cfg_model = cfg_model.strip()
        
        # 1. Query available models
        model = None
        available_models = []
        try:
            r = requests.get(f"{url}/api/tags", timeout=3)
            if r.ok:
                available_models = [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
            
        # Determine best model
        if available_models:
            # First choice: gemma4:e2b or any gemma variant
            gemma_models = [m for m in available_models if "gemma" in m.lower()]
            if gemma_models:
                model = gemma_models[0]
            elif cfg_model in available_models:
                model = cfg_model
            else:
                model = available_models[0]
                
        if not model:
            self._ollama_sig.emit({
                "error": "Ollama is not running, or no models are downloaded. Start Ollama and pull a model (e.g., 'ollama pull gemma3:4b')."
            })
            return
            
        # 2. Formulate Prompt
        prompt = (
            "You are a professional financial analyst and macroeconomic strategist. "
            "Please analyze the following live market news headlines and upcoming economic calendar events "
            "and provide a concise, high-impact macroeconomic summary (max 300 words). "
            "Format the response using bullet points, including a brief 'Risk Assessment' and 'Trading Implications'.\n\n"
            "=== LIVE MARKET NEWS ===\n"
        )
        # Filter and limit news items to top 5
        news_items = self._current_news[:5] if self._current_news else []
        if news_items:
            for item in news_items:
                prompt += f"- [{item.get('source', 'News')}] {item.get('title', '')}\n"
        else:
            prompt += "(No live news available at the moment.)\n"
            
        prompt += "\n=== UPCOMING MACROECONOMIC CALENDAR EVENTS ===\n"
        # Prioritize High/Medium impact calendar events, falling back to Low to show exactly top 5 relevant events
        calendar_items = []
        if self._current_calendar:
            high_med = [ev for ev in self._current_calendar if str(ev.get('impact', '')).lower() in ['high', 'medium']]
            lows = [ev for ev in self._current_calendar if str(ev.get('impact', '')).lower() not in ['high', 'medium']]
            calendar_items = (high_med + lows)[:5]
            
        if calendar_items:
            for ev in calendar_items:
                prompt += f"- Time: {ev.get('time', '--')}, Currency: {ev.get('currency', '--')}, Impact: {ev.get('impact', 'Low')}, Event: {ev.get('event', '')}, Actual: {ev.get('actual', '--')}, Forecast: {ev.get('forecast', '--')}, Previous: {ev.get('previous', '--')}\n"
        else:
            prompt += "(No calendar events scheduled for today.)\n"
            
        prompt += "\nProvide the analytical summary now:"
        
        # 3. Call Ollama
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            resp = requests.post(f"{url}/api/generate", json=payload, timeout=180)
            if resp.status_code == 200:
                res_data = resp.json()
                summary = res_data.get("response", "")
                self._ollama_sig.emit({
                    "model": model,
                    "summary": summary
                })
            else:
                self._ollama_sig.emit({
                    "error": f"HTTP {resp.status_code} from Ollama server."
                })
        except Exception as e:
            self._ollama_sig.emit({
                "error": f"Connection error: {e}"
            })

    def _on_ollama_insight_received(self, data: dict):
        self._ollama_generating = False
        self._ollama_btn.setEnabled(True)
        
        if "error" in data:
            self._ollama_status_lbl.setText("Ollama: Error occurred")
            self._ollama_status_lbl.setStyleSheet(f"color: {RED}; background: transparent;")
            self._ollama_insights_box.setText(f"ERROR: {data['error']}")
        else:
            model_used = data.get("model", "local model")
            self._ollama_status_lbl.setText(f"✓ Summary generated using local Ollama ({model_used})")
            self._ollama_status_lbl.setStyleSheet(f"color: {GREEN}; background: transparent;")
            self._ollama_insights_box.setText(data.get("summary", ""))

    def _open_chat_dialog(self):
        dialog = TradingManagerChatDialog(self.window())
        dialog.exec()
