"""
Main application window.

Wires together the header/toolbar, menu bar, filter sidebar, packet
table, detail panel, status bar, capture engine, database, and
exporters into a single cohesive dashboard-style application.

All capture / filtering / persistence / export logic below is
unchanged from the original implementation — only presentation
(layout, widgets, colors, notifications) has been redesigned.
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

import customtkinter as ctk

from capture.packet_capture import PacketCapture, PacketCaptureError
from capture.filters import PacketFilter
from database.db_manager import DatabaseManager
from utils.exporters import Exporter, ExportError
from utils.constants import APP_TITLE, APP_VERSION, DB_PATH, DEFAULT_EXPORT_DIR

from gui.theme import get_theme, resolve_fonts, RADIUS_LG, RADIUS_MD, RADIUS_SM
from gui.toolbar import Toolbar
from gui.menu_bar import MenuBar
from gui.filter_panel import FilterPanel
from gui.packet_table import PacketTable
from gui.detail_panel import DetailPanel, PacketDetailPopup
from gui.status_bar import StatusBar
from gui.graphs_window import GraphsWindow
from gui.widgets import StatCard, ToastManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Stats shown as big dashboard cards across the top of the window.
DASHBOARD_STAT_KEYS = ["Total", "TCP", "UDP", "HTTP", "DNS"]
# Full breakdown shown in the compact "Live Statistics" side card.
SIDE_STAT_KEYS = ["Total", "TCP", "UDP", "ICMP", "ARP", "DNS", "HTTP", "HTTPS"]


class MainWindow(ctk.CTk):
    POLL_INTERVAL_MS = 200
    STATS_INTERVAL_MS = 1000

    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("1440x860")
        self.minsize(1150, 680)

        self.dark_mode = True
        self.theme = get_theme(self.dark_mode)
        self.fonts = resolve_fonts()
        self.configure(fg_color=self.theme["bg"])

        self.capture = PacketCapture(on_error=self._on_capture_error)
        self.db = DatabaseManager(DB_PATH)
        self.packet_filter = PacketFilter()
        self.graphs_window = None

        self._all_packets = []          # full, unfiltered packet store
        self._last_stat_time = time.time()
        self._last_stat_count = 0
        self._last_stat_bytes = 0

        try:
            interfaces = self.capture.list_interfaces()
        except PacketCaptureError as exc:
            interfaces = []
            messagebox.showwarning("Network Adapter", str(exc))
        if not interfaces:
            interfaces = ["(default)"]
        self._interface_count = len(interfaces)

        # Gentle fade-in on launch instead of the app just "popping" on screen.
        try:
            self.attributes("-alpha", 0.0)
        except tk.TclError:
            pass

        self.toast = ToastManager(self, lambda: self.theme, self.fonts)

        self._build_menu()
        self._build_toolbar(interfaces)
        self._build_body()
        self._build_status_bar()

        self.protocol("WM_DELETE_WINDOW", self._on_exit)
        self._apply_theme()
        self._poll_queue()
        self._update_stats_loop()
        self._fade_in()

    # ------------------------------------------------------------------
    # Launch animation
    # ------------------------------------------------------------------
    def _fade_in(self, step=0.0):
        try:
            step = min(step + 0.12, 1.0)
            self.attributes("-alpha", step)
            if step < 1.0:
                self.after(15, lambda: self._fade_in(step))
        except tk.TclError:
            pass

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_menu(self):
        callbacks = {
            "save": self._save_capture,
            "load": self._load_capture,
            "export_csv": self._export_csv,
            "export_json": self._export_json,
            "exit": self._on_exit,
            "clear": self._clear_packets,
            "focus_search": self._focus_search,
            "start": self._start_capture,
            "stop": self._stop_capture,
            "toggle_theme": self._toggle_theme,
            "graphs": self._open_graphs_window,
            "about": self._show_about,
        }
        self.menu_bar = MenuBar(self, callbacks)
        self.configure(menu=self.menu_bar)
        self.menu_bar.bind_shortcuts(self)

    def _build_toolbar(self, interfaces):
        callbacks = {
            "start": self._start_capture,
            "stop": self._stop_capture,
            "clear": self._clear_packets,
            "save": self._save_capture,
            "load": self._load_capture,
            "export_csv": self._export_csv,
            "export_json": self._export_json,
            "graphs": self._open_graphs_window,
            "toggle_theme": self._toggle_theme,
            "about": self._show_about,
        }
        self.toolbar = Toolbar(self, interfaces, callbacks, dark_mode=self.dark_mode)
        self.toolbar.pack(side="top", fill="x")

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color=self.theme["bg"], corner_radius=0)
        body.pack(side="top", fill="both", expand=True)

        # ---- Dashboard stat cards row ---------------------------------
        cards_row = ctk.CTkFrame(body, fg_color="transparent")
        cards_row.pack(fill="x", padx=20, pady=(18, 6))
        for i in range(6):
            cards_row.grid_columnconfigure(i, weight=1, uniform="cards")

        self.dashboard_cards = {}
        icons = {"Total": "◧", "TCP": "▤", "UDP": "▥", "HTTP": "◨", "DNS": "◈"}
        accents = {
            "Total": self.theme["accent"], "TCP": "#3B82F6", "UDP": "#A855F7",
            "HTTP": "#10B981", "DNS": "#F59E0B",
        }
        for i, key in enumerate(DASHBOARD_STAT_KEYS):
            title = "Total Packets" if key == "Total" else f"{key} Packets" if key in ("TCP", "UDP") else f"{key} Requests"
            card = StatCard(cards_row, self.theme, self.fonts, title, accent=accents[key], icon=icons[key])
            card.grid(row=0, column=i, padx=6, sticky="nsew")
            self.dashboard_cards[key] = card

        self.interfaces_card = StatCard(
            cards_row, self.theme, self.fonts, "Active Interfaces",
            accent=self.theme["success"], icon="⛁",
        )
        self.interfaces_card.grid(row=0, column=5, padx=6, sticky="nsew")
        self.interfaces_card.set_value(self._interface_count)

        # ---- Main 3-column layout: sidebar | table+details | live stats
        main_row = ctk.CTkFrame(body, fg_color="transparent")
        main_row.pack(fill="both", expand=True, padx=20, pady=(6, 16))
        main_row.grid_columnconfigure(1, weight=1)
        main_row.grid_rowconfigure(0, weight=1)

        # Left filter sidebar
        self.filter_panel = FilterPanel(
            main_row, on_apply=self._apply_filters, on_reset=self._reset_filters,
            dark_mode=self.dark_mode, width=250,
        )
        self.filter_panel.grid(row=0, column=0, sticky="ns", padx=(0, 14))

        # Center: packet table (top) + detail panel (bottom) in a paned window
        center_pane = ttk.PanedWindow(main_row, orient="vertical")
        center_pane.grid(row=0, column=1, sticky="nsew", padx=(0, 14))

        self.packet_table = PacketTable(
            center_pane,
            on_row_double_click=self._show_packet_popup,
            on_copy=self._copy_packets_to_clipboard,
            on_start_capture=self._start_capture,
            dark_mode=self.dark_mode,
        )
        center_pane.add(self.packet_table, weight=4)

        self.detail_panel = DetailPanel(center_pane, dark_mode=self.dark_mode)
        center_pane.add(self.detail_panel, weight=1)

        self.packet_table.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # Right: live counters card
        self.stats_frame = ctk.CTkFrame(
            main_row, corner_radius=RADIUS_MD, fg_color=self.theme["card"],
            border_width=1, border_color=self.theme["border"], width=220,
        )
        self.stats_frame.grid(row=0, column=2, sticky="ns")
        self.stats_frame.grid_propagate(False)

        ctk.CTkLabel(
            self.stats_frame, text="Live Statistics", font=self.fonts["h2"],
            text_color=self.theme["text"], anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 10))

        self.stat_labels = {}
        for label in SIDE_STAT_KEYS:
            row = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(
                row, text=label, font=self.fonts["small"], text_color=self.theme["text_muted"],
            ).pack(side="left")
            var = tk.StringVar(value="0")
            ctk.CTkLabel(
                row, textvariable=var, font=self.fonts["small_bold"], text_color=self.theme["text"],
            ).pack(side="right")
            self.stat_labels[label] = var

        sep = tk.Frame(self.stats_frame, height=1, bg=self.theme["border"])
        sep.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            self.stats_frame, text="BANDWIDTH", font=self.fonts["small_bold"],
            text_color=self.theme["text_muted"], anchor="w",
        ).pack(fill="x", padx=16)
        self.pps_label_var = tk.StringVar(value="0.0 pkt/s")
        self.bps_label_var = tk.StringVar(value="0 B/s")
        ctk.CTkLabel(
            self.stats_frame, textvariable=self.pps_label_var, font=self.fonts["body_bold"],
            text_color=self.theme["accent"], anchor="w",
        ).pack(fill="x", padx=16, pady=(6, 2))
        ctk.CTkLabel(
            self.stats_frame, textvariable=self.bps_label_var, font=self.fonts["body"],
            text_color=self.theme["text_muted"], anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 16))

    def _build_status_bar(self):
        self.status_bar = StatusBar(self, dark_mode=self.dark_mode)
        self.status_bar.pack(side="bottom", fill="x")

    # ------------------------------------------------------------------
    # Capture control
    # ------------------------------------------------------------------
    def _start_capture(self):
        if self.capture.is_capturing:
            return
        interface = self.toolbar.get_selected_interface()
        if interface == "(default)":
            interface = None
        try:
            self.capture.start(interface=interface)
        except PacketCaptureError as exc:
            self.toast.show(str(exc), kind="error", title="Capture Error")
            return

        self.toolbar.set_capturing_state(True)
        self.status_bar.set_status(f"Capturing on {interface or 'default interface'}...")
        self.status_bar.start_progress()

    def _stop_capture(self):
        if not self.capture.is_capturing:
            return
        self.capture.stop()
        self.toolbar.set_capturing_state(False)
        self.status_bar.set_status("Capture stopped.")
        self.status_bar.stop_progress()

    def _on_capture_error(self, message):
        self.after(0, lambda: self.toast.show(message, kind="error", title="Capture Error"))

    def _poll_queue(self):
        new_packets = self.capture.drain_queue()
        if new_packets:
            for pkt in new_packets:
                self._all_packets.append(pkt)
                if not self.packet_filter.is_active() or self.packet_filter.matches(pkt):
                    self.packet_table.add_packet(pkt)
            self._update_live_counters()
        self.after(self.POLL_INTERVAL_MS, self._poll_queue)

    def _update_stats_loop(self):
        now = time.time()
        elapsed = max(now - self._last_stat_time, 1e-6)
        total_count, total_bytes = self.capture.get_totals()

        pps = (total_count - self._last_stat_count) / elapsed
        bps = (total_bytes - self._last_stat_bytes) / elapsed

        self.status_bar.set_rates(pps, bps)
        self.status_bar.set_packet_count(len(self._all_packets))
        self.pps_label_var.set(f"{pps:.1f} pkt/s")
        self.bps_label_var.set(self.status_bar._human_bytes(bps) + "/s")

        self._last_stat_time = now
        self._last_stat_count = total_count
        self._last_stat_bytes = total_bytes

        self.after(self.STATS_INTERVAL_MS, self._update_stats_loop)

    def _update_live_counters(self):
        counts = {"Total": 0, "TCP": 0, "UDP": 0, "ICMP": 0, "ARP": 0, "DNS": 0, "HTTP": 0, "HTTPS": 0}
        for pkt in self._all_packets:
            counts["Total"] += 1
            proto = pkt.get("protocol")
            if proto in counts:
                counts[proto] += 1
        for label, var in self.stat_labels.items():
            var.set(str(counts.get(label, 0)))
        for key, card in self.dashboard_cards.items():
            card.set_value(counts.get(key, 0))

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------
    def _apply_filters(self, protocols, ip_text, port_text, search_text):
        self.packet_filter.set_protocols(protocols)
        self.packet_filter.set_ip_filter(ip_text)
        try:
            self.packet_filter.set_port_filter(port_text)
        except ValueError as exc:
            self.toast.show(str(exc), kind="error", title="Invalid Filter")
            return
        self.packet_filter.set_search_text(search_text)

        filtered = self.packet_filter.apply(self._all_packets)
        self.packet_table.apply_filtered_view(filtered)
        self.status_bar.set_status(f"Filter applied \u2014 showing {len(filtered)} of {len(self._all_packets)} packets.")

    def _reset_filters(self):
        self.packet_filter.reset()
        self.packet_table.apply_filtered_view(self._all_packets)
        self.status_bar.set_status("Filters reset \u2014 showing all packets.")

    def _focus_search(self):
        self.filter_panel.search_entry.focus_set()

    # ------------------------------------------------------------------
    # Packet table interactions
    # ------------------------------------------------------------------
    def _on_row_select(self, event):
        selected = self.packet_table.tree.selection()
        if not selected:
            return
        pkt = self.packet_table._row_data.get(selected[0])
        if pkt:
            self.detail_panel.show_packet(pkt)

    def _show_packet_popup(self, pkt):
        if pkt:
            PacketDetailPopup(self, pkt, dark_mode=self.dark_mode)

    def _copy_packets_to_clipboard(self, packets):
        lines = []
        for pkt in packets:
            lines.append(
                f"{pkt.get('timestamp')} | {pkt.get('src_ip')}:{pkt.get('src_port')} -> "
                f"{pkt.get('dst_ip')}:{pkt.get('dst_port')} | {pkt.get('protocol')} | "
                f"{pkt.get('length')} bytes | {pkt.get('info')}"
            )
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self.status_bar.set_status(f"Copied {len(packets)} row(s) to clipboard.")

    def _clear_packets(self):
        if not self._all_packets:
            return
        if messagebox.askyesno("Clear Packets", "Are you sure you want to clear all captured packets?"):
            self._all_packets.clear()
            self.packet_table.clear()
            self.detail_panel.clear()
            self._update_live_counters()
            self.status_bar.set_status("Packet list cleared.")
            self.toast.show("All captured packets were cleared.", kind="success", title="Cleared")

    # ------------------------------------------------------------------
    # Save / Load / Export
    # ------------------------------------------------------------------
    def _save_capture(self):
        if not self._all_packets:
            self.toast.show("There are no packets to save.", kind="info", title="Save Capture")
            return
        name = simpledialog.askstring("Save Capture", "Enter a name for this capture session:")
        if not name:
            return
        try:
            session_id = self.db.save_session(name, self._all_packets)
            self.status_bar.set_status(f"Saved session '{name}' (id={session_id}) with {len(self._all_packets)} packets.")
            self.toast.show(f"Capture saved as '{name}'.", kind="success", title="Save Complete")
        except Exception as exc:
            self.toast.show(f"Could not save capture: {exc}", kind="error", title="Save Error")

    def _load_capture(self):
        sessions = self.db.list_sessions()
        if not sessions:
            self.toast.show("There are no saved capture sessions yet.", kind="info", title="Load Capture")
            return

        theme = self.theme
        picker = tk.Toplevel(self)
        picker.title("Load Capture Session")
        picker.geometry("520x320")
        picker.configure(bg=theme["bg"])

        ctk.CTkLabel(
            picker, text="Saved Capture Sessions", font=self.fonts["h2"], text_color=theme["text"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        list_wrap = ctk.CTkFrame(picker, corner_radius=RADIUS_MD, fg_color=theme["card"],
                                  border_width=1, border_color=theme["border"])
        list_wrap.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        listbox = tk.Listbox(
            list_wrap, bg=theme["input_bg"], fg=theme["text"], selectbackground=theme["accent"],
            selectforeground="#FFFFFF", relief="flat", highlightthickness=0, font=self.fonts["body"],
            borderwidth=0,
        )
        listbox.pack(fill="both", expand=True, padx=10, pady=10)
        for session_id, name, created_at, count in sessions:
            listbox.insert("end", f"[{session_id}] {name} \u2014 {created_at} \u2014 {count} packets")

        def do_load():
            selection = listbox.curselection()
            if not selection:
                return
            session_id = sessions[selection[0]][0]
            try:
                packets = self.db.load_session(session_id)
            except Exception as exc:
                self.toast.show(f"Could not load session: {exc}", kind="error", title="Load Error")
                return
            self._all_packets = packets
            self.packet_table.clear()
            for pkt in packets:
                self.packet_table.add_packet(pkt)
            self._update_live_counters()
            self.status_bar.set_status(f"Loaded {len(packets)} packets from saved session.")
            self.toast.show(f"Loaded {len(packets)} packets.", kind="success", title="Load Complete")
            picker.destroy()

        btn_frame = ctk.CTkFrame(picker, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(
            btn_frame, text="Load Selected", command=do_load, corner_radius=RADIUS_SM,
            fg_color=theme["accent"], hover_color=theme["accent_hover"], font=self.fonts["body_bold"],
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Cancel", command=picker.destroy, corner_radius=RADIUS_SM,
            fg_color=theme["input_bg"], hover_color=theme["card_hover"],
            text_color=theme["text_muted"], font=self.fonts["body_bold"],
        ).pack(side="right")

    def _export_csv(self):
        if not self._all_packets:
            self.toast.show("There are no packets to export.", kind="info", title="Export CSV")
            return
        os.makedirs(DEFAULT_EXPORT_DIR, exist_ok=True)
        filepath = filedialog.asksaveasfilename(
            initialdir=DEFAULT_EXPORT_DIR, defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], title="Export to CSV"
        )
        if not filepath:
            return
        try:
            Exporter.to_csv(self._all_packets, filepath)
            self.status_bar.set_status(f"Exported {len(self._all_packets)} packets to {filepath}")
            self.toast.show("Packets exported successfully.", kind="success", title="Export CSV")
        except ExportError as exc:
            self.toast.show(str(exc), kind="error", title="Export Error")

    def _export_json(self):
        if not self._all_packets:
            self.toast.show("There are no packets to export.", kind="info", title="Export JSON")
            return
        os.makedirs(DEFAULT_EXPORT_DIR, exist_ok=True)
        filepath = filedialog.asksaveasfilename(
            initialdir=DEFAULT_EXPORT_DIR, defaultextension=".json",
            filetypes=[("JSON files", "*.json")], title="Export to JSON"
        )
        if not filepath:
            return
        try:
            Exporter.to_json(self._all_packets, filepath)
            self.status_bar.set_status(f"Exported {len(self._all_packets)} packets to {filepath}")
            self.toast.show("Packets exported successfully.", kind="success", title="Export JSON")
        except ExportError as exc:
            self.toast.show(str(exc), kind="error", title="Export Error")

    # ------------------------------------------------------------------
    # Theming / graphs / misc
    # ------------------------------------------------------------------
    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        if self.graphs_window is not None:
            try:
                self.graphs_window.apply_theme(self.dark_mode)
            except tk.TclError:
                pass

    def _apply_theme(self):
        theme = get_theme(self.dark_mode)
        self.theme = theme
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")

        self.configure(fg_color=theme["bg"])

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=theme["bg"], foreground=theme["text"])
        style.configure("TFrame", background=theme["bg"])
        style.configure("TPanedwindow", background=theme["bg"])

        # Propagate to child components that own their own styling.
        for widget in (self.packet_table, self.detail_panel, self.status_bar):
            if hasattr(widget, "apply_theme"):
                widget.apply_theme(self.dark_mode)

        self.toolbar.theme_btn.configure(text="☀" if self.dark_mode else "☾")

    def _open_graphs_window(self):
        if self.graphs_window is not None:
            try:
                self.graphs_window.lift()
                return
            except tk.TclError:
                self.graphs_window = None
        self.graphs_window = GraphsWindow(self, lambda: self._all_packets, dark_mode=self.dark_mode)

    def _show_about(self):
        theme = self.theme
        dialog = tk.Toplevel(self)
        dialog.title("About")
        dialog.geometry("380x260")
        dialog.configure(bg=theme["bg"])
        dialog.resizable(False, False)

        ctk.CTkLabel(
            dialog, text="◆", font=(self.fonts["display"][0], 30, "bold"), text_color=theme["accent"],
        ).pack(pady=(24, 4))
        ctk.CTkLabel(
            dialog, text=f"{APP_TITLE}", font=self.fonts["h1"], text_color=theme["text"],
        ).pack()
        ctk.CTkLabel(
            dialog, text=f"Version {APP_VERSION}", font=self.fonts["small"], text_color=theme["text_muted"],
        ).pack(pady=(0, 14))
        ctk.CTkLabel(
            dialog,
            text="A Wireshark-inspired live network packet analyzer\nbuilt with Python, Tkinter, and Scapy.\n\nDeveloped as a college major project.",
            font=self.fonts["small"], text_color=theme["text_muted"], justify="center",
        ).pack(padx=20)
        ctk.CTkButton(
            dialog, text="Close", command=dialog.destroy, corner_radius=RADIUS_SM,
            fg_color=theme["accent"], hover_color=theme["accent_hover"], font=self.fonts["body_bold"],
            width=110,
        ).pack(pady=20)

    def _on_exit(self):
        if self.capture.is_capturing:
            self.capture.stop()
        self.destroy()
