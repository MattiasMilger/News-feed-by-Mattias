import tkinter as tk
from tkinter import messagebox, simpledialog
import themes
import config
import time
import re
import random

def update_datetime_label():
    """Update DATETIME_LABEL every second."""
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
    """
    Mocked weather responses.
    Now dynamically generates weather for unknown locations to ensure
    added locations always have data.
    """
    if location == "No Location" or not location:
        return "Not Set"
        
    # Hardcoded mocked data for demo purposes
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
    
    # Return hardcoded if exists
    if location in weather_data:
        return weather_data[location]
    
    # Simulate API for new locations (Dynamic Mock)
    # This ensures users don't see "N/A" for valid formatted cities
    conditions = ["☀️ | Sunny", "☁️ | Cloudy", "🌧️ | Rain", "⛈️ | Storm", "🌥️ | Partly Cloudy"]
    temp = random.randint(-5, 30)
    return f"{temp}°C {random.choice(conditions)}"

def update_weather_display():
    """Update weather display label."""
    theme = themes.THEMES[config.CURRENT_THEME]
    if config.WEATHER_LABEL:
        weather_info = fetch_weather(config.CURRENT_WEATHER_LOCATION)
        display_text = f"📍 {config.CURRENT_WEATHER_LOCATION}: {weather_info}"
        try:
            config.WEATHER_LABEL.config(text=display_text, bg=theme["frame_bg"], fg=theme["fg"])
        except Exception:
            pass

def change_weather_location(new_location, top_level=None):
    """Change active weather location."""
    config.CURRENT_WEATHER_LOCATION = new_location
    config.save_config()
    update_weather_display()
    if top_level:
        try:
            top_level.destroy()
        except Exception:
            pass

def add_new_location_dialog(listbox, manager_root):
    """Add new location with strict Regex validation."""
    new_loc = simpledialog.askstring(
        "Add New Location", 
        "Enter new location in 'City, CC' format (e.g., Paris, FR):", 
        parent=manager_root
    )
    if not new_loc:
        return
    new_loc = new_loc.strip()
    
    # Regex Validation: 
    # Starts with letters/spaces/dots/hyphens, a comma, optional space, exactly 2 letters
    pattern = r"^[A-Za-z\s\.\-]+,\s*[A-Za-z]{2}$"
    
    if not re.match(pattern, new_loc):
        messagebox.showwarning(
            "Format Error", 
            "Invalid format.\n\nMust be 'City, CC' (e.g., 'Paris, FR' or 'New York, US').\nCountry code must be 2 letters.",
            parent=manager_root
        )
        return

    # Normalize: Capitalize city, uppercase country code
    parts = new_loc.split(',')
    city_clean = parts[0].strip().title()
    cc_clean = parts[1].strip().upper()
    final_loc = f"{city_clean}, {cc_clean}"

    if final_loc in config.DEFAULT_LOCATIONS:
        messagebox.showwarning("Duplicate", f"'{final_loc}' already present.", parent=manager_root)
        return

    # "Simulate" a network check:
    # Since fetch_weather now handles dynamic inputs, this essentially checks "is this input valid enough to generate data?"
    weather_check = fetch_weather(final_loc)
    if not weather_check or weather_check == "Not Set":
         messagebox.showerror("Data Error", "Could not fetch weather data for this location.", parent=manager_root)
         return

    config.DEFAULT_LOCATIONS.append(final_loc)
    config.DEFAULT_LOCATIONS.sort()
    config.save_config()
    populate_location_listbox(listbox)
    messagebox.showinfo("Success", f"'{final_loc}' added and saved.", parent=manager_root)

def delete_location(listbox, manager_root):
    """Delete selected location."""
    try:
        idx = listbox.curselection()[0]
        selected_loc = listbox.get(idx)
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{selected_loc}'?", parent=manager_root):
            if selected_loc in config.DEFAULT_LOCATIONS:
                config.DEFAULT_LOCATIONS.remove(selected_loc)
                
                # If we deleted the ACTIVE location, switch to safe fallback
                if selected_loc == config.CURRENT_WEATHER_LOCATION:
                    if config.DEFAULT_LOCATIONS:
                        config.CURRENT_WEATHER_LOCATION = config.DEFAULT_LOCATIONS[0]
                    else:
                        config.CURRENT_WEATHER_LOCATION = "No Location"
                    update_weather_display()
                
                config.save_config()
                populate_location_listbox(listbox)
                messagebox.showinfo("Deleted", "Location removed.", parent=manager_root)
                
    except IndexError:
        messagebox.showwarning("Warning", "Please select a location to delete.", parent=manager_root)

def populate_location_listbox(listbox):
    """Populate location listbox with highlighting for active location."""
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