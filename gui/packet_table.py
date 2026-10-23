"""
Central packet table: a sortable, resizable ttk.Treeview showing all
captured packets, with a right-click context menu, double-click detail
popup support, zebra-striped + hover-highlighted rows, color-coded
protocols, and a friendly empty state when no packets exist.

Public API unchanged from the original widget: `add_packet`,
`clear`, `get_all_packets`, `apply_filtered_view`, `row_count`, the
`tree` attribute and the `_row_data` mapping main_window relies on.
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from utils.constants import TABLE_COLUMNS, COLUMN_WIDTHS
from gui.theme import get_theme, resolve_fonts, PROTOCOL_COLORS, RADIUS_MD
from gui.widgets import EmptyState


class PacketTable(ctk.CTkFrame):
    def __init__(self, parent, on_row_double_click=None, on_copy=None,
                 on_start_capture=None, dark_mode=True, **kwargs):
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        super().__init__(parent, corner_radius=RADIUS_MD, fg_color=theme["card"],
                          border_width=1, border_color=theme["border"], **kwargs)
        self.theme = theme
        self.fonts = fonts
        self.on_row_double_click = on_row_double_click
        self.on_copy = on_copy
        self._sort_reverse = {}
        self._row_data = {}   # Treeview iid -> packet dict
        self._row_tags = {}   # Treeview iid -> base tags (protocol, parity)
        self._parity = 0
        self._hovered_iid = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(
            header, text="Live Packets", font=fonts["h2"], text_color=theme["text"], anchor="w",
        ).pack(side="left")
        self.count_label = ctk.CTkLabel(
            header, text="0 rows", font=fonts["small"], text_color=theme["text_muted"],
        )
        self.count_label.pack(side="right")

        table_wrap = tk.Frame(self, bg=theme["card"])
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        style_name = "Packets.Treeview"
        self._configure_style(theme, fonts, style_name)

        self.tree = ttk.Treeview(
            table_wrap, columns=TABLE_COLUMNS, show="headings",
            selectmode="extended", style=style_name,
        )
        for col in TABLE_COLUMNS:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=COLUMN_WIDTHS.get(col, 100), anchor="w", stretch=True)

        vsb = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self._apply_row_tag_colors(theme)

        self.tree.bind("<Double-1>", self._handle_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Motion>", self._handle_motion)
        self.tree.bind("<Leave>", lambda e: self._clear_hover())

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Copy Row(s)", command=self._copy_selected)
        self.context_menu.add_command(label="View Details", command=self._view_selected_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Remove Selected", command=self._remove_selected)

        # Empty-state overlay, shown whenever the table has zero rows.
        self._empty_state = EmptyState(table_wrap, theme, fonts, on_start=on_start_capture)
        self._empty_state.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self._sync_empty_state()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def _configure_style(self, theme, fonts, style_name):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            style_name,
            background=theme["table_bg"], fieldbackground=theme["table_bg"],
            foreground=theme["text"], rowheight=28, borderwidth=0,
            font=fonts["body"],
        )
        style.map(style_name, background=[("selected", theme["table_selected"])])
        style.configure(
            style_name + ".Heading",
            background=theme["card_alt"], foreground=theme["text_muted"],
            font=fonts["small_bold"], borderwidth=0, relief="flat",
        )
        style.map(style_name + ".Heading", background=[("active", theme["card_hover"])])

    def _apply_row_tag_colors(self, theme):
        for proto, color in PROTOCOL_COLORS.items():
            self.tree.tag_configure(proto, foreground=color)
        self.tree.tag_configure("even", background=theme["table_row_even"])
        self.tree.tag_configure("odd", background=theme["table_row_odd"])
        self.tree.tag_configure("hover", background=theme["table_row_hover"])

    def apply_theme(self, dark_mode: bool):
        """Called by MainWindow whenever the light/dark toggle fires."""
        theme = get_theme(dark_mode)
        self.theme = theme
        self.configure(fg_color=theme["card"], border_color=theme["border"])
        self._configure_style(theme, self.fonts, "Packets.Treeview")
        self._apply_row_tag_colors(theme)

    # ------------------------------------------------------------------
    # Data operations
    # ------------------------------------------------------------------
    def add_packet(self, pkt: dict):
        """Append a single packet as a new row and auto-scroll to it."""
        tags = self._next_tags(pkt)
        iid = self.tree.insert("", "end", values=self._row_values(pkt), tags=tags)
        self._row_data[iid] = pkt
        self._row_tags[iid] = tags
        self.tree.see(iid)
        self._sync_empty_state()
        return iid

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self._row_data.clear()
        self._row_tags.clear()
        self._parity = 0
        self._sync_empty_state()

    def get_all_packets(self):
        return list(self._row_data.values())

    def apply_filtered_view(self, filtered_packets: list):
        """Rebuild the visible rows to show only `filtered_packets`."""
        self.tree.delete(*self.tree.get_children())
        self._row_data.clear()
        self._row_tags.clear()
        self._parity = 0
        for pkt in filtered_packets:
            tags = self._next_tags(pkt)
            iid = self.tree.insert("", "end", values=self._row_values(pkt), tags=tags)
            self._row_data[iid] = pkt
            self._row_tags[iid] = tags
        self._sync_empty_state()

    def row_count(self):
        return len(self.tree.get_children())

    def _next_tags(self, pkt):
        parity = "even" if self._parity % 2 == 0 else "odd"
        self._parity += 1
        return (pkt.get("protocol", "OTHER"), parity)

    def _sync_empty_state(self):
        count = self.row_count()
        self.count_label.configure(text=f"{count} row{'s' if count != 1 else ''}")
        if count == 0:
            self._empty_state.tkraise()
        else:
            self._empty_state.lower()

    @staticmethod
    def _row_values(pkt):
        return (
            pkt.get("no"), pkt.get("timestamp"), pkt.get("src_ip"), pkt.get("dst_ip"),
            pkt.get("src_port"), pkt.get("dst_port"), pkt.get("protocol"),
            pkt.get("length"), pkt.get("src_mac"), pkt.get("dst_mac"), pkt.get("info"),
        )

    def _sort_by(self, col):
        reverse = self._sort_reverse.get(col, False)
        items = [(self.tree.set(iid, col), iid) for iid in self.tree.get_children("")]

        def sort_key(pair):
            value = pair[0]
            try:
                return (0, float(value))
            except (TypeError, ValueError):
                return (1, str(value).lower())

        items.sort(key=sort_key, reverse=reverse)
        for index, (_, iid) in enumerate(items):
            self.tree.move(iid, "", index)
        self._sort_reverse[col] = not reverse

    # ------------------------------------------------------------------
    # Hover / interaction
    # ------------------------------------------------------------------
    def _handle_motion(self, event):
        iid = self.tree.identify_row(event.y)
        if iid == self._hovered_iid:
            return
        self._clear_hover()
        if iid:
            base_tags = self._row_tags.get(iid, ())
            self.tree.item(iid, tags=("hover",) + tuple(base_tags))
            self._hovered_iid = iid

    def _clear_hover(self):
        if self._hovered_iid and self._hovered_iid in self._row_tags:
            self.tree.item(self._hovered_iid, tags=self._row_tags[self._hovered_iid])
        self._hovered_iid = None

    def _handle_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and self.on_row_double_click:
            self.on_row_double_click(self._row_data.get(iid))

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _copy_selected(self):
        selected = self.tree.selection()
        if not selected or not self.on_copy:
            return
        rows = [self._row_data[iid] for iid in selected if iid in self._row_data]
        self.on_copy(rows)

    def _view_selected_details(self):
        selected = self.tree.selection()
        if selected and self.on_row_double_click:
            self.on_row_double_click(self._row_data.get(selected[0]))

    def _remove_selected(self):
        for iid in self.tree.selection():
            self.tree.delete(iid)
            self._row_data.pop(iid, None)
            self._row_tags.pop(iid, None)
        self._sync_empty_state()
