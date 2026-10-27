"""
Orbiter GUI Entry Point
"""
import sys
from PyQt6.QtWidgets import QApplication
from orbiter.gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Orbiter")
    app.setDesktopFileName("orbiter.desktop")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
