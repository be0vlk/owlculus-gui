# Owlculus

Owlculus is a Python GUI application for managing OSINT investigation cases. It provides a graphical interface for creating and organizing cases, running OSINT tools, taking investigation notes, and more.
It provides a quick and easy way to get started with OSINT investigations without having to worry about creating and organizing folders and tracking case numbers. It's all handled for you!


## Features

- Manage existing cases and create new cases with a unique case number
- Creates highly organized folders per case complete with categorized subdirectories and note-taking templates 
- Run third-party OSINT tools and import results to the case folder automatically (currently only supports Maigret)
- Client Manager that allows you to save client details for assigning to cases
- Evidence Manager lets you get a quick glance at what's in your case file
- Thoroughly documented code for easier customization
- Cross-platform (Windows, Linux, Mac)

### Roadmap

- Add more tool compatibility
- Revamp the UI
- Functionality to edit notes directly in the app
- Integrate various AI powers

## Requirements

- Python 3.10+
- PyQt6
- sqlite3
- maigret

## Installation

Clone the repo:

```git clone https://github.com/be0vlk/owlculus.git ```

Install dependencies:

```pip install -r requirements.txt```

## Usage

After cloning the repo and installing requirements, cd into the repo directory and run:

```python owlculus```

- This will bring up the main menu GUI which should be fairly self-explanatory. For added convenience, buttons all have tooltips that will appear when you hover over them.
- IMPORTANT: Run "Settings" from the main menu before creating a case! Although, it will prompt you if needed.
- "Run Tools" functionality is a WIP but for now you can run Maigret. You can also run it from within the Case Manager as you'll see below.<br>

![Imgur](https://i.imgur.com/7Zmxt8x.png)

## Case Manager

- Right-clicking a case will open a context menu. Click "Open Case" and the case folder will open in your default file manager. 
- You can also sort the case list by column, all you gotta do is click the column header. Clicking it again will reverse the sort order.

![Imgur](https://i.imgur.com/6mmkN03.png)

### Creating a New Case

Simply click the button and a new window will appear. Select the type of investigation from the dropdown menu and click "Create". If this is your first run, the app will setup a SQLite database in the "Cases" folder which contains metadata about your cases.<br>
- The default naming convention uses the last two digits of the current year plus the two-digit month, followed by a dash and a unique case number. For example, if you create a case in January 2024, the case number will be "2401-01".
- Case numbers will increment automatically. You don't have to worry about duplicating case numbers since the database tracks it.
- The case folder and all the evidence directories will be stored wherever you have set them in "Settings".

### Deleting a Case

- Click on the desired case from the display menu which will select it. 
- Click the "Delete Case" button and a confirmation window will appear. 
- Click "Yes" to delete the case and all associated files and folders from the disk as well as the entry in the SQLite database.

### Editing a Case

Sometimes we just don't like our case and want to change it. No problem!

- Double-click directly on the cell whose value you want to change.
- The cell will change to edit mode. Make your change and press enter.
- Note that the created date and type is not editable.

### Running Tools

- Right-click directly on a case to bring up the contect menu. Select "Run Tools" and a new window will appear.
- Select the tool and click "Run". The app will run the tool and import the results to the case folder automatically.
- NOTE: Maigret output is stored inside the main case folder and defaults to HTML format.

This is the biggest WIP feature of the app. Currently, the only tool supported is Maigret.

### Taking Notes

The "templates" folder included in the repo contains basic note-taking templates in Markdown format. 

- You can customize these to your liking or create your own. 
- Creating new ones may require you to edit the code in "case_manager.py". 
- The app will automatically copy the template to the appropriate case folder when you create a new case.

## Client Manager

- A separate interface for adding, updating, and deleting clients from the database.
- Double-click directly on a cell to edit the value then press enter when done.
- You can also create new clients via the case creation dialog in the case manager. That will also be reflected in the client manager and vice versa.

![Imgur](https://i.imgur.com/Bb1Ml65.png)
