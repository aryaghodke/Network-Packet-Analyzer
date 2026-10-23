"""
Left-hand sidebar: protocol filter chips, IP filter, port filter,
free-text search, and Apply / Reset buttons.

Validation and callback behaviour is unchanged from the original
implementation — only the widgets themselves are new.
"""

import customtkinter as ctk
from tkinter import messagebox

from utils.constants import (
    PROTO_TCP, PROTO_UDP, PROTO_ICMP, PROTO_ARP,
    PROTO_DNS, PROTO_HTTP, PROTO_HTTPS,
)
from utils.validators import is_valid_port, is_valid_ip_or_partial
from gui.theme import get_theme, resolve_fonts, PROTOCOL_COLORS, RADIUS_MD, RADIUS_SM
from gui.widgets import FilterChip


class FilterPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_apply=None, on_reset=None, dark_mode=True, width=250, **kwargs):
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        super().__init__(
            parent, width=width, corner_radius=0, fg_color=theme["sidebar_bg"],
            scrollbar_button_color=theme["scrollbar"],
            scrollbar_button_hover_color=theme["accent"],
            **kwargs,
        )
        self.theme = theme
        self.fonts = fonts
        self.on_apply = on_apply
        self.on_reset = on_reset

        ctk.CTkLabel(
            self, text="Filters", font=fonts["h1"], text_color=theme["text"], anchor="w",
        ).pack(fill="x", padx=16, pady=(18, 4))
        ctk.CTkLabel(
            self, text="Narrow down live traffic", font=fonts["small"],
            text_color=theme["text_muted"], anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 16))

        # ---- Protocol chips -----------------------------------------
        self._section_title("Protocols")
        chip_wrap = ctk.CTkFrame(self, fg_color="transparent")
        chip_wrap.pack(fill="x", padx=16, pady=(4, 12))

        self.protocol_chips = {}
        protocols = (PROTO_TCP, PROTO_UDP, PROTO_ICMP, PROTO_ARP, PROTO_DNS, PROTO_HTTP, PROTO_HTTPS)
        for i, proto in enumerate(protocols):
            accent = PROTOCOL_COLORS.get(proto, theme["accent"])
            chip = FilterChip(chip_wrap, theme, fonts, proto, accent)
            r, c = divmod(i, 2)
            chip.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
            self.protocol_chips[proto] = chip
        chip_wrap.grid_columnconfigure(0, weight=1)
        chip_wrap.grid_columnconfigure(1, weight=1)

        # ---- IP filter -------------------------------------------------
        self._section_title("IP Address")
        self.ip_entry = self._rounded_entry(placeholder="e.g. 192.168.1.")

        # ---- Port filter -----------------------------------------------
        self._section_title("Port Number")
        self.port_entry = self._rounded_entry(placeholder="e.g. 443")

        # ---- Search ----------------------------------------------------
        self._section_title("Search")
        self.search_entry = self._rounded_entry(placeholder="🔍  Search packets...")
        self.search_entry.bind("<Return>", lambda e: self._apply())

        # ---- Buttons -----------------------------------------------------
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(20, 16))
        ctk.CTkButton(
            btns, text="Apply Filters", command=self._apply, corner_radius=RADIUS_SM,
            fg_color=theme["accent"], hover_color=theme["accent_hover"], height=36,
            font=fonts["body_bold"],
        ).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            btns, text="Reset Filters", command=self._reset, corner_radius=RADIUS_SM,
            fg_color=theme["input_bg"], hover_color=theme["card_hover"],
            text_color=theme["text_muted"], height=36, font=fonts["body_bold"],
        ).pack(fill="x")

    # ------------------------------------------------------------------
    def _section_title(self, text):
        ctk.CTkLabel(
            self, text=text.upper(), font=self.fonts["small_bold"],
            text_color=self.theme["text_muted"], anchor="w",
        ).pack(fill="x", padx=16, pady=(6, 4))

    def _rounded_entry(self, placeholder=""):
        entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, corner_radius=RADIUS_SM, height=34,
            fg_color=self.theme["input_bg"], border_color=self.theme["border"],
            border_width=1, text_color=self.theme["text"],
            placeholder_text_color=self.theme["text_faint"],
            font=self.fonts["body"],
        )
        entry.pack(fill="x", padx=16, pady=(0, 10))
        return entry

    # ------------------------------------------------------------------
    def _apply(self):
        ip_text = self.ip_entry.get().strip()
        port_text = self.port_entry.get().strip()
        search_text = self.search_entry.get().strip()

        if not is_valid_ip_or_partial(ip_text):
            messagebox.showerror("Invalid Filter", "The IP address filter contains invalid characters.")
            return
        if not is_valid_port(port_text):
            messagebox.showerror("Invalid Filter", "Port must be a number between 0 and 65535.")
            return

        selected_protocols = [p for p, chip in self.protocol_chips.items() if chip.is_active()]

        if self.on_apply:
            self.on_apply(selected_protocols, ip_text, port_text, search_text)

    def _reset(self):
        for chip in self.protocol_chips.values():
            chip.set_active(False)
        self.ip_entry.delete(0, "end")
        self.port_entry.delete(0, "end")
        self.search_entry.delete(0, "end")
        if self.on_reset:
            self.on_reset()
