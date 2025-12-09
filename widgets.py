import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import time

import config
import themes
import rss
import utils
import dialogs

def enable_mouse_wheel(canvas):
    def _on_mouse_wheel(event):
        if getattr(event, "delta", 0) < 0 or getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "unit")
        elif getattr(event, "delta", 0) > 0 or getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "unit")
    canvas.bind_all("<Button-4>", _on_mouse_wheel)
    canvas.bind_all("<Button-5>", _on_mouse_wheel)
    canvas.bind_all("<MouseWheel>", _on_mouse_wheel)

def highlight_text(text_widget, term):
    if not term:
        return

    highlight_color = themes.THEMES.get(config.CURRENT_THEME, {}).get("search_bg", "#FFA726")

    text_widget.config(state="normal")
    text_widget.tag_remove("highlight", "1.0", "end")

    term_lower = term.lower()
    content = text_widget.get("1.0", "end-1c").lower()

    start = 0
    while True:
        start = content.find(term_lower, start)
        if start == -1:
            break
        end = start + len(term)
        text_widget.tag_add("highlight", f"1.0+{start}c", f"1.0+{end}c")
        start = end

    text_widget.tag_config("highlight", background=highlight_color)
    text_widget.config(state="disabled")

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

    url_count = len(rss.parse_feed_urls(feed_url))
    is_amalgamated = url_count > 1

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
        error_label = tk.Label(container, text="No news entries found for this feed.", fg=theme["error_fg"], bg=theme["frame_bg"])
        error_label.pack(pady=10)

    for entry in entries_to_display:
        headline = entry.get("title", "No Title")
        link = entry.get("link", "#")
        summary_text = entry.get("summary", entry.get("description", ""))
        summary = (summary_text.split(".")[0] + "...") if summary_text else ""
        source_domain = getattr(entry, '_source_domain', None)

        headline_frame = tk.Frame(container, bg=theme["frame_bg"])
        headline_frame.pack(anchor="w", padx=15, pady=(5, 0), fill="x")

        hl = tk.Text(
            headline_frame,
            wrap="word",
            height=2,
            width=60,
            bg=theme["frame_bg"],
            fg=theme["headline_fg"],
            font=("Arial", 10, "bold"),
            bd=0,
            highlightthickness=0
        )
        hl.insert("1.0", headline)
        hl.config(state="disabled", cursor="hand2")
        hl.pack(side="left", fill="x", expand=True)
        hl.bind("<Button-1>", lambda e, l=link: webbrowser.open_new(l))

        if is_amalgamated and source_domain:
            source_label = tk.Label(
                headline_frame,
                text=f"[{source_domain}]",
                font=("Arial", 8, "italic"),
                fg=theme["summary_fg"],
                bg=theme["frame_bg"],
                anchor="e"
            )
            source_label.pack(side="right", padx=(5, 0))

        sl = tk.Text(
            container,
            wrap="word",
            height=3,
            width=70,
            bg=theme["frame_bg"],
            fg=theme["summary_fg"],
            font=("Arial", 9, "italic"),
            bd=0,
            highlightthickness=0
        )
        sl.insert("1.0", summary)
        sl.config(state="disabled")
        sl.pack(anchor="w", padx=15, pady=(0, 2), fill="x")

        search_word = config.SEARCH_TERM.get().strip()
        highlight_text(hl, search_word)
        highlight_text(sl, search_word)

        tk.Frame(container, height=1, bg=theme["separator_bg"]).pack(fill="x", padx=10, pady=2)

    if total_pages > 1:
        nav = tk.Frame(container, bg=theme["frame_bg"], pady=10)
        nav.pack(fill="x", padx=10)

        state_prev = "normal" if page_number > 1 else "disabled"
        tk.Button(nav, text="← Previous", state=state_prev, command=lambda: display_page(container, category_name, feed_url, page_number - 1)).pack(side="left", padx=10)

        MAX_BUTTONS = 5
        start_page = max(1, page_number - (MAX_BUTTONS // 2))
        end_page = min(total_pages, start_page + MAX_BUTTONS - 1)
        if end_page - start_page < MAX_BUTTONS - 1:
            start_page = max(1, total_pages - MAX_BUTTONS + 1)

        for i in range(start_page, end_page + 1):
            ttk.Button(nav, text=str(i), command=lambda p=i: display_page(container, category_name, feed_url, p), style="TButton").pack(side="left", padx=2)

        state_next = "normal" if page_number < total_pages else "disabled"
        tk.Button(nav, text="Next →", state=state_next, command=lambda: display_page(container, category_name, feed_url, page_number + 1)).pack(side="right", padx=10)

    if config.ROOT:
        config.ROOT.after(50, lambda: container.master.configure(scrollregion=container.master.bbox("all")))
    themes.apply_theme_to_widget(container, config.CURRENT_THEME)

def fetch_and_display_news(feed_url, container, category_name):
    theme = themes.THEMES[config.CURRENT_THEME]
    config.ACTIVE_FEED_URL = feed_url
    config.ACTIVE_FEED_CONTAINER = container

    for w in container.winfo_children():
        w.destroy()

    tk.Label(container, text="Fetching news...", font=("Arial", 12, "italic"), fg=theme["summary_fg"], bg=theme["frame_bg"]).pack(pady=50)

    try:
        entries = rss.fetch_feed_entries(feed_url, max_entries=100)
        config.ALL_ARTICLES[feed_url] = entries
        config.CURRENT_PAGE = 1
        display_page(container, category_name, feed_url, config.CURRENT_PAGE)
    except Exception as e:
        for w in container.winfo_children():
            w.destroy()
        messagebox.showerror("Fetching Error", f"Error fetching RSS:\n{e}")
    finally:
        time.sleep(0.05)

def periodic_refresh(manual=False):
    if config.ACTIVE_FEED_URL and config.ACTIVE_FEED_CONTAINER and config.ACTIVE_FEED_CONTAINER.winfo_exists():
        category_name = "Feed"
        for feed_data in config.CURRENT_FEEDS:
            name, url = feed_data[0], feed_data[1]
            if url == config.ACTIVE_FEED_URL:
                category_name = name
                break
        try:
            entries = rss.fetch_feed_entries(config.ACTIVE_FEED_URL, max_entries=100)
            config.ALL_ARTICLES[config.ACTIVE_FEED_URL] = entries
            display_page(config.ACTIVE_FEED_CONTAINER, category_name, config.ACTIVE_FEED_URL, config.CURRENT_PAGE)
            if manual:
                messagebox.showinfo("Refreshed", f"'{category_name}' refreshed.")
        except Exception as e:
            if manual:
                messagebox.showerror("Error", f"Refresh failed:\n{e}")
    elif manual:
        messagebox.showinfo("Refresh", "No active feed to refresh.")

    if not manual and config.ROOT:
        config.ROOT.after(config.REFRESH_INTERVAL_MS, periodic_refresh)

def update_category_buttons(button_frame, scrollable_frame):
    theme = themes.THEMES[config.CURRENT_THEME]
    for w in button_frame.winfo_children():
        w.destroy()

    main_container = tk.Frame(button_frame, bg=theme["frame_bg"])
    main_container.pack(side="left", fill="both", expand=True)

    feeds_by_row = {i: [] for i in range(1, 11)}
    for name, url, row in config.CURRENT_FEEDS:
        if 1 <= row <= 10:
            feeds_by_row[row].append((name, url, row))

    for row_num in range(1, 11):
        if feeds_by_row[row_num]:
            row_frame = tk.Frame(main_container, bg=theme["frame_bg"])
            row_frame.pack(fill="x", pady=2)

            canvas = tk.Canvas(row_frame, bg=theme["frame_bg"], height=40, highlightthickness=0)
            scrollbar = tk.Scrollbar(row_frame, orient="horizontal", command=canvas.xview)
            button_container = tk.Frame(canvas, bg=theme["frame_bg"])

            button_container.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.create_window((0, 0), window=button_container, anchor="nw")
            canvas.configure(xscrollcommand=scrollbar.set)

            def _on_mouse_wheel(event, c=canvas):
                if getattr(event, "delta", 0) < 0:
                    c.xview_scroll(1, "units")
                elif getattr(event, "delta", 0) > 0:
                    c.xview_scroll(-1, "units")
            canvas.bind_all("<Shift-MouseWheel>", _on_mouse_wheel)

            canvas.pack(side="top", fill="both", expand=True)
            scrollbar.pack(side="bottom", fill="x")

            for name, url, _ in feeds_by_row[row_num]:
                ttk.Button(
                    button_container,
                    text=name,
                    style="TButton",
                    command=lambda u=url, n=name: fetch_and_display_news(u, scrollable_frame, n)
                ).pack(side="left", padx=3, pady=5)

    ttk.Button(button_frame, text="Manage Feeds", command=lambda: dialogs.feed_manager_window(button_frame, scrollable_frame)).pack(side="right", padx=5, fill="y")

    if not config.CURRENT_FEEDS:
        tk.Label(main_container, text="List is empty. Add feeds via 'Manage Feeds'.", fg=theme["error_fg"], bg=theme["frame_bg"]).pack(side="left", padx=10)
        return

    feed_urls = [url for name, url, row in config.CURRENT_FEEDS]
    if config.ACTIVE_FEED_URL not in feed_urls:
        config.ACTIVE_FEED_URL = None

    if config.ACTIVE_FEED_URL is None and config.CURRENT_FEEDS:
        initial_name, initial_url, _ = config.CURRENT_FEEDS[0]
        fetch_and_display_news(initial_url, scrollable_frame, initial_name)

def location_manager_window():
    if config.LOCATION_MANAGER_WINDOW and config.LOCATION_MANAGER_WINDOW.winfo_exists():
        config.LOCATION_MANAGER_WINDOW.lift()
        return

    theme = themes.THEMES[config.CURRENT_THEME]
    manager_root = tk.Toplevel(config.ROOT)
    config.LOCATION_MANAGER_WINDOW = manager_root
    manager_root.title("Location Settings")
    manager_root.geometry("450x400")
    manager_root.configure(bg=theme["bg"])
    manager_root.transient(config.ROOT)
    manager_root.grab_set()

    frame = tk.Frame(manager_root, bg=theme["frame_bg"], padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="📍 Select or Add a Location", font=("Arial", 11, "bold"), bg=theme["frame_bg"], fg=theme["headline_fg"]).pack(fill="x", pady=(0, 5))

    listbox_frame = tk.Frame(frame, bg=theme["frame_bg"])
    listbox_frame.pack(fill="both", expand=True, pady=5)
    scrollbar = tk.Scrollbar(listbox_frame)
    location_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, bg=theme["listbox_bg"], fg=theme["listbox_fg"], highlightthickness=0)
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
            messagebox.showwarning("Error", "Please select a location.", parent=manager_root)

    ttk.Button(button_controls, text="Set Active", command=set_selected_location).pack(side="left", expand=True, padx=2)
    ttk.Button(button_controls, text="Delete Selected", command=lambda: utils.delete_location(location_listbox, manager_root)).pack(side="left", expand=True, padx=2)
    ttk.Button(button_controls, text="Add New", command=lambda: utils.add_new_location_dialog(location_listbox, manager_root)).pack(side="left", expand=True, padx=2)

    def on_close():
        config.LOCATION_MANAGER_WINDOW = None
        manager_root.destroy()

    themes.apply_theme_to_widget(manager_root, config.CURRENT_THEME)
    manager_root.protocol("WM_DELETE_WINDOW", on_close)

def set_default_list():
    config.DEFAULT_LIST_NAME = config.ACTIVE_LIST_NAME
    config.save_config()
    messagebox.showinfo("Default Set", f"'{config.ACTIVE_LIST_NAME}' is now the startup list.")

def on_exit():
    saved_state = config.SAVED_LISTS.get(config.ACTIVE_LIST_NAME, [])
    mem_state_lists = [list(x) for x in config.CURRENT_FEEDS]
    saved_state_lists = [list(x) for x in saved_state]

    if mem_state_lists != saved_state_lists:
        if messagebox.askyesno("Unsaved Changes", f"Save changes to list '{config.ACTIVE_LIST_NAME}' before exiting?"):
            dialogs.save_current_list()

    config.ROOT.destroy()

def setup_gui():
    config.load_config()
    config.ROOT = tk.Tk()
    config.ROOT.title("News Feed by Mattias")
    config.ROOT.geometry("700x700")
    config.ROOT.protocol("WM_DELETE_WINDOW", on_exit)

    themes.configure_ttk_theme(config.CURRENT_THEME)
    theme = themes.THEMES[config.CURRENT_THEME]

    header_frame = tk.Frame(config.ROOT, bg=theme["frame_bg"], padx=10, pady=5)
    header_frame.pack(fill="x", padx=10, pady=(10, 0))

    config.DATETIME_LABEL = tk.Label(header_frame, text="", font=("Arial", 10, "bold"), bg=theme["frame_bg"], fg=theme["fg"])
    config.DATETIME_LABEL.pack(side="left", padx=(0, 20))
    utils.update_datetime_label()

    ttk.Button(header_frame, text="Refresh", width=8, command=lambda: periodic_refresh(manual=True)).pack(side="right", padx=10)

    config.WEATHER_LABEL = tk.Label(header_frame, text="Loading weather...", font=("Arial", 10, "italic"), bg=theme["frame_bg"], fg=theme["fg"])
    config.WEATHER_LABEL.pack(side="right")
    utils.update_weather_display()

    config.SEARCH_TERM = tk.StringVar()
    search_entry = ttk.Entry(header_frame, textvariable=config.SEARCH_TERM, width=20)
    search_entry.pack(side="right", padx=(10, 5))
    search_entry.insert(0, "Search...")
    search_entry.bind("<FocusIn>", lambda e: search_entry.delete(0, "end"))
    search_entry.bind("<KeyRelease>", lambda e: display_page(
        config.ACTIVE_FEED_CONTAINER,
        "Feed",
        config.ACTIVE_FEED_URL,
        config.CURRENT_PAGE
    ) if config.ACTIVE_FEED_URL else None)

    menubar = tk.Menu(config.ROOT, bg=theme["menu_bg"], fg=theme["menu_fg"])
    config.ROOT.config(menu=menubar)

    file_menu = tk.Menu(menubar, tearoff=0, bg=theme["menu_bg"], fg=theme["menu_fg"], activebackground=theme["menu_active_bg"], activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="New List", command=lambda: dialogs.new_list_dialog(button_frame, scrollable_frame))
    file_menu.add_command(label="Open List", command=lambda: dialogs.open_list_dialog(button_frame, scrollable_frame))
    file_menu.add_separator()
    file_menu.add_command(label="Save", command=dialogs.save_current_list)
    file_menu.add_command(label="Save As", command=dialogs.save_current_list_as)
    file_menu.add_separator()
    file_menu.add_command(label="Set as Default", command=set_default_list)
    file_menu.add_command(label="Delete List", command=dialogs.delete_list_dialog)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=on_exit)

    location_menu = tk.Menu(menubar, tearoff=0, bg=theme["menu_bg"], fg=theme["menu_fg"], activebackground=theme["menu_active_bg"], activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="Location", menu=location_menu)
    location_menu.add_command(label="Change Location", command=location_manager_window)

    style_menu = tk.Menu(menubar, tearoff=0, bg=theme["menu_bg"], fg=theme["menu_fg"], activebackground=theme["menu_active_bg"], activeforeground=theme["menu_fg"])
    menubar.add_cascade(label="Style", menu=style_menu)

    def toggle_theme():
        config.CURRENT_THEME = "dark" if config.CURRENT_THEME == "light" else "light"
        config.save_config()
        themes.apply_theme(config.ROOT, config.CURRENT_THEME)
        themes.configure_ttk_theme(config.CURRENT_THEME)
        update_category_buttons(button_frame, scrollable_frame)
        utils.update_weather_display()
        utils.update_datetime_label()

    style_menu.add_command(label="Toggle Dark/Light Mode", command=toggle_theme)

    help_menu = tk.Menu(menubar, tearoff=0, bg=theme["menu_bg"], fg=theme["menu_fg"])
    menubar.add_cascade(label="Help", menu=help_menu)

    def show_info():
        messagebox.showinfo(
            "About this App",
            "This is your personal News Feed app.\n\n"
            "• Select a feed from the top rows.\n"
            "• Headlines and summaries appear below.\n"
            "• Use the Search box (top-right) to highlight words.\n"
            "• Use File → Manage Lists to customize feeds.\n"
            "• Use Location menu to change weather city.\n"
            "• Use Style to toggle dark/light mode.\n\n"
            "Enjoy reading the news!"
        )

    help_menu.add_command(label="Info", command=show_info)

    button_frame = tk.Frame(config.ROOT, bg=theme["frame_bg"])
    button_frame.pack(fill="x", padx=10, pady=(5, 5))

    main_frame = tk.Frame(config.ROOT, bg=theme["bg"])
    main_frame.pack(fill="both", expand=True, padx=10)

    canvas = tk.Canvas(main_frame, bg=theme["canvas_bg"], highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg=theme["frame_bg"])
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    enable_mouse_wheel(canvas)

    update_category_buttons(button_frame, scrollable_frame)
    periodic_refresh()
    themes.apply_theme(config.ROOT, config.CURRENT_THEME)

    config.ROOT.mainloop()
