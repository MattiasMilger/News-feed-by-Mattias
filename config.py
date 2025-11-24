import json
import os

CONFIG_FILE = "rss_config.json"

DEFAULT_FEEDS = [
    ("Technology", "https://techcrunch.com/feed/"),
    ("Finance", "https://www.valuewalk.com/feed"),
    ("World", "http://feeds.bbci.co.uk/news/world/rss.xml")
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

DEFAULT_LOCATIONS = [
    "Stockholm, SE", "London, UK", "New York, US", "Tokyo, JP",
    "Berlin, DE", "Sydney, AU", "Uppsala, SE", "Gothenburg, SE",
    "Malmö, SE", "Huddinge, SE"
]
CURRENT_WEATHER_LOCATION = "Stockholm, SE"
DATETIME_LABEL = None
WEATHER_LABEL = None

ACTIVE_FEED_URL = None
ACTIVE_FEED_CONTAINER = None
REFRESH_INTERVAL_MS = 300000  # 5 minutes

ALL_ARTICLES = {}
CURRENT_PAGE = 1
ARTICLES_PER_PAGE = 12

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

    # Convert all saved lists to proper format (list of tuples)
    for list_name in SAVED_LISTS:
        feeds = SAVED_LISTS[list_name]
        if isinstance(feeds, dict):
            SAVED_LISTS[list_name] = list(feeds.items())
        elif isinstance(feeds, list):
            new_feeds = []
            for item in feeds:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    new_feeds.append((item[0], item[1]))
                elif isinstance(item, dict):
                    for k, v in item.items():
                        new_feeds.append((k, v))
            SAVED_LISTS[list_name] = new_feeds

    # Load the DEFAULT list (the one set to load on startup)
    if DEFAULT_LIST_NAME in SAVED_LISTS:
        loaded_feeds = SAVED_LISTS[DEFAULT_LIST_NAME]
        if isinstance(loaded_feeds, dict):
            CURRENT_FEEDS = list(loaded_feeds.items())
        elif isinstance(loaded_feeds, list):
            new_feeds = []
            for item in loaded_feeds:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    new_feeds.append((item[0], item[1]))
            CURRENT_FEEDS = new_feeds
        else:
            CURRENT_FEEDS = DEFAULT_FEEDS.copy()
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
            saved_lists_json[list_name] = [[name, url] for name, url in feeds]
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