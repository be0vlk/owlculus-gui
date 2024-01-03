"""
Module containing the actual commands to run various tools.
"""

import subprocess
import sqlite3
from settings import load_config
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import *


class ToolRunner:
    """
    Manages running various external tools.
    """

    def __init__(self, case_number=""):
        self.case_folder_path = self._get_case_folder_path(case_number)
        self.cancelled = False

    def _get_case_folder_path(self, case_number):
        """ Get the path to the case folder. """
        try:
            return Path(load_config("paths.base_path")) / case_number
        except TypeError:
            RunToolsDialog.exec()
            return None

    def run_tool(self, tool_name, args):
        tool_config = load_config(f"tools.{tool_name}".lower())
        if not tool_config:
            raise ValueError(f"No configuration for tool named {tool_name}")

        tool_path = tool_config.get("path")
        flag_args = tool_config.get("flag_args", [])
        positional_args = tool_config.get("positional_args", [])
        
        output_folder = self.case_folder_path
        output_folder.mkdir(parents=True, exist_ok=True)

        cmd = [tool_path] + flag_args + [str(output_folder)]
        for arg in positional_args:
            if arg in args:
                cmd.append(args[arg])  # Append positional argument directly
        for arg, value in args.items():
            if arg not in positional_args:
                cmd.append(f"--{arg}")  # Append flag-based arguments
                cmd.append(value)

        return self._execute_command(cmd)


    def cancel(self):
        """
        Cancel the current tool run.
        """

        self.cancelled = True

    def _execute_command(self, command):
        """
        Execute a system command and yield the output.
        """

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for output in iter(process.stdout.readline, ''):
            if self.cancelled:  # Check the cancellation flag
                process.terminate()
                break
            yield output.strip()
        return process.poll()

class RunToolThread(QThread):
    """
    Thread class for running tools without freezing the GUI.
    """

    output_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    completed_signal = pyqtSignal()

    def __init__(self, tool_runner, tool_name, args):
        super().__init__()
        self.tool_runner = tool_runner
        self.tool_name = tool_name
        self.args = args

    def run(self):
        self.status_signal.emit("Running")
        for line in self.tool_runner.run_tool(self.tool_name, self.args):
            self.output_signal.emit(line)
        if not self.tool_runner.cancelled:
            self.completed_signal.emit()
    
    def cancel(self):
        """
        Cancel the current tool run.
        """

        self.tool_runner.cancel()


class RunToolsDialog(QDialog):
    """
    Dialog for running tools within the GUI. 
    """

    def __init__(self, tool_runner=None, parent=None):
        super().__init__(parent)
        self.tool_runner = tool_runner or ToolRunner()
        self.setWindowTitle("Run Tools")
        self.resize(600, 400)
        self.db_path = Path(load_config("paths.cases_db_path")) / "cases.db"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(sorted(["Maigret"]))
        layout.addWidget(QLabel("Select Tool:"))
        layout.addWidget(self.tool_combo)

        # Add a status label and progress bar for the running tool
        self.status_label = QLabel("Status: Idle")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit(readOnly=True)
        layout.addWidget(self.output_text)

        # Create a QHBoxLayout for the buttons
        button_layout = QHBoxLayout()

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.on_run_button_clicked)
        button_layout.addWidget(self.run_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Always create the combo, but make it invisible by default
        self.case_combo = QComboBox()
        layout.addWidget(QLabel("Select Case:"))
        layout.addWidget(self.case_combo)
        self.case_combo.setVisible(False)

        self.setLayout(layout)  # Set the layout after adding all widgets

    def showEvent(self, event):
        self.fetch_and_update_cases()
        super().showEvent(event)

    def fetch_and_update_cases(self):
        case_list = self.fetch_all_case_numbers()

        # Update the case_combo widget 
        if len(case_list) > 0:
            self.case_combo.clear()
            self.case_combo.addItems(case_list)
            self.case_combo.setVisible(True)
            self.run_button.setEnabled(True)
            self.run_button.setText("Run")
        else:
            self.case_combo.setVisible(False)
            self.run_button.setText("Create a case to enable this tool")
            self.run_button.setEnabled(False)

    def fetch_all_case_numbers(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()      
            cursor.execute("SELECT case_number FROM cases")
            case_numbers = [row[0] for row in cursor.fetchall()]
        return case_numbers
    
    def update_status(self, status):
        """
        Update the status label with the provided status.
        """
        self.status_label.setText(f"Status: {status}")

    def update_output(self, line):
        """
        Append the given line to the output text area.
        """
        self.output_text.append(line)

    def tool_completed(self):
        """
        Update the GUI components when the tool is completed.
        """
        self.status_label.setText("Status: Completed")
        self.progress_bar.setValue(100)

    def on_run_button_clicked(self):
        """
        Handle the logic to be executed when the 'Run' button is clicked.
        """
        selected_tool = self.tool_combo.currentText()

        # Fetch the arguments based on the selected tool
        tool_config = load_config(f"tools.{selected_tool}".lower())
        if not tool_config:
            raise ValueError(f"No configuration for tool named {selected_tool}")

        args = {}
        for arg in tool_config.get("positional_args", []):
            value, ok = QInputDialog.getText(self, "Input", f"Enter the {arg}:")
            if not ok:
                print(f"[!] Operation cancelled by the user.")
                return
            args[arg] = value

        if hasattr(self, "case_combo"):
            selected_case = self.case_combo.currentText()
        else:
            selected_case = self.selected_case

        self.tool_runner = ToolRunner(selected_case)
        
        self.thread = RunToolThread(self.tool_runner, selected_tool, args)
        
        # Connect the signals after thread instance is created
        self.thread.status_signal.connect(self.update_status)
        self.thread.output_signal.connect(self.update_output)
        self.thread.completed_signal.connect(self.tool_completed)

        self.thread.start()

    def on_cancel_button_clicked(self):
        """
        Handle the logic to be executed when the 'Cancel' button is clicked.
        """
        if hasattr(self, "thread") and isinstance(self.thread, QThread) and self.thread.isRunning():
            self.thread.cancel()
            self.status_label.setText("Status: Cancelled")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Tool run cancelled")
            self.progress_bar.setStyleSheet("QProgressBar {background-color: #990000;}")

    def closeEvent(self, event):
        if hasattr(self, "thread") and isinstance(self.thread, QThread) and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(5000):  # 5 seconds timeout
                print("[!] Thread didn't stop in time.")
        event.accept()
