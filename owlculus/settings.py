"""
This module contains functionality related to configuration and settings.
"""

import os
import shutil
import sys
import yaml
from pathlib import Path
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import *

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))  # Path of the module itself
CONFIG_FILE = os.path.join(MODULE_PATH, "../config.yaml")


def load_config(config_key=None):
    """
    Load a specific configuration value from the YAML file.
    
    :param config_key: The key for the desired configuration value. If key is nested, provide it as "parent.child".
                E.g., to get cases_db_path: key="paths.cases_db_path".
                If no key is provided, the entire configuration is returned.
    :return: The desired configuration value or the entire configuration if no key is provided.
    """

    with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
        config_value = yaml.load(cf, Loader=yaml.FullLoader)
        
        if config_key:
            keys = config_key.split('.')
            for k in keys:
                config_value = config_value[k]

        return config_value


def update_config(config):
    """
    Update the configuration YAML file for the application.
    """

    with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
        yaml.dump(config, cf, default_flow_style=False)


class SettingsManagerGui(QWidget):
    """
    This class is responsible for managing the settings of the application.
    """

    settingsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.tool_edits = {}  # Dictionary to store QLineEdit objects for each tool
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface elements.
        """

        config = load_config()
        base_path = config["paths"]["base_path"]
        cases_db_path = config["paths"]["cases_db_path"]
        clients_db_path = config["paths"]["clients_db_path"]

        self.setWindowTitle("Owlculus | Settings Manager")
        self.setGeometry(100, 100, 600, 300)

        # Layout
        layout = QVBoxLayout()

        # Base and DB Path fields
        self.base_path_edit = self.create_path_field(layout, "Base Path:", base_path,
                                                     "Directory where the case folders and evidence items will be stored")

        self.cases_db_path_edit = self.create_path_field(layout, "Cases DB Path:", cases_db_path,
                                                         "Directory where the cases.db file should be stored")

        self.clients_db_path_edit = self.create_path_field(layout, "Clients DB Path:", clients_db_path,
                                                           "Directory where the clients.db file should be stored")

        # Dynamically create fields for each tool
        for tool, path in config["tools"].items():
            self.tool_edits[tool] = self.create_path_field(layout, f"{tool.capitalize()} Path:", path,
                                                           f"The path to the {tool.capitalize()} executable")

        # Save button
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.update_config_gui)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        # Connect changes in any QLineEdit to enable the Save button
        self.base_path_edit.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.cases_db_path_edit.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        self.clients_db_path_edit.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        for edit in self.tool_edits.values():
            edit.textChanged.connect(lambda: self.save_btn.setEnabled(True))
        
        self.setLayout(layout)

    def create_path_field(self, layout, label_text, path, hint_text):
        """
        Helper method to create a field for paths in the UI.
        """
        label = QLabel(label_text)
        edit = QLineEdit(path)
        hint = QLabel(hint_text)
        hint.setStyleSheet("color: gray; font-size: 10pt; font-style: italic;")

        field_layout = QVBoxLayout()
        field_layout.addWidget(label)
        field_layout.addWidget(edit)
        field_layout.addWidget(hint)
        layout.addLayout(field_layout)
        layout.addSpacing(10)

        return edit

    def update_config_gui(self):
        config_struct = {
            "paths": {
                "base_path": self.base_path_edit.text(),
                "cases_db_path": self.cases_db_path_edit.text(),
                "clients_db_path": self.clients_db_path_edit.text()
            },
            "tools": {tool: edit.text() for tool, edit in self.tool_edits.items()}
        }

        update_config(config_struct)
        self.settingsChanged.emit()
        self.save_btn.setEnabled(False)


# Initialize configuration file if it does not exist.
if not os.path.exists(CONFIG_FILE):
    print("[!] Configuration file not found, creating a new one...")
    shutil.copy(os.path.join(MODULE_PATH, "../config.yaml.example"), CONFIG_FILE)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsManagerGui()
    window.show()
    sys.exit(app.exec())
