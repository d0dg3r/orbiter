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
from orbiter.device import DEVICE_MODELS
from orbiter.i18n import tr, register_listener
from orbiter.gui.style import DARK_THEME, make_combo_opaque
from orbiter.gui.icons import get_icon
from orbiter.gui.widgets.button_editor import ButtonEditorWidget
from orbiter.gui.widgets.settings_tab import SettingsTabWidget
from orbiter.gui.widgets.sensitivity_tab import SensitivityTabWidget
from orbiter.gui.widgets.live_monitor import LiveMonitorWidget
from orbiter.gui.widgets.auto_rules import AutoRulesWidget

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ICON_PATH = PROJECT_ROOT / "data" / "icons" / "orbiter.svg"
# FHS fallback when installed as package
_FHS_ICON = Path("/usr/share/icons/hicolor/scalable/apps/orbiter.svg")

class MainWindow(QMainWindow):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.config_mgr = ConfigManager()
        self.setWindowTitle(tr("app.title"))
        self.resize(840, 640)
        self.setStyleSheet(DARK_THEME)

        icon_path = ICON_PATH if ICON_PATH.is_file() else _FHS_ICON
        self.app_icon = QIcon(str(icon_path))
        self.setWindowIcon(self.app_icon)

        self.is_2d = True
        self.connected_device = None
        self._updating_profiles = False
        self._retranslating = False
        self._status_fail_count = 0

        self.init_ui()
        self.init_tray()
        register_listener(self._on_language_changed)

        self.check_status_timer = QTimer(self)
        self.check_status_timer.timeout.connect(self.update_daemon_status)
        self.check_status_timer.start(2000)
        self.update_daemon_status()

        if not start_minimized:
            self.show()

    def _on_language_changed(self, _lang):
        if self._retranslating:
            return
        self.retranslate_ui()

    def retranslate_ui(self):
        self._retranslating = True
        try:
            self.setWindowTitle(tr("app.title"))
            self.subtitle_lbl.setText(tr("app.subtitle"))
            self.model_combo.setToolTip(tr("model.tooltip"))
            # Rebuild model combo labels; keep current data
            cur = self.model_combo.currentData()
            self.model_combo.blockSignals(True)
            self.model_combo.clear()
            for key, data in [
                ("model.auto", "auto"),
                ("model.compact", "compact"),
                ("model.explorer", "explorer"),
                ("model.pro", "pro"),
                ("model.enterprise", "enterprise"),
            ]:
                self.model_combo.addItem(tr(key), data)
            idx = self.model_combo.findData(cur or "auto")
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
            self.model_combo.blockSignals(False)

            self.prof_lbl.setText(tr("profile.label"))
            self.new_prof_btn.setText(tr("profile.new"))
            self.copy_prof_btn.setText(tr("profile.duplicate"))
            self.rename_prof_btn.setText(tr("profile.rename"))
            self.del_prof_btn.setText(tr("profile.delete"))

            self.tabs.setTabText(0, tr("tab.buttons"))
            self.tabs.setTabText(1, tr("tab.auto_rules"))
            self.tabs.setTabText(2, tr("tab.sensitivity"))
            self.tabs.setTabText(3, tr("tab.settings"))
            self.tabs.setTabText(4, tr("tab.monitor"))

            self.footer_status.setText(tr("app.footer_live"))
            self.footer_copyright.setText(tr("app.copyright"))
            self.restart_btn.setText(tr("btn.restart_daemon"))
            self.hide_btn.setText(tr("btn.minimize_tray"))

            self.tray.setToolTip(tr("app.tray_tooltip_default"))
            self.tray_profile_menu.setTitle(tr("profile.switch_menu"))
            self.tray_2d_action.setText(tr("tray.toggle_2d"))
            self.open_action.setText(tr("tray.open"))
            self.restart_action.setText(tr("tray.restart"))
            self.quit_action.setText(tr("tray.quit"))
            self.update_tray_profiles()

            if hasattr(self, "btn_tab"):
                self.btn_tab.retranslate_ui()
            if hasattr(self, "auto_rules_tab"):
                self.auto_rules_tab.retranslate_ui()
            if hasattr(self, "sensitivity_tab"):
                self.sensitivity_tab.retranslate_ui()
            if hasattr(self, "settings_tab"):
                self.settings_tab.retranslate_ui()
            if hasattr(self, "monitor_tab"):
                self.monitor_tab.retranslate_ui()

            self.update_daemon_status()
        finally:
            self._retranslating = False

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        # App logo, icon, and title on one row
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)
        brand_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(self.app_icon.pixmap(30, 30))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_box.addWidget(logo_lbl)

        title = QLabel("ORBITER")
        title.setObjectName("appTitle")
        title.setStyleSheet(
            "font-family: 'Inter Tight', 'Inter', -apple-system, sans-serif; "
            "font-size: 22px; font-weight: 800; color: #38bdf8; "
            "letter-spacing: 1.5px; margin: 0; padding: 0;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_box.addWidget(title)

        # Subtle version badge beside the title
        self.subtitle_lbl = QLabel(tr("app.subtitle"))
        self.subtitle_lbl.setStyleSheet(
            "font-family: 'Inter Tight', 'Inter', sans-serif; "
            "color: #64748b; font-size: 11px; font-weight: 500; "
            "margin-left: 4px; padding-top: 2px;"
        )
        self.subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        brand_box.addWidget(self.subtitle_lbl)

        header.addLayout(brand_box)

        header.addStretch()

        # Header Controls Cluster (Unified Hardware & Mode Capsule)
        header_cluster = QFrame()
        header_cluster.setObjectName("headerCluster")
        cluster_layout = QHBoxLayout(header_cluster)
        cluster_layout.setContentsMargins(12, 4, 4, 4)
        cluster_layout.setSpacing(10)

        # 1. Hardware Status Indicator
        self.status_badge = QLabel(tr("status.checking"))
        self.status_badge.setObjectName("deviceStatusLabel")
        cluster_layout.addWidget(self.status_badge)

        # Model selection / override dropdown
        self.model_combo = QComboBox()
        self.model_combo.setToolTip(tr("model.tooltip"))
        make_combo_opaque(self.model_combo)
        self.model_combo.addItem(tr("model.auto"), "auto")
        self.model_combo.addItem(tr("model.compact"), "compact")
        self.model_combo.addItem(tr("model.explorer"), "explorer")
        self.model_combo.addItem(tr("model.pro"), "pro")
        self.model_combo.addItem(tr("model.enterprise"), "enterprise")
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #171b28;
                border: 1px solid #283046;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
                color: #93c5fd;
                font-weight: 600;
            }
            QComboBox:hover {
                border-color: #3b82f6;
                color: #ffffff;
            }
        """)
        # Set initial value
        cur_ov = self.config_mgr.get_model_override()
        for idx in range(self.model_combo.count()):
            if self.model_combo.itemData(idx) == cur_ov:
                self.model_combo.setCurrentIndex(idx)
                break
        self.model_combo.currentIndexChanged.connect(self.on_model_override_changed)
        cluster_layout.addWidget(self.model_combo)

        # 2. Sleek Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setObjectName("headerDivider")
        divider.setFixedHeight(18)
        cluster_layout.addWidget(divider)

        # 3. 2D Mode Interactive Toggle
        self.toggle_2d_btn = QPushButton(tr("mode.2d_on"))
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

        self.prof_lbl = QLabel(tr("profile.label"))
        self.prof_lbl.setStyleSheet("font-weight: 700; color: #93c5fd; font-size: 13px;")
        prof_bar.addWidget(self.prof_lbl)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(190)
        make_combo_opaque(self.profile_combo)
        self.populate_profile_combo()
        self.profile_combo.currentTextChanged.connect(self.on_profile_combo_changed)
        prof_bar.addWidget(self.profile_combo)

        self.new_prof_btn = QPushButton(tr("profile.new"))
        self.new_prof_btn.setObjectName("secondaryBtn")
        self.new_prof_btn.setIcon(get_icon("plus", color="#38bdf8", size=14))
        self.new_prof_btn.clicked.connect(self.create_new_profile)
        prof_bar.addWidget(self.new_prof_btn)

        self.copy_prof_btn = QPushButton(tr("profile.duplicate"))
        self.copy_prof_btn.setObjectName("secondaryBtn")
        self.copy_prof_btn.setIcon(get_icon("copy", color="#94a3b8", size=14))
        self.copy_prof_btn.clicked.connect(self.copy_current_profile)
        prof_bar.addWidget(self.copy_prof_btn)

        self.rename_prof_btn = QPushButton(tr("profile.rename"))
        self.rename_prof_btn.setObjectName("secondaryBtn")
        self.rename_prof_btn.setIcon(get_icon("edit", color="#94a3b8", size=14))
        self.rename_prof_btn.clicked.connect(self.rename_current_profile)
        prof_bar.addWidget(self.rename_prof_btn)

        self.del_prof_btn = QPushButton(tr("profile.delete"))
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
        self.auto_rules_tab = AutoRulesWidget(self.config_mgr, self, self)
        self.sensitivity_tab = SensitivityTabWidget(self.config_mgr, self)
        self.settings_tab = SettingsTabWidget(self.config_mgr, self)
        self.monitor_tab = LiveMonitorWidget(self)

        self.tabs.addTab(self.btn_tab, get_icon("keyboard", color="#38bdf8", active_color="#ffffff", size=18), tr("tab.buttons"))
        self.tabs.addTab(self.auto_rules_tab, get_icon("layout", color="#38bdf8", active_color="#ffffff", size=18), tr("tab.auto_rules"))
        self.tabs.addTab(self.sensitivity_tab, get_icon("sliders", color="#38bdf8", active_color="#ffffff", size=18), tr("tab.sensitivity"))
        self.tabs.addTab(self.settings_tab, get_icon("settings", color="#38bdf8", active_color="#ffffff", size=18), tr("tab.settings"))
        self.tabs.addTab(self.monitor_tab, get_icon("activity", color="#38bdf8", active_color="#ffffff", size=18), tr("tab.monitor"))

        main_layout.addWidget(self.tabs)

        # Footer
        footer = QHBoxLayout()
        self.footer_status = QLabel(tr("app.footer_live"))
        self.footer_status.setStyleSheet("color: #64748b; font-size: 11px;")
        footer.addWidget(self.footer_status)

        self.footer_copyright = QLabel(tr("app.copyright"))
        self.footer_copyright.setTextFormat(Qt.TextFormat.RichText)
        self.footer_copyright.setOpenExternalLinks(True)
        self.footer_copyright.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.footer_copyright.setStyleSheet(
            "color: #64748b; font-size: 11px; margin-left: 12px;"
            " a { color: #38bdf8; text-decoration: none; }"
        )
        footer.addWidget(self.footer_copyright)

        footer.addStretch()

        self.restart_btn = QPushButton(tr("btn.restart_daemon"))
        self.restart_btn.setObjectName("secondaryBtn")
        self.restart_btn.setIcon(get_icon("refresh", color="#94a3b8", size=14))
        self.restart_btn.clicked.connect(self.restart_daemon)
        footer.addWidget(self.restart_btn)

        self.hide_btn = QPushButton(tr("btn.minimize_tray"))
        self.hide_btn.setIcon(get_icon("minimize", color="#ffffff", size=14))
        self.hide_btn.clicked.connect(self.hide)
        footer.addWidget(self.hide_btn)

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

    def on_model_override_changed(self, idx):
        if idx < 0:
            return
        m_id = self.model_combo.itemData(idx)
        self.config_mgr.set_model_override(m_id)
        self.send_ipc_command(f"SET_MODEL_OVERRIDE {m_id}")
        self.btn_tab.populate_table()

    def refresh_all_tabs(self):
        self.btn_tab.populate_table()
        if hasattr(self, "sensitivity_tab"):
            self.sensitivity_tab.load_settings()
        if hasattr(self, "auto_rules_tab"):
            self.auto_rules_tab.populate_rules_table()
            self.auto_rules_tab.populate_profile_combo()

    def create_new_profile(self):
        name, ok = QInputDialog.getText(
            self, tr("profile.dialog_new_title"), tr("profile.dialog_new_label")
        )
        if ok and name.strip():
            clean_name = name.strip()
            res = self.config_mgr.create_profile(clean_name)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(
                    self, tr("profile.error_title"),
                    tr("profile.error_exists", name=clean_name),
                )

    def copy_current_profile(self):
        cur = self.config_mgr.get_active_profile_name()
        name, ok = QInputDialog.getText(
            self,
            tr("profile.dialog_copy_title"),
            tr("profile.dialog_copy_label", cur=cur),
            text=tr("profile.dialog_copy_default", cur=cur),
        )
        if ok and name.strip():
            clean_name = name.strip()
            res = self.config_mgr.create_profile(clean_name, copy_from=cur)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(
                    self, tr("profile.error_title"),
                    tr("profile.error_exists", name=clean_name),
                )

    def rename_current_profile(self):
        cur = self.config_mgr.get_active_profile_name()
        name, ok = QInputDialog.getText(
            self,
            tr("profile.dialog_rename_title"),
            tr("profile.dialog_rename_label", cur=cur),
            text=cur,
        )
        if ok and name.strip() and name.strip() != cur:
            clean_name = name.strip()
            res = self.config_mgr.rename_profile(cur, clean_name)
            if res:
                self.populate_profile_combo()
                self.switch_to_profile(clean_name)
            else:
                QMessageBox.warning(
                    self, tr("profile.error_title"), tr("profile.error_invalid")
                )

    def delete_current_profile(self):
        profs = self.config_mgr.get_profiles()
        if len(profs) <= 1:
            QMessageBox.warning(
                self, tr("profile.error_last_title"), tr("profile.error_last_body")
            )
            return

        cur = self.config_mgr.get_active_profile_name()
        ans = QMessageBox.question(
            self,
            tr("profile.dialog_delete_title"),
            tr("profile.dialog_delete_body", cur=cur),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.config_mgr.delete_profile(cur)
            new_active = self.config_mgr.get_active_profile_name()
            self.populate_profile_combo()
            self.switch_to_profile(new_active)

    def init_tray(self):
        """Create the system tray icon."""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip(tr("app.tray_tooltip_default"))

        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet(DARK_THEME)

        self.tray_status_action = QAction(self.app_icon, "Orbiter", self)
        self.tray_status_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_status_action)
        self.tray_menu.addSeparator()

        self.tray_profile_menu = QMenu(tr("profile.switch_menu"), self.tray_menu)
        self.tray_profile_menu.setIcon(get_icon("layers", color="#38bdf8", size=16))
        self.tray_profile_menu.setStyleSheet(DARK_THEME)
        self.tray_menu.addMenu(self.tray_profile_menu)
        self.update_tray_profiles()

        self.tray_2d_action = QAction(get_icon("target", color="#38bdf8", size=16), tr("tray.toggle_2d"), self)
        self.tray_2d_action.triggered.connect(self.toggle_2d_mode)
        self.tray_menu.addAction(self.tray_2d_action)

        self.open_action = QAction(get_icon("settings", color="#94a3b8", size=16), tr("tray.open"), self)
        self.open_action.triggered.connect(self.show_and_activate)
        self.tray_menu.addAction(self.open_action)

        self.restart_action = QAction(get_icon("refresh", color="#94a3b8", size=16), tr("tray.restart"), self)
        self.restart_action.triggered.connect(self.restart_daemon)
        self.tray_menu.addAction(self.restart_action)

        self.tray_menu.addSeparator()

        self.quit_action = QAction(get_icon("power", color="#f87171", size=16), tr("tray.quit"), self)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(self.quit_action)

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
        next_act = QAction(get_icon("arrow-right", color="#38bdf8", size=14), tr("tray.next_profile"), self)
        next_act.triggered.connect(self.on_tray_next_profile)
        self.tray_profile_menu.addAction(next_act)

        prev_act = QAction(get_icon("arrow-left", color="#38bdf8", size=14), tr("tray.prev_profile"), self)
        prev_act.triggered.connect(self.on_tray_prev_profile)
        self.tray_profile_menu.addAction(prev_act)

    def on_tray_next_profile(self):
        # Daemon is SoT for profile stepping — do not also call next_profile() locally
        self.send_ipc_command("NEXT_PROFILE")
        self.config_mgr.load()
        self.populate_profile_combo()
        self.refresh_all_tabs()
        self.update_tray_profiles()

    def on_tray_prev_profile(self):
        self.send_ipc_command("PREV_PROFILE")
        self.config_mgr.load()
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
        """Keep the tray icon alive when the window is closed."""
        event.ignore()
        self.hide()

    def send_ipc_command(self, cmd, timeout=2.0):
        """Send a command and return the first matching response line.

        Skips stray event JSON lines so status polls stay reliable while the
        device is moving (broadcasts used to share the same client pool).
        """
        if not IPC_SOCKET.exists():
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(timeout)
            client.connect(str(IPC_SOCKET))
            client.sendall((cmd + "\n").encode("utf-8"))
            want_status = cmd.strip() == "GET_STATUS"
            buf = ""
            while True:
                chunk = client.recv(8192)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    if want_status:
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(obj, dict) and "connected" in obj:
                            client.close()
                            return line
                        continue
                    client.close()
                    return line
            client.close()
            return None
        except Exception:
            return None

    def update_daemon_status(self):
        from orbiter.conflicts import spacenavd_running

        if not IPC_SOCKET.exists():
            self._status_fail_count = 0
            if spacenavd_running():
                self.status_badge.setText(
                    f'<span style="color: #f87171; font-size: 13px;">●</span>  '
                    f'<span style="color: #fbbf24;">{tr("status.spacenavd_disable")}</span>'
                )
                self.tray_status_action.setText(tr("status.tray_spacenavd"))
                if hasattr(self, "footer_status"):
                    self.footer_status.setText(tr("app.footer_spacenavd_offline"))
            else:
                self.status_badge.setText(
                    f'<span style="color: #f87171; font-size: 13px;">●</span>  '
                    f'<span style="color: #94a3b8;">{tr("status.offline")}</span>'
                )
                self.tray_status_action.setText(tr("status.tray_offline"))
            self.toggle_2d_btn.setEnabled(False)
            return

        self.toggle_2d_btn.setEnabled(True)
        try:
            resp = self.send_ipc_command("GET_STATUS")
            if not resp:
                raise Exception("Keine Antwort")

            status = json.loads(resp)
            self._status_fail_count = 0
            if status.get("spacenavd_conflict"):
                self.status_badge.setText(
                    f'<span style="color: #f87171; font-size: 13px;">●</span>  '
                    f'<span style="color: #fbbf24;">{tr("status.spacenavd")}</span>'
                )
                self.tray_status_action.setText(tr("status.tray_spacenavd"))
                if hasattr(self, "footer_status"):
                    self.footer_status.setText(tr("app.footer_spacenavd"))
            elif status.get("connected"):
                self.connected_device = status.get("device_name", "SpaceMouse")
                self.status_badge.setText(
                    f'<span style="color: #22c55e; font-size: 13px;">●</span>  <span style="color: #e2e8f0; font-weight: 600;">{self.connected_device}</span>'
                )
                self.tray_status_action.setText(f"● {self.connected_device}")
                if hasattr(self, "footer_status"):
                    self.footer_status.setText(tr("app.footer_live"))
            else:
                self.status_badge.setText(
                    f'<span style="color: #f59e0b; font-size: 13px;">○</span>  <span style="color: #94a3b8;">{tr("status.no_device")}</span>'
                )
                self.tray_status_action.setText(tr("status.tray_no_device"))
                if hasattr(self, "footer_status"):
                    self.footer_status.setText(tr("app.footer_live"))

            # Update live window watcher in AutoRulesWidget
            if hasattr(self, "auto_rules_tab") and "active_window" in status:
                w_info = status["active_window"]
                self.auto_rules_tab.update_detected_window(
                    w_info.get("class", ""),
                    w_info.get("title", "")
                )

            self.is_2d = status.get("mode_2d", True)
            if self.is_2d:
                self.toggle_2d_btn.setText(tr("mode.2d_on"))
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
                self.tray_2d_action.setText(tr("mode.tray_2d_active"))
                self.tray_2d_action.setIcon(get_icon("check", color="#38bdf8", size=16))
            else:
                self.toggle_2d_btn.setText(tr("mode.3d_on"))
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
                self.tray_2d_action.setText(tr("mode.tray_2d_inactive"))
                self.tray_2d_action.setIcon(get_icon("target", color="#64748b", size=16))

            # Detect profile switch triggered by a hardware button
            daemon_active_prof = status.get("active_profile")
            if daemon_active_prof and daemon_active_prof != self.config_mgr.get_active_profile_name():
                self.config_mgr.load()
                self.populate_profile_combo()
                self.refresh_all_tabs()
                self.update_tray_profiles()

            active_name = self.config_mgr.get_active_profile_name()
            self.tray.setToolTip(tr(
                "app.tray_tooltip",
                device=self.connected_device or "SpaceMouse",
                profile=active_name,
            ))

        except Exception:
            # Debounce: one failed poll must not flicker the badge red while
            # the device is still driving the pointer fine.
            self._status_fail_count += 1
            if self._status_fail_count < 3:
                return
            self.status_badge.setText(
                f'<span style="color: #f87171; font-size: 13px;">●</span>  '
                f'<span style="color: #94a3b8;">{tr("status.no_response")}</span>'
            )
            self.tray_status_action.setText(tr("status.tray_no_response"))

    def toggle_2d_mode(self):
        self.send_ipc_command("TOGGLE_2D")
        self.update_daemon_status()

    def restart_daemon(self):
        try:
            subprocess.run(["systemctl", "--user", "restart", "orbiter"], check=False)
            self.update_daemon_status()
            QMessageBox.information(self, "Orbiter", tr("btn.restart_ok"))
        except Exception as e:
            QMessageBox.warning(self, "Orbiter", tr("btn.restart_fail", error=e))
