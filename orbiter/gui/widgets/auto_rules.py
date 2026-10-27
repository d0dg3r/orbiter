"""
Auto-Profile Switching & Window Rules Widget for Orbiter GUI
Erlaubt das Zuordnen von Programmen (Fensterklassen) zu Profilen
und zeigt das aktuell fokussierte Fenster in Echtzeit an.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox,
    QLineEdit, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize
from orbiter.gui.icons import get_icon
from orbiter.gui.style import make_combo_opaque

class AutoRulesWidget(QWidget):
    def __init__(self, config_mgr, main_win, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.main_win = main_win
        self.last_detected_class = ""
        self.last_detected_title = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Header Box mit Auto-Switch Toggle
        top_box = QFrame()
        top_box.setObjectName("capsuleBox")
        top_box.setStyleSheet("background-color: #121522; border: 1px solid #202637; border-radius: 10px; padding: 12px;")
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(8, 6, 8, 6)

        self.enable_cb = QCheckBox("Automatisches Profil-Switching nach aktivem Fenster aktivieren")
        self.enable_cb.setChecked(self.config_mgr.is_auto_switch_enabled())
        self.enable_cb.setStyleSheet("font-weight: 700; font-size: 14px; color: #38bdf8;")
        self.enable_cb.toggled.connect(self.on_toggle_auto_switch)
        top_layout.addWidget(self.enable_cb)

        top_layout.addStretch()
        layout.addWidget(top_box)

        # 2. Live Window Detection Capsule
        detect_box = QFrame()
        detect_box.setStyleSheet("background-color: #141724; border: 1px solid #252c40; border-radius: 10px; padding: 12px;")
        detect_layout = QHBoxLayout(detect_box)
        detect_layout.setContentsMargins(10, 8, 10, 8)
        detect_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("target", color="#38bdf8", size=20).pixmap(20, 20))
        detect_layout.addWidget(icon_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)

        title_lbl = QLabel("Fokussiertes Programmfenster (Echtzeit):")
        title_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600; text-transform: uppercase;")
        info_col.addWidget(title_lbl)

        self.current_window_lbl = QLabel("Ermittle Fenster...")
        self.current_window_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")
        info_col.addWidget(self.current_window_lbl)
        detect_layout.addLayout(info_col)

        detect_layout.addStretch()

        # Schnell-Zuweisungs-Button
        self.quick_assign_btn = QPushButton("Aktuellem Profil zuweisen")
        self.quick_assign_btn.setObjectName("secondaryBtn")
        self.quick_assign_btn.setIcon(get_icon("plus", color="#38bdf8", size=14))
        self.quick_assign_btn.clicked.connect(self.assign_current_window)
        detect_layout.addWidget(self.quick_assign_btn)

        layout.addWidget(detect_box)

        # 3. Tabelle aller Zuweisungen
        table_lbl = QLabel("Regeln für automatischen Wechsel (Programmfenster → Profil):")
        table_lbl.setStyleSheet("color: #94a3b8; font-weight: 600; margin-top: 4px;")
        layout.addWidget(table_lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Fenster-Klasse (class / app)", "Ziel-Profil", "Aktion"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        layout.addWidget(self.table)

        # 4. Manuelle Hinzufügen-Leiste
        add_bar = QHBoxLayout()
        add_bar.setSpacing(8)

        self.add_pattern_edit = QLineEdit()
        self.add_pattern_edit.setPlaceholderText("z. B. chromium, gimp, blender, freecad")
        add_bar.addWidget(self.add_pattern_edit)

        add_bar.addWidget(QLabel("→ Profil:"))
        self.add_profile_combo = QComboBox()
        self.add_profile_combo.setMinimumWidth(160)
        make_combo_opaque(self.add_profile_combo)
        add_bar.addWidget(self.add_profile_combo)

        add_btn = QPushButton("Regel hinzufügen")
        add_btn.setIcon(get_icon("plus", color="#ffffff", size=14))
        add_btn.clicked.connect(self.on_add_rule_manual)
        add_bar.addWidget(add_btn)

        layout.addLayout(add_bar)

        self.populate_rules_table()
        self.populate_profile_combo()

    def populate_profile_combo(self):
        self.add_profile_combo.clear()
        profiles = sorted(self.config_mgr.get_profiles().keys())
        for p in profiles:
            self.add_profile_combo.addItem(get_icon("layers", color="#38bdf8", size=14), p)

    def on_toggle_auto_switch(self, checked):
        self.config_mgr.set_auto_switch_enabled(checked)
        self.main_win.send_ipc_command(f"SET_AUTO_SWITCH {str(checked).lower()}")

    def update_detected_window(self, win_class, win_title):
        self.last_detected_class = win_class.strip()
        self.last_detected_title = win_title.strip()
        if self.last_detected_class:
            t = f" : {self.last_detected_title[:45]}..." if len(self.last_detected_title) > 45 else (f" : {self.last_detected_title}" if self.last_detected_title else "")
            self.current_window_lbl.setText(f"<span style='color: #38bdf8;'>{self.last_detected_class}</span> <span style='color: #94a3b8;'>{t}</span>")
            self.quick_assign_btn.setEnabled(True)
        else:
            self.current_window_lbl.setText("<span style='color: #64748b;'>Kein aktives Fenster oder Desktop fokussiert</span>")
            self.quick_assign_btn.setEnabled(False)

    def assign_current_window(self):
        if not self.last_detected_class:
            return
        active_prof = self.config_mgr.get_active_profile_name()
        ok = self.config_mgr.add_rule_for_profile(active_prof, self.last_detected_class)
        if ok:
            self.main_win.send_ipc_command("RELOAD")
            self.populate_rules_table()
            QMessageBox.information(
                self, "Regel hinzugefügt",
                f"Fenster '{self.last_detected_class}' wechselt jetzt automatisch zum Profil '{active_prof}'!"
            )
        else:
            QMessageBox.warning(self, "Bereits vorhanden", f"Das Fenster '{self.last_detected_class}' ist bereits einer Regel zugeordnet.")

    def on_add_rule_manual(self):
        pat = self.add_pattern_edit.text().strip()
        prof = self.add_profile_combo.currentText().strip()
        if not pat or not prof:
            return
        if self.config_mgr.add_rule_for_profile(prof, pat):
            self.main_win.send_ipc_command("RELOAD")
            self.populate_rules_table()
            self.add_pattern_edit.clear()
        else:
            QMessageBox.warning(self, "Bereits vorhanden", f"Die Regel '{pat}' existiert bereits.")

    def populate_rules_table(self):
        rules = self.config_mgr.get_auto_rules()
        entries = []
        for prof, pats in rules.items():
            for pat in pats:
                entries.append((pat, prof))

        entries.sort(key=lambda x: (x[1], x[0]))
        self.table.setRowCount(len(entries))

        for row, (pat, prof) in enumerate(entries):
            pat_item = QTableWidgetItem(pat)
            pat_item.setForeground(Qt.GlobalColor.white)
            self.table.setItem(row, 0, pat_item)

            prof_item = QTableWidgetItem(prof)
            prof_item.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(row, 1, prof_item)

            del_btn = QPushButton("Löschen")
            del_btn.setObjectName("dangerBtn")
            del_btn.setIcon(get_icon("trash", color="#f87171", size=12))
            del_btn.setFixedHeight(26)
            del_btn.clicked.connect(lambda _, p=prof, pt=pat: self.delete_rule(p, pt))

            container = QWidget()
            box = QHBoxLayout(container)
            box.setContentsMargins(4, 2, 4, 2)
            box.addWidget(del_btn)
            self.table.setCellWidget(row, 2, container)

    def delete_rule(self, profile, pattern):
        if self.config_mgr.remove_rule_for_profile(profile, pattern):
            self.main_win.send_ipc_command("RELOAD")
            self.populate_rules_table()
