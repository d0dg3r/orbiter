"""
Button Mapping Editor Widget & Dialog for Orbiter
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLabel, QComboBox, QLineEdit, QHeaderView,
    QMessageBox, QStackedWidget, QCheckBox, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt

MOUSE_OPTIONS = [
    ("BTN_LEFT", "Linksklick (Standard)"),
    ("BTN_RIGHT", "Rechtsklick"),
    ("BTN_MIDDLE", "Mittelklick (Radklick / 3D-Drehen)"),
    ("BTN_SIDE", "Seitentaste (Zurück / Daumen)"),
    ("BTN_EXTRA", "Zusatztaste (Vorwärts / Vor)")
]

COMMON_KEYS = [
    ("KEY_ESC", "Escape (ESC)"),
    ("KEY_ENTER", "Enter / Return"),
    ("KEY_SPACE", "Leertaste (Space)"),
    ("KEY_TAB", "Tabulator (Tab)"),
    ("KEY_BACKSPACE", "Rücktaste (Backspace)"),
    ("KEY_DELETE", "Entfernen (Del)"),
    ("KEY_HOME", "Pos1 / Home (Ansicht zentrieren)"),
    ("KEY_END", "Ende"),
    ("KEY_PAGEUP", "Bild auf (Page Up)"),
    ("KEY_PAGEDOWN", "Bild ab (Page Down)"),
    ("KEY_UP", "Pfeil Oben"),
    ("KEY_DOWN", "Pfeil Unten"),
    ("KEY_LEFT", "Pfeil Links"),
    ("KEY_RIGHT", "Pfeil Rechts"),
    ("KEY_F1", "F1"),
    ("KEY_F2", "F2"),
    ("KEY_F3", "F3"),
    ("KEY_F4", "F4"),
    ("KEY_F5", "F5 (Neu laden)"),
    ("KEY_F6", "F6"),
    ("KEY_F7", "F7"),
    ("KEY_F8", "F8"),
    ("KEY_F9", "F9"),
    ("KEY_F10", "F10"),
    ("KEY_F11", "F11 (Vollbild)"),
    ("KEY_F12", "F12"),
    ("KEY_PLAYPAUSE", "Medien Play/Pause"),
    ("KEY_NEXTSONG", "Nächster Titel"),
    ("KEY_PREVIOUSSONG", "Vorheriger Titel"),
    ("KEY_MUTE", "Stummschalten (Mute)"),
    ("KEY_VOLUMEUP", "Lautstärke erhöhen (+)"),
    ("KEY_VOLUMEDOWN", "Lautstärke verringern (-)"),
    ("KEY_LEFTCTRL", "Strg / Ctrl"),
    ("KEY_LEFTALT", "Alt-Taste"),
    ("KEY_LEFTSHIFT", "Umschalt / Shift"),
    ("KEY_LEFTMETA", "Super / Windows-Taste"),
]
# A-Z hinzufügen
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    COMMON_KEYS.append((f"KEY_{ch}", f"Taste '{ch}'"))
# 0-9 hinzufügen
for num in "0123456789":
    COMMON_KEYS.append((f"KEY_{num}", f"Ziffer '{num}'"))

HYPRLAND_PRESETS = [
    ("hl.dsp.focus({ workspace = 'e-1' })", "Workspace nach links"),
    ("hl.dsp.focus({ workspace = 'e+1' })", "Workspace nach rechts"),
    ("workspace, previous", "Vorheriger Workspace"),
    ("killactive", "Aktives Fenster schließen"),
    ("fullscreen, 1", "Fenster maximieren"),
    ("fullscreen, 0", "Echter Vollbildmodus an/aus"),
    ("togglefloating", "Fenster Floating an/aus"),
    ("exec, rofi -show drun", "App-Starter (Rofi) öffnen"),
    ("exec, pavucontrol", "Lautstärkeregler (Pavucontrol)")
]


class ButtonEditDialog(QDialog):
    def __init__(self, code, btn_data, config_mgr, parent=None):
        super().__init__(parent)
        self.code = code
        self.btn_data = dict(btn_data)
        self.config_mgr = config_mgr
        self.setWindowTitle(f"Taste konfigurieren: {self.btn_data.get('name', f'Taste {code}')}")
        self.setFixedSize(520, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Name / Label
        name_box = QHBoxLayout()
        name_lbl = QLabel("Tasten-Bezeichnung:")
        name_lbl.setFixedWidth(130)
        self.name_edit = QLineEdit(self.btn_data.get("name", f"Taste {self.code}"))
        name_box.addWidget(name_lbl)
        name_box.addWidget(self.name_edit)
        layout.addLayout(name_box)

        # Typ Dropdown
        type_box = QHBoxLayout()
        type_lbl = QLabel("Aktions-Kategorie:")
        type_lbl.setFixedWidth(130)
        self.type_combo = QComboBox()
        self.type_combo.addItem("🖱️ Mausklick", "mouse")
        self.type_combo.addItem("⚙️ System / Intern & Profile", "builtin")
        self.type_combo.addItem("⌨️ Einzelne Taste (z. B. F11, ESC)", "key")
        self.type_combo.addItem("⚡ Tastenkombination (z. B. Super+D)", "combo")
        self.type_combo.addItem("🪟 Hyprland Dispatcher", "hyprland")
        self.type_combo.addItem("💻 Shell-Befehl ausführen", "shell")
        self.type_combo.addItem("🚫 Deaktiviert (Keine Aktion)", "none")
        type_box.addWidget(type_lbl)
        type_box.addWidget(self.type_combo)
        layout.addLayout(type_box)

        # Trennlinie
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #2b3042;")
        layout.addWidget(line)

        # Stacked Widget für die verschiedenen Typen
        self.stack = QStackedWidget()

        # Page 0: Mausklick
        p_mouse = QWidget()
        l_mouse = QVBoxLayout(p_mouse)
        l_mouse.addWidget(QLabel("Wähle die gewünschte Maustasten-Aktion:"))
        self.mouse_combo = QComboBox()
        for code, label in MOUSE_OPTIONS:
            self.mouse_combo.addItem(f"{label}  ({code})", code)
        l_mouse.addWidget(self.mouse_combo)
        l_mouse.addStretch()
        self.stack.addWidget(p_mouse)

        # Page 1: System / Intern & Profile
        p_builtin = QWidget()
        l_builtin = QVBoxLayout(p_builtin)
        l_builtin.addWidget(QLabel("Wähle eine interne Orbiter-Funktion oder ein Profil zum Umschalten:"))
        self.builtin_combo = QComboBox()
        # Standard Aktionen
        self.builtin_combo.addItem("⚡ Zeiger schneller (+25%)", "speed_up")
        self.builtin_combo.addItem("🐢 Zeiger langsamer (-20%)", "speed_down")
        self.builtin_combo.addItem("🎯 2D-Präzisionsmodus umschalten", "toggle_2d")
        self.builtin_combo.addItem("📁 Nächstes Profil (Durchschalten)", "next_profile")
        self.builtin_combo.addItem("📁 Vorheriges Profil (Zurückschalten)", "prev_profile")

        # Dynamisch alle Profile auflisten
        profiles = self.config_mgr.get_profiles() if self.config_mgr else {}
        for p_name in sorted(profiles.keys()):
            self.builtin_combo.addItem(f"📁 Direkt zu Profil: '{p_name}'", f"profile:{p_name}")

        l_builtin.addWidget(self.builtin_combo)
        builtin_hint = QLabel("Tipp: Du kannst Profile mit 'Nächstes Profil' nacheinander durchblättern oder direkt anwählen.")
        builtin_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        builtin_hint.setWordWrap(True)
        l_builtin.addWidget(builtin_hint)
        l_builtin.addStretch()
        self.stack.addWidget(p_builtin)

        # Page 2: Einzelne Taste
        p_key = QWidget()
        l_key = QVBoxLayout(p_key)
        l_key.addWidget(QLabel("Wähle eine Taste aus der Liste oder tippe einen Tastencode ein:"))
        self.key_combo = QComboBox()
        self.key_combo.setEditable(True)
        for code, label in COMMON_KEYS:
            self.key_combo.addItem(f"{label}  ({code})", code)
        l_key.addWidget(self.key_combo)
        l_key.addStretch()
        self.stack.addWidget(p_key)

        # Page 3: Tastenkombination (Combo)
        p_combo = QWidget()
        l_combo = QVBoxLayout(p_combo)
        l_combo.addWidget(QLabel("Wähle die Sondertasten (Modifier) und die Zieltaste:"))

        mod_box = QHBoxLayout()
        self.mod_ctrl = QCheckBox("Strg (Ctrl)")
        self.mod_alt = QCheckBox("Alt")
        self.mod_shift = QCheckBox("Shift")
        self.mod_meta = QCheckBox("Super (Win)")
        mod_box.addWidget(self.mod_ctrl)
        mod_box.addWidget(self.mod_alt)
        mod_box.addWidget(self.mod_shift)
        mod_box.addWidget(self.mod_meta)
        l_combo.addLayout(mod_box)

        key_target_box = QHBoxLayout()
        key_target_box.addWidget(QLabel("Zieltaste:"))
        self.combo_target_key = QComboBox()
        self.combo_target_key.setEditable(True)
        for code, label in COMMON_KEYS:
            self.combo_target_key.addItem(f"{label} ({code})", code)
        key_target_box.addWidget(self.combo_target_key)
        l_combo.addLayout(key_target_box)

        # Combo Vorschau
        preview_box = QHBoxLayout()
        preview_box.addWidget(QLabel("Vorschau-Aktion:"))
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

        # Page 4: Hyprland Dispatcher
        p_hypr = QWidget()
        l_hypr = QVBoxLayout(p_hypr)
        l_hypr.addWidget(QLabel("Wähle einen Hyprland-Befehl oder gib einen eigenen Dispatcher ein:"))
        self.hypr_combo = QComboBox()
        self.hypr_combo.setEditable(True)
        for cmd, label in HYPRLAND_PRESETS:
            self.hypr_combo.addItem(f"{label}  [{cmd}]", cmd)
        l_hypr.addWidget(self.hypr_combo)
        l_hypr.addStretch()
        self.stack.addWidget(p_hypr)

        # Page 5: Shell-Befehl
        p_shell = QWidget()
        l_shell = QVBoxLayout(p_shell)
        l_shell.addWidget(QLabel("Befehl der im Hintergrund ausgeführt werden soll:"))
        self.shell_edit = QLineEdit()
        self.shell_edit.setPlaceholderText("z.B. alacritty, firefox, notify-send 'Hallo'")
        l_shell.addWidget(self.shell_edit)
        l_shell.addStretch()
        self.stack.addWidget(p_shell)

        # Page 6: Deaktiviert
        p_none = QWidget()
        l_none = QVBoxLayout(p_none)
        lbl_none = QLabel("🚫 Diese Taste führt keine Aktion aus.")
        lbl_none.setStyleSheet("color: #94a3b8; font-style: italic; padding: 20px 0;")
        l_none.addWidget(lbl_none)
        l_none.addStretch()
        self.stack.addWidget(p_none)

        layout.addWidget(self.stack)

        # Beschreibung / Notiz
        desc_box = QHBoxLayout()
        desc_lbl = QLabel("Beschreibung / Notiz:")
        desc_lbl.setFixedWidth(130)
        self.desc_edit = QLineEdit(self.btn_data.get("description", ""))
        desc_box.addWidget(desc_lbl)
        desc_box.addWidget(self.desc_edit)
        layout.addLayout(desc_box)

        # Buttons
        btn_box = QHBoxLayout()
        save_btn = QPushButton("Übernehmen")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)

        self.type_combo.currentIndexChanged.connect(self.on_type_changed)

        # Initiale Werte laden
        self.load_initial_values()

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
        self.combo_preview_lbl.setText(" + ".join(parts) if parts else "Keine Tasten gewählt")

    def load_initial_values(self):
        curr_type = self.btn_data.get("type", "mouse")
        act = self.btn_data.get("action", "")

        # Find type index
        type_idx = 0
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == curr_type:
                type_idx = i
                break
        self.type_combo.setCurrentIndex(type_idx)
        self.stack.setCurrentIndex(type_idx)

        # Pre-fill corresponding page
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
                self.builtin_combo.addItem(f"📁 Direkt zu Profil: '{str(act)[8:]}'", str(act))
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
            if isinstance(act, list):
                keys = act
            else:
                keys = [k.strip() for k in str(act).split("+") if k.strip()]

            self.mod_ctrl.setChecked("KEY_LEFTCTRL" in keys or "KEY_RIGHTCTRL" in keys)
            self.mod_alt.setChecked("KEY_LEFTALT" in keys or "KEY_RIGHTALT" in keys)
            self.mod_shift.setChecked("KEY_LEFTSHIFT" in keys or "KEY_RIGHTSHIFT" in keys)
            self.mod_meta.setChecked("KEY_LEFTMETA" in keys or "KEY_RIGHTMETA" in keys)

            non_mods = [k for k in keys if k not in ("KEY_LEFTCTRL", "KEY_RIGHTCTRL", "KEY_LEFTALT", "KEY_RIGHTALT", "KEY_LEFTSHIFT", "KEY_RIGHTSHIFT", "KEY_LEFTMETA", "KEY_RIGHTMETA")]
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
            if idx >= 0 and self.key_combo.itemData(idx):
                action = self.key_combo.itemData(idx)
            else:
                action = self.key_combo.currentText().strip()
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
            if idx >= 0 and self.combo_target_key.itemData(idx):
                target = self.combo_target_key.itemData(idx)
            else:
                target = self.combo_target_key.currentText().strip()

            if target and target not in parts:
                parts.append(target)
            action = parts
        elif sel_type == "hyprland":
            idx = self.hypr_combo.currentIndex()
            if idx >= 0 and self.hypr_combo.itemData(idx):
                action = self.hypr_combo.itemData(idx)
            else:
                action = self.hypr_combo.currentText().strip()
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
        layout.setContentsMargins(0, 8, 0, 0)

        header = QLabel("Tastenbelegung für das aktive Profil. Doppelklick oder Auswählen & Bearbeiten:")
        header.setStyleSheet("color: #94a3b8; margin-bottom: 6px;")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Taste", "Name", "Kategorie", "Aktion", "Beschreibung"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_selected)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        edit_btn = QPushButton("✏️ Ausgewählte Taste bearbeiten")
        edit_btn.clicked.connect(self.edit_selected)
        btn_row.addWidget(edit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.populate_table()

    def friendly_action_text(self, atype, action):
        if atype == "mouse":
            for code, label in MOUSE_OPTIONS:
                if code == action:
                    return f"{label} ({code})"
            return str(action)
        elif atype == "builtin":
            builtin_map = {
                "speed_up": "⚡ Zeiger schneller (+25%)",
                "speed_down": "🐢 Zeiger langsamer (-20%)",
                "toggle_2d": "🎯 2D-Modus Toggle",
                "next_profile": "📁 Nächstes Profil",
                "prev_profile": "📁 Vorheriges Profil"
            }
            if action in builtin_map:
                return builtin_map[action]
            if str(action).startswith("profile:"):
                return f"📁 Profil aktivieren: '{str(action)[8:]}'"
            return str(action)
        elif atype == "combo":
            if isinstance(action, list):
                return " + ".join(action)
            return str(action)
        elif atype == "key":
            for code, label in COMMON_KEYS:
                if code == action:
                    return f"{label} ({code})"
            return str(action)
        elif atype == "none":
            return "🚫 Deaktiviert"
        return str(action)

    def populate_table(self):
        buttons = self.config_mgr.get("buttons", {})
        self.table.setRowCount(len(buttons))

        type_names = {
            "mouse": "Mausklick",
            "builtin": "System & Profile",
            "key": "Einzelne Taste",
            "combo": "Tastenkombi",
            "hyprland": "Hyprland",
            "shell": "Shell-Befehl",
            "none": "Deaktiviert"
        }

        for row, (code, data) in enumerate(sorted(buttons.items(), key=lambda x: int(x[0]))):
            self.table.setItem(row, 0, QTableWidgetItem(f"Code {code}"))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))

            raw_type = data.get("type", "")
            self.table.setItem(row, 2, QTableWidgetItem(type_names.get(raw_type, raw_type)))

            act = data.get("action", "")
            act_str = self.friendly_action_text(raw_type, act)
            self.table.setItem(row, 3, QTableWidgetItem(act_str))
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
