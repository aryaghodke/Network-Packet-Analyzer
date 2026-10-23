"""
Top-level application menu bar with File / Edit / Capture / View / Help
menus, plus keyboard shortcut bindings.
"""

import tkinter as tk


class MenuBar(tk.Menu):
    def __init__(self, parent, callbacks, **kwargs):
        super().__init__(parent, **kwargs)
        self.callbacks = callbacks

        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="💾  Save Capture...", command=callbacks.get("save"), accelerator="Ctrl+S")
        file_menu.add_command(label="📂  Load Capture...", command=callbacks.get("load"), accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="⬇  Export to CSV...", command=callbacks.get("export_csv"))
        file_menu.add_command(label="⬇  Export to JSON...", command=callbacks.get("export_json"))
        file_menu.add_separator()
        file_menu.add_command(label="✕  Exit", command=callbacks.get("exit"), accelerator="Ctrl+Q")
        self.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(self, tearoff=0)
        edit_menu.add_command(label="🗑  Clear Packets", command=callbacks.get("clear"), accelerator="Ctrl+L")
        edit_menu.add_command(label="🔍  Find / Search...", command=callbacks.get("focus_search"), accelerator="Ctrl+F")
        self.add_cascade(label="Edit", menu=edit_menu)

        capture_menu = tk.Menu(self, tearoff=0)
        capture_menu.add_command(label="▶  Start Capture", command=callbacks.get("start"), accelerator="F5")
        capture_menu.add_command(label="■  Stop Capture", command=callbacks.get("stop"), accelerator="F6")
        self.add_cascade(label="Capture", menu=capture_menu)

        view_menu = tk.Menu(self, tearoff=0)
        view_menu.add_command(label="☾  Toggle Dark / Light Mode", command=callbacks.get("toggle_theme"))
        view_menu.add_command(label="📈  Show Statistics / Graphs", command=callbacks.get("graphs"))
        self.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(self, tearoff=0)
        help_menu.add_command(label="ℹ  About", command=callbacks.get("about"))
        self.add_cascade(label="Help", menu=help_menu)

    def bind_shortcuts(self, root):
        root.bind("<Control-s>", lambda e: self.callbacks.get("save")())
        root.bind("<Control-o>", lambda e: self.callbacks.get("load")())
        root.bind("<Control-q>", lambda e: self.callbacks.get("exit")())
        root.bind("<Control-l>", lambda e: self.callbacks.get("clear")())
        root.bind("<Control-f>", lambda e: self.callbacks.get("focus_search")())
        root.bind("<F5>", lambda e: self.callbacks.get("start")())
        root.bind("<F6>", lambda e: self.callbacks.get("stop")())
