"""
Premium design system for the Network Packet Analyzer.

Centralises every color, font, spacing and radius value used across the
GUI so the whole application stays visually consistent, and so the
Light / Dark toggle only has to swap one dictionary.

Nothing in here touches capture, database, filtering or export logic —
this module is purely presentational.
"""

import tkinter.font as tkfont

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
_PREFERRED_FAMILIES = ("Inter", "Poppins", "Segoe UI", "SF Pro Display", "Helvetica Neue")


def _resolve_font_family():
    try:
        available = set(tkfont.families())
    except Exception:
        available = set()
    for family in _PREFERRED_FAMILIES:
        if family in available:
            return family
    return "Helvetica"


FONT_FAMILY = None  # resolved lazily once a Tk root exists


def resolve_fonts():
    """Call once a Tk root has been created; resolves the best-available
    font family and returns the standard font-size scale used everywhere."""
    global FONT_FAMILY
    FONT_FAMILY = _resolve_font_family()
    return {
        "display": (FONT_FAMILY, 22, "bold"),      # page / dashboard titles
        "h1": (FONT_FAMILY, 16, "bold"),            # section titles
        "h2": (FONT_FAMILY, 13, "bold"),            # card titles
        "body": (FONT_FAMILY, 11, "normal"),        # regular text
        "body_bold": (FONT_FAMILY, 11, "bold"),
        "small": (FONT_FAMILY, 10, "normal"),       # muted / secondary text
        "small_bold": (FONT_FAMILY, 10, "bold"),
        "mono": ("Consolas", 10, "normal"),          # packet detail text
        "stat_value": (FONT_FAMILY, 24, "bold"),     # big numbers on stat cards
    }


# ---------------------------------------------------------------------------
# Spacing / radius scale (used by hand-drawn rounded-rect canvases and
# customtkinter `corner_radius=` params)
# ---------------------------------------------------------------------------
RADIUS_LG = 18
RADIUS_MD = 14
RADIUS_SM = 10
PAD = 16
GAP = 10

# ---------------------------------------------------------------------------
# Protocol accent colors — consistent across both themes so a protocol is
# always instantly recognizable by color.
# ---------------------------------------------------------------------------
PROTOCOL_COLORS = {
    "TCP": "#3B82F6",     # blue
    "UDP": "#A855F7",     # purple
    "HTTP": "#10B981",    # green
    "HTTPS": "#06B6D4",   # cyan
    "DNS": "#F59E0B",     # orange
    "ICMP": "#EF4444",    # red
    "ARP": "#EC4899",     # pink
    "OTHER": "#94A3B8",   # slate
}

# ---------------------------------------------------------------------------
# Full theme palettes
# ---------------------------------------------------------------------------
DARK_THEME = {
    "mode": "dark",
    "bg": "#0F172A",
    "bg_secondary": "#111827",
    "sidebar_bg": "#111827",
    "card": "#1E293B",
    "card_alt": "#182335",
    "card_hover": "#243149",
    "table_bg": "#161F32",
    "table_row_odd": "#161F32",
    "table_row_even": "#1B2740",
    "table_row_hover": "#22314D",
    "table_selected": "#33254F",
    "header_bg": "#111827",
    "toolbar_bg": "#111827",
    "status_bg": "#111827",
    "accent": "#7C3AED",
    "accent_hover": "#8B5CF6",
    "accent_soft": "#2A2050",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#FFFFFF",
    "text_muted": "#CBD5E1",
    "text_faint": "#64748B",
    "border": "#22304A",
    "border_soft": "#1B2740",
    "input_bg": "#1A2338",
    "scrollbar": "#2A3752",
}

LIGHT_THEME = {
    "mode": "light",
    "bg": "#F5F6FA",
    "bg_secondary": "#EEF1F8",
    "sidebar_bg": "#FFFFFF",
    "card": "#FFFFFF",
    "card_alt": "#F8FAFC",
    "card_hover": "#F1F0FE",
    "table_bg": "#FFFFFF",
    "table_row_odd": "#FFFFFF",
    "table_row_even": "#F6F7FC",
    "table_row_hover": "#EFEBFE",
    "table_selected": "#E4DBFC",
    "header_bg": "#FFFFFF",
    "toolbar_bg": "#FFFFFF",
    "status_bg": "#FFFFFF",
    "accent": "#7C3AED",
    "accent_hover": "#8B5CF6",
    "accent_soft": "#EFEBFE",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#0F172A",
    "text_muted": "#475569",
    "text_faint": "#94A3B8",
    "border": "#E4E7F1",
    "border_soft": "#ECEEF6",
    "input_bg": "#F5F6FB",
    "scrollbar": "#DADFEC",
}


def get_theme(dark_mode: bool) -> dict:
    return DARK_THEME if dark_mode else LIGHT_THEME
