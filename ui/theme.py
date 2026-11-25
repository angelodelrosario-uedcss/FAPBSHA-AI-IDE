
DARK_THEME = """
QWidget {
    background-color: #1e1e1e;
    color: #cccccc;
    font-family: 'Segoe UI';
    font-size: 10pt;
}

QMainWindow {
    background-color: #1e1e1e;
}

QMenuBar {
    background-color: #252526;
    color: #cccccc;
    padding: 5px;
}

QMenuBar::item:selected {
    background-color: #37373d;
}

QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #454545;
}

QMenu::item:selected {
    background-color: #094771;
}

QPushButton {
    background-color: transparent;
    color: #cccccc;
    border: none;
    padding: 8px;
}

QPushButton:hover {
    background-color: #37373d;
}

QPushButton:checked {
    background-color: #37373d;
    border-left: 2px solid #007acc;
}

QLabel {
    color: #cccccc;
}

QTreeView {
    background-color: #252526;
    border: none;
    outline: none;
}

QTreeView::item {
    padding: 4px;
}

QTreeView::item:selected {
    background-color: #094771;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #252526;
    color: #999999;
    padding: 8px 16px;
    border: none;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: white;
    border-top: 2px solid #007acc;
}

QTabBar::close-button {
    image: none;
}

QLineEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 7px;
    selection-background-color: #264f78;
}

QStatusBar {
    background-color: #007acc;
    color: white;
}

QStatusBar QLabel {
    color: white;
    padding: 2px 8px;
}

QSplitter::handle {
    background-color: #333333;
}

QToolTip {
    background-color: #252526;
    color: white;
    border: 1px solid #454545;
}
"""
