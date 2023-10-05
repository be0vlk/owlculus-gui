"""
This module contains the ClientManager class, which handles the core logic for managing clients.
"""

import os
import sqlite3
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from settings import load_config

# Get the absolute path of the directory the script is in
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = SCRIPT_DIR.parent


class NewClientDialog(QDialog):
    def __init__(self, client_manager, parent=None):
        super().__init__(parent)
        self.client_manager = client_manager
        self.setWindowTitle("New Client")
        self.resize(400, 200)

        layout = QVBoxLayout()

        # Input fields for client details
        self.name_input = QLineEdit(placeholderText="Name")
        self.poc_input = QLineEdit(placeholderText="Point of Contact")
        self.phone_input = QLineEdit(placeholderText="Phone Number")
        self.email_input = QLineEdit(placeholderText="Email")

        # Buttons
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_client)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        # Add widgets to layout
        layout.addWidget(self.name_input)
        layout.addWidget(self.poc_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.email_input)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def save_client(self):
        """
        Save the client to the database.
        """

        name = self.name_input.text()
        poc = self.poc_input.text()
        phone = self.phone_input.text()
        email = self.email_input.text()

        if self.client_manager.client_exists(name):
            QMessageBox.warning(self, "[!]", f"A client with the name '{name}' already exists.")
            return

        try:
            self.client_manager.add_client(name, poc, phone, email)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "[!]", str(e))


class ClientManager(QWidget):
    """
    This class handles the logic for managing clients.
    """

    def __init__(self, parent=None):

        super().__init__(parent)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Buttons
        self.add_btn = QPushButton("Add Client", icon=QIcon(str(REPO_ROOT / "static/icons8-plus-50.png")))
        self.add_btn.clicked.connect(self.add_client_gui)
        self.delete_btn = QPushButton("Delete Client", icon=QIcon(str(REPO_ROOT / "static/icons8-delete-50.png")))
        self.delete_btn.clicked.connect(self.delete_client_gui)

        # Table to display clients
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Point of Contact", "Phone Number", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.itemChanged.connect(self.handle_item_changed)
        self.table.verticalHeader().setVisible(False)

         # Set the column widths
        total_width = 1920
        column_widths = [0.25, 0.25, 0.25, 0.05]
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, int(total_width * width))

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        main_layout.addLayout(btn_layout)

        main_layout.addWidget(self.table)

        self.db_path = Path(load_config("paths.clients_db_path")) / "clients.db"
        self.initialize_db()
        self.list_clients_gui()

    def initialize_db(self):
        """
        Initializes the database for client management.
        """

        client_path = Path(load_config("paths.clients_db_path"))
        if not client_path.exists():
            client_path.mkdir(parents=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                point_of_contact TEXT,
                phone_number TEXT,
                email TEXT
            )
        """)

        conn.commit()
        conn.close()

    def client_exists(self, name):
        """
        Checks if a client with the given name already exists in the database.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE name = ?", (name,))
        client = cursor.fetchone()
        conn.close()
        return client is not None

    def add_client(self, name, point_of_contact, phone_number, email):
        """
        Adds a new client to the database.
        """

        if self.client_exists(name):
            raise ValueError(f"A client with the name '{name}' already exists.")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clients (name, point_of_contact, phone_number, email) VALUES (?, ?, ?, ?)",
            (name, point_of_contact, phone_number, email)
        )
        conn.commit()
        conn.close()

    def get_client(self, client_id):
        """
        Retrieves a client's details based on the client ID.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = cursor.fetchone()
        conn.close()
        return client
    
    def get_selected_client_id(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None

    def update_client(self, client_id, name=None, point_of_contact=None, phone_number=None, email=None):
        """
        Updates a client's details.
        """

        # Check if the client with the new name already exists
        if name and self.client_exists(name):
            raise ValueError(f"A client with the name '{name}' already exists.")

        # Build the SQL update statement dynamically based on provided arguments
        columns_to_update = []
        values_to_update = []

        if name is not None:
            columns_to_update.append("name = ?")
            values_to_update.append(name)
        if point_of_contact is not None:
            columns_to_update.append("point_of_contact = ?")
            values_to_update.append(point_of_contact)
        if phone_number is not None:
            columns_to_update.append("phone_number = ?")
            values_to_update.append(phone_number)
        if email is not None:
            columns_to_update.append("email = ?")
            values_to_update.append(email)

        # Add the client_id to the values list
        values_to_update.append(client_id)

        # Construct the final SQL statement
        sql = f"UPDATE clients SET {', '.join(columns_to_update)} WHERE id = ?"

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(sql, values_to_update)
        conn.commit()
        conn.close()

    def handle_item_changed(self, item):
        """
        Handle the database update when an item is edited.
        """

        row = item.row()
        column = item.column()
        client_id = int(self.table.item(row, 0).data(Qt.ItemDataRole.UserRole))
        new_value = item.text()

        # Check if the new value is not empty
        if not new_value.strip():
            QMessageBox.warning(self, "[!]", "Value cannot be empty!")
            self.list_clients_gui()
            return

        try:
            if column == 0:
                # Check if client with the new name already exists
                if self.client_exists(new_value):
                    raise ValueError(f"A client with the name '{new_value}' already exists.")
                self.update_client(client_id, name=new_value)
            elif column == 1:
                self.update_client(client_id, point_of_contact=new_value)
            elif column == 2:
                self.update_client(client_id, phone_number=new_value)
            elif column == 3:
                self.update_client(client_id, email=new_value)
        except ValueError as e:
            QMessageBox.warning(self, "[!]", str(e))
            self.list_clients_gui()

    def delete_client(self, client_id):
        """
        Deletes a client from the database.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()
        conn.close()

    def list_clients(self):
        """
        Lists all clients in the database.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients")
        clients = cursor.fetchall()
        conn.close()
        return clients

    def add_client_gui(self):
        dialog = NewClientDialog(self, self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.list_clients_gui()

    def list_clients_gui(self):
        # Block the itemChanged signal temporarily
        self.table.blockSignals(True)

        clients = self.list_clients()
        self.table.setRowCount(len(clients))
        for row, client in enumerate(clients):
            item = QTableWidgetItem(client[1])
            item.setData(Qt.ItemDataRole.UserRole, client[0])
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(client[2]))
            self.table.setItem(row, 2, QTableWidgetItem(client[3]))
            self.table.setItem(row, 3, QTableWidgetItem(client[4]))

        # Re-enable the itemChanged signal
        self.table.blockSignals(False)

    def delete_client_gui(self):
        client_id = self.get_selected_client_id()
        if client_id:
            self.delete_client(client_id)
            self.list_clients_gui()
        else:
            QMessageBox.warning(self, "Error", "No client selected!")
