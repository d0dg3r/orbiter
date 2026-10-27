"""
Orbiter GUI Application Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from orbiter.config import ConfigManager
from orbiter.i18n import init_from_config
from orbiter.gui.main_window import MainWindow

def main():
    init_from_config(ConfigManager())
    app = QApplication(sys.argv)
    app.setApplicationName("Orbiter")
    app.setDesktopFileName("orbiter")
    app.setQuitOnLastWindowClosed(False)

    start_minimized = "--tray" in sys.argv or "--minimized" in sys.argv
    window = MainWindow(start_minimized=start_minimized)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
