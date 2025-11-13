import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import feedparser
import webbrowser
import time
import json
import os 

# --- Configuration & File Paths ---
CONFIG_FILE = "rss_config.json"

# --- Default RSS Feeds (Used if no config file or default list is set) ---
DEFAULT_FEEDS = {
    "Technology": "https://www.theverge.com/rss/index.xml",
    "Finance": "https://www.nytimes.com/services/xml/rss/nyt/World.xml",
    "World": "http://feeds.bbci.co.uk/news/world/rss.xml"
}

# --- Global State Variables ---
CURRENT_FEEDS = {} 
SAVED_LISTS = {}
DEFAULT_LIST_NAME = "Standard Default"
ROOT = None 

# --- File I/O for Feed Management ---

def load_config():
    """Loads saved lists and the default list name from the config file."""
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                SAVED_LISTS = data.get("saved_lists", {})
                DEFAULT_LIST_NAME = data.get("default_list_name", "Standard Default")
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", "Error reading or parsing the config file. Using default settings.")
    
    if DEFAULT_LIST_NAME in SAVED_LISTS:
        CURRENT_FEEDS = SAVED_LISTS[DEFAULT_LIST_NAME].copy()
    else:
        SAVED_LISTS["Standard Default"] = DEFAULT_FEEDS.copy()
        DEFAULT_LIST_NAME = "Standard Default"
        CURRENT_FEEDS = DEFAULT_FEEDS.copy()
        save_config() 

def save_config():
    """Saves the current state of lists and the default name to the config file."""
    global SAVED_LISTS, DEFAULT_LIST_NAME

    data = {
        "saved_lists": SAVED_LISTS,
        "default_list_name": DEFAULT_LIST_NAME
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        messagebox.showerror("Save Error", "Could not write to the config file.")

# --- RSS Fetching Logic ---

def fetch_and_display_news(feed_url, container, category_name):
    """Fetches, parses, and displays news from an RSS feed."""
    
    for widget in container.winfo_children():
        widget.destroy()

    ttk.Label(container, text=f"--- Latest {category_name} Headlines ---", 
              font=("Arial", 12, "bold"), foreground="#4A148C").pack(pady=(10, 5), padx=10, fill='x')

    try:
        feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
        
        if feed.bozo and feed.bozo_exception.__class__.__name__ not in ('NonXMLContentType', 'CharacterEncodingOverride'):
             messagebox.showerror("Feed Error", f"Could not parse feed for **{category_name}** due to a formatting error.")
             return

        entries = feed.entries
        
        if not entries:
            ttk.Label(container, text="No news entries found in the feed.", 
                      foreground="red").pack(pady=10)
            return

        count = 0
        for entry in entries:
            if count >= 15:
                break
            
            headline = entry.get('title', 'No Title Available')
            link = entry.get('link', '#')
            
            summary_text = entry.get('summary', entry.get('description', ''))
            summary = summary_text.split('.')[0] + '...' if summary_text else ''
            
            headline_label = ttk.Label(container, text=headline, wraplength=550, 
                                       font=("Arial", 10, "bold"), cursor="hand2", foreground="#1A237E")
            headline_label.pack(anchor='w', padx=15, pady=(5, 0))
            
            summary_label = ttk.Label(container, text=summary, wraplength=550, 
                                      font=("Arial", 9, "italic"), foreground="#37474F")
            summary_label.pack(anchor='w', padx=15, pady=(0, 2))
            
            headline_label.bind("<Button-1>", lambda e, l=link: webbrowser.open_new(l)) 
            
            ttk.Separator(container, orient='horizontal').pack(fill='x', padx=10, pady=2)
            
            count += 1
            
    except Exception as e:
        messagebox.showerror("Fetching Error", f"An error occurred while fetching the RSS feed:\n{e}")
    finally:
        time.sleep(0.1)


# --- GUI Management Functions ---

def update_category_buttons(button_frame, scrollable_frame):
    """Clears and redraws the buttons based on the CURRENT_FEEDS list."""
    for widget in button_frame.winfo_children():
        widget.destroy()

    ttk.Button(button_frame, text="Manage Current Feeds", 
               command=lambda: feed_manager_window(button_frame, scrollable_frame)).pack(side='right', padx=5, fill='y')

    if not CURRENT_FEEDS:
        ttk.Label(button_frame, text="No feeds loaded. Use the File Menu or 'Manage Feeds' to add one.", foreground="red").pack(side='left', padx=10)
        return

    for name, url in CURRENT_FEEDS.items():
        button = ttk.Button(
            button_frame, 
            text=name, 
            command=lambda u=url, n=name: fetch_and_display_news(u, scrollable_frame, n)
        )
        button.pack(side='left', expand=True, fill='x', padx=5)

    if CURRENT_FEEDS:
        initial_category_url = list(CURRENT_FEEDS.values())[0]
        initial_category_name = list(CURRENT_FEEDS.keys())[0]
        fetch_and_display_news(initial_category_url, scrollable_frame, initial_category_name)


def feed_manager_window(button_frame, scrollable_frame):
    """Creates a Toplevel window for managing the currently active list (add/remove)."""
    
    manager_root = tk.Toplevel(ROOT)
    manager_root.title("Manage Current RSS Feeds")
    manager_root.geometry("500x300")
    manager_root.grab_set() 

    frame = ttk.Frame(manager_root, padding="10")
    frame.pack(fill='both', expand=True)

    listbox_frame = ttk.Frame(frame)
    listbox_frame.pack(fill='both', expand=True, pady=5)
    
    listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    feed_listbox = tk.Listbox(listbox_frame, yscrollcommand=listbox_scrollbar.set, selectmode=tk.SINGLE)
    listbox_scrollbar.config(command=feed_listbox.yview)
    
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    feed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_listbox():
        feed_listbox.delete(0, tk.END)
        for name, url in CURRENT_FEEDS.items():
            feed_listbox.insert(tk.END, f"{name}: {url}")

    button_controls = ttk.Frame(frame)
    button_controls.pack(fill='x', pady=5)

    ttk.Button(button_controls, text="Add New Feed", 
               command=lambda: add_feed(populate_listbox, button_frame, scrollable_frame)).pack(side='left', expand=True, padx=5)
    ttk.Button(button_controls, text="Remove Selected", 
               command=lambda: remove_feed(feed_listbox, populate_listbox, button_frame, scrollable_frame)).pack(side='right', expand=True, padx=5)
    
    populate_listbox()
    manager_root.protocol("WM_DELETE_WINDOW", manager_root.destroy)


def show_saved_lists_window(button_frame, scrollable_frame):
    """Creates a window to load, set default, or delete saved lists."""
    
    saved_root = tk.Toplevel(ROOT)
    saved_root.title("Saved Feed Lists")
    saved_root.geometry("450x300")
    saved_root.grab_set() 
    
    frame = ttk.Frame(saved_root, padding="10")
    frame.pack(fill='both', expand=True)
    
    ttk.Label(frame, text="Select a list to manage:", font=("Arial", 10, "bold")).pack(anchor='w', pady=(0, 5))
    
    listbox_frame = ttk.Frame(frame)
    listbox_frame.pack(fill='both', expand=True, pady=5)
    
    listbox_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    listbox = tk.Listbox(listbox_frame, yscrollcommand=listbox_scrollbar.set, selectmode=tk.SINGLE)
    listbox_scrollbar.config(command=listbox.yview)
    
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_saved_listbox():
        listbox.delete(0, tk.END)
        for name in sorted(SAVED_LISTS.keys()):
            display_name = f"{name} (Default)" if name == DEFAULT_LIST_NAME else name
            listbox.insert(tk.END, display_name)
    
    populate_saved_listbox()

    button_controls = ttk.Frame(frame)
    button_controls.pack(fill='x', pady=5)

    ttk.Button(button_controls, text="Load List", 
               command=lambda: load_list(listbox, populate_saved_listbox, button_frame, scrollable_frame, saved_root)).pack(side='left', expand=True, padx=5)
    ttk.Button(button_controls, text="Set as Default", 
               command=lambda: set_default_list(listbox, populate_saved_listbox)).pack(side='left', expand=True, padx=5)
    ttk.Button(button_controls, text="Delete List", 
               command=lambda: delete_list(listbox, populate_saved_listbox)).pack(side='left', expand=True, padx=5)

    saved_root.protocol("WM_DELETE_WINDOW", saved_root.destroy)


# --- Helpers ---

def add_feed(refresh_listbox, button_frame, scrollable_frame):
    """Opens a dialog to add a new feed without validation."""
    
    name = simpledialog.askstring("Add Feed", "Enter the Category Name (e.g., Tech News):", parent=ROOT)
    if not name:
        return
    
    url = simpledialog.askstring("Add Feed", f"Enter the RSS URL for **{name}**:", parent=ROOT)
    if not url:
        return
    
    if name in CURRENT_FEEDS:
        messagebox.showwarning("Warning", f"A feed named '{name}' already exists. Please choose a unique name.")
        return

    # No validation check
    
    CURRENT_FEEDS[name] = url
    refresh_listbox()
    update_category_buttons(button_frame, scrollable_frame)
    messagebox.showinfo("Success", f"Feed '{name}' has been added to the current list.")

def remove_feed(listbox, refresh_listbox, button_frame, scrollable_frame):
    """Removes the selected feed from the current list."""
    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)
        
        name = selected_item.split(':')[0].strip()

        if name in CURRENT_FEEDS:
            del CURRENT_FEEDS[name]
            refresh_listbox()
            update_category_buttons(button_frame, scrollable_frame)
    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to remove.")


def save_current_list():
    """Saves the CURRENT_FEEDS dictionary under a user-provided name."""
    global SAVED_LISTS
    
    list_name = simpledialog.askstring("Save List", "Enter a name to save the current feed list:", parent=ROOT)

    if not list_name:
        return
    
    if not CURRENT_FEEDS:
        messagebox.showwarning("Warning", "The current list is empty and cannot be saved.")
        return

    SAVED_LISTS[list_name] = CURRENT_FEEDS.copy()
    save_config()
    messagebox.showinfo("Saved", f"Current feed list saved as '{list_name}'.")

def load_list(listbox, refresh_saved_listbox, button_frame, scrollable_frame, saved_root):
    """Loads a selected saved list into CURRENT_FEEDS and updates the main window."""
    global CURRENT_FEEDS

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)
        
        list_name = selected_item.split(' (Default)')[0].strip() 

        if list_name in SAVED_LISTS:
            if messagebox.askyesno("Load Confirmation", f"Are you sure you want to replace the current feeds with list '{list_name}'?"):
                CURRENT_FEEDS = SAVED_LISTS[list_name].copy()
                update_category_buttons(button_frame, scrollable_frame)
                messagebox.showinfo("List Loaded", f"Successfully loaded list: '{list_name}'.")
                saved_root.destroy()
        else:
             messagebox.showwarning("Error", "The selected list was not found.")
    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to load.")


def set_default_list(listbox, refresh_saved_listbox):
    """Sets a selected saved list as the default to load on startup."""
    global DEFAULT_LIST_NAME

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)

        list_name = selected_item.split(' (Default)')[0].strip() 

        if list_name in SAVED_LISTS:
            DEFAULT_LIST_NAME = list_name
            save_config()
            refresh_saved_listbox() 
            messagebox.showinfo("Default Set", f"'{list_name}' is now the default list.")
    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to set as default.")

def delete_list(listbox, refresh_saved_listbox):
    """Deletes a selected saved list."""
    global SAVED_LISTS, DEFAULT_LIST_NAME

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)

        list_name = selected_item.split(' (Default)')[0].strip()

        if list_name == DEFAULT_LIST_NAME:
            messagebox.showwarning("Cannot Delete", "Cannot delete the current **default list**.")
            return

        if list_name in SAVED_LISTS:
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete the list '{list_name}'?"):
                del SAVED_LISTS[list_name]
                save_config()
                refresh_saved_listbox() 
                messagebox.showinfo("Deleted", f"List '{list_name}' has been deleted.")
        else:
            messagebox.showwarning("Error", "The selected list was not found.")

    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to delete.")


# --- Tkinter GUI Setup ---

def setup_gui():
    """Sets up the main Tkinter window and widgets, including the File menu."""
    global ROOT 
    
    load_config()

    ROOT = tk.Tk()
    ROOT.title("Feedparser RSS News Viewer")
    ROOT.geometry("700x700")
    
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10, "bold"), padding=8, background="#EDE7F6")
    
    # --- Menu Bar ---
    menubar = tk.Menu(ROOT)
    ROOT.config(menu=menubar)
    
    button_frame = ttk.Frame(ROOT)
    main_frame = ttk.Frame(ROOT)
    canvas = tk.Canvas(main_frame)
    scrollable_frame = ttk.Frame(canvas)

    # --- File Menu ---
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    
    file_menu.add_command(label="Save Current List...", command=lambda: save_current_list())
    file_menu.add_separator()
    
    file_menu.add_command(label="Load/Manage Saved Lists...", 
                          command=lambda: show_saved_lists_window(button_frame, scrollable_frame))
    
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=ROOT.quit)

    # --- Button Frame ---
    button_frame.pack(fill='x', padx=10, pady=(10, 5))
    
    # --- Main Content Frame and Scrollbar ---
    main_frame.pack(fill='both', expand=True, padx=10)

    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    update_category_buttons(button_frame, scrollable_frame)
    
    ROOT.mainloop()

if __name__ == "__main__":
    setup_gui()