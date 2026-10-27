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
        self.init_ui()
        self.start_worker()

    def init_ui(self):
        layout = QVBoxLayout(self)

        desc = QLabel("Bewege die Kappe oder drücke Tasten, um die Rohdaten des SpaceExplorers live zu sehen:")
        desc.setStyleSheet("color: #94a3b8; margin-bottom: 8px;")
        layout.addWidget(desc)

        # Achsen-Gitter
        axis_group = QGroupBox("6-Achsen Sensorik (Auslenkung)")
        grid = QGridLayout(axis_group)

        self.axis_labels = [
            ("X-Achse (Links/Rechts)", 0),
            ("Y-Achse (Druck/Heben)", 1),
            ("Z-Achse (Vor/Zurück)", 2),
            ("Pitch (Neigung vorn/hinten)", 3),
            ("Roll (Neigung links/rechts)", 4),
            ("Twist / Yaw (Kappe drehen)", 5)
        ]

        self.bars = {}
        self.val_labels = {}

        for row, (name, code) in enumerate(self.axis_labels):
            grid.addWidget(QLabel(name), row, 0)
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

        layout.addWidget(axis_group)

        # Tasten-Feedback
        btn_group = QGroupBox("Tasten-Sensor")
        b_layout = QVBoxLayout(btn_group)
        self.btn_status = QLabel("Keine Taste gedrückt")
        self.btn_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8; padding: 12px;")
        b_layout.addWidget(self.btn_status)
        layout.addWidget(btn_group)

        layout.addStretch()

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
            name = ev.get("name", "Unbekannt")
            code = ev.get("code")
            val = ev.get("value")
            if val == 1:
                self.btn_status.setText(f"Gedrückt: {name} (Code {code})")
                self.btn_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #22c55e; padding: 12px;")
            else:
                self.btn_status.setText(f"Losgelassen: {name} (Code {code})")
                self.btn_status.setStyleSheet("font-size: 16px; font-weight: bold; color: #94a3b8; padding: 12px;")
