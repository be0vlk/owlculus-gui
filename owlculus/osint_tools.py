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
    def __init__(self, case_number=""):
        try:
            self.case_folder_path = Path(load_config("paths.base_path")) / case_number
        except TypeError:
            RunToolsDialog.exec()

    def run_maigret(self, username):
        maigret_path = load_config("tools.maigret")
        output_folder = self.case_folder_path
        output_folder.mkdir(parents=True, exist_ok=True)
        cmd = [maigret_path, username, "--html", "--folderoutput", str(output_folder)]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                yield output.strip()

        rc = process.poll()
        return rc

    def run_tool(self, tool_name, username):
        """
        Dynamically runs the specified tool.
        """

        method_name = f"run_{tool_name.lower()}"
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            return method(username)
        else:
            raise ValueError(f"No method to run tool named {tool_name}")


class RunToolThread(QThread):
    output_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    completed_signal = pyqtSignal()


    def __init__(self, tool_runner, tool_name, username):
        super().__init__()
        self.tool_runner = tool_runner
        self.tool_name = tool_name
        self.username = username

    def run(self):
        self.status_signal.emit("Running")
        for line in self.tool_runner.run_tool(self.tool_name, self.username):
            self.output_signal.emit(line)
        self.completed_signal.emit()


class RunToolsDialog(QDialog):
    def __init__(self, tool_runner=None, parent=None):
        super().__init__(parent)

        if tool_runner is None:
            tool_runner = ToolRunner()
        self.tool_runner = tool_runner
        self.setWindowTitle("Run Tools")
        self.resize(600, 400)
        self.db_path = Path(load_config("paths.cases_db_path")) / "cases.db"
        self.base_path = Path(load_config("paths.base_path"))
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

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.on_run_button_clicked)
        layout.addWidget(self.run_button)

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
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()      
 
        cursor.execute("SELECT case_number FROM cases")
        case_numbers = [row[0] for row in cursor.fetchall()]
        conn.close()
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

        # Fetch the username if the selected tool is Maigret
        # TODO: Make this not bad
        if selected_tool == "Maigret":
            username, ok = QInputDialog.getText(self, "Input", "Enter the username:")
            if not ok:
                print("[!] Operation cancelled by the user.")
                return
        else:
            pass # Add other tools here

        if hasattr(self, "case_combo"):
            selected_case = self.case_combo.currentText()
        else:
            selected_case = self.selected_case

        self.tool_runner = ToolRunner(self.base_path / selected_case)
        
        self.thread = RunToolThread(self.tool_runner, selected_tool, username)
        
        # Connect the signals after thread instance is created
        self.thread.status_signal.connect(self.update_status)
        self.thread.output_signal.connect(self.update_output)
        self.thread.completed_signal.connect(self.tool_completed)

        self.thread.start()

    def closeEvent(self, event):
        if hasattr(self, "thread") and isinstance(self.thread, QThread) and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(5000):  # 5 seconds timeout
                print("[!] Thread didn't stop in time.")
        event.accept()
