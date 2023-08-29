"""
This module handles the underlying logic for case setup including initializing the database.
"""


from datetime import datetime
import sqlite3
import shutil
from pathlib import Path

BASE_PATH = Path.home() / "Desktop/Cases"  # Base path for all cases in which subdirectories will be created
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
        self.db_path = BASE_PATH / "cases.db"  # SQLite database path, can be changed independently of BASE_PATH
        self.initialize_db()

    def initialize_db(self):
        if not BASE_PATH.exists():
            BASE_PATH.mkdir(parents=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS case_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE NOT NULL,
                case_type TEXT NOT NULL,
                client TEXT,
                created_at TEXT NOT NULL
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
        cursor.execute("SELECT * FROM case_numbers WHERE case_number = ?", (case_number,))
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
            "INSERT INTO case_numbers (case_number, case_type, client, created_at) VALUES (?, ?, ?, ?)",
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
        cursor.execute("DELETE FROM case_numbers WHERE case_number = ?", (case_number,))
        conn.commit()
        conn.close()

        case_folder_path = BASE_PATH / case_number
        if case_folder_path.exists():
            shutil.rmtree(case_folder_path)

    def rename_case(self, old_case_number, new_case_number):
        """
        Renames a case in the database.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("UPDATE case_numbers SET case_number = ? WHERE case_number = ?",
                       (new_case_number, old_case_number))
        conn.commit()
        conn.close()

        old_case_folder_path = BASE_PATH / old_case_number
        new_case_folder_path = BASE_PATH / new_case_number
        if old_case_folder_path.exists():
            old_case_folder_path.rename(new_case_folder_path)

    def list_cases(self):
        """
        Lists all cases in the database. Used by the GUI for populating the case list.
        """

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM case_numbers")
        rows = cursor.fetchall()
        conn.close()
        return rows
