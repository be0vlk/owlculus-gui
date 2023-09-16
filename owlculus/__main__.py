import sys
from pathlib import Path
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import *
from case_manager import MainGui, CaseDatabaseManager
from client_manager import ClientManager
from osint_tools import RunToolsDialog
from settings import SettingsManagerGui, load_config


class MainMenu(QMainWindow):
    """
    Main menu for the Owlculus OSINT Toolkit.
    """

    def __init__(self):
        """
        Initialize the main menu.
        """

        super().__init__()
        self._setup_ui()
        self.config = load_config()
    
    def config_check(self):
        paths_to_check = [
            self.config["paths"]["base_path"],
            self.config["paths"]["cases_db_path"],
            self.config["paths"]["clients_db_path"]
        ]

        for path in paths_to_check:
            if Path(path) == Path(""):
                self.show_config_message()
                return False
        return True 

    def show_config_message(self):
        """
        Display a message box when config not set and open the SettingsManager.
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Owlculus | Config Setup")
        msg.setText("Your settings are not properly configured, we need to do that first!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        self.open_settings()

    def reload_config(self):
        """
        Reload the configuration from disk.
        """

        self.config = load_config()

    def center_window(self):
        """ Center the main window on the screen """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = int((screen_geometry.width() - self.width()) / 2)
        y = int((screen_geometry.height() - self.height()) / 2)
        self.move(x, y)

    def _setup_ui(self):
        """
        Set up the user interface.
        """

        # Set window properties
        self.setWindowTitle("Owlculus | OSINT Toolkit")
        self.resize(600, 200)
        self.setWindowIcon(QIcon(""))  # TODO: Add icon

        # Create a central widget for the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add a title label
        title_label = QLabel("Select an Option:", self)
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Define tooltips for each button
        tooltips = {
            "Case Manager": "Open the case management interface where you can create, edit, and delete cases.",
            "Client Manager": "Manage client details and information that can be associated with cases.",
            "Run Tools": "Execute selected OSINT tools. WIP!",
            "Settings": "Configure the application settings."
        }

        # Add buttons for each option with a modern look, hover effect, and tooltips
        buttons = ["Case Manager", "Client Manager", "Run Tools", "Settings"]
        for btn_text in buttons:
            btn = QPushButton(btn_text, self)
            btn.setFont(QFont("Arial", 14))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5b5b5b; 
                    color: white; 
                    border: none; 
                    padding: 15px 32px; 
                    text-align: center; 
                    text-decoration: none; 
                    margin: 4px 2px;
                }
                QPushButton:hover {
                    background-color: #4b4b4b;
                }
            """)
            btn.setToolTip(tooltips[btn_text])
            layout.addWidget(btn)

        # Connect buttons to their respective slots (functions)
        layout.itemAt(1).widget().clicked.connect(self.open_case_manager)
        layout.itemAt(2).widget().clicked.connect(self.open_client_manager)
        layout.itemAt(3).widget().clicked.connect(self.run_tools)
        layout.itemAt(4).widget().clicked.connect(self.open_settings)

        # Add a spacer to push buttons to the top
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        central_widget.setLayout(layout)

    def open_case_manager(self):
        if self.config_check():
            self.case_db_manager = CaseDatabaseManager()
            self.case_manager_app = MainGui(self.case_db_manager)
            self.case_manager_app.show()

    def open_client_manager(self):
        if self.config_check():
            self.client_manager_app = ClientManager()
            self.client_manager_app.show()

    def run_tools(self):
        if self.config_check():
            self.tool_runner_app = RunToolsDialog()
            self.tool_runner_app.show()

    def open_settings(self):
        self.settings_manager_app = SettingsManagerGui()
        self.settings_manager_app.settingsChanged.connect(self.reload_config)
        self.settings_manager_app.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_menu = MainMenu()
    main_menu.show()
    main_menu.center_window()
    main_menu.config_check()
    sys.exit(app.exec())
