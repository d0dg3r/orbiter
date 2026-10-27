"""
Button Mapping Editor Widget & Dialog for Orbiter
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QDialog, QLabel, QComboBox, QLineEdit, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt

class ButtonEditDialog(QDialog):
    def __init__(self, code, btn_data, parent=None):
        super().__init__(parent)
        self.code = code
        self.btn_data = dict(btn_data)
        self.setWindowTitle(f"Taste bearbeiten: {self.btn_data.get('name', code)}")
        self.setFixedSize(450, 300)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name / Label
        layout.addWidget(QLabel("Tasten-Bezeichnung:"))
        self.name_edit = QLineEdit(self.btn_data.get("name", f"Taste {self.code}"))
        layout.addWidget(self.name_edit)

        # Typ
        layout.addWidget(QLabel("Aktions-Typ:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Mausklick",
            "Tastenkombination (z. B. Super+D)",
            "Einzelne Taste (z. B. F11, ESC)",
            "Hyprland Dispatcher",
            "Shell-Befehl",
            "System / Intern"
        ])
        type_map = {
            "mouse": 0,
            "combo": 1,
            "key": 2,
            "hyprland": 3,
            "shell": 4,
            "builtin": 5
        }
        curr_type = self.btn_data.get("type", "mouse")
        self.type_combo.setCurrentIndex(type_map.get(curr_type, 0))
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)

        # Aktion
        self.action_label = QLabel("Aktion:")
        layout.addWidget(self.action_label)
        self.action_edit = QLineEdit()
        act = self.btn_data.get("action", "")
        if isinstance(act, list):
            self.action_edit.setText(" + ".join(act))
        else:
            self.action_edit.setText(str(act))
        layout.addWidget(self.action_edit)

        # Beschreibung
        layout.addWidget(QLabel("Beschreibung / Notiz:"))
        self.desc_edit = QLineEdit(self.btn_data.get("description", ""))
        layout.addWidget(self.desc_edit)

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

        self.on_type_changed(self.type_combo.currentIndex())

    def on_type_changed(self, idx):
        hints = [
            "z.B. BTN_LEFT, BTN_RIGHT, BTN_MIDDLE, BTN_SIDE, BTN_EXTRA",
            "z.B. KEY_LEFTMETA + KEY_D  oder  KEY_LEFTCTRL + KEY_C",
            "z.B. KEY_ESC, KEY_F11, KEY_ENTER, KEY_SPACE",
            "z.B. hl.dsp.focus({ workspace = 'e-1' })",
            "z.B. alacritty  oder  firefox",
            "speed_up, speed_down, toggle_2d"
        ]
        self.action_label.setText(f"Aktion ({hints[idx]}):")

    def save(self):
        type_keys = ["mouse", "combo", "key", "hyprland", "shell", "builtin"]
        sel_type = type_keys[self.type_combo.currentIndex()]

        raw_act = self.action_edit.text().strip()
        if sel_type == "combo":
            parts = [p.strip() for p in raw_act.split("+") if p.strip()]
            action = parts
        else:
            action = raw_act

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

        header = QLabel("Hier kannst du jede Taste der SpaceExplorer frei konfigurieren. Doppelklick zum Bearbeiten:")
        header.setStyleSheet("color: #94a3b8; margin-bottom: 6px;")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Taste", "Name", "Typ", "Aktion", "Beschreibung"])
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
        edit_btn = QPushButton("Ausgewählte Taste bearbeiten")
        edit_btn.clicked.connect(self.edit_selected)
        btn_row.addWidget(edit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.populate_table()

    def populate_table(self):
        buttons = self.config_mgr.get("buttons", {})
        self.table.setRowCount(len(buttons))

        for row, (code, data) in enumerate(sorted(buttons.items(), key=lambda x: int(x[0]))):
            self.table.setItem(row, 0, QTableWidgetItem(f"Code {code}"))
            self.table.setItem(row, 1, QTableWidgetItem(data.get("name", "")))
            self.table.setItem(row, 2, QTableWidgetItem(data.get("type", "")))

            act = data.get("action", "")
            act_str = " + ".join(act) if isinstance(act, list) else str(act)
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

        dlg = ButtonEditDialog(code, btn_data, self)
        if dlg.exec():
            buttons[code] = dlg.btn_data
            self.config_mgr.set("buttons", buttons)
            self.config_mgr.save()
            self.populate_table()
