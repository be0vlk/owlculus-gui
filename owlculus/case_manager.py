"""
This module contains all the code for the Case Management system.
Includes Evidence Management functionality.
"""

from PyQt6.QtWidgets import *
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
import sys
from osint_tools import ToolRunner, RunToolThread, RunToolsDialog
from client_manager import ClientManager, ClientDialog
from settings import BASE_PATH, CASES_DB_PATH
import subprocess
import os
import webbrowser
import platform
from datetime import datetime
import sqlite3
import shutil
from pathlib import Path


COMMON_FOLDERS = sorted(["Associates", "Audio", "Documents", "Other", "Social_Media"])
SOCIAL_MEDIA_FOLDERS = sorted([
    "Discord", "Facebook", "Instagram", "LinkedIn", "Reddit",
    "Signal", "Snapchat", "Telegram", "TikTok", "Twitter", "WhatsApp", "YouTube"
])


class CaseManager:
    """
    This class handles the case setup and initializes the database.
    """

    def __init__(self):
        self.db_path = CASES_DB_PATH  # SQLite database path
        self.initialize_db()

    def initialize_db(self):
        if not BASE_PATH.exists():
            BASE_PATH.mkdir(parents=True)

        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON") 
        cursor = conn.cursor()
        
        # Create the cases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE NOT NULL,
                case_type TEXT NOT NULL,
                client_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL
            )
        """)

        conn.commit()
        conn.close()

    def case_number_exists(self, case_number):
        """
        Checks if a case number already exists in the database.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE case_number = ?", (case_number,))
        exists = bool(cursor.fetchone())
        conn.close()
        return exists

    def add_case_number(self, case_number, case_type, client):
        """
        Adds a new case number to the database.
        """

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cases (case_number, case_type, client_id, created_at) VALUES (?, ?, ?, ?)",
            (case_number, case_type, client, current_datetime)
        )

        conn.commit()
        conn.close()

    def setup_case_folder(self, case_name=None, case_type=None, client=None):
        """
        Sets up a new case folder with the given name and type.
        """

        date = datetime.now().strftime("%y%m")
        templates_path = Path(__file__).parent.parent / "templates"

        # Generate a unique case number
        for i in range(1, 100):
            case_number = f"{date}-{str(i).zfill(2)}"
            if not self.case_number_exists(case_number):
                break
        else:
            print("[!] No available case numbers")
            return

        self.add_case_number(case_number, case_type, client)

        # Create the case folder and subdirectories
        case_folder_path = BASE_PATH / (case_name if case_name else case_number)
        if not BASE_PATH.exists():
            BASE_PATH.mkdir(parents=True)
        case_folder_path.mkdir()

        folders = COMMON_FOLDERS.copy()
        if case_type == "Person":
            pass
        elif case_type == "Company":
            folders.extend(sorted(["Domains", "Executives", "Network"]))
        else:
            pass

        for folder in folders:
            (case_folder_path / folder).mkdir()

        for folder in SOCIAL_MEDIA_FOLDERS:
            (case_folder_path / "Social_Media" / folder).mkdir()

        # Define a mapping between template names and their corresponding folders
        template_to_folder = {
            "Notes": "",
            "SOCMINT": "Social_Media",
            "Associates": "Associates",
            # Add more mappings here as needed
        }

        for template_file in templates_path.glob("*.md"):
            template_name = template_file.name.split('.')[0]  # Extract name without extension
            target_folder = template_to_folder.get(template_name, "")

            if template_name == "Notes":
                with open(template_file, "r") as f:
                    notes_content = f.read()

                # Replaces placeholders in the Markdown templates with actual values
                notes_content = notes_content.replace("**Case Number:**", f"**Case Number:** {case_number}")
                notes_content = notes_content.replace("**Case Type:**", f"**Case Type:** {case_type}")
                notes_content = notes_content.replace("**Date:**", f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

                # Write the modified content back to the new case folder
                with open(case_folder_path / "Notes.md", "w") as f:
                    f.write(notes_content)
            else:
                target_path = case_folder_path / target_folder / template_file.name
                shutil.copy(template_file, target_path)

        print(f"[+] Case {case_name or case_number} created")

    def delete_case(self, case_number):
        """
        Deletes a case from the database and the file system.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cases WHERE case_number = ?", (case_number,))
        conn.commit()
        conn.close()

        case_folder_path = BASE_PATH / case_number
        if case_folder_path.exists():
            shutil.rmtree(case_folder_path)

    def rename_case(self, old_case_number, new_case_number):
        """
        Renames a case in the database.
        """

        if self.case_number_exists(new_case_number):
            raise ValueError(f"Case number {new_case_number} already exists.")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("UPDATE cases SET case_number = ? WHERE case_number = ?",
                    (new_case_number, old_case_number))
        rows_affected = cursor.rowcount  # Get the number of rows affected by the update
        conn.commit()
        conn.close()

        old_case_folder_path = BASE_PATH / old_case_number
        new_case_folder_path = BASE_PATH / new_case_number
        if old_case_folder_path.exists():
            old_case_folder_path.rename(new_case_folder_path)

        return rows_affected

    def list_cases(self):
        """
        Lists all cases in the database. Used by the GUI for populating the case list.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_client(self, case_number, new_client):
        """
        Updates the client for a given case number.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("UPDATE cases SET client = ? WHERE case_number = ?", (new_client, case_number))
        conn.commit()
        conn.close()


class EvidenceDialog(QDialog):
    """
    Custom QDialog to display and manage evidence files.
    """

    def __init__(self, case_number, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Evidence")
        self.resize(400, 300)
        self.case_number = case_number

        layout = QVBoxLayout()

        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Evidence")
        self.tree.itemDoubleClicked.connect(self.open_file)
        self.populate_tree(self.get_evidence_files())

        layout.addWidget(self.tree)

        # Add Evidence button
        add_evidence_button = QPushButton("Add Evidence", self)
        add_evidence_button.clicked.connect(self.add_evidence_file)
        layout.addWidget(add_evidence_button)
        
        # Delete Evidence button
        delete_evidence_button = QPushButton("Delete Evidence", self)
        delete_evidence_button.clicked.connect(self.delete_evidence_file)
        layout.addWidget(delete_evidence_button)

        # Close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def populate_tree(self, evidence_files):
        """
        Populate the tree widget with evidence files and folders.
        """
        self.tree.clear()
        for item in sorted(evidence_files.keys()):
            display_text = item
            
            # Check if it's a directory and add a trailing slash for the display name
            # TODO: Use icons instead of slashes
            if isinstance(evidence_files[item], list) or (evidence_files[item] is None and not os.path.splitext(item)[1]):
                display_text += "/"

            evidence_item = QTreeWidgetItem(self.tree)
            evidence_item.setText(0, display_text)
            evidence_item.setData(0, Qt.ItemDataRole.UserRole, item)

            # If the item has files in it
            if evidence_files[item] is not None:
                for file in sorted(evidence_files[item]):
                    child_item = QTreeWidgetItem(evidence_item)
                    child_item.setText(0, file)
                    child_item.setData(0, Qt.ItemDataRole.UserRole, os.path.join(item, file))

    def open_file(self, item):
        """
        Open the selected evidence file.
        """

        relative_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not relative_path:
            print("[!] No file path associated with the item.")
            return

        # Resolve the absolute path using BASE_PATH and the stored case_number
        absolute_path = BASE_PATH / self.case_number / relative_path

        if platform.system() == "Windows":
            os.startfile(absolute_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(absolute_path)])
        else:
            subprocess.Popen(["xdg-open", str(absolute_path)])

    def get_evidence_files(self):
        """
        Retrieve the evidence files and folders for the given case number.
        """
        evidence_dir = BASE_PATH / self.case_number
        evidence_files = {}

        if evidence_dir.exists() and evidence_dir.is_dir():
            for item in sorted(evidence_dir.iterdir()):
                if item.is_dir():
                    # Get all files in the folder
                    files = [f.name for f in sorted(item.iterdir()) if f.is_file()]
                    evidence_files[item.name] = files if files else None
                elif item.is_file():
                    evidence_files[item.name] = None

        return evidence_files

    def add_evidence_file(self):
        """
        Add a new evidence file to the case.
        """

        file_dialog = QFileDialog(self, "Select Evidence File", "", "All Files (*)")
        file_name, _ = file_dialog.getOpenFileName()
        if file_name:
            # Get the currently selected directory in the GUI
            selected_items = self.tree.selectedItems()
            
            # Default to the base directory
            selected_subdirectory = ""
            
            if selected_items:
                selected_item = selected_items[0]
                selected_path = selected_item.data(0, Qt.ItemDataRole.UserRole)
                
                # Check if selected_path is None or a file
                if selected_path and os.path.isfile(BASE_PATH / self.case_number / selected_path):
                    selected_subdirectory = os.path.dirname(selected_path)
                elif selected_path:
                    selected_subdirectory = selected_path
            
            destination_path = BASE_PATH / self.case_number / selected_subdirectory / os.path.basename(file_name)
            shutil.copy(file_name, destination_path)
            print("[+] File added:", destination_path)
            self.populate_tree(self.get_evidence_files())
            
    def delete_evidence_file(self):
        """
        Delete the selected evidence file or folder.
        """

        selected_items = self.tree.selectedItems()

        if not selected_items:
            print("[!] No item selected for deletion.")
            return

        selected_item = selected_items[0]
        relative_path = selected_item.data(0, Qt.ItemDataRole.UserRole)
        absolute_path = BASE_PATH / self.case_number / relative_path

        # Confirmation before deletion
        confirm_msg = QMessageBox.question(self, "Delete Confirmation",
                                        f"Are you sure you want to delete {relative_path}?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm_msg == QMessageBox.StandardButton.Yes:
            if absolute_path.is_file():
                absolute_path.unlink()  # Delete the file
                print(f"[+] Deleted file: {absolute_path}")
            elif absolute_path.is_dir():
                shutil.rmtree(absolute_path)  # Delete the folder and its contents
                print(f"[+] Deleted folder: {absolute_path}")
            self.populate_tree(self.get_evidence_files())  # Refresh the tree
        else:
            print("[*] Deletion cancelled.")


class CustomTableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSortingEnabled(True)

    def edit(self, index, trigger, event):
        # Allow editing for columns 0 (Case Number) and 2 (Client)
        if index.column() in [0, 2]:
            return super().edit(index, trigger, event)
        return False


class NewCaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Case")

        # Case Type ComboBox
        self.case_type_combo = QComboBox()
        self.case_type_combo.addItems(["Person", "Company", "Threat Intel", "Event"])

        # Client ComboBox
        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.on_client_combo_changed)
        self.populate_clients_dropdown()

        # OK and Cancel buttons
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Case Type:"))
        layout.addWidget(self.case_type_combo)
        layout.addWidget(QLabel("Client:"))
        layout.addWidget(self.client_combo)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_clients_dropdown(self):
        """Populate the client dropdown with client names from the database."""
        # Clear the current items
        self.client_combo.clear()

        # Fetch clients from the database
        client_manager = ClientManager()
        clients = client_manager.list_clients()

        # Populate the dropdown
        for client in clients:
            self.client_combo.addItem(client[1], client[0])

        # Add the "Add New Client" option
        self.client_combo.addItem("Add New Client")

    def on_client_combo_changed(self, index):
        """Handle the selection of "Add New Client" from the dropdown."""
        selected_text = self.client_combo.currentText()
        if selected_text == "Add New Client":
            dialog = ClientDialog(self)
            result = dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                new_client_name = dialog.name_input.text()
                # Refresh the dropdown
                self.populate_clients_dropdown()
                # Set the newly added client as the current selection
                index_of_new_client = self.client_combo.findText(new_client_name)
                if index_of_new_client != -1:
                    self.client_combo.setCurrentIndex(index_of_new_client)


    def get_values(self):
        """Retrieve the selected case type and client name."""
        client_name = self.client_combo.currentText()
        if client_name == "Add New Client":
            client_name = ""  # Handle the case where "Add New Client" is still selected
        return self.case_type_combo.currentText(), client_name


class MainLayout(QMainWindow):

    def __init__(self):
        super().__init__()

        self.case_manager = CaseManager()
        menu_bar = QMenuBar()

        # Menu Bar Actions
        github_action = QAction("GitHub", self)
        github_action.triggered.connect(self.open_github)
        menu_bar.addAction(github_action)

        search_action = QAction("Search", self)
        search_action.triggered.connect(self.search_table)
        menu_bar.addAction(search_action)

        self.setMenuBar(menu_bar)

        # Button Layout
        self.table = CustomTableWidget()
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Case Number", "Type", "Client", "Created"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setColumnWidth(0, 200)  # Case Number
        self.table.setColumnWidth(1, 200)  # Type
        self.table.setColumnWidth(2, 200)  # Client
        self.table.setColumnWidth(3, 100)  # Created

        create_case_button = QPushButton("Create Case")
        create_case_button.clicked.connect(self.create_case)
        create_case_button.setToolTip("Create a new case")

        delete_case_button = QPushButton("Delete Case")
        delete_case_button.clicked.connect(self.delete_case)
        delete_case_button.setToolTip("Delete the selected case")

        button_layout = QHBoxLayout()
        button_layout.addWidget(create_case_button)
        button_layout.addWidget(delete_case_button)

        # Main Layout
        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setWindowTitle("Owlculus | Case Manager")
        self.setGeometry(100, 100, 900, 600)

        self.display_cases()

    def handle_item_changed(self, item):
        row = item.row()
        column = item.column()
        case_number = self.case_manager.list_cases()[row][1]

        if column == 0:  # Case Number column
            new_case_number = item.text()

            try:
                self.case_manager.rename_case(case_number, new_case_number)
            except ValueError as e:
                QMessageBox.warning(self, "Warning", str(e))
                item.setText(case_number)  # Reset to old value if rename fails
        elif column == 2:  # Client column
            new_value = item.text()
            self.case_manager.update_client(case_number, new_value)

        # Reconnect the signal
        self.table.itemChanged.connect(self.handle_item_changed)

    def show_context_menu(self, position):
        context_menu = QMenu(self)

        # Get the currently right-clicked row and store its case number
        selected_row = self.table.rowAt(position.y())
        self.current_case_number = self.table.item(selected_row, 0).text()

        open_case_action = QAction("Open Case", self)
        run_tools_action = QAction("Run Tools", self)
        manage_evidence_action = QAction("Manage Evidence", self)

        open_case_action.triggered.connect(self.open_case_directory)
        run_tools_action.triggered.connect(self.run_tools_dialog)
        manage_evidence_action.triggered.connect(self.manage_evidence)

        context_menu_actions = [open_case_action, run_tools_action, manage_evidence_action]

        for action in context_menu_actions:
            context_menu.addAction(action)

        context_menu.exec(self.table.mapToGlobal(position))

    def display_cases(self):
        self.table.blockSignals(True)  # Block signals to prevent unnecessary database updates
        self.table.setRowCount(0)
        cases = self.case_manager.list_cases()
        
        for row_number, case in enumerate(cases):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(case[1:]):
                self.table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
        
        self.table.sortByColumn(3, Qt.SortOrder.AscendingOrder)  # Sort by "Created" column by default
        self.table.blockSignals(False)  # Unblock signals after populating the table

    def search_table(self):
        """
        Search the table based on user input.
        """

        search_text, ok = QInputDialog.getText(self, "Search", "Enter the value to search:")
        if ok and search_text:
            items = self.table.findItems(search_text, Qt.MatchFlag.MatchContains)
            if items:
                # Select the first matching item
                self.table.setCurrentItem(items[0])
                self.table.scrollToItem(items[0])
            else:
                QMessageBox.information(self, "Search", "No matching items found.")

    def open_github(self):
        webbrowser.open("https://github.com/be0vlk/owlculus")

    def open_case_directory(self):
        selected_row = self.table.currentRow()
        case_number = self.table.item(selected_row, 0).text()
        case_folder_path = BASE_PATH / case_number

        if platform.system() == "Windows":
            os.startfile(case_folder_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", case_folder_path])
        else:
            subprocess.Popen(["xdg-open", case_folder_path])

    def manage_evidence(self):
        """
        Manage evidence files for the selected case.
        """
        # Display the evidence files in a custom dialog
        dialog = EvidenceDialog(self.current_case_number, self)
        dialog.exec()

    def create_case(self):
        dialog = NewCaseDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            case_type, client = dialog.get_values()
            self.case_manager.setup_case_folder(None, case_type, client)
            self.display_cases()

    def delete_case(self):
        selected_row = self.table.currentRow()
        case_number = self.table.item(selected_row, 0).text()
        confirm = QMessageBox.question(self, "Delete Case", f"Are you sure you want to delete case {case_number}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.case_manager.delete_case(case_number)
            self.display_cases()

    def rename_case(self):
        selected_row = self.table.currentRow()
        case_number = self.table.item(selected_row, 0).text()
        new_case_number, ok = QInputDialog.getText(self, "Rename Case", "Enter the new case number:")
        if ok:
            self.case_manager.rename_case(case_number, new_case_number)
            self.display_cases()

    def run_tools_dialog(self):
        # Use the stored case number directly
        if not self.current_case_number:
            QMessageBox.warning(self, "Warning", "No case selected.")
            return

        tool_runner = ToolRunner(self.current_case_number)
        tool_dialog = RunToolsDialog(tool_runner)
        tool_dialog.exec() # This will open the tool selection dialog

    def update_output(self, line):
        """
        Update the output display with the given line.
        """

        self.output_display.append(line)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainLayout()
    window.show()
    sys.exit(app.exec())
