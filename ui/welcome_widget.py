
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt


class WelcomeWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        title = QLabel("FAPBSH AI IDE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #007acc;
        """)

        subtitle = QLabel(
            "A simple and powerful Python development environment"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #999999;
        """)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.new_project_btn = QPushButton(
            "+ New Project"
        )

        self.open_folder_btn = QPushButton(
            "Open Folder"
        )

        for button in (
            self.new_project_btn,
            self.open_folder_btn
        ):
            button.setMinimumWidth(130)
            button.setMinimumHeight(40)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #007acc;
                    color: white;
                    border-radius: 4px;
                    padding: 8px 15px;
                }

                QPushButton:hover {
                    background-color: #168ad2;
                }
            """)

        button_layout.addWidget(self.new_project_btn)
        button_layout.addWidget(self.open_folder_btn)

        description = QLabel(
            "Create a new project or open an existing folder "
            "to start coding."
        )

        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet("color: #777777;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        layout.addSpacing(10)
        layout.addWidget(description)
