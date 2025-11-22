import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import feedparser
import webbrowser
import time
import json
import os 
import datetime 

# ========================================
# CONFIGURATION & FILE PATHS
# ========================================

CONFIG_FILE = "rss_config.json"

# ========================================
# DEFAULT RSS FEEDS
# Used when no configuration file exists or default list is not set
# ========================================

DEFAULT_FEEDS = {
    "Technology": "https://www.theverge.com/rss/index.xml",
    "Finance": "https://www.valuewalk.com/feed",
    "World": "http://feeds.bbci.co.uk/news/world/rss.xml"
}

# ========================================
# GLOBAL STATE VARIABLES
# ========================================

CURRENT_FEEDS = {}  # Currently active RSS feeds
SAVED_LISTS = {}  # Dictionary of saved feed lists
DEFAULT_LIST_NAME = "Standard Default"  # Name of the default list to load on startup
CURRENT_THEME = "light"  # Current theme mode: "light" or "dark"
ROOT = None  # Reference to the main Tkinter window

# --- GLOBAL VARIABLES FOR WEATHER/TIME ---
# Permanent, user-editable list of all available locations
DEFAULT_LOCATIONS = [
    "Stockholm, SE", 
    "London, UK", 
    "New York, US", 
    "Tokyo, JP",
    "Berlin, DE", 
    "Sydney, AU",
    "Uppsala, SE", 
    "Gothenburg, SE", 
    "Malmö, SE",
    "Huddinge, SE"
]

CURRENT_WEATHER_LOCATION = "Stockholm, SE" # DEFAULT to Stockholm, SE
DATETIME_LABEL = None # Widget reference for real-time clock
WEATHER_LABEL = None  # Widget reference for weather display
# ---------------------------------------------

# --- GLOBAL VARIABLES FOR AUTOMATIC REFRESH ---
ACTIVE_FEED_URL = None
ACTIVE_FEED_CONTAINER = None
REFRESH_INTERVAL_MS = 300000 # 5 minutes (300,000 ms) 
# ----------------------------------------------
# --- GLOBAL VARIABLES FOR PAGINATION ---
ALL_ARTICLES = {} # {feed_url: [list of up to 100 article entries]}
CURRENT_PAGE = 1
ARTICLES_PER_PAGE = 12 # Number of articles to show per page
# ---------------------------------------------


# ========================================
# THEME DEFINITIONS
# Color schemes for light and dark modes
# ========================================

THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "fg": "#000000",
        "button_bg": "#EDE7F6",
        "button_fg": "#000000",
        "button_active_bg": "#D1C4E9",
        "headline_fg": "#1A237E",
        "summary_fg": "#37474F",
        "category_fg": "#4A148C",
        "canvas_bg": "#FFFFFF",
        "frame_bg": "#F5F5F5",
        "entry_bg": "#FFFFFF",
        "entry_fg": "#000000",
        "listbox_bg": "#FFFFFF",
        "listbox_fg": "#000000",
        "separator_bg": "#E0E0E0",
        "menu_bg": "#FFFFFF",
        "menu_fg": "#000000",
        "menu_active_bg": "#EDE7F6",
        "error_fg": "#D32F2F"
    },
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#E0E0E0",
        "button_bg": "#2D2D30",
        "button_fg": "#E0E0E0",
        "button_active_bg": "#3E3E42",
        "headline_fg": "#82B1FF",
        "summary_fg": "#B0BEC5",
        "category_fg": "#CE93D8",
        "canvas_bg": "#252526",
        "frame_bg": "#2D2D30",
        "entry_bg": "#3E3E42",
        "entry_fg": "#E0E0E0",
        "listbox_bg": "#2D2D30",
        "listbox_fg": "#E0E0E0",
        "separator_bg": "#3E3E42",
        "menu_bg": "#2D2D30",
        "menu_fg": "#E0E0E0",
        "menu_active_bg": "#3E3E42",
        "error_fg": "#FF6B6B"
    }
}

# ========================================
# FILE I/O FOR CONFIGURATION MANAGEMENT
# ========================================

def load_config():
    """
    Loads saved lists, theme preference, and weather location data 
    from the config file. If the config file doesn't exist, initializes with 
    default values.
    """
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                SAVED_LISTS = data.get("saved_lists", {})
                DEFAULT_LIST_NAME = data.get("default_list_name", "Standard Default")
                CURRENT_THEME = data.get("theme", "light")
                
                # Load the weather location preferences
                DEFAULT_LOCATIONS = data.get("default_locations", DEFAULT_LOCATIONS) # Load permanent list
                CURRENT_WEATHER_LOCATION = data.get("weather_location", "Stockholm, SE") # Default to Stockholm
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", "Error reading or parsing the config file. Using default settings.")
    
    # Load the default feed list into current feeds
    if DEFAULT_LIST_NAME in SAVED_LISTS:
        CURRENT_FEEDS = SAVED_LISTS[DEFAULT_LIST_NAME].copy()
    else:
        # Initialize with default feeds if no saved lists exist
        SAVED_LISTS["Standard Default"] = DEFAULT_FEEDS.copy()
        DEFAULT_LIST_NAME = "Standard Default"
        CURRENT_FEEDS = DEFAULT_FEEDS.copy()
        save_config() 

def save_config():
    """
    Saves the current state of lists, theme, and weather location data 
    to the config file.
    """
    global SAVED_LISTS, DEFAULT_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS

    data = {
        "saved_lists": SAVED_LISTS,
        "default_list_name": DEFAULT_LIST_NAME,
        "theme": CURRENT_THEME,
        "weather_location": CURRENT_WEATHER_LOCATION, # Save current location
        "default_locations": DEFAULT_LOCATIONS # Save the permanent list
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        messagebox.showerror("Save Error", "Could not write to the config file.")

# ========================================
# THEME MANAGEMENT
# ========================================

def configure_ttk_theme():
    """
    Configures ttk widget styles based on the current theme.
    This must be called whenever the theme changes.
    """
    theme = THEMES[CURRENT_THEME]
    style = ttk.Style()
    
    # Use a theme that allows more customization
    try:
        style.theme_use('clam')  # 'clam' theme allows better color customization
    except:
        pass
    
    # Configure TButton style with all states
    style.configure("TButton",
                    background=theme["button_bg"],
                    foreground=theme["button_fg"],
                    bordercolor=theme["button_bg"],
                    darkcolor=theme["button_bg"],
                    lightcolor=theme["button_bg"],
                    borderwidth=1,
                    focuscolor='none',
                    font=("Arial", 10, "bold"),
                    padding=8)
    
    # Map button states for hover and press
    style.map("TButton",
              background=[('active', theme["button_active_bg"]),
                          ('pressed', theme["button_active_bg"]),
                          ('!active', theme["button_bg"])],
              foreground=[('active', theme["button_fg"]),
                          ('pressed', theme["button_fg"]),
                          ('!active', theme["button_fg"])],
              bordercolor=[('active', theme["button_active_bg"]),
                           ('!active', theme["button_bg"])],
              darkcolor=[('active', theme["button_active_bg"]),
                         ('!active', theme["button_bg"])],
              lightcolor=[('active', theme["button_active_bg"]),
                          ('!active', theme["button_bg"])])
    
    # Configure style for active page button (used in pagination)
    style.configure("Active.TButton", 
                    background=theme["headline_fg"],
                    foreground=theme["bg"], 
                    bordercolor=theme["headline_fg"])

    # Map button states for hover and press on active button
    style.map("Active.TButton",
              background=[('active', theme["headline_fg"]),
                          ('pressed', theme["headline_fg"]),
                          ('!active', theme["headline_fg"])],
              foreground=[('active', theme["bg"]),
                          ('pressed', theme["bg"]),
                          ('!active', theme["bg"])])
    
    # Configure TFrame style
    style.configure("TFrame",
                    background=theme["frame_bg"])
    
    # Configure TLabel style
    style.configure("TLabel",
                    background=theme["frame_bg"],
                    foreground=theme["fg"])
    
    # Configure TSeparator style
    style.configure("TSeparator",
                    background=theme["separator_bg"])
    
    # Configure Scrollbar
    style.configure("Vertical.TScrollbar",
                    background=theme["frame_bg"],
                    troughcolor=theme["bg"],
                    bordercolor=theme["frame_bg"],
                    arrowcolor=theme["fg"])
    
    style.map("Vertical.TScrollbar",
              background=[('active', theme["button_active_bg"]),
                          ('!active', theme["frame_bg"])])

def apply_theme_to_widget(widget):
    """
    Recursively applies theme colors to a widget and all its children.
    
    Args:
        widget: The widget to apply the theme to
    """
    theme = THEMES[CURRENT_THEME]
    widget_class = widget.winfo_class()
    
    try:
        # Apply theme based on widget type
        if widget_class == "Toplevel":
            widget.configure(bg=theme["bg"])
        elif widget_class in ("Frame", "Labelframe"):
            widget.configure(bg=theme["frame_bg"])
        elif widget_class == "TFrame":
            # TTK Frame - handled by style
            pass
        elif widget_class == "Label":
            # Check if it's an error label by foreground color
            current_fg = widget.cget("foreground")
            if "red" in str(current_fg).lower() or "#D32F2F" in str(current_fg) or "#FF6B6B" in str(current_fg):
                widget.configure(bg=theme["frame_bg"], fg=theme["error_fg"])
            else:
                widget.configure(bg=theme["frame_bg"], fg=theme["fg"])
        elif widget_class == "TLabel":
            # TTK Label - handled by style
            pass
        elif widget_class == "Canvas":
            widget.configure(bg=theme["canvas_bg"], highlightthickness=0)
        elif widget_class == "Listbox":
            widget.configure(
                bg=theme["listbox_bg"], 
                fg=theme["listbox_fg"],
                selectbackground=theme["button_active_bg"],
                selectforeground=theme["fg"],
                highlightthickness=0
            )
        elif widget_class == "Text":
            widget.configure(
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground=theme["fg"],
                selectbackground=theme["button_active_bg"],
                selectforeground=theme["fg"]
            )
        elif widget_class == "Entry":
            widget.configure(
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground=theme["fg"],
                selectbackground=theme["button_active_bg"],
                selectforeground=theme["fg"]
            )
        elif widget_class == "Button":
            widget.configure(
                bg=theme["button_bg"],
                fg=theme["button_fg"],
                activebackground=theme["button_active_bg"],
                activeforeground=theme["button_fg"],
                highlightthickness=0
            )
        elif widget_class == "Scrollbar":
            widget.configure(
                bg=theme["frame_bg"],
                troughcolor=theme["bg"],
                activebackground=theme["button_active_bg"]
            )
        elif widget_class == "Menu":
            widget.configure(
                bg=theme["menu_bg"],
                fg=theme["menu_fg"],
                activebackground=theme["menu_active_bg"],
                activeforeground=theme["menu_fg"]
            )
    except tk.TclError:
        # Some widgets may not support certain configuration options
        pass
    
    # Recursively apply to all children
    for child in widget.winfo_children():
        apply_theme_to_widget(child)

def apply_theme():
    """
    Applies the current theme to all widgets in the application.
    Updates colors for the main window, canvas, frames, and all child widgets.
    """
    global ROOT, DATETIME_LABEL, WEATHER_LABEL
    
    if ROOT is None:
        return
    
    theme = THEMES[CURRENT_THEME]
    
    # Configure TTK styles first
    configure_ttk_theme()
    
    # Apply theme to root window
    ROOT.configure(bg=theme["bg"])
    
    # Apply theme to menu bar
    try:
        menubar = ROOT.nametowidget(ROOT.cget("menu"))
        apply_theme_to_widget(menubar)
    except:
        pass
    
    # Apply theme to all widgets recursively
    apply_theme_to_widget(ROOT)

    # Manually update Date/Time/Weather labels if they exist
    if DATETIME_LABEL and WEATHER_LABEL:
        update_datetime_label()
        update_weather_display()

def toggle_theme(button_frame, scrollable_frame):
    """
    Toggles between light and dark theme modes.
    Saves the preference and reapplies the theme to all widgets.
    
    Args:
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame containing news content
    """
    global CURRENT_THEME
    
    # Toggle between light and dark
    CURRENT_THEME = "dark" if CURRENT_THEME == "light" else "light"
    
    # Save the preference
    save_config()
    
    # Apply the new theme
    apply_theme()
    
    # Refresh the display to update colors
    update_category_buttons(button_frame, scrollable_frame)

# ========================================
# DATE/TIME AND WEATHER FUNCTIONS
# ========================================

def update_datetime_label():
    """Updates the DATETIME_LABEL with the current date and time (real-time)."""
    global DATETIME_LABEL
    theme = THEMES[CURRENT_THEME]
    
    if DATETIME_LABEL:
        current_time = datetime.datetime.now().strftime("%A, %B %d, %Y | %H:%M:%S")
        DATETIME_LABEL.config(
            text=current_time,
            bg=theme["frame_bg"],
            fg=theme["fg"]
        )
    
    # Schedule the next update after 1000 milliseconds (1 second)
    if ROOT:
        ROOT.after(1000, update_datetime_label)

def fetch_weather(location):
    """
    Mocks fetching weather data for a given location.
    
    NOTE: Replace this function with actual API calls to a weather service.
    
    Args:
        location (str): The selected city/location (e.g., "Stockholm, SE")
        
    Returns:
        str: A formatted weather string or an error message.
    """
    if location == "No Location":
        return "Not Set"

    # Mock data based on location (Expanded for examples)
    weather_data = {
        "Stockholm, SE": "1°C ❄️ | Light Snow",
        "London, UK": "9°C ☁️ | Overcast",
        "New York, US": "12°C ☀️ | Clear",
        "Tokyo, JP": "15°C 🌧️ | Rain Showers",
        "Berlin, DE": "6°C 🌥️ | Partly Cloudy",
        "Sydney, AU": "25°C ☀️ | Sunny",
        "Uppsala, SE": "0°C 🌨️ | Flurries",
        "Gothenburg, SE": "2°C 🌫️ | Fog",
        "Malmö, SE": "4°C ☁️ | Cloudy",
        "Huddinge, SE": "1°C ❄️ | Light Snow"
    }
    
    # Return mock data or a default if location is missing
    return weather_data.get(location, "N/A - Custom Location")

def update_weather_display():
    """Updates the WEATHER_LABEL with weather for the CURRENT_WEATHER_LOCATION."""
    global WEATHER_LABEL, CURRENT_WEATHER_LOCATION
    theme = THEMES[CURRENT_THEME]
    
    if WEATHER_LABEL:
        weather_info = fetch_weather(CURRENT_WEATHER_LOCATION)
        
        display_text = f"📍 {CURRENT_WEATHER_LOCATION}: {weather_info}"

        WEATHER_LABEL.config(
            text=display_text,
            bg=theme["frame_bg"],
            fg=theme["fg"]
        )

def change_weather_location(new_location, top_level=None):
    """
    Handles the change of the weather location, saves it, and updates display.
    
    Args:
        new_location (str): The new location selected or entered.
        top_level (tk.Toplevel, optional): The settings window to close.
    """
    global CURRENT_WEATHER_LOCATION
    CURRENT_WEATHER_LOCATION = new_location
    save_config()
    update_weather_display()
    if top_level:
        top_level.destroy()

# ========================================
# PERIODIC REFRESH FUNCTION 
# ========================================

def periodic_refresh(manual=False):
    """
    Checks if an active feed is set and automatically refreshes its content 
    to ensure non-intrusive, periodic updates. Schedules the next refresh.
    
    Args:
        manual (bool): If True, it was triggered by the button and displays a 
                       confirmation/error message.
    """
    global ROOT, ACTIVE_FEED_URL, ACTIVE_FEED_CONTAINER, CURRENT_FEEDS, REFRESH_INTERVAL_MS, CURRENT_PAGE, ALL_ARTICLES
    
    if ACTIVE_FEED_URL and ACTIVE_FEED_CONTAINER and ACTIVE_FEED_CONTAINER.winfo_exists():
        # Find the category name corresponding to the URL
        category_name = "Refreshed Feed" # Default name
        for name, url in CURRENT_FEEDS.items():
            if url == ACTIVE_FEED_URL:
                category_name = name
                break
        
        # 1. Re-fetch and store all articles (like in fetch_and_display_news)
        try:
            feed = feedparser.parse(ACTIVE_FEED_URL, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
            
            # Check for parsing errors
            if feed.bozo and feed.bozo_exception.__class__.__name__ not in ('NonXMLContentType', 'CharacterEncodingOverride'):
                if manual:
                    messagebox.showerror("Refresh Error", f"Could not refresh feed for **{category_name}** due to a formatting error.")
                return
            
            # Store latest entries
            ALL_ARTICLES[ACTIVE_FEED_URL] = feed.entries[:100]
            
            # 2. Call display_page using the CURRENT_PAGE to maintain user's position
            # Ensure current page is valid after a refresh (e.g. if articles dropped below current page)
            total_articles = len(ALL_ARTICLES[ACTIVE_FEED_URL])
            total_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
            safe_page = min(CURRENT_PAGE, max(1, total_pages))
            
            display_page(ACTIVE_FEED_CONTAINER, category_name, ACTIVE_FEED_URL, safe_page)
            
            if manual:
                 messagebox.showinfo("Refresh Successful", f"The '{category_name}' feed has been refreshed.")

        except Exception as e:
            if manual:
                messagebox.showerror("Refresh Error", f"An error occurred while refreshing the RSS feed:\n{e}")
            # Do nothing silently for automatic refresh errors
            pass 
        
    elif manual:
        # If manual refresh is called but no feed is active, inform user
        messagebox.showinfo("Refresh", "No news category is currently displayed to refresh.")

    
    # Schedule the next refresh only if it wasn't a manual call
    if not manual and ROOT:
        ROOT.after(REFRESH_INTERVAL_MS, periodic_refresh)


# ========================================
# LOCATION MANAGEMENT FUNCTIONS
# ========================================

def add_new_location_dialog(listbox, manager_root):
    """
    Opens a dialog to add a new location with a format viability check.
    """
    global DEFAULT_LOCATIONS
    
    new_loc = simpledialog.askstring(
        "Add New Location", 
        "Enter new location in 'City, CC' format (e.g., Paris, FR):", 
        parent=manager_root
    )

    if not new_loc:
        return

    new_loc = new_loc.strip()

    # --- Viability Check (City, CC format) ---
    parts = new_loc.split(',')
    
    # Check 1: Must have exactly one comma
    if len(parts) != 2:
        messagebox.showwarning("Format Error", "Location must be in 'City, CC' format (e.g., Paris, FR). Missing or extra comma.")
        return

    city = parts[0].strip()
    cc = parts[1].strip()

    # Check 2: City part is not empty, CC part is exactly 2 characters
    if not city or len(cc) != 2 or not cc.isalpha():
        messagebox.showwarning("Format Error", "Location must be in 'City, CC' format (e.g., London, UK). CC should be a 2-letter country code.")
        return

    # Check 3: Uniqueness
    if new_loc in DEFAULT_LOCATIONS:
        messagebox.showwarning("Duplicate", f"'{new_loc}' is already in the list.")
        return
        
    # Add and save
    DEFAULT_LOCATIONS.append(new_loc)
    DEFAULT_LOCATIONS.sort() # Keep the list clean
    save_config()
    
    # Refresh listbox and maintain selection focus if possible
    populate_location_listbox(listbox)
    
    messagebox.showinfo("Success", f"Location '{new_loc}' added and saved.")


def populate_location_listbox(listbox):
    """Populates the listbox with the DEFAULT_LOCATIONS and highlights the active one."""
    global CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    theme = THEMES[CURRENT_THEME]
    
    listbox.delete(0, tk.END)
    
    # Ensure DEFAULT_LOCATIONS is sorted
    DEFAULT_LOCATIONS.sort()
    
    selected_index = -1
    for i, loc in enumerate(DEFAULT_LOCATIONS):
        listbox.insert(tk.END, loc)
        if loc == CURRENT_WEATHER_LOCATION:
            listbox.itemconfig(i, {'bg': theme["button_active_bg"], 
                                   'fg': theme["fg"]})
            selected_index = i
            
    if selected_index != -1:
        # Ensure the selected item is visible and highlighted
        listbox.selection_set(selected_index)
        listbox.see(selected_index)


def location_manager_window():
    """
    Creates a Toplevel window for managing the weather location using a selectable list.
    """
    global CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    theme = THEMES[CURRENT_THEME]
    
    manager_root = tk.Toplevel(ROOT)
    # UPDATED: Window title
    manager_root.title("Location Settings")
    manager_root.geometry("400x350")
    manager_root.configure(bg=theme["bg"])
    manager_root.grab_set() 

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=15, pady=15)
    frame.pack(fill='both', expand=True)

    # Header
    tk.Label(
        frame, 
        # UPDATED: Header text
        text="📍 Select or Add a Location", 
        font=("Arial", 11, "bold"),
        bg=theme["frame_bg"],
        fg=theme["headline_fg"]
    ).pack(fill='x', pady=(0, 5))
    
    # 1. Listbox Setup
    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill='both', expand=True, pady=5)
    
    listbox_scrollbar = tk.Scrollbar(listbox_frame)
    location_listbox = tk.Listbox(
        listbox_frame, 
        yscrollcommand=listbox_scrollbar.set, 
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0
    )
    listbox_scrollbar.config(command=location_listbox.yview)
    
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    location_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Populate the list and highlight active location
    populate_location_listbox(location_listbox)


    # 2. Control Buttons
    button_controls = tk.Frame(frame, bg=theme["frame_bg"])
    button_controls.pack(fill='x', pady=(10, 5))
    
    def set_selected_location():
        """Sets the selected listbox item as the new weather location."""
        try:
            selection_index = location_listbox.curselection()[0]
            new_loc = location_listbox.get(selection_index)
            # Use the existing change function, passing the manager_root to close it
            change_weather_location(new_loc, manager_root)
        except IndexError:
            messagebox.showwarning("Selection Error", "Please select a location from the list.")

    ttk.Button(
        button_controls, 
        text="Set Active Location", 
        command=set_selected_location
    ).pack(side='left', expand=True, padx=5)
    
    ttk.Button(
        button_controls, 
        text="Add New Location...", 
        command=lambda: add_new_location_dialog(location_listbox, manager_root)
    ).pack(side='right', expand=True, padx=5)

    # 3. Footer Note (for context on mock data)
    ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=(5, 5))
    tk.Label(
        frame,
        text="Note: Weather data is mocked. Only listed locations return detailed results. Newly added locations will return 'N/A - Custom Location'.",
        wraplength=350,
        font=("Arial", 8, "italic"),
        bg=theme["frame_bg"],
        fg=theme["summary_fg"]
    ).pack(fill='x')
    
    
    # Apply theme to the new window
    apply_theme_to_widget(manager_root)
    manager_root.protocol("WM_DELETE_WINDOW", manager_root.destroy)
    manager_root.update_idletasks() # Ensure geometry updates before returning

# ========================================
# PAGINATION CORE LOGIC
# ========================================

def display_page(container, category_name, feed_url, page_number):
    """
    Displays the articles for a specific page number, including navigation.
    
    Args:
        container: The widget container to display news in.
        category_name: The name of the category.
        feed_url: The URL of the feed.
        page_number: The page number to display.
    """
    global ALL_ARTICLES, CURRENT_PAGE, ARTICLES_PER_PAGE, ROOT
    theme = THEMES[CURRENT_THEME]
    
    # 1. Update Global State
    CURRENT_PAGE = page_number
    
    # 2. Clear existing content (important for redraw)
    # The loading label is destroyed here if present (when called on successful fetch)
    for widget in container.winfo_children():
        widget.destroy()

    # Get the articles for the current feed
    entries = ALL_ARTICLES.get(feed_url, [])
    total_articles = len(entries)
    # Calculate total pages, ensuring at least 1 page if articles exist
    total_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    total_pages = max(1, total_pages) if total_articles > 0 else 0
    
    # Ensure page number is within bounds
    if total_pages > 0:
        if page_number < 1: page_number = 1
        if page_number > total_pages: page_number = total_pages
    else:
        page_number = 1
        
    CURRENT_PAGE = page_number # Re-set global for safety

    # 3. Calculate indices
    start_index = (page_number - 1) * ARTICLES_PER_PAGE
    end_index = start_index + ARTICLES_PER_PAGE
    
    entries_to_display = entries[start_index:end_index]
    
    # 4. Display Header
    page_text = f" (Page {CURRENT_PAGE} of {total_pages})" if total_pages > 1 else ""
    header_label = tk.Label(
        container, 
        text=f"--- Latest {category_name} Headlines{page_text} ---", 
        font=("Arial", 12, "bold"), 
        foreground=theme["category_fg"],
        background=theme["frame_bg"]
    )
    header_label.pack(pady=(10, 5), padx=10, fill='x')

    # Handle empty or zero-page scenario
    if not entries_to_display and total_articles == 0:
        error_label = tk.Label(
            container, 
            text="No news entries found for this feed.", 
            foreground=theme["error_fg"],
            background=theme["frame_bg"]
        )
        error_label.pack(pady=10)
        
    # 5. Display Entries
    for entry in entries_to_display:
        # Extract entry information
        headline = entry.get('title', 'No Title Available')
        link = entry.get('link', '#')
        
        # Create a brief summary from the description
        summary_text = entry.get('summary', entry.get('description', ''))
        summary = summary_text.split('.')[0] + '...' if summary_text else ''
        
        # Create clickable headline
        headline_label = tk.Label(
            container, 
            text=headline, 
            wraplength=550, 
            font=("Arial", 10, "bold"), 
            cursor="hand2", 
            foreground=theme["headline_fg"],
            background=theme["frame_bg"],
            anchor='w',
            justify='left'
        )
        headline_label.pack(anchor='w', padx=15, pady=(5, 0), fill='x')
        
        # Display summary text
        summary_label = tk.Label(
            container, 
            text=summary, 
            wraplength=550, 
            font=("Arial", 9, "italic"), 
            foreground=theme["summary_fg"],
            background=theme["frame_bg"],
            anchor='w',
            justify='left'
        )
        summary_label.pack(anchor='w', padx=15, pady=(0, 2), fill='x')
        
        # Bind click event to open link in browser
        headline_label.bind("<Button-1>", lambda e, l=link: webbrowser.open_new(l)) 
        
        # Add separator between entries
        sep_frame = tk.Frame(container, height=1, bg=theme["separator_bg"])
        sep_frame.pack(fill='x', padx=10, pady=2)
            
    # 6. Add Navigation Controls (only if more than one page)
    if total_pages > 1:
        nav_frame = tk.Frame(container, bg=theme["frame_bg"], pady=10)
        nav_frame.pack(fill='x', padx=10)
        
        # --- Previous Button ---
        prev_button = ttk.Button(
            nav_frame, 
            text="← Previous Page", 
            command=lambda: display_page(container, category_name, feed_url, page_number - 1)
        )
        prev_button.pack(side='left', padx=10)
        if page_number == 1:
            prev_button.state(['disabled'])

        # --- Page Number Buttons Logic ---
        MAX_BUTTONS = 5
        
        if total_pages <= MAX_BUTTONS:
            start_page = 1
            end_page = total_pages
        else:
            # Calculate range centered around current page
            start_page = max(1, page_number - (MAX_BUTTONS // 2))
            end_page = min(total_pages, start_page + MAX_BUTTONS - 1)
            
            # Adjust start_page if end_page hits total_pages boundary
            if end_page - start_page < MAX_BUTTONS - 1:
                start_page = max(1, total_pages - MAX_BUTTONS + 1)
        
        # Display page number buttons
        for i in range(start_page, end_page + 1):
            btn_style = "Active.TButton" if i == page_number else "TButton"
            btn = ttk.Button(
                nav_frame,
                text=str(i),
                command=lambda p=i: display_page(container, category_name, feed_url, p),
                style=btn_style # Use the custom style
            )
            btn.pack(side='left', padx=2)
            

        # --- Next Button ---
        next_button = ttk.Button(
            nav_frame, 
            text="Next Page →", 
            command=lambda: display_page(container, category_name, feed_url, page_number + 1)
        )
        next_button.pack(side='right', padx=10)
        if page_number == total_pages:
            next_button.state(['disabled'])
            
    # Force the canvas to update its scroll region after drawing all widgets
    if ROOT:
        # Schedule the update to happen after the current set of widgets have been fully created
        ROOT.after(50, lambda: container.master.configure(scrollregion=container.master.bbox("all")))
        
    # Apply theme to the new controls
    apply_theme_to_widget(container)

# ========================================
# RSS FETCHING LOGIC
# ========================================

def fetch_and_display_news(feed_url, container, category_name):
    """
    Fetches, parses, and *stores* all news entries from an RSS feed, 
    then calls display_page to show the first page.
    
    Args:
        feed_url: The URL of the RSS feed to fetch
        container: The widget container to display news in
        category_name: The name of the category for display purposes
    """
    theme = THEMES[CURRENT_THEME]
    
    # Track the currently active feed for automatic refresh
    global ACTIVE_FEED_URL, ACTIVE_FEED_CONTAINER, CURRENT_PAGE, ALL_ARTICLES
    ACTIVE_FEED_URL = feed_url
    ACTIVE_FEED_CONTAINER = container
    
    # Clear existing content immediately for responsiveness
    for widget in container.winfo_children():
        widget.destroy()

    # Display a loading message
    loading_label = tk.Label(
        container, 
        text="Fetching news... please wait.", 
        font=("Arial", 12, "italic"),
        foreground=theme["summary_fg"],
        background=theme["frame_bg"]
    )
    loading_label.pack(pady=50)
    
    # Process the fetch in a try/except/finally block
    try:
        # Fetch and parse the RSS feed
        feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'NewsViewerApp/1.0'})
        
        # Check for parsing errors
        if feed.bozo and feed.bozo_exception.__class__.__name__ not in ('NonXMLContentType', 'CharacterEncodingOverride'):
             messagebox.showerror("Feed Error", f"Could not parse feed for **{category_name}** due to a formatting error.")
             # Clear the loading label on error
             loading_label.destroy()
             return

        # Store ALL entries (or a reasonable limit, e.g., 100)
        ALL_ARTICLES[feed_url] = feed.entries[:100] # Cap to 100 entries max
        
        # Reset to page 1 for the new feed and display
        CURRENT_PAGE = 1
        display_page(container, category_name, feed_url, CURRENT_PAGE)
        
    except Exception as e:
        # Clear loading message and display error
        for widget in container.winfo_children():
            widget.destroy()
            
        messagebox.showerror("Fetching Error", f"An error occurred while fetching the RSS feed:\n{e}")
    
    finally:
        # A brief pause to allow UI updates regardless of success or failure.
        time.sleep(0.1) 


# ========================================
# GUI MANAGEMENT FUNCTIONS 
# ========================================

def update_category_buttons(button_frame, scrollable_frame):
    """
    Clears and redraws the category buttons based on the CURRENT_FEEDS list.
    Also displays a "Manage Current Feeds" button.
    
    Args:
        button_frame: The frame to contain the category buttons
        scrollable_frame: The scrollable frame for news content
    """
    theme = THEMES[CURRENT_THEME]
    
    # Clear existing buttons
    for widget in button_frame.winfo_children():
        widget.destroy()

    # Add management button
    ttk.Button(
        button_frame, 
        text="Manage Current Feeds", 
        command=lambda: feed_manager_window(button_frame, scrollable_frame)
    ).pack(side='right', padx=5, fill='y')

    # Display message if no feeds are loaded
    if not CURRENT_FEEDS:
        label = tk.Label(
            button_frame, 
            text="No feeds loaded. Use the File Menu or 'Manage Feeds' to add one.", 
            foreground=theme["error_fg"],
            bg=theme["frame_bg"]
        )
        label.pack(side='left', padx=10)
        return

    # Create a button for each feed category
    for name, url in CURRENT_FEEDS.items():
        # When a button is clicked, it now calls the updated fetch_and_display_news
        button = ttk.Button(
            button_frame, 
            text=name, 
            command=lambda u=url, n=name: fetch_and_display_news(u, scrollable_frame, n)
        )
        button.pack(side='left', expand=True, fill='x', padx=5)

    # Automatically load the first category
    if CURRENT_FEEDS:
        # Only load if the previous active feed is no longer valid (e.g., if it was deleted/edited)
        is_active_feed_valid = ACTIVE_FEED_URL in CURRENT_FEEDS.values()
        
        if not is_active_feed_valid:
            initial_category_url = list(CURRENT_FEEDS.values())[0]
            initial_category_name = list(CURRENT_FEEDS.keys())[0]
            fetch_and_display_news(initial_category_url, scrollable_frame, initial_category_name)


def feed_manager_window(button_frame, scrollable_frame):
    """
    Creates a Toplevel window for managing the currently active feed list.
    Allows users to add, remove, or edit feeds from the current list.
    
    Args:
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
    """
    theme = THEMES[CURRENT_THEME]
    
    manager_root = tk.Toplevel(ROOT)
    manager_root.title("Manage Current RSS Feeds")
    manager_root.geometry("600x300")
    manager_root.configure(bg=theme["bg"])
    manager_root.grab_set()  # Make window modal

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill='both', expand=True)

    # Create listbox with scrollbar
    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill='both', expand=True, pady=5)
    
    listbox_scrollbar = tk.Scrollbar(listbox_frame)
    feed_listbox = tk.Listbox(
        listbox_frame, 
        yscrollcommand=listbox_scrollbar.set, 
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0
    )
    listbox_scrollbar.config(command=feed_listbox.yview)
    
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    feed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_listbox():
        """Populates the listbox with current feeds."""
        feed_listbox.delete(0, tk.END)
        for name, url in CURRENT_FEEDS.items():
            feed_listbox.insert(tk.END, f"{name}: {url}")

    # Control buttons
    button_controls = tk.Frame(frame, bg=theme["frame_bg"])
    button_controls.pack(fill='x', pady=5)

    ttk.Button(
        button_controls, 
        text="Add New Feed", 
        command=lambda: add_feed(populate_listbox, button_frame, scrollable_frame)
    ).pack(side='left', expand=True, padx=5)
    
    # NEW EDIT BUTTON
    ttk.Button(
        button_controls,
        text="Edit Selected",
        command=lambda: edit_feed(feed_listbox, populate_listbox, button_frame, scrollable_frame)
    ).pack(side='left', expand=True, padx=5)
    
    ttk.Button(
        button_controls, 
        text="Remove Selected", 
        command=lambda: remove_feed(feed_listbox, populate_listbox, button_frame, scrollable_frame)
    ).pack(side='right', expand=True, padx=5)
    
    populate_listbox()
    manager_root.protocol("WM_DELETE_WINDOW", manager_root.destroy)
    
    # Apply theme to the new window
    apply_theme_to_widget(manager_root)

def show_saved_lists_window(button_frame, scrollable_frame):
    """
    Creates a window to load, set default, or delete saved feed lists.
    
    Args:
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
    """
    theme = THEMES[CURRENT_THEME]
    
    saved_root = tk.Toplevel(ROOT)
    saved_root.title("Saved Feed Lists")
    saved_root.geometry("450x300")
    saved_root.configure(bg=theme["bg"])
    saved_root.grab_set()  # Make window modal
    
    frame = tk.Frame(saved_root, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill='both', expand=True)
    
    label = tk.Label(
        frame, 
        text="Select a list to manage:", 
        font=("Arial", 10, "bold"),
        bg=theme["frame_bg"],
        fg=theme["fg"]
    )
    label.pack(anchor='w', pady=(0, 5))
    
    # Create listbox with scrollbar
    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill='both', expand=True, pady=5)
    
    listbox_scrollbar = tk.Scrollbar(listbox_frame)
    listbox = tk.Listbox(
        listbox_frame, 
        yscrollcommand=listbox_scrollbar.set, 
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0
    )
    listbox_scrollbar.config(command=listbox.yview)
    
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_saved_listbox():
        """Populates the listbox with saved lists, marking the default."""
        listbox.delete(0, tk.END)
        for name in sorted(SAVED_LISTS.keys()):
            display_name = f"{name} (Default)" if name == DEFAULT_LIST_NAME else name
            listbox.insert(tk.END, display_name)
    
    populate_saved_listbox()

    # Control buttons
    button_controls = tk.Frame(frame, bg=theme["frame_bg"])
    button_controls.pack(fill='x', pady=5)

    ttk.Button(
        button_controls, 
        text="Load List", 
        command=lambda: load_list(listbox, populate_saved_listbox, button_frame, scrollable_frame, saved_root)
    ).pack(side='left', expand=True, padx=5)
    
    ttk.Button(
        button_controls, 
        text="Set as Default", 
        command=lambda: set_default_list(listbox, populate_saved_listbox)
    ).pack(side='left', expand=True, padx=5)
    
    ttk.Button(
        button_controls, 
        text="Delete List", 
        command=lambda: delete_list(listbox, populate_saved_listbox)
    ).pack(side='left', expand=True, padx=5)

    saved_root.protocol("WM_DELETE_WINDOW", saved_root.destroy)
    
    # Apply theme to the new window
    apply_theme_to_widget(saved_root)

# ========================================
# HELPER FUNCTIONS FOR FEED MANAGEMENT 
# ========================================

def add_feed(refresh_listbox, button_frame, scrollable_frame):
    """
    Opens dialogs to add a new feed to the current list.
    
    Args:
        refresh_listbox: Function to refresh the feed listbox
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
    """
    # Get feed name from user
    name = simpledialog.askstring("Add Feed", "Enter the Category Name (e.g., Tech News):", parent=ROOT)
    if not name:
        return
    
    # Get feed URL from user
    url = simpledialog.askstring("Add Feed", f"Enter the RSS URL for **{name}**:", parent=ROOT)
    if not url:
        return
    
    name = name.strip()
    url = url.strip()
    
    # Check for duplicate names
    if name in CURRENT_FEEDS:
        messagebox.showwarning("Warning", f"A feed named '{name}' already exists. Please choose a unique name.")
        return
    
    # Add the feed to current list
    CURRENT_FEEDS[name] = url
    refresh_listbox()
    update_category_buttons(button_frame, scrollable_frame)
    messagebox.showinfo("Success", f"Feed '{name}' has been added to the current list.")


def edit_feed(listbox, refresh_listbox, button_frame, scrollable_frame):
    """
    Opens dialogs to edit the name and URL of a selected feed.
    
    Args:
        listbox: The listbox widget containing feeds
        refresh_listbox: Function to refresh the feed listbox
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
    """
    global CURRENT_FEEDS, ACTIVE_FEED_URL, ALL_ARTICLES
    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)

        # Extract feed name and URL from the listbox item
        # Format is "Name: URL"
        parts = selected_item.split(': ', 1)
        if len(parts) != 2:
            raise ValueError("Invalid format in listbox item.")
            
        old_name = parts[0].strip()
        old_url = parts[1].strip()

        # 1. Prompt for new name (pre-filling with old name)
        new_name = simpledialog.askstring(
            "Edit Feed Name", 
            f"Enter the new category name for '{old_name}':", 
            initialvalue=old_name,
            parent=ROOT
        )
        if not new_name:
            return
        
        # 2. Prompt for new URL (pre-filling with old URL)
        new_url = simpledialog.askstring(
            "Edit RSS URL", 
            f"Enter the new RSS URL for '{new_name}':", 
            initialvalue=old_url,
            parent=ROOT
        )
        if not new_url:
            return
            
        new_name = new_name.strip()
        new_url = new_url.strip()

        # 3. Check for name conflicts (only if name has changed)
        if new_name != old_name and new_name in CURRENT_FEEDS:
             messagebox.showwarning("Warning", f"A feed named '{new_name}' already exists. Please choose a unique name.")
             return
        
        # 4. Perform Update
        
        # Check if the feed being edited is the active one in the main view
        was_active = (old_url == ACTIVE_FEED_URL)
        
        if new_name != old_name:
            # Delete old entry and add new one
            del CURRENT_FEEDS[old_name]
            CURRENT_FEEDS[new_name] = new_url
            
            # If we delete the old entry, we must move its cached articles if the URL didn't change
            if old_url == new_url and old_url in ALL_ARTICLES:
                 ALL_ARTICLES[new_url] = ALL_ARTICLES.pop(old_url)
                 
        else:
            # Name is the same, just update the URL
            CURRENT_FEEDS[new_name] = new_url
        
        # 5. Refresh GUI
        refresh_listbox()
        update_category_buttons(button_frame, scrollable_frame)
        messagebox.showinfo("Success", f"Feed '{new_name}' has been updated.")
        
        # 6. If the edited feed was active and its URL changed, clear the main display
        if was_active and old_url != new_url:
            # Clear the main display (since the URL is different, old data is invalid)
            for widget in scrollable_frame.winfo_children():
                 widget.destroy()

    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to edit.")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred during editing: {e}")


def remove_feed(listbox, refresh_listbox, button_frame, scrollable_frame):
    """
    Removes the selected feed from the current list.
    
    Args:
        listbox: The listbox widget containing feeds
        refresh_listbox: Function to refresh the feed listbox
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
    """
    global CURRENT_FEEDS
    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)
        
        # Extract feed name from the listbox item
        name = selected_item.split(':')[0].strip()

        if name in CURRENT_FEEDS:
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove the feed '{name}' from the current list?"):
                del CURRENT_FEEDS[name]
                refresh_listbox()
                update_category_buttons(button_frame, scrollable_frame)
                
                # Clear the main display if the removed feed was the active one
                if len(CURRENT_FEEDS) == 0:
                    for widget in scrollable_frame.winfo_children():
                        widget.destroy()
                
    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to remove.")

def save_current_list():
    """
    Saves the CURRENT_FEEDS dictionary under a user-provided name.
    """
    global SAVED_LISTS
    
    list_name = simpledialog.askstring("Save List", "Enter a name to save the current feed list:", parent=ROOT)

    if not list_name:
        return
    
    if not CURRENT_FEEDS:
        messagebox.showwarning("Warning", "The current list is empty and cannot be saved.")
        return

    # Save the current feeds under the provided name
    SAVED_LISTS[list_name] = CURRENT_FEEDS.copy()
    save_config()
    messagebox.showinfo("Saved", f"Current feed list saved as '{list_name}'.")

def load_list(listbox, refresh_saved_listbox, button_frame, scrollable_frame, saved_root):
    """
    Loads a selected saved list into CURRENT_FEEDS and updates the main window.
    
    Args:
        listbox: The listbox widget containing saved lists
        refresh_saved_listbox: Function to refresh the saved lists listbox
        button_frame: The frame containing category buttons
        scrollable_frame: The scrollable frame for news content
        saved_root: The saved lists window to close after loading
    """
    global CURRENT_FEEDS

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)
        
        # Extract list name, removing "(Default)" marker if present
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
    """
    Sets a selected saved list as the default to load on startup.
    
    Args:
        listbox: The listbox widget containing saved lists
        refresh_saved_listbox: Function to refresh the saved lists listbox
    """
    global DEFAULT_LIST_NAME

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)

        # Extract list name, removing "(Default)" marker if present
        list_name = selected_item.split(' (Default)')[0].strip() 

        if list_name in SAVED_LISTS:
            DEFAULT_LIST_NAME = list_name
            save_config()
            refresh_saved_listbox()  # Refresh to show new default marker
            messagebox.showinfo("Default Set", f"'{list_name}' is now the default list.")
    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to set as default.")

def delete_list(listbox, refresh_saved_listbox):
    """
    Deletes a selected saved list from storage.
    
    Args:
        listbox: The listbox widget containing saved lists
        refresh_saved_listbox: Function to refresh the saved lists listbox
    """
    global SAVED_LISTS, DEFAULT_LIST_NAME

    try:
        selection_index = listbox.curselection()[0]
        selected_item = listbox.get(selection_index)

        # Extract list name, removing "(Default)" marker if present
        list_name = selected_item.split(' (Default)')[0].strip()

        # Prevent deletion of the default list
        if list_name == DEFAULT_LIST_NAME:
            messagebox.showwarning("Cannot Delete", "Cannot delete the current **default list**.")
            return

        if list_name in SAVED_LISTS:
            if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete the list '{list_name}'?"):
                del SAVED_LISTS[list_name]
                save_config()
                refresh_saved_listbox()  # Refresh the list display
                messagebox.showinfo("Deleted", f"List '{list_name}' has been deleted.")
        else:
            messagebox.showwarning("Error", "The selected list was not found.")

    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to delete.")

# ========================================
# TKINTER GUI SETUP
# ========================================

def enable_mouse_wheel(canvas):
    """
    Binds the mouse wheel event to the canvas for scrolling across OS platforms.
    """
    # For Windows and Linux
    def _on_mouse_wheel(event):
        # Determine scroll direction and amount based on OS/Event type
        if event.num == 5 or event.delta < 0:
            canvas.yview_scroll(1, "unit")
        elif event.num == 4 or event.delta > 0:
            canvas.yview_scroll(-1, "unit")

    # Bind events
    canvas.bind_all("<Button-4>", _on_mouse_wheel) # Linux scroll up
    canvas.bind_all("<Button-5>", _on_mouse_wheel) # Linux scroll down
    canvas.bind_all("<MouseWheel>", _on_mouse_wheel) # Windows/macOS

def setup_gui():
    """
    Sets up the main Tkinter window and all widgets.
    """
    global ROOT, DATETIME_LABEL, WEATHER_LABEL
    
    # Load configuration and theme preferences
    load_config()

    ROOT = tk.Tk()
    ROOT.title("News Feed by Mattias")
    ROOT.geometry("700x700")
    
    # Configure TTK theme
    configure_ttk_theme()
    
    # ========================================
    # TOP HEADER FRAME (Date, Time, Weather, Refresh)
    # ========================================
    theme = THEMES[CURRENT_THEME]
    
    header_frame = tk.Frame(ROOT, bg=theme["frame_bg"], padx=10, pady=5)
    header_frame.pack(fill='x', padx=10, pady=(10, 0))

    # 1. Date/Time Label
    DATETIME_LABEL = tk.Label(
        header_frame, 
        text="", 
        font=("Arial", 10, "bold"), 
        bg=theme["frame_bg"],
        fg=theme["fg"]
    )
    DATETIME_LABEL.pack(side='left', padx=(0, 20))
    update_datetime_label() # Start the real-time clock
    
    # 2. Manual Refresh Button (Text instead of emoji)
    ttk.Button(
        header_frame, 
        text="Refresh", 
        width=8,
        command=lambda: periodic_refresh(manual=True) # Manually trigger immediate refresh
    ).pack(side='right', padx=10)


    # 3. Weather Display Label 
    WEATHER_LABEL = tk.Label(
        header_frame, 
        text="Loading weather...", 
        font=("Arial", 10, "italic"),
        bg=theme["frame_bg"],
        fg=theme["fg"]
    )
    WEATHER_LABEL.pack(side='right')
    update_weather_display() # Display initial weather

    # ========================================
    # MENU BAR SETUP
    # ========================================
    
    menubar = tk.Menu(ROOT, bg=theme["menu_bg"], fg=theme["menu_fg"])
    ROOT.config(menu=menubar)
    
    # Create main frames before menu commands reference them
    button_frame = tk.Frame(ROOT, bg=theme["frame_bg"])
    main_frame = tk.Frame(ROOT, bg=theme["bg"])
    canvas = tk.Canvas(main_frame, bg=theme["canvas_bg"], highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg=theme["frame_bg"])

    # File Menu - For feed list management
    file_menu = tk.Menu(menubar, tearoff=0, bg=theme["menu_bg"], 
                     fg=theme["menu_fg"], 
                     activebackground=theme["menu_active_bg"], 
                     activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="File", menu=file_menu)
    
    file_menu.add_command(label="Save Current List...", command=lambda: save_current_list())
    file_menu.add_separator()
    
    file_menu.add_command(label="Load/Manage Saved Lists...", 
                          command=lambda: show_saved_lists_window(button_frame, scrollable_frame))
    
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=ROOT.quit)

    # Location Menu 
    location_menu = tk.Menu(menubar, tearoff=0, 
                          bg=theme["menu_bg"], 
                          fg=theme["menu_fg"], 
                          activebackground=theme["menu_active_bg"], 
                          activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="Location", menu=location_menu)
    
    # UPDATED: Menu text
    location_menu.add_command(label="Change Location...", 
                              command=location_manager_window) # Opens the new window
    
    # Style Menu - For theme switching
    style_menu = tk.Menu(menubar, tearoff=0, 
                          bg=theme["menu_bg"], 
                          fg=theme["menu_fg"], 
                          activebackground=theme["menu_active_bg"], 
                          activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="Style", menu=style_menu)
    
    style_menu.add_command(label="Toggle Dark/Light Mode", 
                          command=lambda: toggle_theme(button_frame, scrollable_frame))

    # ========================================
    # MAIN CONTENT LAYOUT
    # ========================================

    # Button frame for category buttons
    button_frame.pack(fill='x', padx=10, pady=(5, 5))
    
    # Main content frame with scrollbar
    main_frame.pack(fill='both', expand=True, padx=10)

    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

    # Configure scrollable frame to resize with content
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
    
    # === MOUSE WHEEL FIX ===
    enable_mouse_wheel(canvas)

    # Initial update of category buttons and content
    update_category_buttons(button_frame, scrollable_frame)
    
    # Start the periodic news refresh 
    periodic_refresh()

    # Apply theme fully to ensure all new widgets are colored correctly
    apply_theme()
    
    ROOT.mainloop()

if __name__ == '__main__':
    setup_gui()
