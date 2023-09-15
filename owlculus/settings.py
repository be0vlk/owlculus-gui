"""
This module contains functionality related to configuration and settings.
"""

import os
import sys
import yaml
from pathlib import Path
from PyQt6.QtWidgets import *

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))  # Path of the module itself

class SettingsManager(QWidget):
    """
    This class is responsible for managing the settings of the application.
    """

    def __init__(self):
        super().__init__()
        self.tool_edits = {}  # Dictionary to store QLineEdit objects for each tool
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface elements.
        """
        
        self.setWindowTitle("Settings Manager")
        self.setGeometry(100, 100, 600, 300)  # x, y, width, height

        # Layout
        layout = QVBoxLayout()

        # Base and DB Path fields
        self.base_path_label = QLabel("Base Path:")
        self.base_path_edit = QLineEdit(LOADED_CONFIG["paths"]["base_path"])
        self.cases_db_path_label = QLabel("Cases DB Path:")
        self.cases_db_path_edit = QLineEdit(LOADED_CONFIG["paths"]["cases_db_path"])

        base_path_layout = QHBoxLayout()
        base_path_layout.addWidget(self.base_path_label)
        base_path_layout.addWidget(self.base_path_edit)
        
        cases_db_path_layout = QHBoxLayout()
        cases_db_path_layout.addWidget(self.cases_db_path_label)
        cases_db_path_layout.addWidget(self.cases_db_path_edit)

        layout.addLayout(base_path_layout)
        layout.addLayout(cases_db_path_layout)

        # Dynamically create fields for each tool
        for tool, path in LOADED_CONFIG["tools"].items():
            label = QLabel(f"{tool.capitalize()} Path:")
            edit = QLineEdit(path)
            self.tool_edits[tool] = edit
            
            tool_layout = QHBoxLayout()
            tool_layout.addWidget(label)
            tool_layout.addWidget(edit)
            layout.addLayout(tool_layout)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.update_config)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def update_config(self):
        """
        Update the configuration YAML file for the application.
        """
        
        # Update the base and DB paths
        LOADED_CONFIG["paths"]["base_path"] = self.base_path_edit.text()
        LOADED_CONFIG["paths"]["cases_db_path"] = self.cases_db_path_edit.text()

        # Update tool paths
        for tool, edit in self.tool_edits.items():
            LOADED_CONFIG["tools"][tool] = edit.text()

        # Save the configuration data back to the YAML file
        with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
            yaml.dump(LOADED_CONFIG, cf, default_flow_style=False)

        print("[+] Settings saved")


try:
    # Load the configuration file
    CONFIG_FILE = os.path.join(MODULE_PATH, "../config.yaml")
    with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
        LOADED_CONFIG = yaml.load(cf, Loader=yaml.FullLoader)
        
        if Path(LOADED_CONFIG["paths"]["base_path"]) == "":
            print("[!] Base path not set in configuration file")
        
        BASE_PATH = Path(LOADED_CONFIG["paths"]["base_path"])
        CASES_DB_PATH = Path(LOADED_CONFIG["paths"]["cases_db_path"])

except FileNotFoundError:
    print("[!] Configuration file not found")
    sys.exit(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsManager(LOADED_CONFIG)
    window.show()
    sys.exit(app.exec())
