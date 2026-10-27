"""
Pointer and scroll sensitivity sliders for Orbiter.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt

from orbiter.gui.style import apply_group_layout, apply_tab_page_layout
from orbiter.i18n import tr


class SensitivityTabWidget(QWidget):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self._loading = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        apply_tab_page_layout(layout)

        self.pointer_group = QGroupBox()
        p_layout = QVBoxLayout(self.pointer_group)
        apply_group_layout(p_layout)

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

        self.tilt_caption = QLabel()
        p_layout.addWidget(self.tilt_caption)
        tilt_box = QHBoxLayout()
        self.tilt_slider = QSlider(Qt.Orientation.Horizontal)
        self.tilt_slider.setRange(0, 100)
        self.tilt_label = QLabel()
        tilt_box.addWidget(self.tilt_slider)
        tilt_box.addWidget(self.tilt_label)
        p_layout.addLayout(tilt_box)

        layout.addWidget(self.pointer_group)

        self.scroll_group = QGroupBox()
        s_layout = QVBoxLayout(self.scroll_group)
        apply_group_layout(s_layout)

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

        self.lift_scroll_check = QCheckBox()
        s_layout.addWidget(self.lift_scroll_check)

        self.lift_dz_caption = QLabel()
        s_layout.addWidget(self.lift_dz_caption)
        lift_dz_box = QHBoxLayout()
        self.lift_dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.lift_dz_slider.setRange(40, 150)
        self.lift_dz_label = QLabel()
        lift_dz_box.addWidget(self.lift_dz_slider)
        lift_dz_box.addWidget(self.lift_dz_label)
        s_layout.addLayout(lift_dz_box)

        layout.addWidget(self.scroll_group)

        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.dz_slider.valueChanged.connect(self.on_dz_changed)
        self.tilt_slider.valueChanged.connect(self.on_tilt_changed)
        self.sc_speed_slider.valueChanged.connect(self.on_sc_speed_changed)
        self.sc_dz_slider.valueChanged.connect(self.on_sc_dz_changed)
        self.lift_dz_slider.valueChanged.connect(self.on_lift_dz_changed)
        self.mode_2d_check.toggled.connect(self.on_mode_2d_toggled)
        self.lift_scroll_check.toggled.connect(self.on_lift_scroll_toggled)

        layout.addStretch()
        self.load_settings()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.pointer_group.setTitle(tr("settings.pointer_group"))
        self.speed_caption.setText(tr("settings.pointer_speed"))
        self.dz_caption.setText(tr("settings.deadzone"))
        self.mode_2d_check.setText(tr("settings.mode_2d_default"))
        self.tilt_caption.setText(tr("settings.tilt_blend"))
        self.scroll_group.setTitle(tr("settings.scroll_group"))
        self.sc_speed_caption.setText(tr("settings.scroll_speed"))
        self.sc_dz_caption.setText(tr("settings.scroll_threshold"))
        self.lift_scroll_check.setText(tr("settings.lift_scroll"))
        self.lift_dz_caption.setText(tr("settings.lift_threshold"))

    def load_settings(self):
        self._loading = True
        try:
            speed = self.config_mgr.get("base_speed", 0.05)
            self.speed_slider.setValue(int(speed * 1000))
            self.speed_label.setText(f"{speed:.3f}")

            dz = self.config_mgr.get("deadzone", 18)
            self.dz_slider.setValue(int(dz))
            self.dz_label.setText(f"{dz}")

            tilt = float(self.config_mgr.get("tilt_blend", 0.4))
            self.tilt_slider.setValue(int(round(tilt * 100)))
            self.tilt_label.setText(f"{int(round(tilt * 100))} %")

            sc_speed = self.config_mgr.get("scroll_speed", 0.0035)
            self.sc_speed_slider.setValue(int(sc_speed * 10000))
            self.sc_speed_label.setText(f"{sc_speed:.4f}")

            sc_dz = self.config_mgr.get("scroll_deadzone_twist", 90)
            self.sc_dz_slider.setValue(int(sc_dz))
            self.sc_dz_label.setText(f"{sc_dz}")

            self.mode_2d_check.setChecked(self.config_mgr.get("mode_2d", True))
            self.lift_scroll_check.setChecked(
                bool(self.config_mgr.get("lift_scroll_enabled", True))
            )

            lift_dz = self.config_mgr.get("scroll_deadzone_lift", 90)
            self.lift_dz_slider.setValue(int(lift_dz))
            self.lift_dz_label.setText(f"{lift_dz}")
            self._update_lift_controls_enabled()
        finally:
            self._loading = False

    def _update_lift_controls_enabled(self):
        enabled = self.lift_scroll_check.isChecked()
        self.lift_dz_caption.setEnabled(enabled)
        self.lift_dz_slider.setEnabled(enabled)
        self.lift_dz_label.setEnabled(enabled)

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

    def on_tilt_changed(self, val):
        if self._loading:
            return
        blend = val / 100.0
        self.tilt_label.setText(f"{val} %")
        self.config_mgr.set("tilt_blend", blend)
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

    def on_lift_dz_changed(self, val):
        if self._loading:
            return
        self.lift_dz_label.setText(f"{val}")
        self.config_mgr.set("scroll_deadzone_lift", val)
        self.config_mgr.save()

    def on_mode_2d_toggled(self, checked):
        if self._loading:
            return
        self.config_mgr.set("mode_2d", checked)
        self.config_mgr.save()

    def on_lift_scroll_toggled(self, checked):
        if self._loading:
            return
        self.config_mgr.set("lift_scroll_enabled", checked)
        self.config_mgr.save()
        self._update_lift_controls_enabled()
