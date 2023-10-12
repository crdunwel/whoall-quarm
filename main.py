import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlite3
import tkinter as tk
from tkinter import ttk
import time
import os
from datetime import datetime, timedelta
import json
import subprocess
import shutil  # Add this import at the beginning


# Add imports at the beginning of your script
import threading

# Global event to notify about file changes
file_modified_event = threading.Event()

# Regular expression pattern to match the log entries
PATTERN = r"^\[.+?\]\s*(AFK\s+)?\[(\d+|ANONYMOUS) ([\w\s]+?)\]\s*(\w+)\s+\(([\w\s]+)\)\s*(?:<(.+?)>)?\s*ZONE:\s*([\w\d\s]+?)\s*(LFG)?\s*$"

#PATTERN = r"^\[.+\]\s*(AFK)?\s*\[(\d+|ANONYMOUS)\s+(\w+(?:\s\w+)?)\]\s*(\w+)\s+\(([\w\s]+)\)(?:\s*<(.+?)>)?\s*ZONE:\s*([\w\d\s]+)(?:\s*(LFG))?\s*$"
#PATTERN = r"^\[.+\]\s*(AFK)?\s*\[([\d]+|ANONYMOUS) ([\w\s]+?)\] (\w+) \(([\w\s]+)\)(?: <(.+?)>)? ZONE: ([\w\d\s]+)( LFG)?\s*$"

TIME_PATTERN = r"\[(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]"


def setup_database(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        level INTEGER,
        class TEXT,
        name TEXT UNIQUE,
        race TEXT,
        zone TEXT,
        guild TEXT,
        lfg INTEGER DEFAULT 0,
        last_updated TIMESTAMP  -- Add this line
    )
    ''')
    conn.commit()


def upsert_player(conn: sqlite3.Connection, level: int, class_: str, name: str, race: str, guild: str, zone: str, lfg: int):
    cursor = conn.cursor()
    now = datetime.now()

    # First, try to insert the record
    cursor.execute('''
    INSERT OR IGNORE INTO players (level, class, name, race, guild, zone, lfg)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (level, class_, name, race, guild, zone, lfg))

    # Then, update the existing record (if any)
    cursor.execute('''
    UPDATE players 
    SET level = ?, class = ?, race = ?, guild = ?, zone = ?, lfg = ?, last_updated = ?
    WHERE name = ?
    ''', (level, class_, race, guild, zone, lfg, now, name))

    print('Inserted or updated player:', name)
    conn.commit()


def dump_db_to_json(conn, json_path):
    # Connect to SQLite database
    cursor = conn.cursor()

    # Fetch all players
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()

    # Convert to list of dicts for easier JSON serialization
    col_names = [desc[0] for desc in cursor.description]
    players_list = [dict(zip(col_names, player)) for player in players]

    output = {
        "last_updated": time.time(),  # This will give the current timestamp in seconds since epoch
        "data": players_list
    }

    # Dump to JSON file
    with open(json_path, 'w') as f:
        json.dump(output, f)

    # Create 'data' directory if it doesn't exist
    archive_directory = 'data'
    if not os.path.exists(archive_directory):
        os.makedirs(archive_directory)

    # Archive the existing data.json to the 'data' directory with a filename based on 'last_updated'
    archive_filename = datetime.fromtimestamp(output["last_updated"]).strftime('%Y-%m-%d %H-%M-%S') + '.json'
    shutil.copy2(json_path, os.path.join(archive_directory, archive_filename))

    conn.close()

    conn.close()


def git_push(file_path, commit_message="Updated data"):
    try:
        subprocess.run(['git', 'add', file_path], check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)  # Change to 'main'
    except subprocess.CalledProcessError as e:
        print(f"Error while pushing to Git: {e}")


def parse_log(conn: sqlite3.Connection, log: str):
    # Get the current time
    now = datetime.now()

    for line in log.splitlines():
        # Extract timestamp from the line
        timestamp_match = re.search(TIME_PATTERN, line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(2)
            line_timestamp = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")

            # Check if the line timestamp is within the last 10 minutes
            if now - line_timestamp <= timedelta(minutes=10):
                # Parse the player data
                match = re.search(PATTERN, line)
                if match:
                    afk, level, class_, name, race, guild, zone, lfg = match.groups()
                    guild = guild or ""  # Set to empty string if guild is None
                    afk = True if afk else False  # Convert afk to boolean
                    lfg = True if lfg else False  # Convert lfg to boolean
                    print(match.groups())
                    upsert_player(conn, int(level) if level != "ANONYMOUS" else None, class_, name, race, guild, zone, lfg)


class LogHandler(FileSystemEventHandler):
    def __init__(self, filepath):
        self.filepath = filepath

    def on_modified(self, event):
        if event.src_path == self.filepath:
            file_modified_event.set()


def setup_and_monitor_file(filepath):
    print("Monitoring started")  # Debugging line
    # Watch the directory for modifications instead of the file
    directory_to_watch = os.path.dirname(filepath)
    event_handler = LogHandler(filepath)  # Still use the filepath in the handler to filter events
    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Keep the thread alive
    except:
        observer.stop()
    observer.join()


def fetch_all_players(conn):
    cursor = conn.cursor()
    query = "SELECT level, class, name, race, guild, zone, lfg FROM players ORDER BY level DESC"
    cursor.execute(query)
    results = cursor.fetchall()
    return results


def copy_to_clipboard(conn):
    data = fetch_all_players(conn)
    formatted_data = [", ".join(map(str, row)) for row in data]
    clipboard_data = "\n".join(formatted_data)

    # Copying data to clipboard using tkinter
    app = tk.Tk()
    app.withdraw()
    app.clipboard_clear()
    app.clipboard_append(clipboard_data)
    app.update()  # This is necessary in some cases to make clipboard work
    app.destroy()

def query_players(conn, level_start=None, level_end=None, class_=None, name=None, race=None, zone=None, guild=None, lfg=None):
    cursor = conn.cursor()

    current_time = datetime.now()
    time_limit = current_time - timedelta(minutes=10)

    query = "SELECT level, class, name, race, guild, zone, lfg FROM players WHERE last_updated >= ?"
    parameters = [time_limit]

    if level_start and level_end:
        query += " AND level BETWEEN ? AND ?"
        parameters.extend([level_start, level_end])

    if class_:
        query += " AND class = ?"
        parameters.append(class_)

    if name:
        query += " AND name LIKE ?"
        parameters.append(f"%{name}%")

    if race:
        query += " AND race = ?"
        parameters.append(race)

    if zone:
        query += " AND zone LIKE ?"
        parameters.append(f"%{zone}%")

    if guild:
        query += " AND guild LIKE ?"
        parameters.append(f"%{guild}%")

    if lfg is not None:  # If LFG is provided in the input
        query += " AND lfg = ?"
        parameters.append(1)

    cursor.execute(query, parameters)
    results = cursor.fetchall()
    return results


DARK_MODE_BG = "#2E2E2E"
DARK_MODE_TEXT = "#FFFFFF"
DARK_MODE_FIELD = "#373737"
DARK_MODE_BTN = "#555555"
DARK_MODE_BTN_TEXT = "#FFFFFF"


class PlayerQueryApp:
    def __init__(self, conn):
        self.conn = conn

        with open(filepath, "r") as f:
            self.file_position = f.tell()

        self.app = tk.Tk()
        self.app.title("Player Query")

        self.sorting_orders = {}  # Dictionary to keep track of sorting order for each column

        self.setup_ui()

        # Start the periodic file check
        self.check_file_changes()

        self.middle_of_screen()

        self.app.mainloop()

    def middle_of_screen(self):
        self.app.update_idletasks()
        width = self.app.winfo_width()
        height = self.app.winfo_height()
        x = (self.app.winfo_screenwidth() // 2) - (width // 2)
        y = (self.app.winfo_screenheight() // 2) - (height // 2)
        self.app.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.app.attributes("-topmost", True)

    def on_upload(self):
        # Specify your paths
        json_path = 'data.json'

        dump_db_to_json(self.conn, json_path)  # Dump in-memory database to a JSON file
        git_push(json_path, 'Uploaded latest data from SQLite database')  # Push the JSON to Git

    def check_file_changes(self):
        if file_modified_event.is_set():
            with open(filepath, "r") as f:
                # Seek to the last known position
                if self.file_position is not None:
                    f.seek(self.file_position)
                log = f.read()
                self.file_position = f.tell()  # Remember the current position

            parse_log(conn, log)
            file_modified_event.clear()  # Clear the event
        self.app.after(1000, self.check_file_changes)

    def search(self):
        level_start = self.level_start_entry.get()
        level_end = self.level_end_entry.get()
        class_ = self.class_entry.get()
        name = self.name_entry.get()
        race = self.race_entry.get()
        zone = self.zone_entry.get()
        guild = self.guild_entry.get()  # Getting the guild value
        lfg = True if self.lfg_var.get() else None  # Getting the LFG status; if unchecked, it'll be treated as None

        self.results.delete(*self.results.get_children())
        rows = query_players(self.conn, level_start, level_end, class_, name, race, zone, guild, lfg)
        for row in rows:
            self.results.insert("", "end", values=row)

        # Update the number of rows label
        self.num_rows_label.config(text=f"Number of rows: {len(rows)}")

    def sort_treeview(self, col):
        # Get all data in the treeview
        data = [(self.results.set(child, col), child) for child in self.results.get_children('')]

        # Toggle sorting order and sort the data
        order = "desc" if self.sorting_orders[col] == "normal" else "normal"
        data.sort(reverse=(order == "desc"))

        # Rearrange items in the treeview based on the sorted order
        for indx, (_, child) in enumerate(data):
            self.results.move(child, '', indx)

        # Update the sorting order for next time
        self.sorting_orders[col] = order
        # Set the heading to change between ascending/descending
        self.results.heading(col, command=lambda _col=col: self.sort_treeview(_col),
                             text=col + (" ▼" if order == "desc" else " ▲"))

    def setup_ui(self):
        # Define a style for ttk elements
        style = ttk.Style()

        style.theme_use("default")

        style.configure("TFrame", background=DARK_MODE_BG)
        style.configure("TLabel", background=DARK_MODE_BG, foreground=DARK_MODE_TEXT)
        style.configure("TEntry", background="#FFFFFF", foreground="#000000")
        style.configure("TButton", background=DARK_MODE_BTN, foreground=DARK_MODE_BTN_TEXT)
        style.configure("TCheckbutton", foreground=DARK_MODE_TEXT)
        style.configure('DarkMode.TCheckbutton', background=DARK_MODE_BG, foreground=DARK_MODE_TEXT,
                        bordercolor=DARK_MODE_BG, darkcolor=DARK_MODE_BG, lightcolor=DARK_MODE_TEXT)
        style.map('DarkMode.TCheckbutton', background=[('active', DARK_MODE_BG), ('pressed', DARK_MODE_TEXT)],
                  foreground=[('active', DARK_MODE_TEXT), ('pressed', DARK_MODE_BG)])

        style.configure("Treeview", background=DARK_MODE_BG, fieldbackground=DARK_MODE_BG, foreground=DARK_MODE_TEXT)
        style.configure("Treeview.Heading", background=DARK_MODE_BTN, foreground=DARK_MODE_TEXT)

        # Window/Frame background
        self.app.configure(bg=DARK_MODE_BG)

        # Level Start
        ttk.Label(self.app, text="Level Start:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.level_start_entry = ttk.Entry(self.app)
        self.level_start_entry.grid(row=0, column=1, padx=5, pady=5)

        # Level End
        ttk.Label(self.app, text="Level End:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.level_end_entry = ttk.Entry(self.app)
        self.level_end_entry.grid(row=1, column=1, padx=5, pady=5)

        # Class, Name, Race, Guild, Zone Entries and Labels
        labels_texts = ["Class:", "Name:", "Race:", "Guild:", "Zone:"]
        self.entries = []
        for idx, label_text in enumerate(labels_texts, 2):
            ttk.Label(self.app, text=label_text).grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(self.app)
            entry.grid(row=idx, column=1, padx=5, pady=5)
            self.entries.append(entry)

        self.class_entry, self.name_entry, self.race_entry, self.guild_entry, self.zone_entry = self.entries

        # LFG Checkbox
        self.lfg_var = tk.IntVar()
        lfg_checkbox = ttk.Checkbutton(self.app, text="LFG", variable=self.lfg_var, style='DarkMode.TCheckbutton')
        lfg_checkbox.grid(row=7, column=0, padx=5, pady=5)

        # Search Button
        ttk.Button(self.app, text="Search", command=self.search).grid(row=7, column=1, pady=10)

        # Treeview Table
        columns = ("Level", "Class", "Name", "Race", "Guild", "Zone", "LFG")
        self.results = ttk.Treeview(self.app, columns=columns, show="headings", height=10)
        self.results.grid(row=8, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.app, orient="vertical", command=self.results.yview)
        self.scrollbar.grid(row=8, column=2, sticky='ns')
        self.results.configure(yscrollcommand=self.scrollbar.set)
        self.results.column("Level", width=50)
        self.results.column("Class", width=125)
        self.results.column("Name", width=125)
        self.results.column("Race", width=100)
        self.results.column("Guild", width=150)
        self.results.column("Zone", width=100)
        self.results.column("LFG", width=50)

        for col in columns:
            self.results.heading(col, text=col, command=lambda _col=col: self.sort_treeview(_col))
            self.sorting_orders[col] = "normal"

        # Label to display the number of rows returned
        self.num_rows_label = ttk.Label(self.app, text="Number of rows: 0", background=DARK_MODE_BG,
                                        foreground=DARK_MODE_TEXT)
        self.num_rows_label.grid(row=9, column=0, columnspan=1, pady=10)

        # ttk.Button(self.app, text="Copy to Clipboard", command=lambda: copy_to_clipboard(self.conn)).grid(row=10,
        #                                                                                                   column=0,
        #                                                                                                   pady=10)

        ttk.Button(self.app, text="Upload", command=self.on_upload).grid(row=9, column=1, pady=10)


def test_regex():

    test_lines = [
        # "[Tue Oct 10 12:10:21 2023] [11 Magician] Devana (High Elf)  ZONE: crushbone",
        # "[Tue Oct 10 12:10:21 2023] [11 Magician] Layzie (Dark Elf)  ZONE: nektulos  ",
        "[Tue Oct 10 12:43:55 2023] [11 Magician] Devana (High Elf)  ZONE: gfaydark   LFG",
        "[Tue Oct 10 12:43:55 2023]  AFK [11 Magician] Layzie (Dark Elf)  ZONE: nektulos  ",
        "[Tue Oct 10 12:32:07 2023] [1 Shadow Knight] Syck (Ogre)  ZONE: oggok  ",
        "[Tue Oct 10 16:49:58 2023] [22 Cleric] Demiaan (Dark Elf) <Seekers of Souls> ZONE:    LFG"
    ]

    for line in test_lines:
        match = re.search(PATTERN, line)
        if match:
            print("Matched:", match.groups())
        else:
            print("No match for line:", line)


if __name__ == "__main__":
    test_regex()
    # Filepath
    filepath = "C:\\Users\\clayt\\AppData\\Local\\VirtualStore\\Program Files (x86)\\Sony\\Project Quarm\\eqlog_Rune_pq.proj.txt"

    # Create and setup the in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    setup_database(conn)

    # Start only the watchdog thread
    threading.Thread(target=setup_and_monitor_file, args=(filepath,)).start()

    PlayerQueryApp(conn)

    # Close the database connection after exiting the UI
    conn.close()
