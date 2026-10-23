"""
Packet detail panel (bottom docked panel) and the packet-detail popup
window (opened on double-click / right-click "View Details").
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from gui.theme import get_theme, resolve_fonts, RADIUS_MD, RADIUS_SM


class DetailPanel(ctk.CTkFrame):
    """Docked panel at the bottom of the main window showing details of
    the currently selected packet."""

    def __init__(self, parent, dark_mode=True, **kwargs):
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        super().__init__(parent, corner_radius=RADIUS_MD, fg_color=theme["card"],
                          border_width=1, border_color=theme["border"], **kwargs)
        self.theme = theme
        self.fonts = fonts

        ctk.CTkLabel(
            self, text="Packet Details", font=fonts["h2"], text_color=theme["text"], anchor="w",
        ).pack(anchor="w", padx=16, pady=(12, 6))

        self.text = tk.Text(
            self, height=7, wrap="word", state="disabled", relief="flat",
            bg=theme["input_bg"], fg=theme["text_muted"], insertbackground=theme["text"],
            font=fonts["mono"], padx=12, pady=10, borderwidth=0, highlightthickness=0,
        )
        self.text.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def apply_theme(self, dark_mode: bool):
        theme = get_theme(dark_mode)
        self.theme = theme
        self.configure(fg_color=theme["card"], border_color=theme["border"])
        self.text.configure(bg=theme["input_bg"], fg=theme["text_muted"], insertbackground=theme["text"])

    def show_packet(self, pkt: dict):
        if pkt is None:
            return
        lines = [
            f"Packet No.        : {pkt.get('no')}",
            f"Timestamp         : {pkt.get('timestamp')}",
            f"Protocol          : {pkt.get('protocol')}",
            f"Source IP         : {pkt.get('src_ip')}",
            f"Destination IP    : {pkt.get('dst_ip')}",
            f"Source Port       : {pkt.get('src_port')}",
            f"Destination Port  : {pkt.get('dst_port')}",
            f"Source MAC        : {pkt.get('src_mac')}",
            f"Destination MAC   : {pkt.get('dst_mac')}",
            f"Length            : {pkt.get('length')} bytes",
            f"Info              : {pkt.get('info')}",
        ]
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


class PacketDetailPopup(tk.Toplevel):
    """A standalone popup window showing full details of one packet."""

    def __init__(self, parent, pkt: dict, dark_mode=True):
        super().__init__(parent)
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        self.title(f"Packet #{pkt.get('no')} Details")
        self.geometry("500x440")
        self.resizable(True, True)
        self.configure(bg=theme["bg"])

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Detail.TNotebook", background=theme["bg"], borderwidth=0)
        style.configure(
            "Detail.TNotebook.Tab", background=theme["card"], foreground=theme["text_muted"],
            padding=(14, 8), font=fonts["small_bold"], borderwidth=0,
        )
        style.map(
            "Detail.TNotebook.Tab",
            background=[("selected", theme["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )
        style.configure("Detail.TFrame", background=theme["bg"])
        style.configure("Detail.TLabel", background=theme["bg"], foreground=theme["text_muted"], font=fonts["body"])
        style.configure("DetailBold.TLabel", background=theme["bg"], foreground=theme["text"], font=fonts["body_bold"])

        notebook = ttk.Notebook(self, style="Detail.TNotebook")
        notebook.pack(fill="both", expand=True, padx=14, pady=14)

        summary_tab = ttk.Frame(notebook, style="Detail.TFrame")
        notebook.add(summary_tab, text="Summary")

        fields = [
            ("Packet No.", pkt.get("no")),
            ("Timestamp", pkt.get("timestamp")),
            ("Protocol", pkt.get("protocol")),
            ("Source IP", pkt.get("src_ip")),
            ("Destination IP", pkt.get("dst_ip")),
            ("Source Port", pkt.get("src_port")),
            ("Destination Port", pkt.get("dst_port")),
            ("Source MAC", pkt.get("src_mac")),
            ("Destination MAC", pkt.get("dst_mac")),
            ("Length", f"{pkt.get('length')} bytes"),
        ]
        for row, (label, value) in enumerate(fields):
            ttk.Label(summary_tab, text=label + ":", style="DetailBold.TLabel").grid(
                row=row, column=0, sticky="w", padx=12, pady=5)
            ttk.Label(summary_tab, text=str(value), style="Detail.TLabel").grid(
                row=row, column=1, sticky="w", padx=12, pady=5)

        info_tab = ttk.Frame(notebook, style="Detail.TFrame")
        notebook.add(info_tab, text="Info / Raw Summary")
        info_text = tk.Text(
            info_tab, wrap="word", relief="flat", bg=theme["input_bg"], fg=theme["text_muted"],
            insertbackground=theme["text"], font=fonts["mono"], padx=12, pady=10,
            borderwidth=0, highlightthickness=0,
        )
        info_text.pack(fill="both", expand=True, padx=10, pady=10)
        info_text.insert("1.0", str(pkt.get("info", "")) + "\n\n" + str(pkt.get("raw_summary", "")))
        info_text.configure(state="disabled")

        ctk.CTkButton(
            self, text="Close", command=self.destroy, corner_radius=RADIUS_SM,
            fg_color=theme["accent"], hover_color=theme["accent_hover"],
            font=fonts["body_bold"], height=34, width=110,
        ).pack(pady=(0, 14))
