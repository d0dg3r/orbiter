"""
Settings & Sensitivity Sliders Widget for Orbiter
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt

class SettingsTabWidget(QWidget):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self._loading = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Zeiger-Einstellungen
        pointer_group = QGroupBox("Mauszeiger-Empfindlichkeit")
        p_layout = QVBoxLayout(pointer_group)

        # Base Speed
        p_layout.addWidget(QLabel("Zeiger-Geschwindigkeit:"))
        speed_box = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 200) # 0.010 bis 0.200
        self.speed_label = QLabel()
        speed_box.addWidget(self.speed_slider)
        speed_box.addWidget(self.speed_label)
        p_layout.addLayout(speed_box)

        # Deadzone
        p_layout.addWidget(QLabel("Zitterfilter (Deadzone für Zeiger):"))
        dz_box = QHBoxLayout()
        self.dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.dz_slider.setRange(5, 50)
        self.dz_label = QLabel()
        dz_box.addWidget(self.dz_slider)
        dz_box.addWidget(self.dz_label)
        p_layout.addLayout(dz_box)

        # 2D Mode Checkbox
        self.mode_2d_check = QCheckBox("2D-Präzisionsmodus standardmäßig aktiv (ignoriert Kappen-Neigung)")
        p_layout.addWidget(self.mode_2d_check)

        layout.addWidget(pointer_group)

        # 2. Scroll-Einstellungen
        scroll_group = QGroupBox("Scrollrad-Verhalten (Kappe drehen / Twist)")
        s_layout = QVBoxLayout(scroll_group)

        # Scroll Speed
        s_layout.addWidget(QLabel("Scroll-Geschwindigkeit:"))
        sc_speed_box = QHBoxLayout()
        self.sc_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_speed_slider.setRange(10, 100) # 0.0010 bis 0.0100
        self.sc_speed_label = QLabel()
        sc_speed_box.addWidget(self.sc_speed_slider)
        sc_speed_box.addWidget(self.sc_speed_label)
        s_layout.addLayout(sc_speed_box)

        # Scroll Deadzone
        s_layout.addWidget(QLabel("Scroll-Schwelle (Schutz gegen versehentliches Drehen beim Bewegen):"))
        sc_dz_box = QHBoxLayout()
        self.sc_dz_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_dz_slider.setRange(40, 150)
        self.sc_dz_label = QLabel()
        sc_dz_box.addWidget(self.sc_dz_slider)
        sc_dz_box.addWidget(self.sc_dz_label)
        s_layout.addLayout(sc_dz_box)

        layout.addWidget(scroll_group)

        # Sliders Connect
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.dz_slider.valueChanged.connect(self.on_dz_changed)
        self.sc_speed_slider.valueChanged.connect(self.on_sc_speed_changed)
        self.sc_dz_slider.valueChanged.connect(self.on_sc_dz_changed)
        self.mode_2d_check.toggled.connect(self.on_mode_2d_toggled)

        layout.addStretch()

        # Load values
        self.load_settings()

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
        self.speed_label.setText(f"{sc_speed:.4f}")
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
