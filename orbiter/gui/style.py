"""
Modern Dark Theme Styling for Orbiter GUI
"""

DARK_THEME = """
QWidget {
    background-color: #16181e;
    color: #e2e8f0;
    font-family: 'Inter', 'Noto Sans', 'Segoe UI', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #121318;
}

QTabWidget::pane {
    border: 1px solid #232733;
    border-radius: 8px;
    background-color: #181a20;
    top: -1px;
}

QTabBar::tab {
    background-color: #1e212b;
    color: #94a3b8;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #272c3a;
    color: #f1f5f9;
}

QTableWidget {
    background-color: #181a20;
    gridline-color: #232733;
    border: 1px solid #232733;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #1e212b;
    color: #cbd5e1;
    padding: 8px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #2563eb;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton#secondaryBtn {
    background-color: #272c3a;
    color: #cbd5e1;
}

QPushButton#secondaryBtn:hover {
    background-color: #333a4c;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #272c3a;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #2563eb;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #2563eb;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QProgressBar {
    background-color: #222634;
    border-radius: 4px;
    text-align: center;
    color: #f8fafc;
    font-weight: 600;
    border: 1px solid #2b3042;
}

QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 4px;
}

QGroupBox {
    border: 1px solid #232733;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: bold;
    color: #93c5fd;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #181a20;
}

QLineEdit, QComboBox {
    background-color: #1e212b;
    border: 1px solid #333a4c;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #1e212b;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
}
"""
