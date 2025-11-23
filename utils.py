import tkinter as tk
from tkinter import messagebox, simpledialog
import themes
import config
import time

def update_datetime_label():
    """
    Update DATETIME_LABEL every second.
    """
    theme = themes.THEMES[config.CURRENT_THEME]
    if config.DATETIME_LABEL:
        now = time.strftime("%A, %B %d, %Y | %H:%M:%S")
        try:
            config.DATETIME_LABEL.config(text=now, bg=theme["frame_bg"], fg=theme["fg"])
        except Exception:
            pass
    if config.ROOT:
        config.ROOT.after(1000, update_datetime_label)

def fetch_weather(location):
    # Mocked weather responses
    if location == "No Location":
        return "Not Set"
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
    return weather_data.get(location, "N/A - Custom Location")

def update_weather_display():
    theme = themes.THEMES[config.CURRENT_THEME]
    if config.WEATHER_LABEL:
        weather_info = fetch_weather(config.CURRENT_WEATHER_LOCATION)
        display_text = f"📍 {config.CURRENT_WEATHER_LOCATION}: {weather_info}"
        try:
            config.WEATHER_LABEL.config(text=display_text, bg=theme["frame_bg"], fg=theme["fg"])
        except Exception:
            pass

def change_weather_location(new_location, top_level=None):
    config.CURRENT_WEATHER_LOCATION = new_location
    config.save_config()
    update_weather_display()
    if top_level:
        try:
            top_level.destroy()
        except Exception:
            pass

def add_new_location_dialog(listbox, manager_root):
    new_loc = simpledialog.askstring("Add New Location", "Enter new location in 'City, CC' format (e.g., Paris, FR):", parent=manager_root)
    if not new_loc:
        return
    new_loc = new_loc.strip()
    parts = new_loc.split(',')
    if len(parts) != 2:
        messagebox.showwarning("Format Error", "Location must be 'City, CC' (e.g., Paris, FR).")
        return
    city = parts[0].strip(); cc = parts[1].strip()
    if not city or len(cc) != 2 or not cc.isalpha():
        messagebox.showwarning("Format Error", "Country code must be 2 letters.")
        return
    if new_loc in config.DEFAULT_LOCATIONS:
        messagebox.showwarning("Duplicate", f"'{new_loc}' already present.")
        return
    config.DEFAULT_LOCATIONS.append(new_loc); config.DEFAULT_LOCATIONS.sort()
    config.save_config()
    populate_location_listbox(listbox)
    messagebox.showinfo("Success", f"'{new_loc}' added and saved.")

def populate_location_listbox(listbox):
    theme = themes.THEMES[config.CURRENT_THEME]
    listbox.delete(0, tk.END)
    config.DEFAULT_LOCATIONS.sort()
    selected_index = -1
    for i, loc in enumerate(config.DEFAULT_LOCATIONS):
        listbox.insert(tk.END, loc)
        if loc == config.CURRENT_WEATHER_LOCATION:
            try:
                listbox.itemconfig(i, {'bg': theme["button_active_bg"], 'fg': theme["fg"]})
            except Exception:
                pass
            selected_index = i
    if selected_index != -1:
        listbox.selection_set(selected_index)
        listbox.see(selected_index)