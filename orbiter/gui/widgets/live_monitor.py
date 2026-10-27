"""
Live Hardware Monitor & Axis Tester Widget for Orbiter
"""
import socket
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal
from orbiter.config import IPC_SOCKET
from orbiter.i18n import tr


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
        self.init_ui()
        self.start_worker()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.desc = QLabel()
        self.desc.setStyleSheet("color: #94a3b8; margin-bottom: 8px;")
        layout.addWidget(self.desc)

        self.axis_group = QGroupBox()
        grid = QGridLayout(self.axis_group)

        self.bars = {}
        self.val_labels = {}

        for row, code in enumerate(range(6)):
            name_lbl = QLabel()
            grid.addWidget(name_lbl, row, 0)
            self._axis_name_labels[code] = name_lbl
            bar = QProgressBar()
            bar.setRange(-400, 400)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(14)
            grid.addWidget(bar, row, 1)

            val_lbl = QLabel("0")
            val_lbl.setFixedWidth(50)
            grid.addWidget(val_lbl, row, 2)

            self.bars[code] = bar
            self.val_labels[code] = val_lbl

        layout.addWidget(self.axis_group)

        self.btn_group = QGroupBox()
        b_layout = QVBoxLayout(self.btn_group)
        self.btn_status = QLabel()
        self.btn_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8; padding: 12px;")
        b_layout.addWidget(self.btn_status)
        layout.addWidget(self.btn_group)

        layout.addStretch()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.desc.setText(tr("monitor.desc"))
        self.axis_group.setTitle(tr("monitor.axis_group"))
        for code, lbl in self._axis_name_labels.items():
            lbl.setText(tr(f"monitor.axis.{code}"))
        self.btn_group.setTitle(tr("monitor.btn_group"))
        # Idle text only if not showing a press state (heuristic: green = pressed)
        if "22c55e" not in self.btn_status.styleSheet():
            self.btn_status.setText(tr("monitor.btn_idle"))

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
                self.val_labels[code].setText(str(val))

        elif etype == "button":
            name = ev.get("name", tr("monitor.unknown"))
            code = ev.get("code")
            val = ev.get("value")
            if val == 1:
                self.btn_status.setText(tr("monitor.btn_down", name=name, code=code))
                self.btn_status.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #22c55e; padding: 12px;"
                )
            else:
                self.btn_status.setText(tr("monitor.btn_up", name=name, code=code))
                self.btn_status.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #94a3b8; padding: 12px;"
                )
