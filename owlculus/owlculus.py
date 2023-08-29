"""
This module contains all the GUI code for application.
"""

import platform
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel, Text, Button
from case_manager import CaseManager, BASE_PATH
from tools import ToolRunner
from ttkthemes import ThemedTk
import threading
import subprocess
import os
import webbrowser


class ToolTip:
    """
    Create a tooltip for a given widget.
    """

    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.delay = delay
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event=None):
        """
        Schedule the tooltip to appear after a delay.
        """

        self.id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self, event=None):
        """
        Display the tooltip.
        """

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 50
        y += self.widget.winfo_rooty() + 50

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, bg="yellow", relief="solid", borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        """
        Hide the tooltip.
        """

        if self.id:
            self.widget.after_cancel(self.id)
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class RunToolsDialog(tk.Toplevel):
    """
    Dialog for running tools.
    """

    def __init__(self, parent, case_list):
        super().__init__(parent)
        self.title("Run Tools")
        self.tool = None
        self.case = None

        tk.Label(self, text="Select Tool:").grid(row=1, column=0, padx=10, pady=10)
        self.tools = sorted(["Maigret"])
        self.tool_var = tk.StringVar()
        self.tool_var.set("Maigret")
        tk.OptionMenu(self, self.tool_var, *self.tools).grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self, text="Select Case:").grid(row=2, column=0, padx=10, pady=10)
        self.case_var = tk.StringVar()
        self.case_var.set(case_list[0])
        tk.OptionMenu(self, self.case_var, *case_list).grid(row=2, column=1, padx=10, pady=10)

        tk.Button(self, text="Run", command=self.run_tool).grid(row=3, columnspan=2, pady=10)

    def run_tool(self):
        self.tool = self.tool_var.get()
        self.case = self.case_var.get()
        self.destroy()


class CreateCaseDialog(tk.Toplevel):
    """
    Dialog for creating a new case.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Create Case")
        self.case_name = None
        self.case_type = None
        self.client = None

        tk.Label(self, text="Case Type:").grid(row=1, column=0, padx=10, pady=10)
        self.case_types = sorted(["Person", "Company", "Threat Intel", "Event"])
        self.type_var = tk.StringVar()
        self.type_var.set("Person")
        tk.OptionMenu(self, self.type_var, *self.case_types).grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self, text="Client:").grid(row=2, column=0, padx=10, pady=10)
        self.client_entry = tk.Entry(self)
        self.client_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Button(self, text="Create", command=self.create).grid(row=3, columnspan=2, pady=10)

    def create(self):
        self.case_type = self.type_var.get()
        self.client = self.client_entry.get()
        self.destroy()


class CaseManagerApp:
    def __init__(self, tk_root):
        self.root = tk_root
        self.root.title("Owlculus | OSINT Case Manager")
        self.case_manager = CaseManager()

        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.menu_bar.add_command(label="GitHub", command=self.open_github)
        self.menu_bar.add_command(label="Run Tools", command=self.run_tools_dialog)
        self.root.config(menu=self.menu_bar)

        # Toolbar
        create_case_button = ttk.Button(tk_root, text="Create Case", command=self.create_case)
        create_case_button.grid(row=0, column=0, padx=10, pady=10)
        ToolTip(create_case_button, "Create a new case")

        delete_case_button = ttk.Button(tk_root, text="Delete Case", command=self.delete_case)
        delete_case_button.grid(row=0, column=1, padx=10, pady=10)
        ToolTip(delete_case_button, "Delete the selected case both from the database and the file system")

        rename_case_button = ttk.Button(tk_root, text="Rename Case", command=self.rename_case)
        rename_case_button.grid(row=0, column=2, padx=10, pady=10)
        ToolTip(rename_case_button, "Change the case number of the selected case")

        # Treeview
        self.tree = ttk.Treeview(
            tk_root, columns=("Case Number", "Type", "Client", "Created"), show='headings'
        )
        self.tree.grid(row=1, columnspan=4, padx=20, pady=20)

        self.tree.heading("#1", text="Case Number", command=lambda: self.sort_column("#1", False))
        self.tree.heading("#2", text="Type", command=lambda: self.sort_column("#2", False))
        self.tree.heading("#3", text="Client", command=lambda: self.sort_column("#3", False))
        self.tree.heading("#4", text="Created", command=lambda: self.sort_column("#4", False))

        self.tree.bind("<Double-1>", self.open_case_directory)

        self.display_cases()

    def sort_column(self, col, reverse):
        """
        Sort tree contents when a column is clicked on.
        """

        x = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        x.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(x):
            self.tree.move(k, '', index)

        # Reverse sort direction for next sort operation
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def display_cases(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        cases = self.case_manager.list_cases()
        for case in cases:
            self.tree.insert("", tk.END, values=case[1:])

    def run_tools_dialog(self):
        case_numbers = [self.tree.item(item, "values")[0] for item in self.tree.get_children()]
        if not case_numbers:
            messagebox.showwarning("Warning", "No cases available.")
            return

        dialog = RunToolsDialog(self.root, case_numbers)
        self.root.wait_window(dialog)
        if dialog.tool and dialog.case:
            if dialog.tool == "Maigret":
                self.run_maigret(dialog.case)

    def open_case_directory(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        selected_item = selected_items[0]
        case_number = self.tree.item(selected_item, "values")[0]
        case_folder_path = BASE_PATH / case_number

        if platform.system() == "Windows":
            os.startfile(case_folder_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", case_folder_path])
        else:
            subprocess.Popen(["xdg-open", case_folder_path])

    def create_case(self):
        dialog = CreateCaseDialog(self.root)
        self.root.wait_window(dialog)
        if dialog.case_type:
            self.case_manager.setup_case_folder(dialog.case_name, dialog.case_type, dialog.client)
            self.display_cases()

    def delete_case(self):
        selected_item = self.tree.selection()[0]
        case_number = self.tree.item(selected_item, "values")[0]
        if messagebox.askokcancel("Confirm Delete", f"Are you sure you want to delete case {case_number}?"):
            self.case_manager.delete_case(case_number)
            self.display_cases()

    def rename_case(self):
        selected_item = self.tree.selection()[0]
        old_case_number = self.tree.item(selected_item, "values")[0]
        new_case_number = simpledialog.askstring("Input", "Enter the new case number:")
        if new_case_number:
            self.case_manager.rename_case(old_case_number, new_case_number)
            self.display_cases()

    @staticmethod
    def open_github():
        webbrowser.open("https://github.com/be0vlk/owlculus")

    def run_maigret(self, case):

        username = simpledialog.askstring("Input", "Enter the username:")
        if username:
            case_folder_path = BASE_PATH / case
            tool_runner = ToolRunner(case_folder_path)

            output_window = Toplevel(self.root)
            output_window.title("Maigret Output")
            output_text = Text(output_window, wrap="none", width=100, height=20)
            output_text.pack()

            def update_output():
                for line in tool_runner.run_maigret(username):
                    output_text.insert("end", line)
                    output_text.see("end")
                    output_window.update_idletasks()

            tool_thread = threading.Thread(target=update_output)
            tool_thread.daemon = True
            tool_thread.start()

            def cancel_tool():
                tool_thread.join(0)
                if tool_thread.is_alive():
                    messagebox.showinfo("Info", "Tool is still running. Close the window to cancel.")
                else:
                    output_window.destroy()

            Button(output_window, text="Close", command=cancel_tool).pack()


if __name__ == "__main__":
    root = ThemedTk(theme="adapta")
    app = CaseManagerApp(root)
    root.mainloop()
