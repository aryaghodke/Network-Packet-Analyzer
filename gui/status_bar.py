"""
Bottom status bar: shows capture status, packet counts, live rates,
and a progress indicator while capturing.

Public API unchanged: `set_status`, `set_packet_count`, `set_rates`,
`start_progress`, `stop_progress`, and the `_human_bytes` static
helper that main_window calls directly.
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from gui.theme import get_theme, resolve_fonts


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, dark_mode=True, **kwargs):
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        super().__init__(parent, corner_radius=0, fg_color=theme["status_bg"], height=36, **kwargs)
        self.theme = theme
        self.fonts = fonts

        border = tk.Frame(self, height=1, bg=theme["border"])
        border.pack(side="top", fill="x")

        self.status_var = tk.StringVar(value="Ready")
        self.packet_count_var = tk.StringVar(value="Packets: 0")
        self.pps_var = tk.StringVar(value="0.0 pkt/s")
        self.bps_var = tk.StringVar(value="0 B/s")

        self.status_label = ctk.CTkLabel(
            self, textvariable=self.status_var, anchor="w",
            font=fonts["small"], text_color=theme["text_muted"],
        )
        self.status_label.pack(side="left", padx=16, pady=6)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Modern.Horizontal.TProgressbar", troughcolor=theme["input_bg"],
            background=theme["accent"], bordercolor=theme["input_bg"],
            lightcolor=theme["accent"], darkcolor=theme["accent"], thickness=6,
        )
        self.progress = ttk.Progressbar(
            self, mode="indeterminate", length=110, style="Modern.Horizontal.TProgressbar",
        )
        self.progress.pack(side="left", padx=8)

        self.bps_label = self._pill(self.bps_var)
        self.bps_label.pack(side="right", padx=(4, 16))
        self.pps_label = self._pill(self.pps_var)
        self.pps_label.pack(side="right", padx=4)
        self.packet_count_label = self._pill(self.packet_count_var, accent=True)
        self.packet_count_label.pack(side="right", padx=4)

    def _pill(self, var, accent=False):
        return ctk.CTkLabel(
            self, textvariable=var, font=self.fonts["small_bold"],
            text_color=self.theme["accent"] if accent else self.theme["text_muted"],
            fg_color=self.theme["card"], corner_radius=10, height=22, padx=10,
        )

    def apply_theme(self, dark_mode: bool):
        theme = get_theme(dark_mode)
        self.theme = theme
        self.configure(fg_color=theme["status_bg"])
        self.status_label.configure(text_color=theme["text_muted"])
        for lbl, accent in ((self.bps_label, False), (self.pps_label, False), (self.packet_count_label, True)):
            lbl.configure(
                fg_color=theme["card"],
                text_color=theme["accent"] if accent else theme["text_muted"],
            )

    def set_status(self, text: str):
        self.status_var.set(text)

    def set_packet_count(self, count: int):
        self.packet_count_var.set(f"Packets: {count}")

    def set_rates(self, pps: float, bps: float):
        self.pps_var.set(f"{pps:.1f} pkt/s")
        self.bps_var.set(self._human_bytes(bps) + "/s")

    def start_progress(self):
        self.progress.start(50)

    def stop_progress(self):
        self.progress.stop()

    @staticmethod
    def _human_bytes(n: float) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"
