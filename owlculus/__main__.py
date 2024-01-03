import os
import sys

try:
    from pathlib import Path
    from PyQt6.QtWidgets import *
    from PyQt6.QtGui import QIcon
except ImportError:
    print("[!] Please run 'pip install -r requirements.txt' to install the dependencies first.")
    sys.exit(1)

from case_manager import MainGui, CaseDatabaseManager
from client_manager import ClientManager
from osint_tools import RunToolsDialog
from settings import SettingsManagerGui, load_config

# Get the absolute path of the directory the script is in
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = SCRIPT_DIR.parent


class MainMenu(QMainWindow):
    """
    Main menu for the Owlculus OSINT Toolkit.
    """

    def __init__(self):

        super().__init__()
        
        self.config = load_config()
        if self.config_check():
            self._setup_ui()
        else:
            self.show_config_message()

    def config_check(self):
        """
        Verify that the config file is not in the default state.
        """

        paths_to_check = [
            self.config["paths"]["base_path"],
            self.config["paths"]["cases_db_path"],
            self.config["paths"]["clients_db_path"]
        ]
        return all(Path(path) != Path("") for path in paths_to_check)

    def show_config_message(self):
        msg = QMessageBox()
        msg.setWindowTitle("Owlculus | Config Setup")
        msg.setText("Your settings are not properly configured, we need to do that first!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

        if self.open_settings():
            self._setup_ui()

    def reload_config(self):
        self.config = load_config()

    def center_window(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def _setup_ui(self):
        """Setup the UI for the main window."""

        self.setWindowTitle("Owlculus | OSINT Toolkit")
        self.resize(1920, 1080)
        self.setWindowIcon(QIcon(""))  # TODO: Add icon


        # Icons8 attribution link per their license
        link_label = QLabel()
        link_label.setText('<a href="https://icons8.com" style="color: grey;">Icons by Icons8</a>')
        link_label.setOpenExternalLinks(True)
        link_label.setStyleSheet("color: gray; font-size: 8pt; font-style: italic;")

        main_layout = QHBoxLayout()

        # Sidebar for navigation
        sidebar_layout = QVBoxLayout()
        button_data = [
            ("Case Manager", REPO_ROOT / "static/icons8-folder-50.png"), 
            ("Client Manager", REPO_ROOT / "static/icons8-contacts-50.png"), 
            ("Run Tools", REPO_ROOT / "static/icons8-toolbox-50.png"), 
            ("Settings", REPO_ROOT / "static/icons8-settings-50.png")
        ]

        sidebar_layout.addStretch(1)  # Top spacer
        self.sidebar_buttons = []
        for btn_text, icon_path in button_data:
            btn = QPushButton(QIcon(str(icon_path)), btn_text, self)
            btn.setObjectName("sidebarButton")
            btn.clicked.connect(self._change_view)
            sidebar_layout.addWidget(btn)
            sidebar_layout.addSpacing(40)
            self.sidebar_buttons.append(btn)
        sidebar_layout.addWidget(link_label)
        sidebar_layout.addStretch(1)  # Bottom spacer
        self.set_active_button(self.sidebar_buttons[0])

        # Stacked Widget for displaying case manager, client manager, etc.
        self.stacked_widget = QStackedWidget()
        self.case_manager_app = MainGui(CaseDatabaseManager())
        self.stacked_widget.addWidget(self.case_manager_app)
        self.client_manager_app = ClientManager()
        self.stacked_widget.addWidget(self.client_manager_app)
        self.tool_runner_app = RunToolsDialog()
        self.stacked_widget.addWidget(self.tool_runner_app)
        self.settings_manager_app = SettingsManagerGui()
        self.stacked_widget.addWidget(self.settings_manager_app)

        main_layout.addLayout(sidebar_layout)
        main_layout.addWidget(self.stacked_widget)

        central_widget = QWidget(self)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _change_view(self):
        sender = self.sender()
        sender_text = self.sender().text()
        if sender_text == "Case Manager":
            self.stacked_widget.setCurrentWidget(self.case_manager_app)
        elif sender_text == "Client Manager":
            self.stacked_widget.setCurrentWidget(self.client_manager_app)
        elif sender_text == "Run Tools":
            self.stacked_widget.setCurrentWidget(self.tool_runner_app)
        elif sender_text == "Settings":
            self.stacked_widget.setCurrentWidget(self.settings_manager_app)
        self.set_active_button(sender)

    def open_settings(self):
        self.settings_manager_app = SettingsManagerGui()
        self.settings_manager_app.settingsChanged.connect(self.reload_config)
        self.settings_manager_app.show()

    def set_active_button(self, active_button):
        # Reset all buttons to default style so we can apply style to the active one
        for btn in self.sidebar_buttons:
            btn.setStyleSheet("")
        active_button.setStyleSheet("background-color: #666666")


def load_stylesheet(qss_path: str) -> str:
    with open(qss_path, "r") as f:
        return f.read()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qss_content = load_stylesheet(REPO_ROOT / "static/default_style.qss")
    app.setStyleSheet(qss_content)
    main_menu = MainMenu()
    if main_menu.config_check():
        main_menu.show()
        main_menu.center_window()
    sys.exit(app.exec())
