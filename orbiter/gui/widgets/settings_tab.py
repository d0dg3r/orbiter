"""
App preferences: language and config export/import.
"""
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QPushButton, QFileDialog, QMessageBox
)

from orbiter.gui.style import apply_group_layout, apply_tab_page_layout, make_combo_opaque
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
        apply_tab_page_layout(layout)

        self.lang_group = QGroupBox()
        lang_layout = QVBoxLayout(self.lang_group)
        apply_group_layout(lang_layout)
        self.lang_combo = QComboBox()
        make_combo_opaque(self.lang_combo)
        self._rebuild_lang_combo()
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        self.lang_hint = QLabel()
        self.lang_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        lang_layout.addWidget(self.lang_hint)
        layout.addWidget(self.lang_group)

        self.backup_group = QGroupBox()
        b_layout = QHBoxLayout(self.backup_group)
        apply_group_layout(b_layout)
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

        layout.addStretch()
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
