"""
Orbiter Main Application Window with System Tray Icon
"""
import sys
import socket
import json
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QMessageBox, QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QAction

from orbiter.config import ConfigManager, IPC_SOCKET
from orbiter.gui.style import DARK_THEME
from orbiter.gui.widgets.button_editor import ButtonEditorWidget
from orbiter.gui.widgets.settings_tab import SettingsTabWidget
from orbiter.gui.widgets.live_monitor import LiveMonitorWidget

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ICON_PATH = PROJECT_ROOT / "data" / "icons" / "orbiter.svg"

class MainWindow(QMainWindow):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.config_mgr = ConfigManager()
        self.setWindowTitle("Orbiter — 3Dconnexion Controller")
        self.resize(780, 580)
        self.setStyleSheet(DARK_THEME)

        self.app_icon = QIcon(str(ICON_PATH))
        self.setWindowIcon(self.app_icon)

        self.is_2d = True
        self.connected_device = None

        self.init_ui()
        self.init_tray()

        self.check_status_timer = QTimer(self)
        self.check_status_timer.timeout.connect(self.update_daemon_status)
        self.check_status_timer.start(2000)
        self.update_daemon_status()

        if not start_minimized:
            self.show()

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
        self.footer_status = QLabel("Änderungen wirken sofort live im Dienst.")
        self.footer_status.setStyleSheet("color: #64748b; font-size: 11px;")
        footer.addWidget(self.footer_status)

        footer.addStretch()

        restart_btn = QPushButton("Dienst neustarten")
        restart_btn.setObjectName("secondaryBtn")
        restart_btn.clicked.connect(self.restart_daemon)
        footer.addWidget(restart_btn)

        hide_btn = QPushButton("Ins Tray minimieren")
        hide_btn.clicked.connect(self.hide)
        footer.addWidget(hide_btn)

        main_layout.addLayout(footer)

    def init_tray(self):
        """Erstellt das Tray-Icon in der Systemleiste."""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip("Orbiter — 3Dconnexion Controller")

        # Kontextmenü für Tray
        menu = QMenu()
        menu.setStyleSheet(DARK_THEME)

        self.tray_status_action = QAction("● Orbiter", self)
        self.tray_status_action.setEnabled(False)
        menu.addAction(self.tray_status_action)
        menu.addSeparator()

        self.tray_2d_action = QAction("2D-Präzisionsmodus umschalten", self)
        self.tray_2d_action.triggered.connect(self.toggle_2d_mode)
        menu.addAction(self.tray_2d_action)

        open_action = QAction("⚙️ Einstellungen öffnen", self)
        open_action.triggered.connect(self.show_and_activate)
        menu.addAction(open_action)

        restart_action = QAction("🔄 Dienst neustarten", self)
        restart_action.triggered.connect(self.restart_daemon)
        menu.addAction(restart_action)

        menu.addSeparator()

        quit_action = QAction("❌ Beenden", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()

    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Beim Schließen des Fensters bleibt das Tray-Icon aktiv."""
        event.ignore()
        self.hide()

    def update_daemon_status(self):
        if not IPC_SOCKET.exists():
            self.status_badge.setText("● Dienst offline")
            self.status_badge.setStyleSheet("background-color: #3f1d1d; color: #f87171; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
            self.tray_status_action.setText("● Dienst offline")
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
                self.connected_device = status.get("device_name", "SpaceMouse")
                self.status_badge.setText(f"● {self.connected_device} verbunden")
                self.status_badge.setStyleSheet("background-color: #14532d; color: #4ade80; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
                self.tray_status_action.setText(f"● {self.connected_device}")
            else:
                self.status_badge.setText("○ Kein Gerät gefunden")
                self.status_badge.setStyleSheet("background-color: #451a03; color: #fb923c; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
                self.tray_status_action.setText("○ Kein Gerät verbunden")

            self.is_2d = status.get("mode_2d", True)
            self.toggle_2d_btn.setText(f"2D-Modus: {'AN' if self.is_2d else 'AUS'}")
            if self.is_2d:
                self.toggle_2d_btn.setStyleSheet("background-color: #1e3a8a; color: #93c5fd;")
                self.tray_2d_action.setText("✓ 2D-Präzisionsmodus (Aktiv)")
            else:
                self.toggle_2d_btn.setStyleSheet("background-color: #272c3a; color: #94a3b8;")
                self.tray_2d_action.setText("  2D-Präzisionsmodus (Inaktiv)")

            self.tray.setToolTip(f"Orbiter — {self.connected_device or 'SpaceMouse'} (2D: {'AN' if self.is_2d else 'AUS'})")

        except Exception:
            self.status_badge.setText("● Dienst antwortet nicht")
            self.status_badge.setStyleSheet("background-color: #3f1d1d; color: #f87171; padding: 6px 12px; border-radius: 6px; font-weight: 600;")
            self.tray_status_action.setText("● Dienst antwortet nicht")

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
