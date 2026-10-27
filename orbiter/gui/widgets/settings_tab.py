"""
Settings & Sensitivity Sliders Widget for Orbiter
"""
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSlider, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from orbiter.gui.style import make_combo_opaque
from orbiter.gui.icons import get_icon
from orbiter.i18n import (
    tr, set_language, resolve_lang, available_languages, language_native_name
)


class SettingsTabWidget(QWidget):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.main_win = parent
        self._loading = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.lang_group = QGroupBox()
        lang_layout = QVBoxLayout(self.lang_group)
        self.lang_combo = QComboBox()
        make_combo_opaque(self.lang_combo)
        self._rebuild_lang_combo()
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        self.lang_hint = QLabel()
        self.lang_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        lang_layout.addWidget(self.lang_hint)
        layout.addWidget(self.lang_group)

        self.pointer_group = QGroupBox()
        p_layout = QVBoxLayout(self.pointer_group)

        self.speed_caption = QLabel()
        p_layout.addWidget(self.speed_caption)
        speed_box = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 200)
        self.speed_label = QLabel()
        speed_box.addWidget(self.speed_slider)
        speed_box.addWidget(self.speed_label)
        p_layout.addLayout(speed_box)

        self.dz_caption = QLabel()
        p_layout.addWidget(self.dz_caption)
        dz_box = QHBoxLayout()
        self.dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.dz_slider.setRange(5, 50)
        self.dz_label = QLabel()
        dz_box.addWidget(self.dz_slider)
        dz_box.addWidget(self.dz_label)
        p_layout.addLayout(dz_box)

        self.mode_2d_check = QCheckBox()
        p_layout.addWidget(self.mode_2d_check)
        layout.addWidget(self.pointer_group)

        self.scroll_group = QGroupBox()
        s_layout = QVBoxLayout(self.scroll_group)

        self.sc_speed_caption = QLabel()
        s_layout.addWidget(self.sc_speed_caption)
        sc_speed_box = QHBoxLayout()
        self.sc_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_speed_slider.setRange(10, 100)
        self.sc_speed_label = QLabel()
        sc_speed_box.addWidget(self.sc_speed_slider)
        sc_speed_box.addWidget(self.sc_speed_label)
        s_layout.addLayout(sc_speed_box)

        self.sc_dz_caption = QLabel()
        s_layout.addWidget(self.sc_dz_caption)
        sc_dz_box = QHBoxLayout()
        self.sc_dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_dz_slider.setRange(40, 150)
        self.sc_dz_label = QLabel()
        sc_dz_box.addWidget(self.sc_dz_slider)
        sc_dz_box.addWidget(self.sc_dz_label)
        s_layout.addLayout(sc_dz_box)

        layout.addWidget(self.scroll_group)

        self.backup_group = QGroupBox()
        b_layout = QHBoxLayout(self.backup_group)
        self.export_btn = QPushButton()
        self.export_btn.setObjectName("secondaryBtn")
        self.export_btn.setIcon(get_icon("copy", color="#38bdf8", size=14))
        self.export_btn.clicked.connect(self.on_export_config)
        self.import_btn = QPushButton()
        self.import_btn.setObjectName("secondaryBtn")
        self.import_btn.setIcon(get_icon("edit", color="#94a3b8", size=14))
        self.import_btn.clicked.connect(self.on_import_config)
        b_layout.addWidget(self.export_btn)
        b_layout.addWidget(self.import_btn)
        b_layout.addStretch()
        layout.addWidget(self.backup_group)

        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.dz_slider.valueChanged.connect(self.on_dz_changed)
        self.sc_speed_slider.valueChanged.connect(self.on_sc_speed_changed)
        self.sc_dz_slider.valueChanged.connect(self.on_sc_dz_changed)
        self.mode_2d_check.toggled.connect(self.on_mode_2d_toggled)

        layout.addStretch()
        self.load_settings()
        self.retranslate_ui()

    def _rebuild_lang_combo(self):
        self._loading = True
        cur = self.config_mgr.get("ui_language", "auto")
        self.lang_combo.blockSignals(True)
        self.lang_combo.clear()
        self.lang_combo.addItem(tr("settings.language_auto"), "auto")
        for code in available_languages():
            self.lang_combo.addItem(language_native_name(code), code)
        idx = self.lang_combo.findData(cur)
        if idx < 0:
            idx = 0
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)
        self._loading = False

    def retranslate_ui(self):
        self.lang_group.setTitle(tr("settings.language"))
        self.lang_hint.setText(tr("settings.language_hint"))
        self._rebuild_lang_combo()
        self.pointer_group.setTitle(tr("settings.pointer_group"))
        self.speed_caption.setText(tr("settings.pointer_speed"))
        self.dz_caption.setText(tr("settings.deadzone"))
        self.mode_2d_check.setText(tr("settings.mode_2d_default"))
        self.scroll_group.setTitle(tr("settings.scroll_group"))
        self.sc_speed_caption.setText(tr("settings.scroll_speed"))
        self.sc_dz_caption.setText(tr("settings.scroll_threshold"))
        self.backup_group.setTitle(tr("settings.backup_group"))
        self.export_btn.setText(tr("settings.export"))
        self.import_btn.setText(tr("settings.import"))

    def on_export_config(self):
        stamp = datetime.now().strftime("%Y%m%d")
        default = str(Path.home() / f"orbiter-config-{stamp}.json")
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("settings.export_title"),
            default,
            tr("settings.filter_json"),
        )
        if not path:
            return
        try:
            out = self.config_mgr.export_config(path)
            QMessageBox.information(self, "Orbiter", tr("settings.export_ok", path=out))
        except Exception as e:
            QMessageBox.warning(self, "Orbiter", tr("settings.export_fail", error=e))

    def on_import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings.import_title"),
            str(Path.home()),
            tr("settings.filter_json"),
        )
        if not path:
            return
        try:
            self.config_mgr.import_config(path)
        except Exception as e:
            QMessageBox.warning(self, "Orbiter", tr("settings.import_fail", error=e))
            return
        if self.main_win and hasattr(self.main_win, "send_ipc_command"):
            self.main_win.send_ipc_command("RELOAD")
            self.main_win.populate_profile_combo()
            self.main_win.refresh_all_tabs()
            self.main_win.update_tray_profiles()
        QMessageBox.information(self, "Orbiter", tr("settings.import_ok", path=path))

    def on_language_changed(self, idx):
        if self._loading or idx < 0:
            return
        code = self.lang_combo.itemData(idx)
        self.config_mgr.set("ui_language", code)
        self.config_mgr.save()
        set_language(resolve_lang(code))

    def load_settings(self):
        self._loading = True
        try:
            speed = self.config_mgr.get("base_speed", 0.05)
            self.speed_slider.setValue(int(speed * 1000))
            self.speed_label.setText(f"{speed:.3f}")

            dz = self.config_mgr.get("deadzone", 18)
            self.dz_slider.setValue(int(dz))
            self.dz_label.setText(f"{dz}")

            sc_speed = self.config_mgr.get("scroll_speed", 0.0035)
            self.sc_speed_slider.setValue(int(sc_speed * 10000))
            self.sc_speed_label.setText(f"{sc_speed:.4f}")

            sc_dz = self.config_mgr.get("scroll_deadzone_twist", 90)
            self.sc_dz_slider.setValue(int(sc_dz))
            self.sc_dz_label.setText(f"{sc_dz}")

            self.mode_2d_check.setChecked(self.config_mgr.get("mode_2d", True))
        finally:
            self._loading = False

    def on_speed_changed(self, val):
        if self._loading:
            return
        speed = val / 1000.0
        self.speed_label.setText(f"{speed:.3f}")
        self.config_mgr.set("base_speed", speed)
        self.config_mgr.save()

    def on_dz_changed(self, val):
        if self._loading:
            return
        self.dz_label.setText(f"{val}")
        self.config_mgr.set("deadzone", val)
        self.config_mgr.save()

    def on_sc_speed_changed(self, val):
        if self._loading:
            return
        sc_speed = val / 10000.0
        self.sc_speed_label.setText(f"{sc_speed:.4f}")
        self.config_mgr.set("scroll_speed", sc_speed)
        self.config_mgr.save()

    def on_sc_dz_changed(self, val):
        if self._loading:
            return
        self.sc_dz_label.setText(f"{val}")
        self.config_mgr.set("scroll_deadzone_twist", val)
        self.config_mgr.save()

    def on_mode_2d_toggled(self, checked):
        if self._loading:
            return
        self.config_mgr.set("mode_2d", checked)
        self.config_mgr.save()
