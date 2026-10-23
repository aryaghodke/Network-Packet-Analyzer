"""
Small, reusable, purely-presentational widgets shared across the app:
stat cards, filter chips, toast notifications, the animated "recording"
dot, and the empty-state overlay for the packet table.

None of these contain any capture / filtering / storage logic — they
only render data handed to them and call back out through plain
callables, exactly like the widgets they replace.
"""

import tkinter as tk

import customtkinter as ctk

from gui.theme import RADIUS_LG, RADIUS_MD, RADIUS_SM


# ---------------------------------------------------------------------------
# Stat card — used on the dashboard header row ("Total Packets", "TCP", ...)
# ---------------------------------------------------------------------------
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, theme, fonts, title, accent=None, icon="●", **kwargs):
        accent = accent or theme["accent"]
        super().__init__(
            parent,
            corner_radius=RADIUS_MD,
            fg_color=theme["card"],
            border_width=1,
            border_color=theme["border"],
            **kwargs,
        )
        self.theme = theme
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 0))

        badge = ctk.CTkLabel(
            top, text=icon, text_color=accent, font=(fonts["h1"][0], 14, "bold"),
            fg_color=theme["accent_soft"], corner_radius=RADIUS_SM, width=30, height=30,
        )
        badge.pack(side="left")

        ctk.CTkLabel(
            top, text=title.upper(), font=fonts["small_bold"], text_color=theme["text_muted"],
        ).pack(side="left", padx=(10, 0))

        self.value_label = ctk.CTkLabel(
            self, text="0", font=fonts["stat_value"], text_color=theme["text"], anchor="w",
        )
        self.value_label.pack(fill="x", padx=16, pady=(6, 14))

    def set_value(self, value):
        self.value_label.configure(text=str(value))


# ---------------------------------------------------------------------------
# Protocol filter chip — toggle button used inside the sidebar
# ---------------------------------------------------------------------------
class FilterChip(ctk.CTkButton):
    def __init__(self, parent, theme, fonts, text, accent, command=None, **kwargs):
        self.theme = theme
        self.accent = accent
        self._active = False
        super().__init__(
            parent,
            text=text,
            font=fonts["small_bold"],
            corner_radius=RADIUS_SM,
            height=30,
            fg_color=theme["input_bg"],
            hover_color=theme["card_hover"],
            text_color=theme["text_muted"],
            border_width=1,
            border_color=theme["border"],
            command=self._on_click,
            **kwargs,
        )
        self._user_command = command

    def _on_click(self):
        self.set_active(not self._active)
        if self._user_command:
            self._user_command(self._active)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=self.accent, text_color="#FFFFFF", border_color=self.accent)
        else:
            self.configure(
                fg_color=self.theme["input_bg"], text_color=self.theme["text_muted"],
                border_color=self.theme["border"],
            )

    def is_active(self):
        return self._active


# ---------------------------------------------------------------------------
# Animated "recording" dot — glowing green while capture is active
# ---------------------------------------------------------------------------
class CaptureDot(tk.Canvas):
    def __init__(self, parent, theme, size=14, bg=None, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0,
                          bg=bg or theme["card"], **kwargs)
        self.theme = theme
        self.size = size
        self._active = False
        self._phase = 0
        self._job = None
        self._idle_color = theme["text_faint"]
        self._active_color = theme["success"]
        self._draw(self._idle_color, glow=0)

    def _draw(self, color, glow):
        self.delete("all")
        c = self.size / 2
        if glow:
            self.create_oval(1, 1, self.size - 1, self.size - 1, fill="", outline=color, width=1)
        r = c - 3.5 if glow else c - 2
        self.create_oval(c - r, c - r, c + r, c + r, fill=color, outline="")

    def set_active(self, active: bool):
        self._active = active
        if active and self._job is None:
            self._pulse()
        elif not active:
            if self._job is not None:
                self.after_cancel(self._job)
                self._job = None
            self._draw(self._idle_color, glow=0)

    def _pulse(self):
        if not self._active:
            self._job = None
            return
        self._phase = (self._phase + 1) % 20
        glow = self._phase > 10
        self._draw(self._active_color, glow=glow)
        self._job = self.after(120, self._pulse)


# ---------------------------------------------------------------------------
# Toast notifications — slide in top-right, auto-dismiss
# ---------------------------------------------------------------------------
class ToastManager:
    """Owns a stack of floating toast cards anchored to the top-right
    corner of `host` (any widget that supports .place())."""

    KIND_COLORS_KEY = {"success": "success", "error": "danger", "info": "accent", "warning": "warning"}
    KIND_ICON = {"success": "✓", "error": "✕", "info": "ℹ", "warning": "!"}

    def __init__(self, host, theme_getter, fonts):
        self.host = host
        self.theme_getter = theme_getter
        self.fonts = fonts
        self._toasts = []

    def show(self, message, kind="info", title=None, duration_ms=3600):
        theme = self.theme_getter()
        color = theme[self.KIND_COLORS_KEY.get(kind, "accent")]
        icon = self.KIND_ICON.get(kind, "ℹ")

        card = ctk.CTkFrame(
            self.host, corner_radius=RADIUS_MD, fg_color=theme["card"],
            border_width=1, border_color=color,
        )
        icon_lbl = ctk.CTkLabel(
            card, text=icon, text_color=color, font=(self.fonts["h1"][0], 13, "bold"),
            fg_color="transparent", width=22,
        )
        icon_lbl.pack(side="left", padx=(14, 6), pady=12)

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.pack(side="left", padx=(0, 16), pady=10, fill="both", expand=True)
        if title:
            ctk.CTkLabel(
                text_frame, text=title, font=self.fonts["small_bold"],
                text_color=theme["text"], anchor="w", justify="left",
            ).pack(anchor="w")
        ctk.CTkLabel(
            text_frame, text=message, font=self.fonts["small"], text_color=theme["text_muted"],
            anchor="w", justify="left", wraplength=280,
        ).pack(anchor="w")

        card.update_idletasks()
        self._toasts.append(card)
        self._relayout()

        card.after(duration_ms, lambda: self._dismiss(card))

    def _relayout(self):
        y = 16
        for card in self._toasts:
            card.place(relx=1.0, x=-16, y=y, anchor="ne")
            card.update_idletasks()
            y += card.winfo_reqheight() + 10

    def _dismiss(self, card):
        if card in self._toasts:
            self._toasts.remove(card)
        try:
            card.destroy()
        except Exception:
            pass
        self._relayout()


# ---------------------------------------------------------------------------
# Empty state overlay — shown over the packet table when there's no data
# ---------------------------------------------------------------------------
class EmptyState(ctk.CTkFrame):
    def __init__(self, parent, theme, fonts, on_start=None, **kwargs):
        super().__init__(parent, corner_radius=0, fg_color=theme["table_bg"], **kwargs)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center, text="📡", font=(fonts["display"][0], 42), text_color=theme["text_faint"],
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            center, text="No packets captured yet", font=fonts["h1"], text_color=theme["text"],
        ).pack()
        ctk.CTkLabel(
            center, text="Start a live capture to see traffic flow in here.",
            font=fonts["small"], text_color=theme["text_muted"],
        ).pack(pady=(2, 16))

        if on_start is not None:
            ctk.CTkButton(
                center, text="▶  Start Capture", command=on_start, corner_radius=RADIUS_SM,
                fg_color=theme["accent"], hover_color=theme["accent_hover"], height=36,
                font=fonts["body_bold"],
            ).pack()
