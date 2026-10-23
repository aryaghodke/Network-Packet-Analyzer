"""
Network Packet Analyzer
========================
Entry point for the application.

Run with:
    python main.py

Note: Live packet capture requires administrator / root privileges on
most operating systems, because Scapy uses raw sockets under the hood.
On Windows, also make sure Npcap (https://npcap.com/) is installed.
On Linux/macOS, run with sudo, e.g.:

    sudo python3 main.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox


def main():
    try:
        from gui.main_window import MainWindow
    except ImportError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing Dependency",
            f"A required package is missing: {exc}\n\n"
            "Please install all dependencies first:\n"
            "    pip install -r requirements.txt"
        )
        sys.exit(1)

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
