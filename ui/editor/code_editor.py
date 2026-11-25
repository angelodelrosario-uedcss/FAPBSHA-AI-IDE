
import re

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QTextFormat,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)


class PythonHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        def add_rule(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))

            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)

            if italic:
                fmt.setFontItalic(True)

            self.rules.append((re.compile(pattern), fmt))

        # Python keywords
        keywords = (
            "False None True and as assert async await break "
            "class continue def del elif else except finally "
            "for from global if import in is lambda nonlocal "
            "not or pass raise return try while with yield"
        ).split()

        for keyword in keywords:
            add_rule(rf"\b{keyword}\b", "#569CD6", bold=True)

        # Built-in functions
        builtins = (
            "print len range str int float list dict set "
            "tuple bool type super open input enumerate zip "
            "map filter sorted sum min max abs round isinstance "
            "hasattr getattr setattr property"
        ).split()

        for name in builtins:
            add_rule(rf"\b{name}\b", "#DCDCAA")

        # Strings
        add_rule(
            r"'([^'\\]|\\.)*'|\"([^\"\\]|\\.)*\"",
            "#CE9178"
        )

        # Numbers
        add_rule(
            r"\b\d+(\.\d+)?\b",
            "#B5CEA8"
        )

        # Function calls
        add_rule(
            r"\b[A-Za-z_]\w*(?=\s*\()",
            "#DCDCAA"
        )

        # Comments
        add_rule(
            r"#[^\n]*",
            "#6A9955",
            italic=True
        )

        # Decorators
        add_rule(
            r"@[A-Za-z_]\w*",
            "#C586C0"
        )

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    fmt
                )


class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.paint_line_numbers(event)


class CodeEditor(QPlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.line_number_area = LineNumberArea(self)

        self.setFont(QFont("Consolas", 11))

        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * 4
        )

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
                padding: 5px;
            }
        """)

        self.highlighter = PythonHighlighter(self.document())

        self.blockCountChanged.connect(
            self.update_line_number_width
        )

        self.updateRequest.connect(
            self.update_line_number_area
        )

        self.cursorPositionChanged.connect(
            self.highlight_current_line
        )

        self.update_line_number_width(0)
        self.highlight_current_line()

    # -----------------------------
    # LINE NUMBERS
    # -----------------------------

    def line_number_width(self):
        digits = max(
            2,
            len(str(max(1, self.blockCount())))
        )

        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_width(self, _):
        self.setViewportMargins(
            self.line_number_width(), 0, 0, 0
        )

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0,
                rect.y(),
                self.line_number_area.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        rect = self.contentsRect()

        self.line_number_area.setGeometry(
            QRect(
                rect.left(),
                rect.top(),
                self.line_number_width(),
                rect.height()
            )
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)

        painter.fillRect(
            event.rect(),
            QColor("#1e1e1e")
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )

        bottom = top + int(
            self.blockBoundingRect(block).height()
        )

        while block.isValid() and top <= event.rect().bottom():

            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                painter.setPen(QColor("#858585"))

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()
            top = bottom

            if block.isValid():
                bottom = top + int(
                    self.blockBoundingRect(block).height()
                )

            block_number += 1

    # -----------------------------
    # CURRENT LINE HIGHLIGHT
    # -----------------------------

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            selection.format.setBackground(
                QColor("#2A2D2E")
            )

            selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection,
                True
            )

            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    # -----------------------------
    # AUTOMATIC INDENTATION
    # -----------------------------

    def keyPressEvent(self, event):

        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter
        ):
            cursor = self.textCursor()
            current_line = cursor.block().text()

            match = re.match(r"^\s*", current_line)
            indentation = match.group() if match else ""

            extra = ""

            if current_line.rstrip().endswith(":"):
                extra = "    "

            super().keyPressEvent(event)

            self.insertPlainText(indentation + extra)
            return

        # Insert four spaces when Tab is pressed
        if event.key() == Qt.Key.Key_Tab:

            if self.textCursor().hasSelection():
                super().keyPressEvent(event)
            else:
                self.insertPlainText("    ")

            return

        super().keyPressEvent(event)
