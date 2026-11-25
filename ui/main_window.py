
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QDir, QProcess
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton,
    QTreeView, QFileSystemModel,
    QTabWidget, QTextEdit, QSplitter,
    QFileDialog, QMessageBox, QStatusBar,
    QInputDialog, QLineEdit, QToolBar
)

from ui.welcome_widget import WelcomeWidget
from ui.editor.code_editor import CodeEditor
from ui.editor.find_replace import FindReplaceDialog
from ui.execution.python_runner import PythonRunner
from ui.terminal.terminal_widget import TerminalWidget

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("FAPBSH AI IDE")
        self.resize(1250, 780)
        self.setMinimumSize(900, 600)
        self.showMaximized()

        self.project_path = None

        # Stores editor information for each tab
        self.documents = {}

        # Python execution manager
        self.python_runner = PythonRunner(self)
        self.python_runner.output_received.connect(
            self.display_program_output
        )
        self.python_runner.error_received.connect(
            self.display_program_error
        )
        self.python_runner.process_started.connect(
            self.on_python_started
        )
        self.python_runner.process_finished.connect(
            self.on_python_finished
        )
        self.python_runner.process_error.connect(
            self.on_python_error
        )

        self.setup_menu()
        self.setup_toolbar()
        self.setup_interface()
        self.setup_statusbar()

    # =================================
    # MENU BAR
    # =================================

    def setup_menu(self):

        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        self.add_action(
            file_menu, "New File",
            "Ctrl+N", self.new_file
        )

        self.add_action(
            file_menu, "Open File",
            "Ctrl+O", self.open_file
        )

        self.add_action(
            file_menu, "Open Folder",
            "Ctrl+Shift+O", self.open_folder
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "Save",
            "Ctrl+S", self.save_file
        )

        self.add_action(
            file_menu, "Save As",
            "Ctrl+Shift+S", self.save_file_as
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "New Project",
            None, self.new_project
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "Exit",
            "Alt+F4", self.close
        )

        edit_menu = menubar.addMenu("Edit")

        self.add_action(
            edit_menu, "Undo",
            "Ctrl+Z", self.editor_command,
            "undo"
        )

        self.add_action(
            edit_menu, "Redo",
            "Ctrl+Y", self.editor_command,
            "redo"
        )

        edit_menu.addSeparator()

        self.add_action(
            edit_menu, "Cut",
            "Ctrl+X", self.editor_command,
            "cut"
        )

        self.add_action(
            edit_menu, "Copy",
            "Ctrl+C", self.editor_command,
            "copy"
        )

        self.add_action(
            edit_menu, "Paste",
            "Ctrl+V", self.editor_command,
            "paste"
        )

        edit_menu.addSeparator()

        self.add_action(
            edit_menu, "Find and Replace",
            "Ctrl+F", self.find_replace
        )

        view_menu = menubar.addMenu("View")

        self.add_action(
            view_menu, "Toggle Explorer",
            None, self.toggle_sidebar
        )

        self.add_action(
            view_menu, "Toggle Bottom Panel",
            None, self.toggle_bottom_panel
        )

        help_menu = menubar.addMenu("Help")

        self.add_action(
            help_menu, "About FAPBSH AI IDE",
            None, self.show_about
        )

    def add_action(
        self, menu, title, shortcut,
        callback, *args
    ):

        action = QAction(title, self)

        if shortcut:
            action.setShortcut(
                QKeySequence(shortcut)
            )

        action.triggered.connect(
            lambda checked=False:
            callback(*args)
        )

        menu.addAction(action)

        return action

    # =================================
    # PYTHON EXECUTION TOOLBAR
    # =================================

    def setup_toolbar(self):

        toolbar = QToolBar("Python Execution")
        toolbar.setMovable(False)
        self.addToolBar(
            Qt.ToolBarArea.TopToolBarArea,
            toolbar
        )

        self.run_action = QAction("▶ Run Python", self)
        self.run_action.setShortcut(QKeySequence("F5"))
        self.run_action.triggered.connect(
            self.run_python_file
        )
        toolbar.addAction(self.run_action)

        self.stop_action = QAction("■ Stop", self)
        self.stop_action.setShortcut(QKeySequence("Shift+F5"))
        self.stop_action.triggered.connect(
            self.stop_python_file
        )
        self.stop_action.setEnabled(False)
        toolbar.addAction(self.stop_action)

    # =================================
    # PYTHON EXECUTION
    # =================================

    def append_console(self, text):

        self.terminal.moveCursor(
            QTextCursor.MoveOperation.End
        )
        self.terminal.insertPlainText(text)
        self.terminal.ensureCursorVisible()

    def run_python_file(self):

        editor = self.current_editor()

        if not editor:
            QMessageBox.information(
                self,
                "Run Python",
                "Please open a Python file first."
            )
            return

        path = self.documents.get(editor)

        if not path:
            self.save_file_as()
            path = self.documents.get(editor)

            if not path:
                return

        # Save modified content before execution.
        if editor.document().isModified():
            self.write_file(editor, path)

            if editor.document().isModified():
                return

        file_path = Path(path).resolve()

        if not file_path.is_file():
            QMessageBox.warning(
                self,
                "File Not Found",
                "The selected file does not exist."
            )
            return

        if file_path.suffix.lower() != ".py":
            QMessageBox.warning(
                self,
                "Invalid File",
                "Only Python (.py) files can be executed."
            )
            return

        if (
            self.python_runner.process.state()
            != QProcess.ProcessState.NotRunning
        ):
            QMessageBox.warning(
                self,
                "Program Running",
                "Stop the current program first."
            )
            return

        self.terminal.clear()
        self.bottom_panel.setCurrentWidget(
            self.terminal_container
        )
        self.bottom_panel.setVisible(True)

        self.append_console(
            f"Running: {file_path.name}\n"
            f"Interpreter: {sys.executable}\n\n"
        )

        self.status_message.setText(
            "Starting Python program..."
        )

        try:
            self.python_runner.run(str(file_path))

        except (OSError, RuntimeError) as error:
            self.append_console(
                f"\n[ERROR] {error}\n"
            )
            self.status_message.setText(
                "Unable to execute Python program"
            )

    def stop_python_file(self):

        if (
            self.python_runner.process.state()
            != QProcess.ProcessState.NotRunning
        ):
            self.append_console(
                "\n[STOP] Stopping Python program...\n"
            )
            self.python_runner.stop()

    def send_terminal_input(self):

        text = self.terminal_input.text()

        if (
            self.python_runner.process.state()
            != QProcess.ProcessState.Running
        ):
            return

        self.append_console(text + "\n")
        self.python_runner.send_input(text + "\n")
        self.terminal_input.clear()

    def display_program_output(self, text):
        self.append_console(text)

    def display_program_error(self, text):
        self.append_console(text)

    def on_python_started(self):

        self.terminal_input.setEnabled(True)
        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)

        self.status_message.setText(
            "Python program is running..."
        )

        self.terminal_input.setFocus()

    def on_python_finished(self, exit_code, status):

        self.terminal_input.setEnabled(False)
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)

        self.append_console(
            f"\n\nProcess finished with exit code "
            f"{exit_code} ({status}).\n"
        )

        self.status_message.setText(
            f"Execution finished: exit code {exit_code}"
        )

    def on_python_error(self, message):

        self.terminal_input.setEnabled(False)
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)

        self.append_console(
            f"\n[EXECUTION ERROR] {message}\n"
        )

        self.status_message.setText(
            "Python execution error"
        )

    # =================================
    # MAIN INTERFACE
    # =================================

    def setup_interface(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(38)
        header.setStyleSheet(
            "background-color: #323233;"
        )

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        logo = QLabel("FAPBSH AI IDE")
        logo.setStyleSheet(
            "font-weight: bold; color: #007acc;"
        )

        header_layout.addWidget(logo)
        header_layout.addSpacing(20)
        header_layout.addWidget(
            QLabel("Python Development Environment")
        )
        header_layout.addStretch()

        main_layout.addWidget(header)

        # Body
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Activity bar
        self.activity_bar = QWidget()
        self.activity_bar.setFixedWidth(50)
        self.activity_bar.setStyleSheet(
            "background-color: #333333;"
        )

        activity_layout = QVBoxLayout(self.activity_bar)
        activity_layout.setContentsMargins(0, 10, 0, 10)

        self.activity_buttons = []

        activities = [
            ("▤", "Explorer"),
            ("⌕", "Search"),
            ("◇", "Extensions"),
            ("⚙", "Settings")
        ]

        for symbol, name in activities:

            button = QPushButton(symbol)
            button.setCheckable(True)
            button.setToolTip(name)
            button.setFixedSize(50, 45)

            button.clicked.connect(
                lambda checked, n=name:
                self.activity_selected(n)
            )

            activity_layout.addWidget(button)
            self.activity_buttons.append(button)

        self.activity_buttons[0].setChecked(True)
        activity_layout.addStretch()

        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet(
            "background-color: #252526;"
        )

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 10, 0, 0)

        self.sidebar_title = QLabel("  EXPLORER")
        sidebar_layout.addWidget(self.sidebar_title)

        self.project_label = QLabel(
            "  NO FOLDER OPENED"
        )

        self.project_label.setStyleSheet(
            "color: #888888; padding: 10px;"
        )

        sidebar_layout.addWidget(self.project_label)

        self.file_model = QFileSystemModel()

        self.file_model.setFilter(
            QDir.Filter.AllEntries |
            QDir.Filter.NoDotAndDotDot
        )

        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.setHeaderHidden(True)

        for column in range(1, 4):
            self.file_tree.hideColumn(column)

        self.file_tree.doubleClicked.connect(
            self.open_selected_file
        )

        sidebar_layout.addWidget(self.file_tree)

        # Workspace
        self.workspace = QWidget()
        workspace_layout = QVBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        self.splitter = QSplitter(
            Qt.Orientation.Vertical
        )

        # Editor tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.currentChanged.connect(
            self.update_editor_status
        )

        self.editor_tabs.tabCloseRequested.connect(
            self.close_tab
        )

        self.editor_tabs.setDocumentMode(True)

        self.welcome = WelcomeWidget()

        self.welcome.open_folder_btn.clicked.connect(
            self.open_folder
        )

        self.welcome.new_project_btn.clicked.connect(
            self.new_project
        )

        self.editor_tabs.addTab(
            self.welcome, "Welcome"
        )

        self.splitter.addWidget(self.editor_tabs)

        # Bottom panel
        self.bottom_panel = QTabWidget()
        self.bottom_panel.setMinimumHeight(100)
        self.bottom_panel.setMaximumHeight(250)

        self.problems = QTextEdit()
        self.problems.setReadOnly(True)
        self.problems.setPlaceholderText(
            "No problems to display."
        )

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Program output will appear here."
        )

        # Python execution terminal
        self.terminal_container = QWidget()
        terminal_layout = QVBoxLayout(self.terminal_container)
        terminal_layout.setContentsMargins(5, 5, 5, 5)
        terminal_layout.setSpacing(5)

        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setPlaceholderText(
            "Python execution output will appear here."
        )
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)

        self.terminal_input = QLineEdit()

        self.terminal_input.setPlaceholderText(
            "Type your input here and press Enter..."
        )

        self.terminal_input.setFixedHeight(35)

        self.terminal_input.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                color: #ffffff;
                border: 1px solid #007acc;
                padding: 5px;
                font-family: Consolas;
                font-size: 10pt;
            }

            QLineEdit:disabled {
                background-color: #333333;
                color: #777777;
                border: 1px solid #444444;
            }
        """)

        self.terminal_input.setEnabled(False)

        self.terminal_input.returnPressed.connect(
            self.send_terminal_input
        )

        terminal_layout.addWidget(self.terminal)
        terminal_layout.addWidget(self.terminal_input)

        self.bottom_panel.addTab(
            self.problems, "Problems"
        )

        self.bottom_panel.addTab(
            self.output, "Output"
        )

        self.bottom_panel.addTab(
            self.terminal_container, "Python Output"
        )

        self.system_terminal = TerminalWidget(
            self,
            working_directory=self.project_path or Path.cwd()
        )

        self.bottom_panel.addTab(
            self.system_terminal, "Terminal"
        )

        self.splitter.addWidget(self.bottom_panel)
        self.splitter.setSizes([550, 180])

        workspace_layout.addWidget(self.splitter)

        body_layout.addWidget(self.activity_bar)
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.workspace)

        main_layout.addWidget(body)


    # =================================
    # STATUS BAR
    # =================================

    def setup_statusbar(self):

        status = QStatusBar()
        self.setStatusBar(status)

        self.status_message = QLabel("Ready")
        self.cursor_status = QLabel("Ln 1, Col 1")

        status.addWidget(self.status_message)
        status.addPermanentWidget(self.cursor_status)
        status.addPermanentWidget(QLabel("UTF-8"))
        status.addPermanentWidget(QLabel("Python"))

    def update_editor_status(self, index):

        editor = self.current_editor()

        if editor:
            cursor = editor.textCursor()

            self.cursor_status.setText(
                f"Ln {cursor.blockNumber() + 1}, "
                f"Col {cursor.positionInBlock() + 1}"
            )

    # =================================
    # EDITOR HELPERS
    # =================================

    def current_editor(self):

        widget = self.editor_tabs.currentWidget()

        if isinstance(widget, CodeEditor):
            return widget

        return None

    def current_path(self):

        editor = self.current_editor()

        if editor:
            return self.documents.get(editor)

        return None

    def create_editor(self, path=None, content=""):

        # Remove welcome tab when creating first editor
        welcome_index = self.editor_tabs.indexOf(
            self.welcome
        )

        if welcome_index != -1:
            self.editor_tabs.removeTab(welcome_index)

        editor = CodeEditor()

        editor.setPlainText(content)

        if path:
            editor.document().setModified(False)

        editor.cursorPositionChanged.connect(
            lambda: self.update_editor_status(
                self.editor_tabs.indexOf(editor)
            )
        )

        editor.textChanged.connect(
            lambda: self.update_tab_title(editor)
        )

        self.documents[editor] = path

        name = Path(path).name if path else "Untitled"

        index = self.editor_tabs.addTab(
            editor, name
        )

        self.editor_tabs.setCurrentIndex(index)

        self.update_tab_title(editor)

        return editor

    def update_tab_title(self, editor):

        index = self.editor_tabs.indexOf(editor)

        if index == -1:
            return

        path = self.documents.get(editor)

        name = Path(path).name if path else "Untitled"

        if editor.document().isModified():
            name = "*" + name

        self.editor_tabs.setTabText(index, name)

    # =================================
    # NEW FILE
    # =================================

    def new_file(self):

        self.create_editor()

        self.status_message.setText(
            "New file created"
        )

    # =================================
    # OPEN FILE
    # =================================

    def open_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Python File",
            str(Path.home()),
            "Python Files (*.py);;All Files (*.*)"
        )

        if path:
            self.load_file(path)

    def load_file(self, path):

        path = str(Path(path).resolve())

        # Check whether file is already open
        for editor, existing_path in self.documents.items():

            if existing_path == path:
                self.editor_tabs.setCurrentWidget(editor)
                return

        try:
            content = Path(path).read_text(
                encoding="utf-8"
            )

            self.create_editor(path, content)

            self.status_message.setText(
                f"Opened: {path}"
            )

        except (OSError, UnicodeError) as error:

            QMessageBox.critical(
                self,
                "Open Error",
                str(error)
            )

    # =================================
    # SAVE FILE
    # =================================

    def save_file(self):

        editor = self.current_editor()

        if not editor:
            return

        path = self.documents.get(editor)

        if not path:
            self.save_file_as()
            return

        self.write_file(editor, path)

    def save_file_as(self):

        editor = self.current_editor()

        if not editor:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Python File",
            str(Path.home() / "untitled.py"),
            "Python Files (*.py);;All Files (*.*)"
        )

        if not path:
            return

        if not Path(path).suffix:
            path += ".py"

        # Prevent overwriting another open document
        resolved_path = str(Path(path).resolve())

        for other_editor, other_path in self.documents.items():

            if other_editor is not editor and other_path == resolved_path:

                QMessageBox.warning(
                    self,
                    "File Already Open",
                    "This file is already open in another tab."
                )

                self.editor_tabs.setCurrentWidget(other_editor)
                return

        self.documents[editor] = resolved_path

        self.write_file(editor, resolved_path)

    def write_file(self, editor, path):

        try:
            Path(path).write_text(
                editor.toPlainText(),
                encoding="utf-8"
            )

            editor.document().setModified(False)

            self.update_tab_title(editor)

            self.status_message.setText(
                f"Saved: {path}"
            )

        except OSError as error:

            QMessageBox.critical(
                self,
                "Save Error",
                str(error)
            )

    # =================================
    # CLOSE TAB
    # =================================

    def close_tab(self, index):

        widget = self.editor_tabs.widget(index)

        if widget == self.welcome:
            return

        if isinstance(widget, CodeEditor):

            if widget.document().isModified():

                name = self.editor_tabs.tabText(index)

                answer = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Save changes to {name}?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )

                if answer == QMessageBox.StandardButton.Cancel:
                    return

                if answer == QMessageBox.StandardButton.Save:

                    self.editor_tabs.setCurrentIndex(index)

                    if not self.documents.get(widget):
                        self.save_file_as()
                    else:
                        self.save_file()

                    if widget.document().isModified():
                        return

            self.documents.pop(widget, None)

        self.editor_tabs.removeTab(index)
        widget.deleteLater()

        if self.editor_tabs.count() == 0:
            self.show_welcome()

    def show_welcome(self):

        if self.editor_tabs.count() == 0:

            self.editor_tabs.addTab(
                self.welcome, "Welcome"
            )

    # =================================
    # FILE EXPLORER
    # =================================

    def open_selected_file(self, index):

        path = self.file_model.filePath(index)

        if Path(path).is_file():
            self.load_file(path)

    def open_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Project Folder",
            str(Path.home())
        )

        if folder:
            self.load_project(folder)


    def load_project(self, folder):

        folder = str(Path(folder).resolve())

        if not Path(folder).is_dir():
            QMessageBox.warning(
                self,
                "Invalid Project",
                "The selected project folder does not exist."
            )
            return

        # Store the currently opened project
        self.project_path = folder

        # Update integrated terminal directory
        if hasattr(self, "system_terminal"):
            self.system_terminal.set_working_directory(folder)

        root_index = self.file_model.setRootPath(folder)

        self.file_tree.setRootIndex(root_index)

        self.project_label.setText(
            "  " + Path(folder).name.upper()
        )

        self.status_message.setText(
            f"Project opened: {folder}"
        )

        self.activity_selected("Explorer")

    def new_project(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Project Location",
            str(Path.home())
        )

        if not folder:
            return

        name, accepted = QInputDialog.getText(
            self,
            "New Project",
            "Enter project name:"
        )

        if not accepted or not name.strip():
            return

        if name in (".", "..") or Path(name).name != name:
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Enter a valid project folder name."
            )
            return

        project = Path(folder) / name

        try:
            project.mkdir(
                parents=True,
                exist_ok=False
            )

            main_file = project / "main.py"

            main_file.write_text(
                'print("Hello from FAPBSH AI IDE!")\n',
                encoding="utf-8"
            )

            self.load_project(str(project))
            self.load_file(str(main_file))

        except FileExistsError:

            QMessageBox.warning(
                self,
                "Project Exists",
                "A folder with that name already exists."
            )

        except OSError as error:

            QMessageBox.critical(
                self,
                "Project Error",
                str(error)
            )

    # =================================
    # FIND AND REPLACE
    # =================================

    def find_replace(self):

        editor = self.current_editor()

        if not editor:
            return

        dialog = FindReplaceDialog(
            editor, self
        )

        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    # =================================
    # EDIT COMMANDS
    # =================================

    def editor_command(self, command):

        editor = self.current_editor()

        if editor:
            getattr(editor, command)()

    # =================================
    # ACTIVITY BAR
    # =================================

    def activity_selected(self, name):

        for button in self.activity_buttons:

            button.setChecked(
                button.toolTip() == name
            )

        self.sidebar.setVisible(True)

        self.sidebar_title.setText(
            "  " + name.upper()
        )

        if name == "Explorer":

            self.project_label.setText(
                "  " + (
                    Path(self.project_path).name.upper()
                    if self.project_path
                    else "NO FOLDER OPENED"
                )
            )

        else:

            self.project_label.setText(
                "  " + name.upper() + " COMING SOON"
            )

    # =================================
    # VIEW
    # =================================

    def toggle_sidebar(self):

        self.sidebar.setVisible(
            not self.sidebar.isVisible()
        )

    def toggle_bottom_panel(self):

        self.bottom_panel.setVisible(
            not self.bottom_panel.isVisible()
        )

    # =================================
    # ABOUT
    # =================================

    def show_about(self):

        QMessageBox.about(
            self,
            "About FAPBSH AI IDE",
            """
            <h2>FAPBSH AI IDE</h2>
            <p>Custom Python Integrated Development Environment.</p>
            <p>Version 1.0</p>
            <p>Developed using Python and PySide6.</p>
            """
        )

    # =================================
    # APPLICATION CLOSE
    # =================================

    def closeEvent(self, event):

        for index in range(self.editor_tabs.count()):

            widget = self.editor_tabs.widget(index)

            if not isinstance(widget, CodeEditor):
                continue

            if widget.document().isModified():

                self.editor_tabs.setCurrentWidget(widget)

                name = self.editor_tabs.tabText(
                    self.editor_tabs.currentIndex()
                )

                answer = QMessageBox.question(
                    self,
                    "Unsaved Changes",
                    f"Save changes to {name} before exiting?",
                    QMessageBox.StandardButton.Save |
                    QMessageBox.StandardButton.Discard |
                    QMessageBox.StandardButton.Cancel
                )

                if answer == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return

                if answer == QMessageBox.StandardButton.Save:

                    if not self.documents.get(widget):
                        self.save_file_as()
                    else:
                        self.save_file()

                    if widget.document().isModified():
                        event.ignore()
                        return

        if (
            self.python_runner.process.state()
            != QProcess.ProcessState.NotRunning
        ):
            self.python_runner.stop()

        if hasattr(self, "system_terminal"):
            self.system_terminal.stop()

        event.accept()
