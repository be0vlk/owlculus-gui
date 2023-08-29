"""
Module containing the actual commands to run various tools.
"""

import subprocess
import yaml
from pathlib import Path


class ToolRunner:
    def __init__(self, case_folder_path):
        self.case_folder_path = case_folder_path
        self.load_config()

    def load_config(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def run_maigret(self, username):
        maigret_path = self.config.get("maigret", "maigret")
        output_folder = self.case_folder_path / "Social_Media"
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
