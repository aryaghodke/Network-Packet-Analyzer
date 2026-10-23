"""
Top header bar: brand, interface selector, capture controls (Start /
Stop), and the row of quick actions (Clear, Save, Load, Export,
Graphs, Theme toggle).

Public API kept identical to the original toolbar so `main_window.py`
does not need to change how it talks to this widget:
    Toolbar(parent, interfaces, callbacks)
    .set_capturing_state(bool)
    .get_selected_interface() -> str
    .start_btn / .stop_btn / .interface_combo / .interface_var
"""

import tkinter as tk

import customtkinter as ctk

from gui.theme import get_theme, resolve_fonts, RADIUS_MD, RADIUS_SM
from gui.widgets import CaptureDot


class Toolbar(ctk.CTkFrame):
    def __init__(self, parent, interfaces, callbacks, dark_mode=True, **kwargs):
        theme = get_theme(dark_mode)
        fonts = resolve_fonts()
        super().__init__(parent, corner_radius=0, fg_color=theme["header_bg"], **kwargs)
        self.theme = theme
        self.fonts = fonts
        self.callbacks = callbacks

        # Thin bottom border for separation from the body
        border = tk.Frame(self, height=1, bg=theme["border"])
        border.pack(side="bottom", fill="x")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(14, 10))

        # ---- Brand -------------------------------------------------
        brand = ctk.CTkFrame(row, fg_color="transparent")
        brand.pack(side="left")
        ctk.CTkLabel(
            brand, text="◆", font=(fonts["display"][0], 20, "bold"),
            text_color=theme["accent"], width=28,
        ).pack(side="left")
        ctk.CTkLabel(
            brand, text="PacketScope", font=fonts["h1"], text_color=theme["text"],
        ).pack(side="left", padx=(4, 0))

        # ---- Capture controls ---------------------------------------
        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", padx=(28, 0))

        ctk.CTkLabel(
            controls, text="INTERFACE", font=fonts["small_bold"], text_color=theme["text_muted"],
        ).pack(side="left", padx=(0, 8))

        self.interface_var = tk.StringVar(value=interfaces[0] if interfaces else "")
        self.interface_combo = ctk.CTkComboBox(
            controls, values=interfaces, variable=self.interface_var,
            width=220, corner_radius=RADIUS_SM, state="readonly",
            fg_color=theme["input_bg"], border_color=theme["border"],
            button_color=theme["accent"], button_hover_color=theme["accent_hover"],
            dropdown_fg_color=theme["card"], text_color=theme["text"],
            font=fonts["body"],
        )
        self.interface_combo.pack(side="left")

        self.dot = CaptureDot(controls, theme, size=12, bg=theme["header_bg"])
        self.dot.pack(side="left", padx=(16, 6))

        self.start_btn = ctk.CTkButton(
            controls, text="▶  Start Capture", command=callbacks.get("start"),
            corner_radius=RADIUS_SM, height=34, fg_color=theme["accent"],
            hover_color=theme["accent_hover"], font=fonts["body_bold"],
        )
        self.start_btn.pack(side="left", padx=(6, 6))

        self.stop_btn = ctk.CTkButton(
            controls, text="■  Stop", command=callbacks.get("stop"),
            corner_radius=RADIUS_SM, height=34, fg_color=theme["danger"],
            hover_color="#DC2626", font=fonts["body_bold"], state="disabled",
            width=90,
        )
        self.stop_btn.pack(side="left")

        # ---- Right-side icon actions ---------------------------------
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right")

        self.theme_btn = self._icon_button(right, "☾", callbacks.get("toggle_theme"), tooltip="Toggle theme")
        self.theme_btn.pack(side="right", padx=(6, 0))
        self._icon_button(right, "⚙", callbacks.get("about"), tooltip="About / Settings").pack(side="right", padx=(6, 0))
        self._icon_button(right, "📈", callbacks.get("graphs"), tooltip="Live statistics").pack(side="right", padx=(6, 0))

        # ---- Secondary quick-action row --------------------------------
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(0, 12))

        self._action_button(actions, "🗑  Clear", callbacks.get("clear")).pack(side="left", padx=(0, 8))
        self._action_button(actions, "💾  Save", callbacks.get("save")).pack(side="left", padx=(0, 8))
        self._action_button(actions, "📂  Load", callbacks.get("load")).pack(side="left", padx=(0, 8))
        self._sep(actions).pack(side="left", padx=8, fill="y")
        self._action_button(actions, "⬇  Export CSV", callbacks.get("export_csv")).pack(side="left", padx=(0, 8))
        self._action_button(actions, "⬇  Export JSON", callbacks.get("export_json")).pack(side="left")

    # ------------------------------------------------------------------
    def _icon_button(self, parent, symbol, command, tooltip=None):
        return ctk.CTkButton(
            parent, text=symbol, command=command, width=34, height=34,
            corner_radius=RADIUS_SM, fg_color=self.theme["input_bg"],
            hover_color=self.theme["card_hover"], text_color=self.theme["text"],
            font=(self.fonts["h1"][0], 13),
        )

    def _action_button(self, parent, text, command):
        return ctk.CTkButton(
            parent, text=text, command=command, height=30, corner_radius=RADIUS_SM,
            fg_color=self.theme["input_bg"], hover_color=self.theme["card_hover"],
            text_color=self.theme["text_muted"], font=self.fonts["small_bold"],
        )

    def _sep(self, parent):
        return tk.Frame(parent, width=1, bg=self.theme["border"])

    # ------------------------------------------------------------------
    def set_capturing_state(self, is_capturing: bool):
        self.start_btn.configure(state="disabled" if is_capturing else "normal")
        self.stop_btn.configure(state="normal" if is_capturing else "disabled")
        self.interface_combo.configure(state="disabled" if is_capturing else "readonly")
        self.dot.set_active(is_capturing)

    def get_selected_interface(self):
        return self.interface_var.get()
