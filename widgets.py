# File: widgets.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import webbrowser
import time

import config
import themes
import rss
import utils


# ---------- MOUSE SCROLL SUPPORT ----------
def enable_mouse_wheel(canvas):
    def _on_mouse_wheel(event):
        if getattr(event, "delta", 0) < 0 or getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "unit")
        elif getattr(event, "delta", 0) > 0 or getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "unit")

    canvas.bind_all("<Button-4>", _on_mouse_wheel)
    canvas.bind_all("<Button-5>", _on_mouse_wheel)
    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)


# ---------- PAGINATION + ARTICLE DISPLAY ----------
def display_page(container, category_name, feed_url, page_number):
    theme = themes.THEMES[config.CURRENT_THEME]
    config.CURRENT_PAGE = page_number

    for w in container.winfo_children():
        w.destroy()

    entries = config.ALL_ARTICLES.get(feed_url, [])
    total_articles = len(entries)
    total_pages = (total_articles + config.ARTICLES_PER_PAGE - 1) // config.ARTICLES_PER_PAGE
    total_pages = max(1, total_pages) if total_articles > 0 else 0

    if total_pages > 0:
        if page_number < 1:
            page_number = 1
        if page_number > total_pages:
            page_number = total_pages
    else:
        page_number = 1

    config.CURRENT_PAGE = page_number
    start_index = (page_number - 1) * config.ARTICLES_PER_PAGE
    end_index = start_index + config.ARTICLES_PER_PAGE
    entries_to_display = entries[start_index:end_index]

    page_text = f" (Page {page_number} of {total_pages})" if total_pages > 1 else ""
    header_label = tk.Label(
        container,
        text=f"--- Latest {category_name} Headlines{page_text} ---",
        font=("Arial", 12, "bold"),
        fg=theme["category_fg"],
        bg=theme["frame_bg"]
    )
    header_label.pack(pady=(10, 5), padx=10, fill="x")

    if not entries_to_display and total_articles == 0:
        error_label = tk.Label(
            container,
            text="No news entries found for this feed.",
            fg=theme["error_fg"],
            bg=theme["frame_bg"],
        )
        error_label.pack(pady=10)

    for entry in entries_to_display:
        headline = entry.get("title", "No Title")
        link = entry.get("link", "#")
        summary_text = entry.get("summary", entry.get("description", ""))
        summary = (summary_text.split(".")[0] + "...") if summary_text else ""

        hl = tk.Label(
            container,
            text=headline,
            wraplength=550,
            font=("Arial", 10, "bold"),
            cursor="hand2",
            fg=theme["headline_fg"],
            bg=theme["frame_bg"],
            anchor="w",
            justify="left",
        )
        hl.pack(anchor="w", padx=15, pady=(5, 0), fill="x")
        sl = tk.Label(
            container,
            text=summary,
            wraplength=550,
            font=("Arial", 9, "italic"),
            fg=theme["summary_fg"],
            bg=theme["frame_bg"],
            anchor="w",
            justify="left",
        )
        sl.pack(anchor="w", padx=15, pady=(0, 2), fill="x")

        hl.bind("<Button-1>", lambda e, l=link: webbrowser.open_new(l))

        sep = tk.Frame(container, height=1, bg=theme["separator_bg"])
        sep.pack(fill="x", padx=10, pady=2)

    if total_pages > 1:
        nav = tk.Frame(container, bg=theme["frame_bg"], pady=10)
        nav.pack(fill="x", padx=10)

        prev_btn = tk.Button(
            nav,
            text="← Previous Page",
            command=lambda: display_page(container, category_name, feed_url, page_number - 1),
        )
        prev_btn.pack(side="left", padx=10)
        if page_number == 1:
            prev_btn.config(state="disabled")

        MAX_BUTTONS = 5
        if total_pages <= MAX_BUTTONS:
            start_page = 1
            end_page = total_pages
        else:
            start_page = max(1, page_number - (MAX_BUTTONS // 2))
            end_page = min(total_pages, start_page + MAX_BUTTONS - 1)
            if end_page - start_page < MAX_BUTTONS - 1:
                start_page = max(1, total_pages - MAX_BUTTONS + 1)

        for i in range(start_page, end_page + 1):
            style = "Active.TButton" if i == page_number else "TButton"
            b = ttk.Button(
                nav,
                text=str(i),
                command=lambda p=i: display_page(container, category_name, feed_url, p),
                style=style,
            )
            b.pack(side="left", padx=2)

        next_btn = tk.Button(
            nav,
            text="Next Page →",
            command=lambda: display_page(container, category_name, feed_url, page_number + 1),
        )
        next_btn.pack(side="right", padx=10)
        if page_number == total_pages:
            next_btn.config(state="disabled")

    if config.ROOT:
        config.ROOT.after(50, lambda: container.master.configure(scrollregion=container.master.bbox("all")))

    themes.apply_theme_to_widget(container, config.CURRENT_THEME)


# ---------- FETCH NEWS ----------
def fetch_and_display_news(feed_url, container, category_name):
    theme = themes.THEMES[config.CURRENT_THEME]
    config.ACTIVE_FEED_URL = feed_url
    config.ACTIVE_FEED_CONTAINER = container

    for w in container.winfo_children():
        w.destroy()

    loading = tk.Label(
        container,
        text="Fetching news... please wait.",
        font=("Arial", 12, "italic"),
        fg=theme["summary_fg"],
        bg=theme["frame_bg"],
    )
    loading.pack(pady=50)

    try:
        entries = rss.fetch_feed_entries(feed_url, max_entries=100)
        config.ALL_ARTICLES[feed_url] = entries
        config.CURRENT_PAGE = 1
        display_page(container, category_name, feed_url, config.CURRENT_PAGE)
    except Exception as e:
        for w in container.winfo_children():
            w.destroy()
        messagebox.showerror(
            "Fetching Error", f"An error occurred while fetching the RSS feed:\n{e}"
        )
    finally:
        time.sleep(0.05)


# ---------- PERIODIC AUTO REFRESH ----------
def periodic_refresh(manual=False):
    if (
        config.ACTIVE_FEED_URL
        and config.ACTIVE_FEED_CONTAINER
        and config.ACTIVE_FEED_CONTAINER.winfo_exists()
    ):
        category_name = "Refreshed Feed"
        # ÄNDRING 1: Iterera över lista av tuples
        for name, url in config.CURRENT_FEEDS:
            if url == config.ACTIVE_FEED_URL:
                category_name = name
                break

        try:
            entries = rss.fetch_feed_entries(config.ACTIVE_FEED_URL, max_entries=100)
            config.ALL_ARTICLES[config.ACTIVE_FEED_URL] = entries

            total_articles = len(entries)
            total_pages = (
                total_articles + config.ARTICLES_PER_PAGE - 1
            ) // config.ARTICLES_PER_PAGE
            safe_page = min(config.CURRENT_PAGE, max(1, total_pages))
            display_page(
                config.ACTIVE_FEED_CONTAINER,
                category_name,
                config.ACTIVE_FEED_URL,
                safe_page,
            )

            if manual:
                messagebox.showinfo(
                    "Refresh Successful",
                    f"The '{category_name}' feed has been refreshed.",
                )
        except Exception as e:
            if manual:
                messagebox.showerror(
                    "Refresh Error", f"Error refreshing RSS feed:\n{e}"
                )
    elif manual:
        messagebox.showinfo(
            "Refresh", "No news category is currently displayed to refresh."
        )

    if not manual and config.ROOT:
        config.ROOT.after(config.REFRESH_INTERVAL_MS, periodic_refresh)


# ---------- FEED BUTTON BAR ----------
def update_category_buttons(button_frame, scrollable_frame):
    theme = themes.THEMES[config.CURRENT_THEME]

    for w in button_frame.winfo_children():
        w.destroy()

    ttk.Button(
        button_frame,
        text="Manage Current Feeds",
        command=lambda: feed_manager_window(button_frame, scrollable_frame),
    ).pack(side="right", padx=5, fill="y")

    if not config.CURRENT_FEEDS:
        tk.Label(
            button_frame,
            text="No feeds loaded. Use File Menu or 'Manage Feeds' to add one.",
            fg=theme["error_fg"],
            bg=theme["frame_bg"],
        ).pack(side="left", padx=10)
        return

    # ÄNDRING 1: Iterera över lista av tuples
    for name, url in config.CURRENT_FEEDS:
        button = ttk.Button(
            button_frame,
            text=name,
            command=lambda u=url, n=name: fetch_and_display_news(u, scrollable_frame, n),
        )
        button.pack(side="left", expand=True, fill="x", padx=5)

    # Auto-load first feed if none active
    feed_urls = [url for name, url in config.CURRENT_FEEDS]
    if config.ACTIVE_FEED_URL not in feed_urls:
        # ÄNDRING 1: Använd första elementet i listan
        if config.CURRENT_FEEDS:
            initial_category_name, initial_category_url = config.CURRENT_FEEDS[0]
            fetch_and_display_news(
                initial_category_url, scrollable_frame, initial_category_name
            )

# ---------- FEED MANAGER HELPER (ÄNDRING 1) ----------
def get_feed_list_index_by_name(feed_name):
    """Hjälpfunktion för att hitta index i CURRENT_FEEDS-listan."""
    for i, (name, url) in enumerate(config.CURRENT_FEEDS):
        if name == feed_name:
            return i
    return -1

def move_feed(listbox, refresh_listbox, direction, button_frame, scrollable_frame):
    """Flyttar det valda flödet upp (-1) eller ner (+1) i listan."""
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        name = item.split(":")[0].strip()
        
        current_index = get_feed_list_index_by_name(name)
        
        if current_index == -1:
            return

        new_index = current_index + direction
        
        if 0 <= new_index < len(config.CURRENT_FEEDS):
            # Flytta objektet i den centrala listan
            feed_to_move = config.CURRENT_FEEDS.pop(current_index)
            config.CURRENT_FEEDS.insert(new_index, feed_to_move)
            
            # Spara och uppdatera huvud-UI
            config.save_config()
            update_category_buttons(button_frame, scrollable_frame)
            
            refresh_listbox()
            # Välj det flyttade objektet
            listbox.selection_set(new_index)
            listbox.see(new_index)
            
    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to move.")

# ---------- FEED MANAGER WINDOW (ÄNDRING 1, 2) ----------
def feed_manager_window(button_frame, scrollable_frame):
    # ÄNDRING 2: Förhindra dubbelöppning
    if config.FEED_MANAGER_WINDOW and config.FEED_MANAGER_WINDOW.winfo_exists():
        config.FEED_MANAGER_WINDOW.lift()
        return

    theme = themes.THEMES[config.CURRENT_THEME]

    manager_root = tk.Toplevel(config.ROOT)
    config.FEED_MANAGER_WINDOW = manager_root # Spara referens
    manager_root.title("Manage Current RSS Feeds")
    manager_root.geometry("600x350")
    manager_root.configure(bg=theme["bg"])
    manager_root.grab_set()

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill="both", expand=True, pady=5)

    scrollbar = tk.Scrollbar(listbox_frame)
    feed_listbox = tk.Listbox(
        listbox_frame,
        yscrollcommand=scrollbar.set,
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0,
    )
    scrollbar.config(command=feed_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    feed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_listbox():
        feed_listbox.delete(0, tk.END)
        # ÄNDRING 1: Iterera över lista av tuples
        for name, url in config.CURRENT_FEEDS:
            feed_listbox.insert(tk.END, f"{name}: {url}")

    # ÄNDRING 1: Kontroller för att flytta flöden
    move_ctrl = tk.Frame(frame, bg=theme["frame_bg"])
    move_ctrl.pack(fill="x", pady=5)
    
    ttk.Button(
        move_ctrl,
        text="Move Up (↑)",
        command=lambda: move_feed(feed_listbox, populate_listbox, -1, button_frame, scrollable_frame),
    ).pack(side="left", expand=True, padx=5)
    
    ttk.Button(
        move_ctrl,
        text="Move Down (↓)",
        command=lambda: move_feed(feed_listbox, populate_listbox, 1, button_frame, scrollable_frame),
    ).pack(side="left", expand=True, padx=5)
    
    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)

    ctrl = tk.Frame(frame, bg=theme["frame_bg"])
    ctrl.pack(fill="x", pady=5)

    ttk.Button(
        ctrl,
        text="Add New Feed",
        command=lambda: add_feed(populate_listbox, button_frame, scrollable_frame),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        ctrl,
        text="Edit Selected",
        command=lambda: edit_feed(
            feed_listbox, populate_listbox, button_frame, scrollable_frame
        ),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        ctrl,
        text="Remove Selected",
        command=lambda: remove_feed(
            feed_listbox, populate_listbox, button_frame, scrollable_frame
        ),
    ).pack(side="right", expand=True, padx=5)

    populate_listbox()
    
    # ÄNDRING 2: Återställ referensen när fönstret stängs
    def on_close():
        config.FEED_MANAGER_WINDOW = None
        manager_root.destroy()
        
    manager_root.protocol("WM_DELETE_WINDOW", on_close)
    themes.apply_theme_to_widget(manager_root, config.CURRENT_THEME)


# ---------- SAVED LISTS HELPER (ÄNDRING 4) ----------
def save_current_list_and_refresh(refresh_listbox):
    """Saves the current feed list and updates the saved lists listbox."""
    save_current_list()
    refresh_listbox()


# ---------- SAVED LISTS (ÄNDRING 2, 4) ----------
def show_saved_lists_window(button_frame, scrollable_frame):
    # ÄNDRING 2: Förhindra dubbelöppning
    if config.SAVED_LISTS_WINDOW and config.SAVED_LISTS_WINDOW.winfo_exists():
        config.SAVED_LISTS_WINDOW.lift()
        return

    theme = themes.THEMES[config.CURRENT_THEME]

    saved_root = tk.Toplevel(config.ROOT)
    config.SAVED_LISTS_WINDOW = saved_root # Spara referens
    saved_root.title("Manage Feed Lists") # ÄNDRING 4: Ny titel
    saved_root.geometry("600x300")
    saved_root.configure(bg=theme["bg"])
    saved_root.grab_set()

    frame = tk.Frame(saved_root, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text="Select a list to manage:",
        font=("Arial", 10, "bold"),
        bg=theme["frame_bg"],
        fg=theme["fg"],
    ).pack(anchor="w", pady=(0, 5))

    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill="both", expand=True, pady=5)

    listbox_scrollbar = tk.Scrollbar(listbox_frame)
    listbox = tk.Listbox(
        listbox_frame,
        yscrollcommand=listbox_scrollbar.set,
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0,
    )
    listbox_scrollbar.config(command=listbox.yview)
    listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_saved_listbox():
        listbox.delete(0, tk.END)
        for name in sorted(config.SAVED_LISTS.keys()):
            display_name = (
                f"{name} (Default)"
                if name == config.DEFAULT_LIST_NAME
                else name
            )
            listbox.insert(tk.END, display_name)

    populate_saved_listbox()

    button_controls = tk.Frame(frame, bg=theme["frame_bg"])
    button_controls.pack(fill="x", pady=5)

    # ÄNDRING 4: Lägg till "Save Current List" som en sub-funktion
    ttk.Button(
        button_controls,
        text="Save Current List",
        command=lambda: save_current_list_and_refresh(populate_saved_listbox),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        button_controls,
        text="Load List",
        command=lambda: load_list(
            listbox, populate_saved_listbox, button_frame, scrollable_frame, saved_root
        ),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        button_controls,
        text="Set as Default",
        command=lambda: set_default_list(listbox, populate_saved_listbox),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        button_controls,
        text="Delete List",
        command=lambda: delete_list(listbox, populate_saved_listbox),
    ).pack(side="left", expand=True, padx=5)

    # ÄNDRING 2: Återställ referensen när fönstret stängs
    def on_close():
        config.SAVED_LISTS_WINDOW = None
        saved_root.destroy()
        
    saved_root.protocol("WM_DELETE_WINDOW", on_close)
    themes.apply_theme_to_widget(saved_root, config.CURRENT_THEME)


# ---------- FEED CRUD (ÄNDRING 1) ----------
def add_feed(refresh_listbox, button_frame, scrollable_frame):
    name = simpledialog.askstring(
        "Add Feed", "Enter the Category Name (e.g., Tech News):", parent=config.ROOT
    )
    if not name:
        return

    url = simpledialog.askstring(
        "Add Feed", f"Enter the RSS URL for {name}:", parent=config.ROOT
    )
    if not url:
        return

    name = name.strip()
    url = url.strip()

    # ÄNDRING 1: Kolla mot lista av tuples
    existing_names = [n for n, u in config.CURRENT_FEEDS]
    if name in existing_names:
        messagebox.showwarning("Warning", f"A feed named '{name}' already exists.")
        return

    # ÄNDRING 1: Lägg till som en tuple i listan
    config.CURRENT_FEEDS.append((name, url))
    config.save_config() # Spara ändringen
    refresh_listbox()
    update_category_buttons(button_frame, scrollable_frame)
    messagebox.showinfo("Success", f"Feed '{name}' has been added.")


def edit_feed(listbox, refresh_listbox, button_frame, scrollable_frame):
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        parts = item.split(": ", 1)
        if len(parts) != 2:
            raise ValueError("Invalid listbox item")

        old_name, old_url = parts[0].strip(), parts[1].strip()

        new_name = simpledialog.askstring(
            "Edit Feed Name",
            f"Enter new name for '{old_name}':",
            initialvalue=old_name,
            parent=config.ROOT,
        )
        if not new_name:
            return

        new_url = simpledialog.askstring(
            "Edit RSS URL",
            f"Enter new URL for '{new_name}':",
            initialvalue=old_url,
            parent=config.ROOT,
        )
        if not new_url:
            return

        new_name = new_name.strip()
        new_url = new_url.strip()

        # ÄNDRING 1: Kolla mot lista av tuples
        existing_names = [n for n, u in config.CURRENT_FEEDS if n != old_name]
        if new_name in existing_names:
            messagebox.showwarning(
                "Warning", f"A feed named '{new_name}' already exists."
            )
            return

        # ÄNDRING 1: Hitta index och uppdatera elementet
        current_index = get_feed_list_index_by_name(old_name)
        if current_index == -1: return

        was_active = old_url == config.ACTIVE_FEED_URL

        # ÄNDRING 1: Uppdatera elementet i listan
        config.CURRENT_FEEDS[current_index] = (new_name, new_url)

        # Update ALL_ARTICLES key if URL changed
        if old_url != new_url and old_url in config.ALL_ARTICLES:
            config.ALL_ARTICLES[new_url] = config.ALL_ARTICLES.pop(old_url)
        # Dictionary-specifik logik borttagen

        config.save_config() # Spara ändringen
        refresh_listbox()
        update_category_buttons(button_frame, scrollable_frame)
        messagebox.showinfo("Success", f"Feed '{new_name}' updated.")

        if was_active and old_url != new_url:
            for w in scrollable_frame.winfo_children():
                w.destroy()

    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to edit.")
    except Exception as e:
        messagebox.showerror("Error", f"Error editing feed: {e}")


def remove_feed(listbox, refresh_listbox, button_frame, scrollable_frame):
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        name = item.split(":")[0].strip()

        # ÄNDRING 1: Hitta index och ta bort från listan
        current_index = get_feed_list_index_by_name(name)

        if current_index != -1 and messagebox.askyesno(
            "Confirm", f"Remove '{name}'?"
        ):
            del config.CURRENT_FEEDS[current_index]
            config.save_config() # Spara ändringen
            refresh_listbox()
            update_category_buttons(button_frame, scrollable_frame)

            if len(config.CURRENT_FEEDS) == 0:
                for w in scrollable_frame.winfo_children():
                    w.destroy()

    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to remove.")


def save_current_list():
    list_name = simpledialog.askstring(
        "Save List",
        "Enter a name to save the current feed list:",
        parent=config.ROOT,
    )
    if not list_name:
        return

    if not config.CURRENT_FEEDS:
        messagebox.showwarning(
            "Warning", "The current list is empty and cannot be saved."
        )
        return

    # ÄNDRING 1: Spara listan av tuples
    config.SAVED_LISTS[list_name] = config.CURRENT_FEEDS.copy()
    config.save_config()

    messagebox.showinfo("Saved", f"Current feed list saved as '{list_name}'.")


def load_list(listbox, refresh_saved_listbox, button_frame, scrollable_frame, saved_root):
    try:
        idx = listbox.curselection()[0]
        selected_item = listbox.get(idx)
        list_name = selected_item.split(" (Default)")[0].strip()

        if list_name in config.SAVED_LISTS and messagebox.askyesno(
            "Load", f"Replace current feeds with '{list_name}'?"
        ):
            loaded_feeds = config.SAVED_LISTS[list_name]
            
            # ÄNDRING 1: Hantera bakåtkompatibilitet
            if isinstance(loaded_feeds, dict):
                config.CURRENT_FEEDS = list(loaded_feeds.items())
            else:
                config.CURRENT_FEEDS = loaded_feeds.copy()
                
            config.save_config() # Spara den nya listan som CURRENT_FEEDS
            update_category_buttons(button_frame, scrollable_frame)
            messagebox.showinfo("Loaded", f"Loaded list: '{list_name}'.")
            saved_root.destroy()
        else:
            messagebox.showwarning("Error", "Selected list not found.")

    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to load.")


def set_default_list(listbox, refresh_saved_listbox):
    try:
        idx = listbox.curselection()[0]
        selected_item = listbox.get(idx)
        list_name = selected_item.split(" (Default)")[0].strip()

        if list_name in config.SAVED_LISTS:
            config.DEFAULT_LIST_NAME = list_name
            config.save_config()
            refresh_saved_listbox()
            messagebox.showinfo("Default Set", f"'{list_name}' is now default.")

    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to set as default.")


def delete_list(listbox, refresh_saved_listbox):
    try:
        idx = listbox.curselection()[0]
        selected_item = listbox.get(idx)
        list_name = selected_item.split(" (Default)")[0].strip()

        if list_name == config.DEFAULT_LIST_NAME:
            messagebox.showwarning(
                "Cannot Delete", "Cannot delete the current default list."
            )
            return

        if list_name in config.SAVED_LISTS and messagebox.askyesno(
            "Confirm Delete", f"Delete '{list_name}' permanently?"
        ):
            del config.SAVED_LISTS[list_name]
            config.save_config()
            refresh_saved_listbox()
            messagebox.showinfo("Deleted", f"List '{list_name}' deleted.")

    except IndexError:
        messagebox.showwarning("Warning", "Please select a list to delete.")


# ---------- LOCATION MANAGER (ÄNDRING 2, 3) ----------
def location_manager_window():
    # ÄNDRING 2: Förhindra dubbelöppning
    if config.LOCATION_MANAGER_WINDOW and config.LOCATION_MANAGER_WINDOW.winfo_exists():
        config.LOCATION_MANAGER_WINDOW.lift()
        return

    theme = themes.THEMES[config.CURRENT_THEME]

    manager_root = tk.Toplevel(config.ROOT)
    config.LOCATION_MANAGER_WINDOW = manager_root # Spara referens
    manager_root.title("Location Settings")
    manager_root.geometry("400x350")
    manager_root.configure(bg=theme["bg"])
    manager_root.grab_set()

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(
        frame,
        text="📍 Select or Add a Location",
        font=("Arial", 11, "bold"),
        bg=theme["frame_bg"],
        fg=theme["headline_fg"],
    ).pack(fill="x", pady=(0, 5))

    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill="both", expand=True, pady=5)

    scrollbar = tk.Scrollbar(listbox_frame)

    location_listbox = tk.Listbox(
        listbox_frame,
        yscrollcommand=scrollbar.set,
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0,
    )
    scrollbar.config(command=location_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    location_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    utils.populate_location_listbox(location_listbox)

    button_controls = tk.Frame(frame, bg=theme["frame_bg"])
    button_controls.pack(fill="x", pady=(10, 5))

    def set_selected_location():
        try:
            sel = location_listbox.curselection()[0]
            new_loc = location_listbox.get(sel)
            utils.change_weather_location(new_loc, manager_root)
        except IndexError:
            messagebox.showwarning("Selection Error", "Please select a location.")

    ttk.Button(
        button_controls, text="Set Active Location", command=set_selected_location
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        button_controls,
        # ÄNDRING 3: Ta bort "..."
        text="Add New Location",
        command=lambda: utils.add_new_location_dialog(location_listbox, manager_root),
    ).pack(side="right", expand=True, padx=5)

    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=(5, 5))

    tk.Label(
        frame,
        text="Note: Weather data is mocked. New locations return 'N/A - Custom Location'.",
        wraplength=350,
        font=("Arial", 8, "italic"),
        bg=theme["frame_bg"],
        fg=theme["summary_fg"],
    ).pack(fill="x")
    
    # ÄNDRING 2: Återställ referensen när fönstret stängs
    def on_close():
        config.LOCATION_MANAGER_WINDOW = None
        manager_root.destroy()
        
    themes.apply_theme_to_widget(manager_root, config.CURRENT_THEME)

    manager_root.protocol("WM_DELETE_WINDOW", on_close)
    manager_root.update_idletasks()


# ---------- GUI SETUP (ÄNDRING 3, 4) ----------
def setup_gui():
    config.load_config()

    config.ROOT = tk.Tk()
    config.ROOT.title("News Feed by Mattias")
    config.ROOT.geometry("700x700")

    themes.configure_ttk_theme(config.CURRENT_THEME)
    theme = themes.THEMES[config.CURRENT_THEME]

    header_frame = tk.Frame(config.ROOT, bg=theme["frame_bg"], padx=10, pady=5)
    header_frame.pack(fill="x", padx=10, pady=(10, 0))

    config.DATETIME_LABEL = tk.Label(
        header_frame,
        text="",
        font=("Arial", 10, "bold"),
        bg=theme["frame_bg"],
        fg=theme["fg"],
    )
    config.DATETIME_LABEL.pack(side="left", padx=(0, 20))
    utils.update_datetime_label()

    ttk.Button(
        header_frame,
        text="Refresh",
        width=8,
        command=lambda: periodic_refresh(manual=True),
    ).pack(side="right", padx=10)

    config.WEATHER_LABEL = tk.Label(
        header_frame,
        text="Loading weather...",
        font=("Arial", 10, "italic"),
        bg=theme["frame_bg"],
        fg=theme["fg"],
    )
    config.WEATHER_LABEL.pack(side="right")
    utils.update_weather_display()

    # Menus
    menubar = tk.Menu(config.ROOT, bg=theme["menu_bg"], fg=theme["menu_fg"])
    config.ROOT.config(menu=menubar)

    # FILE MENU
    file_menu = tk.Menu(
        menubar,
        tearoff=0,
        bg=theme["menu_bg"],
        fg=theme["menu_fg"],
        activebackground=theme["menu_active_bg"],
        activeforeground=theme["menu_fg"],
    )
    menubar.add_cascade(label="File", menu=file_menu)

    # ÄNDRING 4: 'Save Current List' har flyttats till fönstret Manage Feed Lists och tas bort härifrån.

    # ÄNDRING 3 & 4: Döp om menyvalet och ta bort "..."
    file_menu.add_command(
        label="Manage Feed Lists",
        command=lambda: show_saved_lists_window(button_frame, scrollable_frame),
    )
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=config.ROOT.quit)

    # LOCATION MENU
    location_menu = tk.Menu(
        menubar,
        tearoff=0,
        bg=theme["menu_bg"],
        fg=theme["menu_fg"],
        activebackground=theme["menu_active_bg"],
        activeforeground=theme["menu_fg"],
    )
    menubar.add_cascade(label="Location", menu=location_menu)
    # ÄNDRING 3: Ta bort "..."
    location_menu.add_command(
        label="Change Location", command=location_manager_window
    )

    # STYLE MENU
    style_menu = tk.Menu(
        menubar,
        tearoff=0,
        bg=theme["menu_bg"],
        fg=theme["menu_fg"],
        activebackground=theme["menu_active_bg"],
        activeforeground=theme["menu_fg"],
    )
    menubar.add_cascade(label="Style", menu=style_menu)

    # theme toggle
    def toggle_theme():
        config.CURRENT_THEME = "dark" if config.CURRENT_THEME == "light" else "light"
        config.save_config()
        themes.apply_theme(config.ROOT, config.CURRENT_THEME)
        update_category_buttons(button_frame, scrollable_frame)

    style_menu.add_command(label="Toggle Dark/Light Mode", command=toggle_theme)

    # Main frames
    button_frame = tk.Frame(config.ROOT, bg=theme["frame_bg"])
    button_frame.pack(fill="x", padx=10, pady=(5, 5))

    main_frame = tk.Frame(config.ROOT, bg=theme["bg"])
    main_frame.pack(fill="both", expand=True, padx=10)

    canvas = tk.Canvas(main_frame, bg=theme["canvas_bg"], highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg=theme["frame_bg"])

    scrollbar = tk.Scrollbar(
        main_frame, orient="vertical", command=canvas.yview
    )
    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    enable_mouse_wheel(canvas)

    update_category_buttons(button_frame, scrollable_frame)

    periodic_refresh()

    themes.apply_theme(config.ROOT, config.CURRENT_THEME)

    config.ROOT.mainloop()
