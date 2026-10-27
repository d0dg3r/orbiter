"""
Button Mapping Editor Widget & Dialog for Orbiter
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLabel, QComboBox, QLineEdit, QHeaderView,
    QStackedWidget, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QSize
from orbiter.gui.icons import get_icon
from orbiter.gui.style import apply_tab_page_layout, make_combo_opaque
from orbiter.i18n import tr

# Stable IDs only — labels via tr()
MOUSE_IDS = ["BTN_LEFT", "BTN_RIGHT", "BTN_MIDDLE", "BTN_SIDE", "BTN_EXTRA"]

COMMON_KEY_IDS = [
    "KEY_ESC", "KEY_ENTER", "KEY_SPACE", "KEY_TAB", "KEY_BACKSPACE", "KEY_DELETE",
    "KEY_HOME", "KEY_END", "KEY_PAGEUP", "KEY_PAGEDOWN",
    "KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT",
    *[f"KEY_F{i}" for i in range(1, 13)],
    "KEY_PLAYPAUSE", "KEY_NEXTSONG", "KEY_PREVIOUSSONG", "KEY_MUTE",
    "KEY_VOLUMEUP", "KEY_VOLUMEDOWN",
    "KEY_LEFTCTRL", "KEY_LEFTALT", "KEY_LEFTSHIFT", "KEY_LEFTMETA",
]
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    COMMON_KEY_IDS.append(f"KEY_{ch}")
for num in "0123456789":
    COMMON_KEY_IDS.append(f"KEY_{num}")

# (command, locale key suffix under hypr.*)
HYPRLAND_PRESETS = [
    ("hl.dsp.focus({ workspace = 'e-1' })", "ws_left"),
    ("hl.dsp.focus({ workspace = 'e+1' })", "ws_right"),
    ("workspace, previous", "ws_prev"),
    ("killactive", "killactive"),
    ("fullscreen, 1", "maximize"),
    ("fullscreen, 0", "fullscreen"),
    ("togglefloating", "floating"),
    ("exec, rofi -show drun", "rofi"),
    ("exec, pavucontrol", "pavucontrol"),
]

BUILTIN_IDS = ["speed_up", "speed_down", "toggle_2d", "next_profile", "prev_profile"]


def _key_label(code: str) -> str:
    if len(code) == 5 and code.startswith("KEY_") and code[4].isalpha():
        return tr("key.letter", ch=code[4])
    if len(code) == 5 and code.startswith("KEY_") and code[4].isdigit():
        return tr("key.digit", num=code[4])
    return tr(f"key.{code}")


def _mouse_label(code: str) -> str:
    return tr(f"mouse.{code}")


class ButtonEditDialog(QDialog):
    def __init__(self, code, btn_data, config_mgr, parent=None):
        super().__init__(parent)
        self.code = code
        self.btn_data = dict(btn_data)
        self.config_mgr = config_mgr
        self.setFixedSize(540, 440)
        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        name_box = QHBoxLayout()
        self.name_lbl = QLabel()
        self.name_lbl.setFixedWidth(140)
        self.name_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.name_edit = QLineEdit(self.btn_data.get("name", ""))
        name_box.addWidget(self.name_lbl)
        name_box.addWidget(self.name_edit)
        layout.addLayout(name_box)

        type_box = QHBoxLayout()
        self.type_lbl = QLabel()
        self.type_lbl.setFixedWidth(140)
        self.type_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.type_combo = QComboBox()
        self.type_combo.setIconSize(QSize(16, 16))
        make_combo_opaque(self.type_combo)
        type_box.addWidget(self.type_lbl)
        type_box.addWidget(self.type_combo)
        layout.addLayout(type_box)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #242a3c;")
        layout.addWidget(line)

        self.stack = QStackedWidget()

        p_mouse = QWidget()
        l_mouse = QVBoxLayout(p_mouse)
        self.mouse_hint = QLabel()
        l_mouse.addWidget(self.mouse_hint)
        self.mouse_combo = QComboBox()
        self.mouse_combo.setIconSize(QSize(16, 16))
        make_combo_opaque(self.mouse_combo)
        l_mouse.addWidget(self.mouse_combo)
        l_mouse.addStretch()
        self.stack.addWidget(p_mouse)

        p_builtin = QWidget()
        l_builtin = QVBoxLayout(p_builtin)
        self.builtin_hint = QLabel()
        l_builtin.addWidget(self.builtin_hint)
        self.builtin_combo = QComboBox()
        self.builtin_combo.setIconSize(QSize(16, 16))
        make_combo_opaque(self.builtin_combo)
        l_builtin.addWidget(self.builtin_combo)
        self.builtin_note = QLabel()
        self.builtin_note.setStyleSheet("color: #64748b; font-size: 11px;")
        self.builtin_note.setWordWrap(True)
        l_builtin.addWidget(self.builtin_note)
        l_builtin.addStretch()
        self.stack.addWidget(p_builtin)

        p_key = QWidget()
        l_key = QVBoxLayout(p_key)
        self.key_hint = QLabel()
        l_key.addWidget(self.key_hint)
        self.key_combo = QComboBox()
        self.key_combo.setIconSize(QSize(16, 16))
        self.key_combo.setEditable(True)
        make_combo_opaque(self.key_combo)
        l_key.addWidget(self.key_combo)
        l_key.addStretch()
        self.stack.addWidget(p_key)

        p_combo = QWidget()
        l_combo = QVBoxLayout(p_combo)
        self.combo_hint = QLabel()
        l_combo.addWidget(self.combo_hint)
        mod_box = QHBoxLayout()
        self.mod_ctrl = QCheckBox()
        self.mod_alt = QCheckBox()
        self.mod_shift = QCheckBox()
        self.mod_meta = QCheckBox()
        for w in (self.mod_ctrl, self.mod_alt, self.mod_shift, self.mod_meta):
            mod_box.addWidget(w)
        l_combo.addLayout(mod_box)
        key_target_box = QHBoxLayout()
        self.target_key_lbl = QLabel()
        key_target_box.addWidget(self.target_key_lbl)
        self.combo_target_key = QComboBox()
        self.combo_target_key.setIconSize(QSize(16, 16))
        self.combo_target_key.setEditable(True)
        make_combo_opaque(self.combo_target_key)
        key_target_box.addWidget(self.combo_target_key)
        l_combo.addLayout(key_target_box)
        preview_box = QHBoxLayout()
        self.combo_label_lbl = QLabel()
        preview_box.addWidget(self.combo_label_lbl)
        self.combo_preview_lbl = QLabel("")
        self.combo_preview_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")
        preview_box.addWidget(self.combo_preview_lbl)
        preview_box.addStretch()
        l_combo.addLayout(preview_box)
        self.mod_ctrl.toggled.connect(self.update_combo_preview)
        self.mod_alt.toggled.connect(self.update_combo_preview)
        self.mod_shift.toggled.connect(self.update_combo_preview)
        self.mod_meta.toggled.connect(self.update_combo_preview)
        self.combo_target_key.currentIndexChanged.connect(self.update_combo_preview)
        self.combo_target_key.editTextChanged.connect(self.update_combo_preview)
        l_combo.addStretch()
        self.stack.addWidget(p_combo)

        p_hypr = QWidget()
        l_hypr = QVBoxLayout(p_hypr)
        self.hypr_hint = QLabel()
        l_hypr.addWidget(self.hypr_hint)
        self.hypr_combo = QComboBox()
        self.hypr_combo.setIconSize(QSize(16, 16))
        self.hypr_combo.setEditable(True)
        make_combo_opaque(self.hypr_combo)
        l_hypr.addWidget(self.hypr_combo)
        l_hypr.addStretch()
        self.stack.addWidget(p_hypr)

        p_shell = QWidget()
        l_shell = QVBoxLayout(p_shell)
        self.shell_hint = QLabel()
        l_shell.addWidget(self.shell_hint)
        self.shell_edit = QLineEdit()
        l_shell.addWidget(self.shell_edit)
        l_shell.addStretch()
        self.stack.addWidget(p_shell)

        p_none = QWidget()
        l_none = QVBoxLayout(p_none)
        self.none_hint = QLabel()
        self.none_hint.setStyleSheet("color: #64748b; font-style: italic; padding: 20px 0;")
        l_none.addWidget(self.none_hint)
        l_none.addStretch()
        self.stack.addWidget(p_none)

        layout.addWidget(self.stack)

        desc_box = QHBoxLayout()
        self.desc_lbl = QLabel()
        self.desc_lbl.setFixedWidth(140)
        self.desc_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.desc_edit = QLineEdit(self.btn_data.get("description", ""))
        desc_box.addWidget(self.desc_lbl)
        desc_box.addWidget(self.desc_edit)
        layout.addLayout(desc_box)

        btn_box = QHBoxLayout()
        self.save_btn = QPushButton()
        self.save_btn.setIcon(get_icon("check", color="#ffffff", size=14))
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("secondaryBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(self.cancel_btn)
        btn_box.addWidget(self.save_btn)
        layout.addLayout(btn_box)

        self.type_combo.currentIndexChanged.connect(self.on_type_changed)

    def _refill_combos(self):
        # types
        cur_type = self.type_combo.currentData() if self.type_combo.count() else None
        self.type_combo.blockSignals(True)
        self.type_combo.clear()
        for data, icon, key in [
            ("mouse", "mouse", "editor.type.mouse"),
            ("builtin", "cpu", "editor.type.builtin"),
            ("key", "keyboard", "editor.type.key"),
            ("combo", "command", "editor.type.combo"),
            ("hyprland", "layout", "editor.type.hyprland"),
            ("shell", "terminal", "editor.type.shell"),
            ("none", "ban", "editor.type.none"),
        ]:
            color = "#f87171" if data == "none" else "#38bdf8"
            self.type_combo.addItem(get_icon(icon, color=color, size=16), tr(key), data)
        if cur_type:
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == cur_type:
                    self.type_combo.setCurrentIndex(i)
                    break
        self.type_combo.blockSignals(False)

        self.mouse_combo.clear()
        for code in MOUSE_IDS:
            self.mouse_combo.addItem(
                get_icon("mouse", color="#94a3b8", size=16),
                f"{_mouse_label(code)} ({code})",
                code,
            )

        self.builtin_combo.clear()
        icons = {
            "speed_up": "trending-up",
            "speed_down": "trending-down",
            "toggle_2d": "target",
            "next_profile": "arrow-right",
            "prev_profile": "arrow-left",
        }
        for bid in BUILTIN_IDS:
            self.builtin_combo.addItem(
                get_icon(icons[bid], color="#38bdf8", size=16),
                tr(f"editor.builtin.{bid}"),
                bid,
            )
        profiles = self.config_mgr.get_profiles() if self.config_mgr else {}
        for p_name in sorted(profiles.keys()):
            self.builtin_combo.addItem(
                get_icon("layers", color="#93c5fd", size=16),
                tr("editor.builtin.profile", name=p_name),
                f"profile:{p_name}",
            )

        self.key_combo.clear()
        self.combo_target_key.clear()
        for code in COMMON_KEY_IDS:
            label = f"{_key_label(code)} ({code})"
            self.key_combo.addItem(get_icon("keyboard", color="#94a3b8", size=16), label, code)
            self.combo_target_key.addItem(get_icon("keyboard", color="#94a3b8", size=16), label, code)

        self.hypr_combo.clear()
        for cmd, hid in HYPRLAND_PRESETS:
            self.hypr_combo.addItem(
                get_icon("layout", color="#94a3b8", size=16),
                f"{tr(f'hypr.{hid}')} [{cmd}]",
                cmd,
            )

    def retranslate_ui(self):
        name = self.btn_data.get("name") or tr("editor.btn_fallback", code=self.code)
        self.setWindowTitle(tr("editor.dialog_title", name=name))
        if not self.name_edit.text():
            self.name_edit.setText(tr("editor.btn_fallback", code=self.code))
        self.name_lbl.setText(tr("editor.name_label"))
        self.type_lbl.setText(tr("editor.type_label"))
        self.mouse_hint.setText(tr("editor.mouse_hint"))
        self.builtin_hint.setText(tr("editor.builtin_hint"))
        self.builtin_note.setText(tr("editor.builtin.note"))
        self.key_hint.setText(tr("editor.key_hint"))
        self.combo_hint.setText(tr("editor.combo_hint"))
        self.mod_ctrl.setText(tr("editor.mod_ctrl"))
        self.mod_alt.setText(tr("editor.mod_alt"))
        self.mod_shift.setText(tr("editor.mod_shift"))
        self.mod_meta.setText(tr("editor.mod_meta"))
        self.target_key_lbl.setText(tr("editor.target_key"))
        self.combo_label_lbl.setText(tr("editor.combo_label"))
        self.hypr_hint.setText(tr("editor.hypr_hint"))
        self.shell_hint.setText(tr("editor.shell_hint"))
        self.shell_edit.setPlaceholderText(tr("editor.shell_placeholder"))
        self.none_hint.setText(tr("editor.none_hint"))
        self.desc_lbl.setText(tr("editor.desc_label"))
        self.save_btn.setText(tr("editor.save"))
        self.cancel_btn.setText(tr("editor.cancel"))
        self._refill_combos()
        self.load_initial_values()
        self.update_combo_preview()

    def on_type_changed(self, idx):
        self.stack.setCurrentIndex(idx)

    def update_combo_preview(self):
        parts = []
        if self.mod_ctrl.isChecked():
            parts.append("KEY_LEFTCTRL")
        if self.mod_alt.isChecked():
            parts.append("KEY_LEFTALT")
        if self.mod_shift.isChecked():
            parts.append("KEY_LEFTSHIFT")
        if self.mod_meta.isChecked():
            parts.append("KEY_LEFTMETA")
        idx = self.combo_target_key.currentIndex()
        if idx >= 0 and self.combo_target_key.itemData(idx):
            target = self.combo_target_key.itemData(idx)
        else:
            target = self.combo_target_key.currentText().strip()
        if target:
            parts.append(target)
        self.combo_preview_lbl.setText(" + ".join(parts) if parts else tr("editor.combo_empty"))

    def load_initial_values(self):
        curr_type = self.btn_data.get("type", "mouse")
        act = self.btn_data.get("action", "")
        type_idx = 0
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == curr_type:
                type_idx = i
                break
        self.type_combo.setCurrentIndex(type_idx)
        self.stack.setCurrentIndex(type_idx)

        if curr_type == "mouse":
            for i in range(self.mouse_combo.count()):
                if self.mouse_combo.itemData(i) == str(act):
                    self.mouse_combo.setCurrentIndex(i)
                    break
        elif curr_type == "builtin":
            found = False
            for i in range(self.builtin_combo.count()):
                if self.builtin_combo.itemData(i) == str(act):
                    self.builtin_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found and str(act).startswith("profile:"):
                self.builtin_combo.addItem(
                    get_icon("layers", color="#93c5fd", size=16),
                    tr("editor.builtin.profile", name=str(act)[8:]),
                    str(act),
                )
                self.builtin_combo.setCurrentIndex(self.builtin_combo.count() - 1)
        elif curr_type == "key":
            found = False
            for i in range(self.key_combo.count()):
                if self.key_combo.itemData(i) == str(act):
                    self.key_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self.key_combo.setCurrentText(str(act))
        elif curr_type == "combo":
            keys = act if isinstance(act, list) else [k.strip() for k in str(act).split("+") if k.strip()]
            self.mod_ctrl.setChecked("KEY_LEFTCTRL" in keys or "KEY_RIGHTCTRL" in keys)
            self.mod_alt.setChecked("KEY_LEFTALT" in keys or "KEY_RIGHTALT" in keys)
            self.mod_shift.setChecked("KEY_LEFTSHIFT" in keys or "KEY_RIGHTSHIFT" in keys)
            self.mod_meta.setChecked("KEY_LEFTMETA" in keys or "KEY_RIGHTMETA" in keys)
            mods = {
                "KEY_LEFTCTRL", "KEY_RIGHTCTRL", "KEY_LEFTALT", "KEY_RIGHTALT",
                "KEY_LEFTSHIFT", "KEY_RIGHTSHIFT", "KEY_LEFTMETA", "KEY_RIGHTMETA",
            }
            non_mods = [k for k in keys if k not in mods]
            if non_mods:
                target = non_mods[0]
                found = False
                for i in range(self.combo_target_key.count()):
                    if self.combo_target_key.itemData(i) == target:
                        self.combo_target_key.setCurrentIndex(i)
                        found = True
                        break
                if not found:
                    self.combo_target_key.setCurrentText(target)
            self.update_combo_preview()
        elif curr_type == "hyprland":
            found = False
            for i in range(self.hypr_combo.count()):
                if self.hypr_combo.itemData(i) == str(act):
                    self.hypr_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self.hypr_combo.setCurrentText(str(act))
        elif curr_type == "shell":
            self.shell_edit.setText(str(act))

    def save(self):
        sel_type = self.type_combo.currentData()
        action = None
        if sel_type == "mouse":
            action = self.mouse_combo.currentData()
        elif sel_type == "builtin":
            action = self.builtin_combo.currentData()
        elif sel_type == "key":
            idx = self.key_combo.currentIndex()
            action = self.key_combo.itemData(idx) if idx >= 0 and self.key_combo.itemData(idx) else self.key_combo.currentText().strip()
        elif sel_type == "combo":
            parts = []
            if self.mod_ctrl.isChecked():
                parts.append("KEY_LEFTCTRL")
            if self.mod_alt.isChecked():
                parts.append("KEY_LEFTALT")
            if self.mod_shift.isChecked():
                parts.append("KEY_LEFTSHIFT")
            if self.mod_meta.isChecked():
                parts.append("KEY_LEFTMETA")
            idx = self.combo_target_key.currentIndex()
            target = self.combo_target_key.itemData(idx) if idx >= 0 and self.combo_target_key.itemData(idx) else self.combo_target_key.currentText().strip()
            if target and target not in parts:
                parts.append(target)
            action = parts
        elif sel_type == "hyprland":
            idx = self.hypr_combo.currentIndex()
            action = self.hypr_combo.itemData(idx) if idx >= 0 and self.hypr_combo.itemData(idx) else self.hypr_combo.currentText().strip()
        elif sel_type == "shell":
            action = self.shell_edit.text().strip()
        elif sel_type == "none":
            action = None
        self.btn_data["name"] = self.name_edit.text().strip()
        self.btn_data["type"] = sel_type
        self.btn_data["action"] = action
        self.btn_data["description"] = self.desc_edit.text().strip()
        self.accept()


class ButtonEditorWidget(QWidget):
    def __init__(self, config_mgr, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        apply_tab_page_layout(layout)
        self.header = QLabel()
        self.header.setStyleSheet("color: #94a3b8; font-weight: 500;")
        layout.addWidget(self.header)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self.edit_selected)
        layout.addWidget(self.table)
        btn_row = QHBoxLayout()
        self.edit_btn = QPushButton()
        self.edit_btn.setObjectName("secondaryBtn")
        self.edit_btn.setIcon(get_icon("edit", color="#38bdf8", size=14))
        self.edit_btn.clicked.connect(self.edit_selected)
        btn_row.addWidget(self.edit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.header.setText(tr("editor.header"))
        self.table.setHorizontalHeaderLabels([
            tr("editor.col_btn"), tr("editor.col_name"), tr("editor.col_cat"),
            tr("editor.col_action"), tr("editor.col_desc"),
        ])
        self.edit_btn.setText(tr("editor.edit"))
        self.populate_table()

    def friendly_action_text(self, atype, action):
        if atype == "mouse":
            if action in MOUSE_IDS:
                return f"{_mouse_label(action)} ({action})"
            return str(action)
        if atype == "builtin":
            if action in BUILTIN_IDS:
                return tr(f"editor.builtin.{action}")
            if str(action).startswith("profile:"):
                return tr("editor.builtin.profile_activate", name=str(action)[8:])
            return str(action)
        if atype == "combo":
            return " + ".join(action) if isinstance(action, list) else str(action)
        if atype == "key":
            if action in COMMON_KEY_IDS:
                return f"{_key_label(action)} ({action})"
            return str(action)
        if atype == "none":
            return tr("editor.disabled")
        return str(action)

    def populate_table(self):
        buttons = self.config_mgr.get("buttons", {})
        override = self.config_mgr.get_model_override()
        from orbiter.device import DEVICE_MODELS, detect_device_model, localized_button_info
        if override != "auto" and override in DEVICE_MODELS:
            model = DEVICE_MODELS[override]
        else:
            model = detect_device_model()
        model_buttons = model.get("buttons", {})
        if model_buttons:
            filtered_codes = sorted(model_buttons.keys(), key=lambda x: int(x))
        else:
            filtered_codes = sorted(buttons.keys(), key=lambda x: int(x))
        self.table.setRowCount(len(filtered_codes))
        type_icon_map = {
            "mouse": "mouse", "builtin": "cpu", "key": "keyboard", "combo": "command",
            "hyprland": "layout", "shell": "terminal", "none": "ban",
        }
        for row, code in enumerate(filtered_codes):
            data = buttons.get(code, {})
            info = localized_button_info(code, model_buttons.get(code, {}))
            hw_label = info["name"]
            self.table.setItem(row, 0, QTableWidgetItem(f"{tr('editor.btn_fallback', code=code)} ({hw_label})"))
            btn_name = data.get("name") or hw_label
            self.table.setItem(row, 1, QTableWidgetItem(btn_name))
            raw_type = data.get("type", "none")
            type_item = QTableWidgetItem(tr(f"editor.cat.{raw_type}") if raw_type else tr("editor.cat.none"))
            type_item.setIcon(get_icon(type_icon_map.get(raw_type, "keyboard"), color="#38bdf8", size=14))
            self.table.setItem(row, 2, type_item)
            self.table.setItem(row, 3, QTableWidgetItem(self.friendly_action_text(raw_type, data.get("action", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(data.get("description", "")))
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, code)

    def edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        code = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        buttons = self.config_mgr.get("buttons", {})
        btn_data = buttons.get(code, {})
        dlg = ButtonEditDialog(code, btn_data, self.config_mgr, self)
        if dlg.exec():
            buttons[code] = dlg.btn_data
            self.config_mgr.set("buttons", buttons)
            self.config_mgr.save()
            self.populate_table()
