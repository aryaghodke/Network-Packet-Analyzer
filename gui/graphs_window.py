"""
Separate Toplevel window that hosts the live statistics graphs
(pie chart, bar chart, timeline).
"""

import tkinter as tk

import customtkinter as ctk

from graphs.stats_graphs import StatsGraphs
from gui.theme import get_theme, resolve_fonts, RADIUS_LG


class GraphsWindow(tk.Toplevel):
    def __init__(self, parent, get_packets_callback, dark_mode=False):
        super().__init__(parent)
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        self.title("Live Traffic Statistics")
        self.geometry("940x680")
        self.configure(bg=theme["bg"])
        self.get_packets_callback = get_packets_callback

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(
            header, text="Live Traffic Statistics", font=fonts["h1"], text_color=theme["text"],
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="Auto-refreshing every 2s", font=fonts["small"], text_color=theme["text_muted"],
        ).pack(side="right")

        card = ctk.CTkFrame(
            self, corner_radius=RADIUS_LG, fg_color=theme["card"],
            border_width=1, border_color=theme["border"],
        )
        card.pack(fill="both", expand=True, padx=20, pady=(6, 20))

        container = tk.Frame(card, bg=theme["card"])
        container.pack(fill="both", expand=True, padx=14, pady=14)

        self.stats_graphs = StatsGraphs(container, dark_mode=dark_mode)

        self._refresh_job = None
        self._auto_refresh()

    def _auto_refresh(self):
        try:
            packets = self.get_packets_callback()
            self.stats_graphs.refresh(packets)
        except tk.TclError:
            return
        self._refresh_job = self.after(2000, self._auto_refresh)

    def apply_theme(self, dark_mode: bool):
        self.stats_graphs.apply_theme(dark_mode)

    def destroy(self):
        if self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        super().destroy()
