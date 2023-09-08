import sys
from PyQt6.QtGui import QColor, QFont, QIcon, QPalette
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
from case_manager import MainLayout
from client_manager import ClientManager
from osint_tools import ToolRunner


class MainMenu(QMainWindow):
    """Main menu for the Owlculus OSINT Toolkit."""

    def __init__(self):
        """Initialize the main menu."""
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Set window properties
        self.setWindowTitle("Owlculus | OSINT Toolkit")
        self.setGeometry(600, 600, 600, 200)
        self.setWindowIcon(QIcon("path_to_icon.png"))

        # Create a central widget for the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        layout = QVBoxLayout()

        # Add a title label with a modern font
        title_label = QLabel("Select an Option:", self)
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Define tooltips for each button
        tooltips = {
            "Case Manager": "Open the case management interface where you can create, edit, and delete cases.",
            "Client Manager": "Manage client details and information that can be associated with cases.",
            "Run Tools": "Execute selected OSINT tools. WIP!"
        }

        # Add buttons for each option with a modern look, hover effect, and tooltips
        buttons = ["Case Manager", "Client Manager", "Run Tools"]
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

        # Add a spacer to push buttons to the top
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        central_widget.setLayout(layout)

    def open_case_manager(self):
        """Open the case manager."""
        self.case_manager_app = MainLayout()
        self.case_manager_app.show()

    def open_client_manager(self):
        """Open the client manager."""
        self.client_manager_app = ClientManager()
        self.client_manager_app.show()

    def run_tools(self):
        """Run the selected tools."""
        self.tool_runner_app = ToolRunner()
        self.tool_runner_app.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set a modern palette for the application
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(142, 45, 197))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)


    main_menu = MainMenu()
    main_menu.show()

    sys.exit(app.exec())
