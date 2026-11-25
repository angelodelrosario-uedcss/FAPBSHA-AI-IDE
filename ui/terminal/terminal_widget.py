
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QComboBox,
    QPushButton,
    QLabel,
)


class TerminalInput(QLineEdit):

    history_up = Signal()
    history_down = Signal()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Up:
            self.history_up.emit()
            return

        if event.key() == Qt.Key.Key_Down:
            self.history_down.emit()
            return

        super().keyPressEvent(event)


class TerminalWidget(QWidget):

    def __init__(self, parent=None, working_directory=None):
        super().__init__(parent)

        self.working_directory = str(
            Path(working_directory or Path.cwd()).resolve()
        )

        self.process = QProcess(self)

        self.process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )

        self.command_history = []
        self.history_index = 0

        self.switching_shell = False

        self.process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.process.started.connect(
            self.on_started
        )

        self.process.finished.connect(
            self.on_finished
        )

        self.process.errorOccurred.connect(
            self.on_process_error
        )

        self.setup_ui()

        self.append_output(
            "FAPBSH AI IDE Integrated Terminal\n"
            f"Python interpreter: {sys.executable}\n"
            f"Python version: {sys.version.split()[0]}\n"
            f"Working directory: {self.working_directory}\n\n"
        )

        self.start_shell()

    # =================================
    # USER INTERFACE
    # =================================

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Shell:"))

        self.shell_selector = QComboBox()

        self.shell_selector.addItem(
            "Command Prompt", "cmd"
        )

        self.shell_selector.addItem(
            "PowerShell", "powershell"
        )

        self.shell_selector.currentIndexChanged.connect(
            self.change_shell
        )

        toolbar.addWidget(self.shell_selector)

        self.directory_label = QLabel(
            self.working_directory
        )

        self.directory_label.setToolTip(
            self.working_directory
        )

        self.directory_label.setStyleSheet(
            "color: #999999;"
        )

        toolbar.addWidget(self.directory_label, 1)

        self.clear_button = QPushButton("Clear")

        self.clear_button.clicked.connect(
            self.clear_terminal
        )

        toolbar.addWidget(self.clear_button)

        self.restart_button = QPushButton("Restart")

        self.restart_button.clicked.connect(
            self.restart_shell
        )

        toolbar.addWidget(self.restart_button)

        layout.addLayout(toolbar)

        # Terminal output
        self.output = QTextEdit()

        self.output.setReadOnly(True)

        self.output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)

        layout.addWidget(self.output, 1)

        # Terminal command input
        self.command_input = TerminalInput()

        self.command_input.setEnabled(False)

        self.command_input.setPlaceholderText(
            "Type a command and press Enter..."
        )

        self.command_input.setFixedHeight(35)

        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #007acc;
                padding: 7px;
                font-family: Consolas;
                font-size: 10pt;
            }

            QLineEdit:focus {
                border: 1px solid #00aaff;
            }

            QLineEdit:disabled {
                color: #777777;
                background-color: #333333;
                border: 1px solid #444444;
            }
        """)

        self.command_input.returnPressed.connect(
            self.execute_command
        )

        self.command_input.history_up.connect(
            self.show_previous_command
        )

        self.command_input.history_down.connect(
            self.show_next_command
        )

        layout.addWidget(self.command_input)

    # =================================
    # SHELL MANAGEMENT
    # =================================

    def selected_shell(self):

        return self.shell_selector.currentData()

    def start_shell(self):

        if self.process.state() != QProcess.ProcessState.NotRunning:
            return

        if self.selected_shell() == "powershell":

            program = "powershell.exe"

            arguments = [
                "-NoLogo",
                "-NoProfile",
                "-NoExit"
            ]

        else:

            program = "cmd.exe"

            arguments = ["/Q", "/D"]

        self.process.setWorkingDirectory(
            self.working_directory
        )

        self.process.setProgram(program)
        self.process.setArguments(arguments)

        self.command_input.setEnabled(False)

        self.append_output(
            f"\n[Starting {self.shell_selector.currentText()}...]\n"
        )

        self.process.start()

    def on_started(self):

        self.command_input.setEnabled(True)
        self.command_input.setReadOnly(False)
        self.command_input.setFocus()

        if self.selected_shell() == "cmd":

            self.process.write(
                b"chcp 65001>nul\r\n"
            )

            self.process.write(
                b"prompt $P$G\r\n"
            )

        else:

            commands = (
                "$OutputEncoding = "
                "[Console]::OutputEncoding = "
                "New-Object System.Text.UTF8Encoding;"
                "Set-Location -LiteralPath "
                f"'{self.working_directory.replace(chr(39), chr(39) * 2)}'"
                "\r\n"
            )

            self.process.write(
                commands.encode("utf-8")
            )

        self.append_output(
            "\n[Terminal ready.]\n"
        )

    def restart_shell(self):

        if self.process.state() != QProcess.ProcessState.NotRunning:

            self.switching_shell = True
            self.process.kill()
            return

        self.start_shell()

    def change_shell(self):

        if self.process.state() != QProcess.ProcessState.NotRunning:

            self.switching_shell = True
            self.process.kill()
            return

        self.start_shell()

    # =================================
    # COMMAND EXECUTION
    # =================================

    def execute_command(self):

        command = self.command_input.text().strip()

        if not command:
            return

        if self.process.state() != QProcess.ProcessState.Running:

            self.append_output(
                "\n[Terminal is not running. Click Restart.]\n"
            )

            return

        self.command_history.append(command)

        self.history_index = len(
            self.command_history
        )

        self.append_output(
            f"> {command}\n"
        )

        self.process.write(
            (command + "\r\n").encode("utf-8")
        )

        self.command_input.clear()
        self.command_input.setFocus()

    # =================================
    # COMMAND HISTORY
    # =================================

    def show_previous_command(self):

        if not self.command_history:
            return

        self.history_index = max(
            0,
            self.history_index - 1
        )

        self.command_input.setText(
            self.command_history[self.history_index]
        )

    def show_next_command(self):

        if not self.command_history:
            return

        self.history_index = min(
            len(self.command_history),
            self.history_index + 1
        )

        if self.history_index == len(self.command_history):

            self.command_input.clear()

        else:

            self.command_input.setText(
                self.command_history[self.history_index]
            )

    # =================================
    # OUTPUT
    # =================================

    def read_output(self):

        data = self.process.readAllStandardOutput()

        text = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if text:
            self.append_output(text)

    def append_output(self, text):

        cursor = self.output.textCursor()

        cursor.movePosition(
            QTextCursor.MoveOperation.End
        )

        self.output.setTextCursor(cursor)

        self.output.insertPlainText(text)

        self.output.ensureCursorVisible()

    def clear_terminal(self):

        self.output.clear()

    # =================================
    # WORKING DIRECTORY
    # =================================

    def set_working_directory(self, directory):

        path = Path(directory).resolve()

        if not path.is_dir():
            return

        self.working_directory = str(path)

        self.directory_label.setText(
            self.working_directory
        )

        self.directory_label.setToolTip(
            self.working_directory
        )

        if self.process.state() != QProcess.ProcessState.Running:

            self.process.setWorkingDirectory(
                self.working_directory
            )

            return

        if self.selected_shell() == "cmd":

            command = (
                f'cd /d "{self.working_directory}"\r\n'
            )

        else:

            escaped = self.working_directory.replace(
                "'", "''"
            )

            command = (
                "Set-Location -LiteralPath "
                f"'{escaped}'\r\n"
            )

        self.process.write(
            command.encode("utf-8")
        )

    # =================================
    # PROCESS EVENTS
    # =================================

    def on_finished(self, exit_code, exit_status):

        self.read_output()

        self.command_input.setEnabled(False)

        if self.switching_shell:

            self.switching_shell = False
            self.start_shell()
            return

        result = (
            "normal exit"
            if exit_status == QProcess.ExitStatus.NormalExit
            else "crashed"
        )

        self.append_output(
            f"\n[Shell ended: {result}, "
            f"exit code {exit_code}. "
            "Click Restart to start it again.]\n"
        )

    def on_process_error(self, error):

        if error == QProcess.ProcessError.FailedToStart:

            self.command_input.setEnabled(False)

            self.switching_shell = False

            self.append_output(
                f"\n[Could not start shell: "
                f"{self.process.errorString()}]\n"
            )

    def stop(self):

        self.switching_shell = False

        if self.process.state() != QProcess.ProcessState.NotRunning:

            self.process.kill()
            self.process.waitForFinished(1000)
