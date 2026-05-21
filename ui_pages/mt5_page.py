"""MetaTrader 5 Dashboard page — display account status, watchlist, open positions, and AI suggestions."""
from __future__ import annotations
import json
import threading
from typing import Any
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout, QFrame,
    QStackedWidget
)
from PyQt6.QtGui import QFont, QColor
from .base import (
    OctoPage, BG, PANEL, PANEL2, BORDER, BORDER_B, PRI, PRI_DIM, PRI_GHO,
    ACC, ACC2, GREEN, GREEN_D, RED, TEXT, TEXT_DIM, TEXT_MED, WHITE, DARK
)

class Mt5Page(OctoPage):
    _status_sig = pyqtSignal(dict)
    _suggestion_sig = pyqtSignal(dict)
    _timesfm_sig = pyqtSignal(dict)
    _news_sig = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._watchlist_symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD"]
        self._status_sig.connect(self._on_status_updated)
        self._suggestion_sig.connect(self._on_suggestion_received)
        self._timesfm_sig.connect(self._on_timesfm_received)
        self._news_sig.connect(self._on_news_received)

        # Build UI layout
        self._lay = self.page_layout()
        self._build_header()
        self._build_offline_banner()
        self._build_dashboard()

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
        add_sym_row.addWidget(self._sym_input, stretch=3)
        add_sym_row.addWidget(add_btn, stretch=1)
        wl_lay.addLayout(add_sym_row)

        self._wl_table = QTableWidget(0, 5)
        self._wl_table.setHorizontalHeaderLabels([
            "Symbol", "Bid", "Ask", "Spread", "Suggest"
        ])
        self._style_table(self._wl_table)
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
        news_tab_lay = QHBoxLayout(self._news_tab_w)
        news_tab_lay.setContentsMargins(0, 0, 0, 0)
        news_tab_lay.setSpacing(8)
        
        # Left: Live News
        news_card, news_card_lay = self.card("📰 LIVE FOREX FACTORY NEWS", PRI)
        news_hdr_lay = QHBoxLayout()
        self._news_status_lbl = self.lbl("Polling latest news...", 7, color=TEXT_DIM)
        ref_news_btn = self.btn("↺ Refresh News", color=PRI, height=22)
        ref_news_btn.clicked.connect(self._refresh_news)
        news_hdr_lay.addWidget(self._news_status_lbl)
        news_hdr_lay.addStretch()
        news_hdr_lay.addWidget(ref_news_btn)
        news_card_lay.addLayout(news_hdr_lay)
        
        self._news_table = QTableWidget(0, 2)
        self._news_table.setHorizontalHeaderLabels(["Source", "Headline"])
        self._style_table(self._news_table)
        self._news_table.setFixedHeight(200)
        self._news_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self._news_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._news_table.setColumnWidth(0, 110)
        news_card_lay.addWidget(self._news_table)
        
        news_tab_lay.addWidget(news_card, stretch=4)
        
        # Right: Economic Calendar
        cal_card, cal_card_lay = self.card("📅 ECONOMIC CALENDAR", ACC2)
        cal_hdr_lay = QHBoxLayout()
        self._cal_status_lbl = self.lbl("Today's live high-impact macroeconomic events", 7, color=TEXT_DIM)
        cal_hdr_lay.addWidget(self._cal_status_lbl)
        cal_card_lay.addLayout(cal_hdr_lay)
        
        self._cal_table = QTableWidget(0, 7)
        self._cal_table.setHorizontalHeaderLabels([
            "Time", "Curr", "Impact", "Event Details", "Actual", "Forecast", "Previous"
        ])
        self._style_table(self._cal_table)
        self._cal_table.setFixedHeight(200)
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
        
        news_tab_lay.addWidget(cal_card, stretch=5)
        
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
            self._sym_input.clear()
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
        try:
            res = call_tool("metatrader5", "get_trading_suggestion", {"symbol": symbol, "timeframe": timeframe})
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
                                "previous": previous or "--"
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
                self._set_cell(self._news_table, idx, 0, item["source"]).setForeground(QColor(TEXT_DIM))
                self._set_cell(self._news_table, idx, 1, item["title"], bold=True)
                
        # 2. Update calendar table
        if calendar_error:
            self._cal_status_lbl.setText(f"Failed: {calendar_error}")
            self._cal_status_lbl.setStyleSheet(f"color: {RED}; background: transparent;")
            self._cal_table.setRowCount(1)
            self._set_cell(self._cal_table, 0, 0, "--")
            self._set_cell(self._cal_table, 0, 1, "--")
            self._set_cell(self._cal_table, 0, 2, "High")
            self._set_cell(self._cal_table, 0, 3, f"Unable to fetch economic calendar: {calendar_error}", bold=True).setForeground(QColor(RED))
            self._set_cell(self._cal_table, 0, 4, "--")
            self._set_cell(self._cal_table, 0, 5, "--")
            self._set_cell(self._cal_table, 0, 6, "--")
        else:
            self._cal_status_lbl.setText(f"Economic events synced ({len(calendar)} active events)")
            self._cal_status_lbl.setStyleSheet(f"color: {TEXT_MED}; background: transparent;")
            self._cal_table.setRowCount(len(calendar))
            for idx, ev in enumerate(calendar):
                self._set_cell(self._cal_table, idx, 0, ev["time"])
                self._set_cell(self._cal_table, idx, 1, ev["currency"], bold=True)
                
                impact_item = self._set_cell(self._cal_table, idx, 2, ev["impact"], bold=True)
                if ev["impact"] == "High":
                    impact_item.setForeground(QColor(RED))
                elif ev["impact"] == "Medium":
                    impact_item.setForeground(QColor(ACC2))
                else:
                    impact_item.setForeground(QColor(GREEN))
                    
                self._set_cell(self._cal_table, idx, 3, ev["event"], bold=True)
                self._set_cell(self._cal_table, idx, 4, ev["actual"])
                self._set_cell(self._cal_table, idx, 5, ev["forecast"]).setForeground(QColor(TEXT_DIM))
                self._set_cell(self._cal_table, idx, 6, ev["previous"]).setForeground(QColor(TEXT_DIM))
