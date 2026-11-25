
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal


class PythonRunner(QObject):

    # Signals
    output_received = Signal(str)
    error_received = Signal(str)

    process_started = Signal()
    process_finished = Signal(int, str)
    process_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.process = QProcess(self)

        # Connect process signals
        self.process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.process.readyReadStandardError.connect(
            self.read_error
        )

        self.process.started.connect(
            self.process_started.emit
        )

        self.process.finished.connect(
            self.on_finished
        )

        self.process.errorOccurred.connect(
            self.on_error
        )

    # -----------------------------
    # RUN PYTHON FILE
    # -----------------------------

    def run(self, file_path):

        if self.process.state() != QProcess.ProcessState.NotRunning:
            raise RuntimeError(
                "A Python program is already running."
            )

        path = Path(file_path).resolve()

        if not path.is_file():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        # Use the Python interpreter running the IDE
        self.process.setProgram(sys.executable)

        # -u enables unbuffered output
        self.process.setArguments([
            "-u",
            str(path)
        ])

        # Set working directory to the script directory
        self.process.setWorkingDirectory(
            str(path.parent)
        )

        self.process.start()

    # -----------------------------
    # READ STANDARD OUTPUT
    # -----------------------------

    def read_output(self):

        data = self.process.readAllStandardOutput()

        output = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if output:
            self.output_received.emit(output)

    # -----------------------------
    # READ ERROR OUTPUT
    # -----------------------------

    def read_error(self):

        data = self.process.readAllStandardError()

        error = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if error:
            self.error_received.emit(error)

    # -----------------------------
    # PROCESS FINISHED
    # -----------------------------

    def on_finished(self, exit_code, exit_status):

        # Read any remaining output
        self.read_output()
        self.read_error()

        status = (
            "Normal"
            if exit_status == QProcess.ExitStatus.NormalExit
            else "Crashed"
        )

        self.process_finished.emit(
            exit_code,
            status
        )

    # -----------------------------
    # PROCESS ERROR
    # -----------------------------

    def on_error(self, error):

        if error == QProcess.ProcessError.FailedToStart:
            self.process_error.emit(
                self.process.errorString()
            )

    # -----------------------------
    # SEND INPUT TO PROGRAM
    # -----------------------------

    def send_input(self, text):

        if self.process.state() == QProcess.ProcessState.Running:
            self.process.write(
                text.encode("utf-8")
            )

    # -----------------------------
    # STOP PYTHON PROGRAM
    # -----------------------------

    def stop(self):

        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
