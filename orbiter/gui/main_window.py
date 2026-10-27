"""
Orbiter Main Application Window
"""
import socket
import json
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon

from orbiter.config import ConfigManager, IPC_SOCKET
from orbiter.gui.style import DARK_THEME
from orbiter.gui.widgets.button_editor import ButtonEditorWidget
from orbiter.gui.widgets.settings_tab import SettingsTabWidget
from orbiter.gui.widgets.live_monitor import LiveMonitorWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_mgr = ConfigManager()
        self.setWindowTitle("Orbiter — 3Dconnexion SpaceMouse Control")
        self.resize(780, 580)
        self.setStyleSheet(DARK_THEME)

        self.init_ui()
        self.check_status_timer = QTimer(self)
        self.check_status_timer.timeout.connect(self.update_daemon_status)
        self.check_status_timer.start(2000)
        self.update_daemon_status()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("ORBITER")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;")
        subtitle = QLabel("3Dconnexion SpaceMouse Bridge & Linux Driver")
        subtitle.setStyleSheet("color: #64748b; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        # 2D Toggle Quick Button
        self.toggle_2d_btn = QPushButton("2D-Modus: AN")
        self.toggle_2d_btn.setObjectName("secondaryBtn")
        self.toggle_2d_btn.clicked.connect(self.toggle_2d_mode)
        header.addWidget(self.toggle_2d_btn)

        # Status Badge
        self.status_badge = QLabel("Prüfe Verbindung...")
        self.status_badge.setStyleSheet("background-color: #1e212b; padding: 6px 12px; border-radius: 6px; font-weight: 600; color: #94a3b8;")
        header.addWidget(self.status_badge)

        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.btn_tab = ButtonEditorWidget(self.config_mgr, self)
        self.settings_tab = SettingsTabWidget(self.config_mgr, self)
        self.monitor_tab = LiveMonitorWidget(self)

        self.tabs.addTab(self.btn_tab, "🎮 Tastenbelegung")
        self.tabs.addTab(self.settings_tab, "⚙️ Empfindlichkeit & Kurven")
        self.tabs.addTab(self.monitor_tab, "📡 Live Hardware-Tester")

        main_layout.addWidget(self.tabs)

        # Footer
        footer = QHBoxLayout()
        self.footer_status = QLabel("Änderungen werden sofort live im Dienst aktiv.")
        self.footer_status.setStyleSheet("color: #64748b; font-size: 11px;")
        footer.addWidget(self.footer_status)

        footer.addStretch()

        restart_btn = QPushButton("Dienst neustarten")
        restart_btn.setObjectName("secondaryBtn")
        restart_btn.clicked.connect(self.restart_daemon)
        footer.addWidget(restart_btn)

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)

        main_layout.addLayout(footer)

    def update_daemon_status(self):
        if not IPC_SOCKET.exists():
            self.status_badge.setText("● Dienst offline")
            self.status_badge.setStyleSheet("background-color: #3f1d1d; color: #f87171; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
            return

        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(str(IPC_SOCKET))
            client.sendall(b"GET_STATUS\n")
            resp = client.recv(1024).decode("utf-8").strip()
            client.close()

            status = json.loads(resp)
            if status.get("connected"):
                dev_name = status.get("device_name", "SpaceMouse")
                self.status_badge.setText(f"● {dev_name} verbunden")
                self.status_badge.setStyleSheet("background-color: #14532d; color: #4ade80; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
            else:
                self.status_badge.setText("○ Kein Gerät gefunden")
                self.status_badge.setStyleSheet("background-color: #451a03; color: #fb923c; padding: 6px 12px; border-radius: 6px; font-weight: 600;")

            is_2d = status.get("mode_2d", True)
            self.toggle_2d_btn.setText(f"2D-Modus: {'AN' if is_2d else 'AUS'}")
            if is_2d:
                self.toggle_2d_btn.setStyleSheet("background-color: #1e3a8a; color: #93c5fd;")
            else:
                self.toggle_2d_btn.setStyleSheet("background-color: #272c3a; color: #94a3b8;")

        except Exception:
            self.status_badge.setText("● Dienst antwortet nicht")
            self.status_badge.setStyleSheet("background-color: #3f1d1d; color: #f87171; padding: 6px 12px; border-radius: 6px; font-weight: 600;")

    def toggle_2d_mode(self):
        if not IPC_SOCKET.exists():
            return
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(str(IPC_SOCKET))
            client.sendall(b"TOGGLE_2D\n")
            client.close()
            self.update_daemon_status()
        except Exception:
            pass

    def restart_daemon(self):
        try:
            subprocess.run(["systemctl", "--user", "restart", "orbiter"], check=False)
            self.update_daemon_status()
            QMessageBox.information(self, "Orbiter", "Dienst wurde neu gestartet.")
        except Exception as e:
            QMessageBox.warning(self, "Orbiter", f"Konnte Dienst nicht neu starten: {e}")
