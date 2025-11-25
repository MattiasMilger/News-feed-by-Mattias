import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import config
import themes
import rss

def get_feed_list_index_by_name(feed_name):
    """Helper function to find index in CURRENT_FEEDS list."""
    for i, (name, url) in enumerate(config.CURRENT_FEEDS):
        if name == feed_name:
            return i
    return -1

def move_feed(listbox, refresh_listbox, direction, button_frame, scrollable_frame):
    """Move the selected feed up (-1) or down (+1) in the list."""
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        name = item.split(":")[0].strip()
        
        current_index = get_feed_list_index_by_name(name)
        
        if current_index == -1:
            return

        new_index = current_index + direction
        
        if 0 <= new_index < len(config.CURRENT_FEEDS):
            # Move object in central list
            feed_to_move = config.CURRENT_FEEDS.pop(current_index)
            config.CURRENT_FEEDS.insert(new_index, feed_to_move)
            
            # Update the dictionary in memory (but do not save to disk yet)
            config.SAVED_LISTS[config.ACTIVE_LIST_NAME] = config.CURRENT_FEEDS.copy()
            
            from widgets import update_category_buttons
            update_category_buttons(button_frame, scrollable_frame)
            
            refresh_listbox()
            # Select moved item
            listbox.selection_set(new_index)
            listbox.see(new_index)
            
    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to move.", parent=config.FEED_MANAGER_WINDOW)

def feed_manager_window(button_frame, scrollable_frame):
    """Window to manage current RSS feeds with ordering."""
    if config.FEED_MANAGER_WINDOW and config.FEED_MANAGER_WINDOW.winfo_exists():
        config.FEED_MANAGER_WINDOW.lift()
        return

    theme = themes.THEMES[config.CURRENT_THEME]

    manager_root = tk.Toplevel(config.ROOT)
    config.FEED_MANAGER_WINDOW = manager_root
    manager_root.title(f"Editing: {config.ACTIVE_LIST_NAME}")
    manager_root.minsize(650, 400)
    manager_root.geometry("650x400")
    manager_root.configure(bg=theme["bg"])
    
    # ON TOP Logic
    manager_root.transient(config.ROOT)
    manager_root.grab_set()

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill="both", expand=True)

    # Active list indicator
    active_label = tk.Label(
        frame,
        text=f"List: {config.ACTIVE_LIST_NAME} (Unsaved changes in memory)",
        font=("Arial", 10, "bold"),
        fg=theme["headline_fg"],
        bg=theme["frame_bg"]
    )
    active_label.pack(fill="x", pady=(0, 5))

    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill="both", expand=True, pady=5)

    scrollbar = tk.Scrollbar(listbox_frame)
    
    # Explicitly set colors here to avoid blue flash
    feed_listbox = tk.Listbox(
        listbox_frame,
        yscrollcommand=scrollbar.set,
        selectmode=tk.SINGLE,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        highlightthickness=0,
        activestyle='none',
        exportselection=False # Prevents weird blue selection conflicts
    )
    scrollbar.config(command=feed_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    feed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def populate_listbox():
        feed_listbox.delete(0, tk.END)
        for name, url in config.CURRENT_FEEDS:
            feed_listbox.insert(tk.END, f"{name}: {url}")

    # Controls - Changed to UP/DOWN
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
        command=lambda: add_feed(populate_listbox, button_frame, scrollable_frame, manager_root),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        ctrl,
        text="Edit Selected",
        command=lambda: edit_feed(
            feed_listbox, populate_listbox, button_frame, scrollable_frame, manager_root
        ),
    ).pack(side="left", expand=True, padx=5)

    ttk.Button(
        ctrl,
        text="Remove Selected",
        command=lambda: remove_feed(
            feed_listbox, populate_listbox, button_frame, scrollable_frame, manager_root
        ),
    ).pack(side="right", expand=True, padx=5)

    populate_listbox()
    
    def on_close():
        config.FEED_MANAGER_WINDOW = None
        manager_root.destroy()
        
    manager_root.protocol("WM_DELETE_WINDOW", on_close)
    themes.apply_theme_to_widget(manager_root, config.CURRENT_THEME)

def add_feed(refresh_listbox, button_frame, scrollable_frame, parent_win):
    """Add new feed with validation (updates memory only)."""
    name = simpledialog.askstring(
        "Add Feed", "Enter the Category Name (e.g., Tech News):", parent=parent_win
    )
    if not name:
        return

    url = simpledialog.askstring(
        "Add Feed", f"Enter the RSS URL for {name}:", parent=parent_win
    )
    if not url:
        return

    name = name.strip()
    url = url.strip()

    existing_names = [n for n, u in config.CURRENT_FEEDS]
    if name in existing_names:
        messagebox.showwarning("Warning", f"A feed named '{name}' already exists.", parent=parent_win)
        return

    # Removed: messagebox.showinfo("Validating", "Validating feed URL... This may take a moment.", parent=parent_win)
    valid, error_msg = rss.validate_feed(url)
    
    if not valid:
        messagebox.showerror("Invalid Feed", f"Feed validation failed:\n{error_msg}", parent=parent_win)
        return

    config.CURRENT_FEEDS.append((name, url))
    config.SAVED_LISTS[config.ACTIVE_LIST_NAME] = config.CURRENT_FEEDS.copy()
    
    refresh_listbox()
    from widgets import update_category_buttons
    update_category_buttons(button_frame, scrollable_frame)
    messagebox.showinfo("Success", f"Feed '{name}' added. Remember to File > Save to keep changes.", parent=parent_win)

def edit_feed(listbox, refresh_listbox, button_frame, scrollable_frame, parent_win):
    """Edit existing feed (updates memory only)."""
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        parts = item.split(": ", 1)
        if len(parts) != 2:
            raise ValueError("Invalid listbox item")

        old_name, old_url = parts[0].strip(), parts[1].strip()

        new_name = simpledialog.askstring(
            "Edit Feed Name", f"Enter new name for '{old_name}':",
            initialvalue=old_name, parent=parent_win,
        )
        if not new_name: return

        new_url = simpledialog.askstring(
            "Edit RSS URL", f"Enter new URL for '{new_name}':",
            initialvalue=old_url, parent=parent_win,
        )
        if not new_url: return

        new_name = new_name.strip()
        new_url = new_url.strip()

        existing_names = [n for n, u in config.CURRENT_FEEDS if n != old_name]
        if new_name in existing_names:
            messagebox.showwarning("Warning", f"A feed named '{new_name}' already exists.", parent=parent_win)
            return

        if old_url != new_url:
            # Removed: messagebox.showinfo("Validating", "Validating feed URL...", parent=parent_win)
            valid, error_msg = rss.validate_feed(new_url)
            if not valid:
                messagebox.showerror("Invalid Feed", f"Validation failed:\n{error_msg}", parent=parent_win)
                return

        current_index = get_feed_list_index_by_name(old_name)
        if current_index == -1: return

        was_active = old_url == config.ACTIVE_FEED_URL
        config.CURRENT_FEEDS[current_index] = (new_name, new_url)

        if old_url != new_url and old_url in config.ALL_ARTICLES:
            config.ALL_ARTICLES[new_url] = config.ALL_ARTICLES.pop(old_url)

        config.SAVED_LISTS[config.ACTIVE_LIST_NAME] = config.CURRENT_FEEDS.copy()

        refresh_listbox()
        from widgets import update_category_buttons
        update_category_buttons(button_frame, scrollable_frame)
        messagebox.showinfo("Success", "Feed updated. Remember to File > Save.", parent=parent_win)

        if was_active and old_url != new_url:
            for w in scrollable_frame.winfo_children(): w.destroy()

    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to edit.", parent=parent_win)
    except Exception as e:
        messagebox.showerror("Error", f"Error editing feed: {e}", parent=parent_win)

def remove_feed(listbox, refresh_listbox, button_frame, scrollable_frame, parent_win):
    """Remove selected feed (updates memory only)."""
    try:
        idx = listbox.curselection()[0]
        item = listbox.get(idx)
        name = item.split(":")[0].strip()
        current_index = get_feed_list_index_by_name(name)

        if current_index != -1 and messagebox.askyesno("Confirm", f"Remove '{name}'?", parent=parent_win):
            del config.CURRENT_FEEDS[current_index]
            config.SAVED_LISTS[config.ACTIVE_LIST_NAME] = config.CURRENT_FEEDS.copy()
            
            refresh_listbox()
            from widgets import update_category_buttons
            update_category_buttons(button_frame, scrollable_frame)

            if len(config.CURRENT_FEEDS) == 0:
                for w in scrollable_frame.winfo_children(): w.destroy()

    except IndexError:
        messagebox.showwarning("Warning", "Please select a feed to remove.", parent=parent_win)

def new_list_dialog(button_frame, scrollable_frame):
    """Create a new list."""
    dialog = tk.Toplevel(config.ROOT)
    dialog.title("New List")
    dialog.geometry("350x250")
    dialog.transient(config.ROOT)
    dialog.grab_set()
    
    theme = themes.THEMES[config.CURRENT_THEME]
    dialog.configure(bg=theme["bg"])
    
    frame = tk.Frame(dialog, bg=theme["frame_bg"], padx=20, pady=20)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="Create New Feed List", font=("Arial", 12, "bold"), bg=theme["frame_bg"], fg=theme["headline_fg"]).pack(pady=(0, 10))
    tk.Label(frame, text="Enter list name:", bg=theme["frame_bg"], fg=theme["fg"]).pack()
    
    name_entry = tk.Entry(frame, width=30, bg=theme["entry_bg"], fg=theme["entry_fg"])
    name_entry.pack(pady=(5, 15))
    name_entry.focus()
    
    choice_var = tk.StringVar(value="blank")
    tk.Radiobutton(frame, text="Create blank list", variable=choice_var, value="blank", bg=theme["frame_bg"], fg=theme["fg"], selectcolor=theme["entry_bg"]).pack(anchor="w")
    tk.Radiobutton(frame, text="Create from Default", variable=choice_var, value="default", bg=theme["frame_bg"], fg=theme["fg"], selectcolor=theme["entry_bg"]).pack(anchor="w", pady=(5, 15))
    
    def create():
        list_name = name_entry.get().strip()
        if not list_name: return
        if list_name in config.SAVED_LISTS:
            messagebox.showwarning("Warning", f"List '{list_name}' already exists.", parent=dialog)
            return
        
        if choice_var.get() == "blank":
            config.SAVED_LISTS[list_name] = []
        else:
            config.SAVED_LISTS[list_name] = config.DEFAULT_FEEDS.copy()
        
        # Switch to new list
        config.ACTIVE_LIST_NAME = list_name
        config.CURRENT_FEEDS = config.SAVED_LISTS[list_name]
        
        # KEY FIX: Reset Active Feed URL so it forces a refresh on the first item
        config.ACTIVE_FEED_URL = None
        
        config.save_config() # Save creation of new list
        
        from widgets import update_category_buttons
        update_category_buttons(button_frame, scrollable_frame)
        
        # Clear articles if the new list is truly blank
        if not config.CURRENT_FEEDS:
            for w in scrollable_frame.winfo_children(): w.destroy()
        
        messagebox.showinfo("Success", f"List '{list_name}' created and loaded.", parent=dialog)
        dialog.destroy()
    
    ttk.Button(frame, text="Create", command=create).pack(side="left", expand=True)
    ttk.Button(frame, text="Cancel", command=dialog.destroy).pack(side="right", expand=True)
    themes.apply_theme_to_widget(dialog, config.CURRENT_THEME)

def open_list_dialog(button_frame, scrollable_frame):
    """Simple dialog to open an existing list."""
    dialog = tk.Toplevel(config.ROOT)
    dialog.title("Open List")
    dialog.geometry("300x400")
    dialog.transient(config.ROOT)
    dialog.grab_set()
    
    theme = themes.THEMES[config.CURRENT_THEME]
    dialog.configure(bg=theme["bg"])
    
    frame = tk.Frame(dialog, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="Select List to Open:", bg=theme["frame_bg"], fg=theme["fg"]).pack(pady=(0,5))
    
    # Explicit styling to fix blue background issue
    listbox = tk.Listbox(
        frame,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        exportselection=False, # Fixes selection conflicts/blue color
        activestyle='none'
    )
    listbox.pack(fill="both", expand=True, pady=5)
    
    # Populate and Highlight Current
    active_index = None
    sorted_names = sorted(config.SAVED_LISTS.keys())
    
    for i, name in enumerate(sorted_names):
        display_text = name
        if name == config.ACTIVE_LIST_NAME:
            display_text += " (Current)"
            active_index = i
        listbox.insert(tk.END, display_text)
        
    if active_index is not None:
        listbox.selection_set(active_index)
        listbox.see(active_index)
        
    def load():
        try:
            sel = listbox.curselection()[0]
            raw_text = listbox.get(sel)
            name = raw_text.replace(" (Current)", "")
            
            config.ACTIVE_LIST_NAME = name
            # Deep copy to ensure we work on memory version
            config.CURRENT_FEEDS = [tuple(x) for x in config.SAVED_LISTS[name]]
            
            # Reset ACTIVE_FEED_URL to ensure widgets.py fetches the first feed of the NEW list
            config.ACTIVE_FEED_URL = None
            
            from widgets import update_category_buttons
            update_category_buttons(button_frame, scrollable_frame)
            if not config.CURRENT_FEEDS:
                for w in scrollable_frame.winfo_children(): w.destroy()
            
            messagebox.showinfo("Loaded", f"Loaded '{name}'.", parent=dialog)
            dialog.destroy()
        except IndexError:
            pass
            
    ttk.Button(frame, text="Open", command=load).pack(pady=10)
    themes.apply_theme_to_widget(dialog, config.CURRENT_THEME)

def delete_list_dialog():
    """Simple dialog to delete a list."""
    dialog = tk.Toplevel(config.ROOT)
    dialog.title("Delete List")
    dialog.geometry("300x400")
    dialog.transient(config.ROOT)
    dialog.grab_set()
    
    theme = themes.THEMES[config.CURRENT_THEME]
    dialog.configure(bg=theme["bg"])
    
    frame = tk.Frame(dialog, bg=theme["frame_bg"], padx=10, pady=10)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="Select List to Delete:", bg=theme["frame_bg"], fg=theme["fg"]).pack(pady=(0,5))
    
    # Explicit styling to fix blue background issue
    listbox = tk.Listbox(
        frame,
        bg=theme["listbox_bg"],
        fg=theme["listbox_fg"],
        selectbackground=theme["button_active_bg"],
        selectforeground=theme["fg"],
        exportselection=False, # Fixes selection conflicts
        activestyle='none'
    )
    listbox.pack(fill="both", expand=True, pady=5)
    
    # Populate and Highlight Current
    active_index = None
    sorted_names = sorted(config.SAVED_LISTS.keys())
    
    for i, name in enumerate(sorted_names):
        display_text = name
        if name == config.ACTIVE_LIST_NAME:
            display_text += " (Current)"
            active_index = i
        listbox.insert(tk.END, display_text)
        
    if active_index is not None:
        listbox.selection_set(active_index)
        listbox.see(active_index)
        
    def delete_action():
        try:
            sel = listbox.curselection()[0]
            raw_text = listbox.get(sel)
            name = raw_text.replace(" (Current)", "")
            
            if name == config.ACTIVE_LIST_NAME:
                messagebox.showwarning("Error", "Cannot delete the currently active list.", parent=dialog)
                return
            
            if messagebox.askyesno("Confirm", f"Permanently delete '{name}'?", parent=dialog):
                del config.SAVED_LISTS[name]
                if config.DEFAULT_LIST_NAME == name:
                    config.DEFAULT_LIST_NAME = config.ACTIVE_LIST_NAME
                config.save_config()
                
                listbox.delete(sel)
                messagebox.showinfo("Deleted", f"Deleted '{name}'.", parent=dialog)
        except IndexError:
            pass

    ttk.Button(frame, text="Delete Selected", command=delete_action).pack(pady=10)
    themes.apply_theme_to_widget(dialog, config.CURRENT_THEME)

def save_current_list():
    """Save current memory feeds to disk."""
    config.SAVED_LISTS[config.ACTIVE_LIST_NAME] = config.CURRENT_FEEDS.copy()
    if config.save_config():
        messagebox.showinfo("Saved", f"Changes to '{config.ACTIVE_LIST_NAME}' have been saved to disk.", parent=config.ROOT)
    else:
        messagebox.showerror("Error", "Failed to save configuration file.", parent=config.ROOT)

def save_current_list_as():
    """Save current feeds as new list."""
    list_name = simpledialog.askstring("Save List As", "Enter new list name:", parent=config.ROOT)
    if not list_name: return
    
    if list_name in config.SAVED_LISTS:
        if not messagebox.askyesno("Overwrite", f"'{list_name}' exists. Overwrite?", parent=config.ROOT):
            return
            
    config.SAVED_LISTS[list_name] = config.CURRENT_FEEDS.copy()
    config.ACTIVE_LIST_NAME = list_name # Switch to new list
    config.save_config()
    messagebox.showinfo("Saved", f"Saved as '{list_name}'.", parent=config.ROOT)