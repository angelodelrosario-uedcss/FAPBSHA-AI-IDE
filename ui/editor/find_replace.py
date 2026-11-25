
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QMessageBox
)


class FindReplaceDialog(QDialog):

    def __init__(self, editor, parent=None):
        super().__init__(parent)

        self.editor = editor

        self.setWindowTitle("Find and Replace")
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Find:"))

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText(
            "Enter text to find..."
        )

        layout.addWidget(self.find_input)

        layout.addWidget(QLabel("Replace with:"))

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText(
            "Enter replacement text..."
        )

        layout.addWidget(self.replace_input)

        buttons = QHBoxLayout()

        find_button = QPushButton("Find Next")
        replace_button = QPushButton("Replace")
        all_button = QPushButton("Replace All")

        buttons.addWidget(find_button)
        buttons.addWidget(replace_button)
        buttons.addWidget(all_button)

        layout.addLayout(buttons)

        find_button.clicked.connect(self.find_next)
        replace_button.clicked.connect(self.replace_one)
        all_button.clicked.connect(self.replace_all)

    def find_next(self):

        text = self.find_input.text()

        if not text:
            return

        found = self.editor.find(text)

        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(
                cursor.MoveOperation.Start
            )
            self.editor.setTextCursor(cursor)

            found = self.editor.find(text)

        if not found:
            QMessageBox.information(
                self,
                "Find",
                "No matching text found."
            )

    def replace_one(self):

        text = self.find_input.text()

        if not text:
            return

        cursor = self.editor.textCursor()

        if not cursor.hasSelection():
            self.find_next()
            cursor = self.editor.textCursor()

        if cursor.hasSelection() and cursor.selectedText() == text:
            cursor.insertText(
                self.replace_input.text()
            )

        self.find_next()

    def replace_all(self):

        old_text = self.find_input.text()
        new_text = self.replace_input.text()

        if not old_text:
            return

        content = self.editor.toPlainText()

        count = content.count(old_text)

        if count == 0:
            QMessageBox.information(
                self,
                "Replace All",
                "No matching text found."
            )
            return

        updated = content.replace(
            old_text,
            new_text
        )

        self.editor.setPlainText(updated)

        QMessageBox.information(
            self,
            "Replace All",
            f"Successfully replaced {count} occurrence(s)."
        )
