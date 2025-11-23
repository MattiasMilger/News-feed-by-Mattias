# Global configuration and state (ultra-simple central globals).
import json
import os

CONFIG_FILE = "rss_config.json"

# ÄNDRING 1: Ändrat DEFAULT_FEEDS till en lista av tuples för att bevara ordning.
DEFAULT_FEEDS = [
    ("Technology", "https://techcrunch.com/feed/"),
    ("Finance", "https://www.valuewalk.com/feed"),
    ("World", "http://feeds.bbci.co.uk/news/world/rss.xml")
]

# Runtime state (mutated by modules)
# ÄNDRING 1: Ändrat CURRENT_FEEDS till en lista av tuples.
CURRENT_FEEDS = []
SAVED_LISTS = {}
DEFAULT_LIST_NAME = "Standard Default"
CURRENT_THEME = "light"
ROOT = None

# ÄNDRING 2: Globala variabler för att spåra öppna fönster.
FEED_MANAGER_WINDOW = None
SAVED_LISTS_WINDOW = None
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

ALL_ARTICLES = {}  # feed_url -> entries list
CURRENT_PAGE = 1
ARTICLES_PER_PAGE = 12

def load_config():
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                SAVED_LISTS = data.get("saved_lists", {})
                DEFAULT_LIST_NAME = data.get("default_list_name", DEFAULT_LIST_NAME)
                CURRENT_THEME = data.get("theme", CURRENT_THEME)
                DEFAULT_LOCATIONS = data.get("default_locations", DEFAULT_LOCATIONS)
                CURRENT_WEATHER_LOCATION = data.get("weather_location", CURRENT_WEATHER_LOCATION)
        except json.JSONDecodeError:
            pass

    if DEFAULT_LIST_NAME in SAVED_LISTS:
        loaded_feeds = SAVED_LISTS[DEFAULT_LIST_NAME]
        
        # ÄNDRING 1: Bakåtkompatibilitet: Konvertera gammal dictionary till lista av tuples
        if isinstance(loaded_feeds, dict):
            CURRENT_FEEDS = list(loaded_feeds.items())
        else:
            CURRENT_FEEDS = loaded_feeds.copy()
    else:
        SAVED_LISTS["Standard Default"] = DEFAULT_FEEDS.copy()
        DEFAULT_LIST_NAME = "Standard Default"
        CURRENT_FEEDS = DEFAULT_FEEDS.copy()
        save_config()

def save_config():
    global SAVED_LISTS, CURRENT_FEEDS, DEFAULT_LIST_NAME, CURRENT_THEME, CURRENT_WEATHER_LOCATION, DEFAULT_LOCATIONS
    
    # ÄNDRING 1: Uppdatera sparad lista med aktuell lista innan sparande
    SAVED_LISTS[DEFAULT_LIST_NAME] = CURRENT_FEEDS.copy() 
    
    data = {
        "saved_lists": SAVED_LISTS,
        "default_list_name": DEFAULT_LIST_NAME,
        "theme": CURRENT_THEME,
        "weather_location": CURRENT_WEATHER_LOCATION,
        "default_locations": DEFAULT_LOCATIONS
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass
