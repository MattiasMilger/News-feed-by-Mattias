import tkinter as tk
import tkinter.ttk as ttk

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
        "error_fg": "#D32F2F",
        "search_bg": "#FFA726"
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
        "error_fg": "#FF6B6B",
        "search_bg": "#FFA726"
    }
}

def configure_ttk_theme(current_theme_name):
    theme = THEMES[current_theme_name]
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass

    # Configure generic button (TButton)
    style.configure("TButton",
                    background=theme["button_bg"],
                    foreground=theme["button_fg"],
                    borderwidth=1,
                    focuscolor=theme["button_bg"],
                    font=("Arial", 10, "bold"),
                    padding=8)
    
    # Map states for TButton
    style.map("TButton",
              background=[('active', theme["button_active_bg"]), ('pressed', theme["button_active_bg"])],
              focuscolor=[('active', theme["button_bg"]), ('focus', theme["button_bg"])])

    # NOTE: Active.TButton style removed entirely to prevent any custom color.
    # The active button will now just be a standard TButton.

    style.configure("TFrame", background=theme["frame_bg"])
    style.configure("TLabel", background=theme["frame_bg"], foreground=theme["fg"])
    style.configure("TSeparator", background=theme["separator_bg"])
    style.configure("Vertical.TScrollbar", background=theme["frame_bg"], troughcolor=theme["bg"])

def apply_theme_to_widget(widget, current_theme_name):
    theme = THEMES[current_theme_name]
    widget_class = widget.winfo_class()
    try:
        if widget_class in ("Frame", "Labelframe"):
            widget.configure(bg=theme["frame_bg"])
        elif widget_class == "Label":
            widget.configure(bg=theme["frame_bg"], fg=theme["fg"])
        elif widget_class == "Canvas":
            widget.configure(bg=theme["canvas_bg"], highlightthickness=0)
        elif widget_class == "Listbox":
            # activestyle='none' removes the underline on selected items
            widget.configure(bg=theme["listbox_bg"], fg=theme["listbox_fg"],
                             selectbackground=theme["button_active_bg"], selectforeground=theme["fg"],
                             activestyle='none')
        elif widget_class == "Text":
            widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        elif widget_class == "Entry":
            widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        elif widget_class == "Button":
            widget.configure(bg=theme["button_bg"], fg=theme["button_fg"],
                             activebackground=theme["button_active_bg"], activeforeground=theme["button_fg"])
        elif widget_class == "Menu":
            widget.configure(bg=theme["menu_bg"], fg=theme["menu_fg"],
                             activebackground=theme["menu_active_bg"], activeforeground=theme["menu_fg"])
    except Exception:
        pass
    for child in widget.winfo_children():
        apply_theme_to_widget(child, current_theme_name)

def apply_theme(root, current_theme_name):
    configure_ttk_theme(current_theme_name)
    theme = THEMES[current_theme_name]
    try:
        root.configure(bg=theme["bg"])
    except Exception:
        pass
    apply_theme_to_widget(root, current_theme_name)