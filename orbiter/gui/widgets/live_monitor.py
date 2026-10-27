"""
Live Hardware Monitor & Axis Tester Widget for Orbiter
"""
import socket
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from orbiter.config import IPC_SOCKET
from orbiter.gui.style import apply_group_layout, apply_tab_page_layout
from orbiter.i18n import tr

_BTN_IDLE_STYLE = (
    "font-size: 15px; font-weight: 600; color: #38bdf8; padding: 14px;"
    "background-color: #121522; border: 1px solid #202637; border-radius: 10px;"
)
_BTN_DOWN_STYLE = (
    "font-size: 15px; font-weight: 600; color: #22c55e; padding: 14px;"
    "background-color: #121522; border: 1px solid #166534; border-radius: 10px;"
)
_BTN_UP_STYLE = (
    "font-size: 15px; font-weight: 600; color: #94a3b8; padding: 14px;"
    "background-color: #121522; border: 1px solid #202637; border-radius: 10px;"
)


class LiveMonitorThread(QThread):
    event_received = pyqtSignal(dict)

    def run(self):
        if not IPC_SOCKET.exists():
            return

        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(str(IPC_SOCKET))
            buf = ""
            while not self.isInterruptionRequested():
                data = client.recv(1024)
                if not data:
                    break
                buf += data.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            ev = json.loads(line)
                            self.event_received.emit(ev)
                        except json.JSONDecodeError:
                            pass
        except Exception:
            pass


class LiveMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._axis_name_labels = {}
        self._btn_state = "idle"
        self.init_ui()
        self.start_worker()

    def init_ui(self):
        layout = QVBoxLayout(self)
        apply_tab_page_layout(layout)

        self.desc = QLabel()
        self.desc.setStyleSheet("color: #94a3b8; margin-bottom: 4px;")
        layout.addWidget(self.desc)

        self.axis_group = QGroupBox()
        grid = QGridLayout(self.axis_group)
        apply_group_layout(grid)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 120)

        self.bars = {}
        self.val_labels = {}

        for row, code in enumerate(range(6)):
            name_lbl = QLabel()
            name_lbl.setFixedWidth(120)
            name_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            name_lbl.setTextFormat(Qt.TextFormat.RichText)
            grid.addWidget(name_lbl, row, 0)
            self._axis_name_labels[code] = name_lbl

            bar = QProgressBar()
            bar.setRange(-400, 400)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            grid.addWidget(bar, row, 1)

            val_lbl = QLabel("0")
            val_lbl.setFixedWidth(56)
            val_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            val_lbl.setStyleSheet(
                "font-family: 'JetBrains Mono', 'Fira Code', monospace;"
                "font-size: 12px; color: #e2e8f0;"
            )
            grid.addWidget(val_lbl, row, 2)

            self.bars[code] = bar
            self.val_labels[code] = val_lbl

        layout.addWidget(self.axis_group)

        self.btn_group = QGroupBox()
        b_layout = QVBoxLayout(self.btn_group)
        apply_group_layout(b_layout)
        self.btn_status = QLabel()
        self.btn_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_status.setMinimumHeight(48)
        self.btn_status.setStyleSheet(_BTN_IDLE_STYLE)
        b_layout.addWidget(self.btn_status)
        layout.addWidget(self.btn_group)

        layout.addStretch()
        self.retranslate_ui()

    def _axis_label_html(self, code: int) -> str:
        name = tr(f"monitor.axis.{code}.name")
        hint = tr(f"monitor.axis.{code}.hint")
        return (
            f"<div style='line-height:1.25;'>"
            f"<span style='font-weight:700;color:#f8fafc;font-size:13px;'>{name}</span><br>"
            f"<span style='font-weight:500;color:#64748b;font-size:11px;'>{hint}</span>"
            f"</div>"
        )

    def retranslate_ui(self):
        self.desc.setText(tr("monitor.desc"))
        self.axis_group.setTitle(tr("monitor.axis_group"))
        for code, lbl in self._axis_name_labels.items():
            lbl.setText(self._axis_label_html(code))
        self.btn_group.setTitle(tr("monitor.btn_group"))
        if self._btn_state == "idle":
            self.btn_status.setText(tr("monitor.btn_idle"))
            self.btn_status.setStyleSheet(_BTN_IDLE_STYLE)

    def start_worker(self):
        self.worker = LiveMonitorThread(self)
        self.worker.event_received.connect(self.on_event)
        self.worker.start()

    def on_event(self, ev):
        etype = ev.get("type")
        if etype == "axis":
            code = ev.get("code")
            val = ev.get("value", 0)
            if code in self.bars:
                self.bars[code].setValue(max(-400, min(400, val)))
                sign = "+" if val > 0 else ""
                self.val_labels[code].setText(f"{sign}{val}")

        elif etype == "button":
            name = ev.get("name", tr("monitor.unknown"))
            code = ev.get("code")
            val = ev.get("value")
            if val == 1:
                self._btn_state = "down"
                self.btn_status.setText(tr("monitor.btn_down", name=name, code=code))
                self.btn_status.setStyleSheet(_BTN_DOWN_STYLE)
            else:
                self._btn_state = "up"
                self.btn_status.setText(tr("monitor.btn_up", name=name, code=code))
                self.btn_status.setStyleSheet(_BTN_UP_STYLE)
