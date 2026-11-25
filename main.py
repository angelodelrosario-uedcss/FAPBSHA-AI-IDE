
import sys

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.theme import DARK_THEME


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("FAPBSH AI IDE")
    app.setOrganizationName("FAPBSH AI IDE")

    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
