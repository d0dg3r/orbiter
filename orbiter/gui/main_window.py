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
    QPushButton, QMessageBox, QSystemTrayIcon, QMenu, QApplication,
    QComboBox, QInputDialog, QFrame
)
from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QIcon, QAction

from orbiter.config import ConfigManager, IPC_SOCKET
from orbiter.gui.style import DARK_THEME
from orbiter.gui.icons import get_icon
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
        self.resize(840, 640)
        self.setStyleSheet(DARK_THEME)

        self.app_icon = QIcon(str(ICON_PATH))
        self.setWindowIcon(self.app_icon)

        self.is_2d = True
        self.connected_device = None
        self._updating_profiles = False

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
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        # App Logo Icon + Titles
        logo_lbl = QLabel()
        logo_lbl.setPixmap(self.app_icon.pixmap(36, 36))
        header.addWidget(logo_lbl)

        title_box = QVBoxLayout()
        title = QLabel("ORBITER")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;")
        subtitle = QLabel("3Dconnexion SpaceMouse Driver & Linux Bridge")
        subtitle.setStyleSheet("color: #64748b; font-size: 11px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)

        header.addStretch()

        # Header Controls Cluster (Unified Hardware & Mode Capsule)
        header_cluster = QFrame()
        header_cluster.setObjectName("headerCluster")
        cluster_layout = QHBoxLayout(header_cluster)
        cluster_layout.setContentsMargins(12, 4, 4, 4)
        cluster_layout.setSpacing(10)

        # 1. Hardware Status Indicator
        self.status_badge = QLabel("Prüfe Verbindung...")
        self.status_badge.setObjectName("deviceStatusLabel")
        cluster_layout.addWidget(self.status_badge)

        # 2. Sleek Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setObjectName("headerDivider")
        divider.setFixedHeight(18)
        cluster_layout.addWidget(divider)

        # 3. 2D Mode Interactive Toggle
        self.toggle_2d_btn = QPushButton("2D-Gleiten: AN")
        self.toggle_2d_btn.setObjectName("modeToggleBtn")
        self.toggle_2d_btn.setFixedHeight(28)
        self.toggle_2d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_2d_btn.clicked.connect(self.toggle_2d_mode)
        cluster_layout.addWidget(self.toggle_2d_btn)

        header.addWidget(header_cluster)

        main_layout.addLayout(header)

        # Profile Toolbar
        prof_bar = QHBoxLayout()
        prof_bar.setSpacing(8)

        prof_icon_lbl = QLabel()
        prof_icon_lbl.setPixmap(get_icon("layers", color="#38bdf8", size=18).pixmap(18, 18))
        prof_bar.addWidget(prof_icon_lbl)

        prof_lbl = QLabel("Profil:")
        prof_lbl.setStyleSheet("font-weight: 700; color: #93c5fd; font-size: 13px;")
        prof_bar.addWidget(prof_lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(190)
        self.populate_profile_combo()
        self.profile_combo.currentTextChanged.connect(self.on_profile_combo_changed)
        prof_bar.addWidget(self.profile_combo)

        self.new_prof_btn = QPushButton("Neu")
        self.new_prof_btn.setObjectName("secondaryBtn")
        self.new_prof_btn.setIcon(get_icon("plus", color="#38bdf8", size=14))
        self.new_prof_btn.clicked.connect(self.create_new_profile)
        prof_bar.addWidget(self.new_prof_btn)

        self.copy_prof_btn = QPushButton("Duplizieren")
        self.copy_prof_btn.setObjectName("secondaryBtn")
        self.copy_prof_btn.setIcon(get_icon("copy", color="#94a3b8", size=14))
        self.copy_prof_btn.clicked.connect(self.copy_current_profile)
        prof_bar.addWidget(self.copy_prof_btn)

        self.rename_prof_btn = QPushButton("Umbenennen")
        self.rename_prof_btn.setObjectName("secondaryBtn")
        self.rename_prof_btn.setIcon(get_icon("edit", color="#94a3b8", size=14))
        self.rename_prof_btn.clicked.connect(self.rename_current_profile)
        prof_bar.addWidget(self.rename_prof_btn)

        self.del_prof_btn = QPushButton("Löschen")
        self.del_prof_btn.setObjectName("dangerBtn")
        self.del_prof_btn.setIcon(get_icon("trash", color="#f87171", size=14))
        self.del_prof_btn.clicked.connect(self.delete_current_profile)
        prof_bar.addWidget(self.del_prof_btn)

        prof_bar.addStretch()
        main_layout.addLayout(prof_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(18, 18))

        self.btn_tab = ButtonEditorWidget(self.config_mgr, self)
        self.settings_tab = SettingsTabWidget(self.config_mgr, self)
        self.monitor_tab = LiveMonitorWidget(self)

        self.tabs.addTab(self.btn_tab, get_icon("keyboard", color="#38bdf8", active_color="#ffffff", size=18), "Tastenbelegung")
        self.tabs.addTab(self.settings_tab, get_icon("sliders", color="#38bdf8", active_color="#ffffff", size=18), "Empfindlichkeit && Kurven")
        self.tabs.addTab(self.monitor_tab, get_icon("activity", color="#38bdf8", active_color="#ffffff", size=18), "Live Hardware-Tester")

        main_layout.addWidget(self.tabs)

        # Footer
        footer = QHBoxLayout()
        self.footer_status = QLabel("Änderungen wirken sofort live im Dienst.")
        self.footer_status.setStyleSheet("color: #64748b; font-size: 11px;")
        footer.addWidget(self.footer_status)

        footer.addStretch()

        restart_btn = QPushButton("Dienst neustarten")
        restart_btn.setObjectName("secondaryBtn")
        restart_btn.setIcon(get_icon("refresh", color="#94a3b8", size=14))
        restart_btn.clicked.connect(self.restart_daemon)
        footer.addWidget(restart_btn)

        hide_btn = QPushButton("Ins Tray minimieren")
        hide_btn.setIcon(get_icon("minimize", color="#ffffff", size=14))
        hide_btn.clicked.connect(self.hide)
        footer.addWidget(hide_btn)

        main_layout.addLayout(footer)

    def populate_profile_combo(self):
        self._updating_profiles = True
        self.profile_combo.clear()
        profiles = sorted(self.config_mgr.get_profiles().keys())
        active = self.config_mgr.get_active_profile_name()
        for p in profiles:
            self.profile_combo.addItem(get_icon("layers", color="#38bdf8", size=14), p)
        idx = self.profile_combo.findText(active)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        self._updating_profiles = False

    def on_profile_combo_changed(self, text):
        if self._updating_profiles or not text:
            return
        if text != self.config_mgr.get_active_profile_name():
            self.switch_to_profile(text)

    def switch_to_profile(self, name):
        self.config_mgr.set_active_profile(name)
        self.send_ipc_command(f"SWITCH_PROFILE {name}")
        self.refresh_all_tabs()
        self.update_tray_profiles()

    def refresh_all_tabs(self):
        self.btn_tab.populate_table()
        self.settings_tab.load_settings()

    def create_new_profile(self):
        name, ok = QInputDialog.getText(self, "Neues Profil", "Name für das neue Profil:")
        if ok and name.strip():
            clean_name = name.strip()
            res = self.config_mgr.create_profile(clean_name)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{clean_name}' existiert bereits.")

    def copy_current_profile(self):
        cur = self.config_mgr.get_active_profile_name()
        name, ok = QInputDialog.getText(self, "Profil duplizieren", f"Name für Kopie von '{cur}':", text=f"{cur} (Kopie)")
        if ok and name.strip():
            clean_name = name.strip()
            res = self.config_mgr.create_profile(clean_name, copy_from=cur)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(self, "Fehler", f"Ein Profil mit dem Namen '{clean_name}' existiert bereits.")

    def rename_current_profile(self):
        cur = self.config_mgr.get_active_profile_name()
        name, ok = QInputDialog.getText(self, "Profil umbenennen", f"Neuer Name für '{cur}':", text=cur)
        if ok and name.strip() and name.strip() != cur:
            clean_name = name.strip()
            res = self.config_mgr.rename_profile(cur, clean_name)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(self, "Fehler", "Ungültiger Name oder Profil existiert bereits.")

    def delete_current_profile(self):
        profs = self.config_mgr.get_profiles()
        if len(profs) <= 1:
            QMessageBox.warning(self, "Löschen nicht möglich", "Das letzte verbleibende Profil kann nicht gelöscht werden.")
            return

        cur = self.config_mgr.get_active_profile_name()
        ans = QMessageBox.question(
            self, "Profil löschen",
            f"Möchtest du das Profil '{cur}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.config_mgr.delete_profile(cur)
            new_active = self.config_mgr.get_active_profile_name()
            self.populate_profile_combo()
            self.switch_to_profile(new_active)

    def init_tray(self):
        """Erstellt das Tray-Icon in der Systemleiste."""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip("Orbiter — 3Dconnexion Controller")

        # Kontextmenü für Tray
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet(DARK_THEME)

        self.tray_status_action = QAction(self.app_icon, "Orbiter", self)
        self.tray_status_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_status_action)
        self.tray_menu.addSeparator()

        # Profil-Untermenü
        self.tray_profile_menu = QMenu("Profil wechseln", self.tray_menu)
        self.tray_profile_menu.setIcon(get_icon("layers", color="#38bdf8", size=16))
        self.tray_profile_menu.setStyleSheet(DARK_THEME)
        self.tray_menu.addMenu(self.tray_profile_menu)
        self.update_tray_profiles()

        self.tray_2d_action = QAction(get_icon("target", color="#38bdf8", size=16), "2D-Präzisionsmodus umschalten", self)
        self.tray_2d_action.triggered.connect(self.toggle_2d_mode)
        self.tray_menu.addAction(self.tray_2d_action)

        open_action = QAction(get_icon("settings", color="#94a3b8", size=16), "Einstellungen öffnen", self)
        open_action.triggered.connect(self.show_and_activate)
        self.tray_menu.addAction(open_action)

        restart_action = QAction(get_icon("refresh", color="#94a3b8", size=16), "Dienst neustarten", self)
        restart_action.triggered.connect(self.restart_daemon)
        self.tray_menu.addAction(restart_action)

        self.tray_menu.addSeparator()

        quit_action = QAction(get_icon("power", color="#f87171", size=16), "Beenden", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(quit_action)

        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def update_tray_profiles(self):
        self.tray_profile_menu.clear()
        profiles = sorted(self.config_mgr.get_profiles().keys())
        active = self.config_mgr.get_active_profile_name()

        for p in profiles:
            if p == active:
                act = QAction(get_icon("check", color="#38bdf8", size=14), p, self)
            else:
                act = QAction(get_icon("layers", color="#64748b", size=14), p, self)
            act.triggered.connect(lambda checked, name=p: self.switch_to_profile(name))
            self.tray_profile_menu.addAction(act)

        self.tray_profile_menu.addSeparator()
        next_act = QAction(get_icon("arrow-right", color="#38bdf8", size=14), "Nächstes Profil", self)
        next_act.triggered.connect(self.on_tray_next_profile)
        self.tray_profile_menu.addAction(next_act)

        prev_act = QAction(get_icon("arrow-left", color="#38bdf8", size=14), "Vorheriges Profil", self)
        prev_act.triggered.connect(self.on_tray_prev_profile)
        self.tray_profile_menu.addAction(prev_act)

    def on_tray_next_profile(self):
        self.config_mgr.next_profile()
        self.send_ipc_command("NEXT_PROFILE")
        self.populate_profile_combo()
        self.refresh_all_tabs()
        self.update_tray_profiles()

    def on_tray_prev_profile(self):
        self.config_mgr.prev_profile()
        self.send_ipc_command("PREV_PROFILE")
        self.populate_profile_combo()
        self.refresh_all_tabs()
        self.update_tray_profiles()

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

    def send_ipc_command(self, cmd):
        if not IPC_SOCKET.exists():
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(str(IPC_SOCKET))
            client.sendall((cmd + "\n").encode("utf-8"))
            resp = client.recv(1024).decode("utf-8").strip()
            client.close()
            return resp
        except Exception:
            return None

    def update_daemon_status(self):
        if not IPC_SOCKET.exists():
            self.status_badge.setText('<span style="color: #f87171; font-size: 13px;">●</span>  <span style="color: #94a3b8;">Dienst offline</span>')
            self.tray_status_action.setText("● Dienst offline")
            self.toggle_2d_btn.setEnabled(False)
            return

        self.toggle_2d_btn.setEnabled(True)
        try:
            resp = self.send_ipc_command("GET_STATUS")
            if not resp:
                raise Exception("Keine Antwort")

            status = json.loads(resp)
            if status.get("connected"):
                self.connected_device = status.get("device_name", "SpaceMouse")
                self.status_badge.setText(
                    f'<span style="color: #22c55e; font-size: 13px;">●</span>  <span style="color: #e2e8f0; font-weight: 600;">{self.connected_device}</span>'
                )
                self.tray_status_action.setText(f"● {self.connected_device}")
            else:
                self.status_badge.setText(
                    '<span style="color: #f59e0b; font-size: 13px;">○</span>  <span style="color: #94a3b8;">Kein Gerät verbunden</span>'
                )
                self.tray_status_action.setText("○ Kein Gerät verbunden")

            self.is_2d = status.get("mode_2d", True)
            if self.is_2d:
                self.toggle_2d_btn.setText("2D-Gleiten: AN")
                self.toggle_2d_btn.setIcon(get_icon("target", color="#ffffff", size=13))
                self.toggle_2d_btn.setStyleSheet("""
                    QPushButton#modeToggleBtn {
                        background-color: #2563eb;
                        color: #ffffff;
                        border: 1px solid #3b82f6;
                    }
                    QPushButton#modeToggleBtn:hover {
                        background-color: #3b82f6;
                        border-color: #60a5fa;
                    }
                """)
                self.tray_2d_action.setText("2D-Präzisionsmodus (Aktiv)")
                self.tray_2d_action.setIcon(get_icon("check", color="#38bdf8", size=16))
            else:
                self.toggle_2d_btn.setText("3D-Hybrid: AN")
                self.toggle_2d_btn.setIcon(get_icon("target", color="#94a3b8", size=13))
                self.toggle_2d_btn.setStyleSheet("""
                    QPushButton#modeToggleBtn {
                        background-color: #1a1e2d;
                        color: #94a3b8;
                        border: 1px solid #2a3147;
                    }
                    QPushButton#modeToggleBtn:hover {
                        background-color: #242b3e;
                        color: #f1f5f9;
                        border-color: #3b4664;
                    }
                """)
                self.tray_2d_action.setText("2D-Präzisionsmodus (Inaktiv)")
                self.tray_2d_action.setIcon(get_icon("target", color="#64748b", size=16))

            # Externer Profilwechsel über Hardware-Taste erkennen
            daemon_active_prof = status.get("active_profile")
            if daemon_active_prof and daemon_active_prof != self.config_mgr.get_active_profile_name():
                self.config_mgr.load()
                self.populate_profile_combo()
                self.refresh_all_tabs()
                self.update_tray_profiles()

            active_name = self.config_mgr.get_active_profile_name()
            self.tray.setToolTip(f"Orbiter — {self.connected_device or 'SpaceMouse'} (Profil: {active_name})")

        except Exception:
            self.status_badge.setText('<span style="color: #f87171; font-size: 13px;">●</span>  <span style="color: #94a3b8;">Dienst antwortet nicht</span>')
            self.tray_status_action.setText("● Dienst antwortet nicht")

    def toggle_2d_mode(self):
        self.send_ipc_command("TOGGLE_2D")
        self.update_daemon_status()

    def restart_daemon(self):
        try:
            subprocess.run(["systemctl", "--user", "restart", "orbiter"], check=False)
            self.update_daemon_status()
            QMessageBox.information(self, "Orbiter", "Dienst wurde erfolgreich neu gestartet.")
        except Exception as e:
            QMessageBox.warning(self, "Orbiter", f"Konnte Dienst nicht neu starten: {e}")
