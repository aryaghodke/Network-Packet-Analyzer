"""
Matplotlib-based graphing widgets embedded in the Tkinter GUI.

Provides:
    - Protocol distribution pie chart
    - Packets-per-protocol bar chart
    - Packets-per-second timeline
"""

import collections
import time

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.constants import ALL_PROTOCOLS, PROTOCOL_COLORS


class StatsGraphs:
    """
    Owns three Matplotlib subplots (pie, bar, timeline) embedded in a
    single Tkinter canvas, and knows how to refresh them from the
    current list of captured packets.
    """

    def __init__(self, parent_frame, dark_mode=False):
        self.dark_mode = dark_mode
        self.figure = Figure(figsize=(9, 6), dpi=100)
        self.ax_pie = self.figure.add_subplot(221)
        self.ax_bar = self.figure.add_subplot(222)
        self.ax_timeline = self.figure.add_subplot(212)
        self.figure.subplots_adjust(hspace=0.6, wspace=0.4)

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Per-second packet counters, used to build the timeline chart.
        self._timeline_buckets = collections.OrderedDict()

        self.apply_theme(dark_mode)

    def apply_theme(self, dark_mode: bool):
        self.dark_mode = dark_mode
        bg = "#1E293B" if dark_mode else "#ffffff"
        fg = "#CBD5E1" if dark_mode else "#0F172A"
        for ax in (self.ax_pie, self.ax_bar, self.ax_timeline):
            ax.set_facecolor(bg)
            ax.tick_params(colors=fg, labelsize=7)
            for spine in ax.spines.values():
                spine.set_color(fg)
            ax.title.set_color(fg)
        self.figure.patch.set_facecolor(bg)
        self.canvas.draw_idle()

    def record_packet_time(self, ts_epoch: int):
        """Increment the per-second bucket used for the timeline chart."""
        self._timeline_buckets[ts_epoch] = self._timeline_buckets.get(ts_epoch, 0) + 1
        while len(self._timeline_buckets) > 60:
            self._timeline_buckets.popitem(last=False)

    def refresh(self, packets: list):
        """Recompute and redraw all three charts from the given packet list."""
        now = int(time.time())
        self._timeline_buckets.setdefault(now, self._timeline_buckets.get(now, 0))
        self._recompute_timeline_from_packets(packets)
        self._refresh_pie(packets)
        self._refresh_bar(packets)
        self._refresh_timeline()
        self.canvas.draw_idle()

    def _recompute_timeline_from_packets(self, packets):
        """Build per-second buckets from packet timestamps (last 60s window)."""
        buckets = collections.OrderedDict()
        for pkt in packets[-2000:]:
            ts = pkt.get("timestamp")
            if not ts:
                continue
            try:
                second_key = ts.split(".")[0]
            except Exception:
                continue
            buckets[second_key] = buckets.get(second_key, 0) + 1
        # Keep only the most recent 30 buckets for readability
        while len(buckets) > 30:
            buckets.popitem(last=False)
        self._string_buckets = buckets

    def _refresh_pie(self, packets):
        self.ax_pie.clear()
        self.ax_pie.set_title("Protocol Distribution", fontsize=9)
        counts = collections.Counter(p.get("protocol", "OTHER") for p in packets)
        labels = [p for p in counts if counts[p] > 0]
        sizes = [counts[p] for p in labels]
        if sizes:
            colors = [PROTOCOL_COLORS.get(p, "#7C3AED") for p in labels]
            self.ax_pie.pie(sizes, labels=labels, autopct="%1.0f%%", textprops={"fontsize": 7}, colors=colors)
        else:
            self.ax_pie.text(0.5, 0.5, "No data yet", ha="center", va="center", fontsize=8)
        self.apply_theme(self.dark_mode)

    def _refresh_bar(self, packets):
        self.ax_bar.clear()
        self.ax_bar.set_title("Packets per Protocol", fontsize=9)
        counts = collections.Counter(p.get("protocol", "OTHER") for p in packets)
        values = [counts.get(proto, 0) for proto in ALL_PROTOCOLS]
        colors = [PROTOCOL_COLORS.get(proto, "#7C3AED") for proto in ALL_PROTOCOLS]
        self.ax_bar.bar(ALL_PROTOCOLS, values, color=colors)
        self.ax_bar.tick_params(axis="x", rotation=45, labelsize=6)
        self.apply_theme(self.dark_mode)

    def _refresh_timeline(self):
        self.ax_timeline.clear()
        self.ax_timeline.set_title("Packets per Second (recent activity)", fontsize=9)
        buckets = getattr(self, "_string_buckets", {})
        if buckets:
            labels = list(buckets.keys())
            values = list(buckets.values())
            self.ax_timeline.plot(labels, values, color="#7C3AED", marker="o", markersize=3)
            self.ax_timeline.tick_params(axis="x", rotation=60, labelsize=6)
        else:
            self.ax_timeline.text(0.5, 0.5, "No data yet", ha="center", va="center", fontsize=8)
        self.apply_theme(self.dark_mode)
