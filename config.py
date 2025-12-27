import json
import os

# Configuration file
CONFIG_FILE = "rss_config.json"

# Application Constants
MAX_ROWS = 10
MIN_ROW = 1
DEFAULT_ROW = 1
MAX_ENTRIES_PER_FEED = 100
ARTICLES_PER_PAGE = 12
FEED_FETCH_TIMEOUT = 10
REFRESH_INTERVAL_MS = 300000  # 5 minutes
MAX_PAGE_BUTTONS = 5

# Text Display Constants
HEADLINE_TEXT_HEIGHT = 2
SUMMARY_TEXT_HEIGHT = 3
HEADLINE_FONT_SIZE = 10
SUMMARY_FONT_SIZE = 9
HEADER_FONT_SIZE = 12
DATETIME_FONT_SIZE = 10
LOCATION_FONT_SIZE = 10

# UI Spacing Constants
BUTTON_PADDING = 8
BUTTON_FONT_SIZE = 10
HORIZONTAL_ROW_HEIGHT = 40
SEARCH_ENTRY_WIDTH = 30
REFRESH_BUTTON_WIDTH = 8

# Window Geometry Constants
MAIN_WINDOW_WIDTH = 1000
MAIN_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 700
FEED_MANAGER_WIDTH = 650
FEED_MANAGER_HEIGHT = 450
FEED_MANAGER_MIN_WIDTH = 650
FEED_MANAGER_MIN_HEIGHT = 450
LOCATION_MANAGER_WIDTH = 450
LOCATION_MANAGER_HEIGHT = 400
URL_DIALOG_WIDTH = 500
URL_DIALOG_HEIGHT = 250
NEW_LIST_DIALOG_WIDTH = 350
NEW_LIST_DIALOG_HEIGHT = 250
OPEN_LIST_DIALOG_WIDTH = 300
OPEN_LIST_DIALOG_HEIGHT = 400
DELETE_LIST_DIALOG_WIDTH = 300
DELETE_LIST_DIALOG_HEIGHT = 400

# URL Input Dialog Constants
URL_TEXT_HEIGHT = 6
URL_TEXT_WIDTH = 60

# Padding Constants
DIALOG_PADDING = 15
FRAME_PADDING_X = 10
FRAME_PADDING_Y = 10
HEADER_PADDING_X = 10
HEADER_PADDING_Y = 5
BUTTON_ROW_PADDING = 3
BUTTON_ROW_MARGIN = 5

# UI Update Intervals
DATETIME_UPDATE_INTERVAL_MS = 1000  # 1 second
CANVAS_UPDATE_DELAY_MS = 50

# Unicode Characters (fixing encoding issues)
LINK_EMOJI = "🔗"
LOCATION_EMOJI = "📍"

# Default Feeds
DEFAULT_FEEDS = [
    ("Technology", "https://techcrunch.com/feed/", DEFAULT_ROW),
    ("Finance", "https://www.valuewalk.com/feed", DEFAULT_ROW),
    ("World", "http://feeds.bbci.co.uk/news/world/rss.xml", DEFAULT_ROW)
]

# Runtime state
CURRENT_FEEDS = []
SAVED_LISTS = {}
DEFAULT_LIST_NAME = "Standard Default"
ACTIVE_LIST_NAME = "Standard Default"
CURRENT_THEME = "light"
ROOT = None

# Global variables to track open windows
FEED_MANAGER_WINDOW = None
LOCATION_MANAGER_WINDOW = None

# Weather/Location defaults
DEFAULT_LOCATIONS = [
    "Stockholm, SE", "London, UK", "New York, US", "Tokyo, JP",
    "Berlin, DE", "Sydney, AU", "Uppsala, SE", "Gothenburg, SE",
    "Malmö, SE", "Huddinge, SE"
]
CURRENT_WEATHER_LOCATION = "Stockholm, SE"
DATETIME_LABEL = None
WEATHER_LABEL = None

# Active feed tracking
ACTIVE_FEED_URL = None
ACTIVE_FEED_CONTAINER = None

# Article cache and pagination
ALL_ARTICLES = {}
CURRENT_PAGE = 1

def load_config():
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME, ACTIVE_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                SAVED_LISTS = data.get("saved_lists", {})
                DEFAULT_LIST_NAME = data.get("default_list_name", DEFAULT_LIST_NAME)
                ACTIVE_LIST_NAME = data.get("active_list_name", DEFAULT_LIST_NAME)
                CURRENT_THEME = data.get("theme", CURRENT_THEME)
                DEFAULT_LOCATIONS = data.get("default_locations", DEFAULT_LOCATIONS)
                CURRENT_WEATHER_LOCATION = data.get("weather_location", CURRENT_WEATHER_LOCATION)
        except json.JSONDecodeError:
            pass

    # Convert all saved lists to proper format (list of tuples with row support)
    for list_name in SAVED_LISTS:
        feeds = SAVED_LISTS[list_name]
        new_feeds = []
        
        if isinstance(feeds, dict):
            # Old format: dict
            for name, url in feeds.items():
                new_feeds.append((name, url, DEFAULT_ROW))
        elif isinstance(feeds, list):
            for item in feeds:
                if isinstance(item, (list, tuple)):
                    if len(item) == 2:
                        # Old format: (name, url)
                        new_feeds.append((item[0], item[1], DEFAULT_ROW))
                    elif len(item) == 3:
                        # New format: (name, url, row)
                        new_feeds.append((item[0], item[1], item[2]))
                elif isinstance(item, dict):
                    for k, v in item.items():
                        new_feeds.append((k, v, DEFAULT_ROW))
        
        SAVED_LISTS[list_name] = new_feeds

    # Load the DEFAULT list (the one set to load on startup)
    if DEFAULT_LIST_NAME in SAVED_LISTS:
        CURRENT_FEEDS = [tuple(x) for x in SAVED_LISTS[DEFAULT_LIST_NAME]]
        ACTIVE_LIST_NAME = DEFAULT_LIST_NAME
    else:
        SAVED_LISTS["Standard Default"] = DEFAULT_FEEDS.copy()
        DEFAULT_LIST_NAME = "Standard Default"
        ACTIVE_LIST_NAME = "Standard Default"
        CURRENT_FEEDS = DEFAULT_FEEDS.copy()
        save_config()

def save_config():
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME, ACTIVE_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    
    saved_lists_json = {}
    for list_name, feeds in SAVED_LISTS.items():
        if isinstance(feeds, list):
            # Save as [name, url, row]
            saved_lists_json[list_name] = [[name, url, row] for name, url, row in feeds]
        else:
            saved_lists_json[list_name] = feeds
    
    data = {
        "saved_lists": saved_lists_json,
        "default_list_name": DEFAULT_LIST_NAME,
        "active_list_name": ACTIVE_LIST_NAME,
        "theme": CURRENT_THEME,
        "weather_location": CURRENT_WEATHER_LOCATION,
        "default_locations": DEFAULT_LOCATIONS
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False