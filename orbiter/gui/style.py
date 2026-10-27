"""
Modern Sleek Dark Theme Styling for Orbiter GUI
Professional look inspired by modern developer & creator tools.
"""

DARK_THEME = """
QWidget {
    background-color: #0e111a;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #090b11;
}

QDialog {
    background-color: #121520;
    border: 1px solid #242a3c;
    border-radius: 12px;
}

QTabWidget::pane {
    border: 1px solid #202637;
    border-radius: 10px;
    background-color: #121521;
    top: -1px;
}

QTabBar {
    qproperty-drawBase: 0;
    border: none;
    background: transparent;
}

QTabBar::tab {
    background-color: #171b28;
    color: #94a3b8;
    padding: 10px 22px;
    margin-right: 6px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #22283a;
}

QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
}

QTabBar::tab:hover:!selected {
    background-color: #22283b;
    color: #f1f5f9;
    border: 1px solid #313a52;
}

QTableWidget {
    background-color: #121521;
    gridline-color: #1c2130;
    border: 1px solid #202637;
    border-radius: 8px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    outline: none;
}

QTableWidget::item {
    padding: 6px 10px;
    border-bottom: 1px solid #181c2b;
}

QTableWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #171b28;
    color: #94a3b8;
    padding: 9px 10px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: none;
    border-bottom: 2px solid #202637;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: 1px solid #3b82f6;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    outline: none;
}

QPushButton:focus {
    outline: none;
}

QPushButton:hover {
    background-color: #3b82f6;
    border-color: #60a5fa;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

/* Unified Header Cluster */
QFrame#headerCluster {
    background-color: #141724;
    border: 1px solid #232a3d;
    border-radius: 10px;
}

QLabel#deviceStatusLabel {
    font-size: 12px;
    font-weight: 600;
    color: #cbd5e1;
    background: transparent;
    border: none;
    padding-left: 2px;
}

QFrame#headerDivider {
    background-color: #242c40;
    border: none;
    width: 1px;
}

QPushButton#modeToggleBtn {
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    outline: none;
}

QPushButton#modeToggleBtn:focus {
    outline: none;
}

QPushButton#secondaryBtn {
    background-color: #1a1f2d;
    color: #cbd5e1;
    border: 1px solid #293147;
    outline: none;
}

QPushButton#secondaryBtn:hover {
    background-color: #242b3e;
    color: #ffffff;
    border-color: #3b4664;
}

QPushButton#secondaryBtn:pressed {
    background-color: #151924;
}

QPushButton#dangerBtn {
    background-color: #1e1922;
    color: #f87171;
    border: 1px solid #3d232c;
}

QPushButton#dangerBtn:hover {
    background-color: #451a1a;
    color: #fca5a5;
    border-color: #ef4444;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #1f2537;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #2563eb;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #38bdf8;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #38bdf8;
    border-color: #ffffff;
}

QProgressBar {
    background-color: #191d2b;
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    font-weight: 600;
    border: 1px solid #262c3e;
}

QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 5px;
}

QGroupBox {
    border: 1px solid #202637;
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 22px;
    padding-left: 14px;
    padding-right: 14px;
    padding-bottom: 14px;
    font-weight: 700;
    color: #38bdf8;
    background-color: #141724;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 12px;
    background-color: #1a1e2e;
    border: 1px solid #2b3248;
    border-radius: 6px;
    color: #93c5fd;
    font-size: 12px;
}

QLineEdit, QComboBox {
    background-color: #161925;
    border: 1px solid #293044;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
    background-color: #1a1e2d;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid #293044;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox QAbstractItemView {
    background-color: #141724;
    background: #141724;
    color: #f8fafc;
    border: 1px solid #2e364e;
    border-radius: 8px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 6px 10px;
    border-radius: 5px;
    color: #f8fafc;
    background: transparent;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #202638;
    color: #ffffff;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QComboBoxPrivateContainer {
    background-color: #141724;
    background: #141724;
    border: 1px solid #2e364e;
    border-radius: 8px;
}

QCheckBox {
    spacing: 10px;
    color: #cbd5e1;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #3d465f;
    background-color: #161925;
}

QCheckBox::indicator:hover {
    border-color: #38bdf8;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border: 1px solid #3b82f6;
}

QMenu {
    background-color: #151825;
    border: 1px solid #2a3147;
    border-radius: 8px;
    padding: 6px;
}

QMenu::item {
    padding: 7px 24px 7px 12px;
    border-radius: 5px;
    color: #cbd5e1;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background-color: #242a3c;
    margin: 4px 6px;
}
"""

def make_combo_opaque(combo):
    """Avoid QComboBox dropdown transparency glitches on Wayland."""
    from PyQt6.QtCore import Qt
    view = combo.view()
    view.setAutoFillBackground(True)
    view.setStyleSheet("background-color: #141724; color: #f8fafc;")
    container = view.parentWidget()
    if container:
        container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        container.setAutoFillBackground(True)
        container.setStyleSheet("background-color: #141724; border: 1px solid #2e364e; border-radius: 8px;")

