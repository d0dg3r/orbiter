"""
Settings & Sensitivity Sliders Widget for Orbiter
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSlider, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt

from orbiter.gui.style import make_combo_opaque
from orbiter.i18n import tr, set_language, resolve_lang


class SettingsTabWidget(QWidget):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self._loading = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Language
        lang_group = QGroupBox(tr("settings.language"))
        lang_layout = QVBoxLayout(lang_group)
        self.lang_combo = QComboBox()
        make_combo_opaque(self.lang_combo)
        self.lang_combo.addItem(tr("settings.language_auto"), "auto")
        self.lang_combo.addItem(tr("settings.language_de"), "de")
        self.lang_combo.addItem(tr("settings.language_en"), "en")
        cur = self.config_mgr.get("ui_language", "auto")
        idx = self.lang_combo.findData(cur)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        hint = QLabel(tr("settings.language_hint"))
        hint.setStyleSheet("color: #64748b; font-size: 11px;")
        lang_layout.addWidget(hint)
        layout.addWidget(lang_group)

        # 1. Zeiger-Einstellungen
        pointer_group = QGroupBox(tr("settings.pointer_group"))
        p_layout = QVBoxLayout(pointer_group)

        p_layout.addWidget(QLabel(tr("settings.pointer_speed")))
        speed_box = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 200)
        self.speed_label = QLabel()
        speed_box.addWidget(self.speed_slider)
        speed_box.addWidget(self.speed_label)
        p_layout.addLayout(speed_box)

        p_layout.addWidget(QLabel(tr("settings.deadzone")))
        dz_box = QHBoxLayout()
        self.dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.dz_slider.setRange(5, 50)
        self.dz_label = QLabel()
        dz_box.addWidget(self.dz_slider)
        dz_box.addWidget(self.dz_label)
        p_layout.addLayout(dz_box)

        self.mode_2d_check = QCheckBox(tr("settings.mode_2d_default"))
        p_layout.addWidget(self.mode_2d_check)

        layout.addWidget(pointer_group)

        scroll_group = QGroupBox(tr("settings.scroll_group"))
        s_layout = QVBoxLayout(scroll_group)

        s_layout.addWidget(QLabel(tr("settings.scroll_speed")))
        sc_speed_box = QHBoxLayout()
        self.sc_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_speed_slider.setRange(10, 100)
        self.sc_speed_label = QLabel()
        sc_speed_box.addWidget(self.sc_speed_slider)
        sc_speed_box.addWidget(self.sc_speed_label)
        s_layout.addLayout(sc_speed_box)

        s_layout.addWidget(QLabel(tr("settings.scroll_threshold")))
        sc_dz_box = QHBoxLayout()
        self.sc_dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_dz_slider.setRange(40, 150)
        self.sc_dz_label = QLabel()
        sc_dz_box.addWidget(self.sc_dz_slider)
        sc_dz_box.addWidget(self.sc_dz_label)
        s_layout.addLayout(sc_dz_box)

        layout.addWidget(scroll_group)

        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.dz_slider.valueChanged.connect(self.on_dz_changed)
        self.sc_speed_slider.valueChanged.connect(self.on_sc_speed_changed)
        self.sc_dz_slider.valueChanged.connect(self.on_sc_dz_changed)
        self.mode_2d_check.toggled.connect(self.on_mode_2d_toggled)

        layout.addStretch()
        self.load_settings()

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
