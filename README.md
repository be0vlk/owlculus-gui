# Owlculus

Owlculus is a Python GUI application for managing OSINT investigation cases. It provides a graphical interface for creating and organizing cases, running OSINT tools, and taking investigation notes.
It provides a quick and easy way to get started with OSINT investigations without having to worry about creating and organizing folders and tracking case numbers. It's all handled for you!


## Features

- Manage existing cases and create new cases complete with a unique case number
- Creates highly organized folders per case complete with categorized subdirectories and note-taking templates 
- Run third-party OSINT tools and import results to the case folder automatically (currently only supports Maigret)
- Thoroughly documented code for easy customization
- Cross-platform (Windows, Linux, Mac)

## Requirements

- Python 3.10+
- Tkinter (should come included with Python)
- sqlite3 
- ttkthemes
- maigret (optional)

## Installation

Clone the repo:

```git clone https://github.com/be0vlk/owlculus.git ```

Install dependencies:

```pip install -r requirements.txt```

Remove the trailing ".example" from "config.yaml.example" and edit to add the path to the given tool. If you installed Maigret with pip, you can leave the path as-is.

## Usage

After cloning the repo and installing requirements, cd into the owlculus directory and run:

```python owlculus.py```

- This will bring up the GUI which should be fairly self-explanatory. For added convenience, buttons all have tooltips that will appear when you hover over them.<br>
- You can also sort the case list by column, all you gotta do is click the column header. Clicking it again will reverse the sort order.
- Double-clicking a case from the display menu will open the case folder in your default file manager.

![Imgur](https://i.imgur.com/1dtmhhj.png)

### Creating a New Case

Simply click the button and a new window will appear. Select the type of investigation from the dropdown menu and click "Create". If this is your first run, the app will setup a SQLite database in the "Cases" folder which contains metadata about your cases.<br>
- The default naming convention uses the last two digits of the current year plus the two-digit month, followed by a dash and a unique case number. For example, if you create a case in January 2024, the case number will be "2401-01".
- Case numbers will increment automatically. You don't have to worry about duplicating case numbers since the database tracks it.
- By default, the app will create the "Cases" folder on your desktop. You can manually change this in the "case_manager.py" module if you wish.

### Deleting a Case

- Click on the desired case from the display menu which will select it. 
- Click the "Delete Case" button and a confirmation window will appear. 
- Click "Yes" to delete the case and all associated files and folders from the disk as well as the entry in the SQLite database.

### Renaming a Case

Sometimes we just don't like our case number and want to change it. No problem!

- Click on the desired case from the display menu which will select it.
- Click the "Rename Case" button and a new window will appear for you to enter the new case number.

### Running Tools

- Click the "Run Tools" button up on the top toolbar and a new window will appear.
- Enter the information requested and click "Run". The app will run the tool and import the results to the case folder automatically.
- NOTE: Maigret output is stored in the "Social_Media" subdirectory inside the main "Cases" folder and defaults to HTML format.

This is the biggest WIP feature of the app. Currently, the only tool supported is Maigret.

### Taking Notes

The "templates" folder included in the repo contains basic note-taking templates in Markdown format. 

- You can customize these to your liking or create your own. 
- Creating new ones may require you to edit the code in "case_manager.py". 
- The app will automatically copy the template to the appropriate case folder when you create a new case.
