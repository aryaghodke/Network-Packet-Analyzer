# Network Packet Analyzer

A professional, Wireshark-inspired desktop application for **live network packet capture, analysis, and visualization**, built with Python, Tkinter, and Scapy.

![Status](https://img.shields.io/badge/status-complete-brightgreen) ![Python](https://img.shields.io/badge/python-3.12%2B-blue) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 1. Project Overview

Network Packet Analyzer is a full-featured GUI application that captures live network traffic, decodes it in real time, and presents it in a professional, sortable, filterable table alongside live statistics and graphs. It is designed to demonstrate practical understanding of networking protocols (TCP/UDP/ICMP/ARP/DNS/HTTP/HTTPS), multithreaded GUI programming, and data persistence — making it well suited as a college major project in Computer Networks, Cybersecurity, or Software Engineering.

The application never freezes while capturing, because packet sniffing runs on a dedicated background thread and communicates with the GUI through a thread-safe queue.

---

## 2. Features

### Core Capture & Data Management
- Live packet capturing via Scapy (`AsyncSniffer`) on a background thread
- Start / Stop capture controls
- Clear captured packets
- Save a full capture session to a local SQLite database
- Load any previously saved capture session
- Export captured packets to **CSV**
- Export captured packets to **JSON**
- Free-text search across all packet fields
- Filter by protocol (TCP, UDP, ICMP, ARP, DNS, HTTP, HTTPS), IP address, and port number

### Packet Details Captured
- Timestamp (millisecond precision)
- Source / Destination IP
- Source / Destination Port
- Protocol
- Packet length (bytes)
- Source / Destination MAC address (when available)
- Human-readable info string (e.g. TCP flags, DNS query name, HTTP request line)

### Advanced / Professional Features
- Live statistics panel: total packets, and per-protocol counters (TCP, UDP, ICMP, ARP, DNS, HTTP, HTTPS)
- Bandwidth monitor: live packets-per-second and bytes-per-second
- Live-updating graphs: protocol distribution pie chart, per-protocol bar chart, and packets-per-second timeline (Matplotlib, in a dedicated window)
- Dark Mode / Light Mode toggle
- Packet detail popup window (double-click any row, or right-click → "View Details")
- Right-click context menu (copy rows, view details, remove selected)
- Sortable, resizable table columns (click any header to sort)
- Scrollable packet table (vertical + horizontal)
- Status bar with live packet count, capture status, and progress indicator
- Full toolbar and menu bar
- Keyboard shortcuts (see below)
- Robust error handling for permission errors, missing adapters, invalid filters, and file I/O failures

### Keyboard Shortcuts
| Shortcut | Action |
|---|---|
| `F5` | Start Capture |
| `F6` | Stop Capture |
| `Ctrl+S` | Save Capture |
| `Ctrl+O` | Load Capture |
| `Ctrl+L` | Clear Packets |
| `Ctrl+F` | Focus Search Box |
| `Ctrl+Q` | Exit |

---

## 3. Requirements

- Python **3.12+**
- OS: Windows, Linux, or macOS
- Administrator / root privileges (required by Scapy for raw packet capture)
- **Windows only:** [Npcap](https://npcap.com/) must be installed (install with "WinPcap API-compatible mode" checked)
- **Linux:** libpcap is typically already available; you may need `sudo apt install libpcap-dev` on some distributions

All Python dependencies are listed in `requirements.txt`.

---

## 4. Installation

```bash
# 1. Clone / extract the project folder
cd NetworkPacketAnalyzer

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 5. How to Run

Because live packet capture uses raw sockets, the application must be run with elevated privileges:

**Windows** (run terminal "as Administrator"):
```bash
python main.py
```

**Linux / macOS:**
```bash
sudo python3 main.py
```

If you only want to explore the interface (Save/Load, filters, exports, graphs) without live capture, you can run it without elevated privileges — clicking **Start Capture** will show a clear, friendly error message explaining what is needed, rather than crashing.

---

## 6. Screenshots

> _Screenshots go here once the application has been run in your environment. Suggested captures:_
- `assets/screenshot_main.png` – Main window during a live capture
- `assets/screenshot_graphs.png` – Live statistics / graphs window
- `assets/screenshot_dark.png` – Dark mode
- `assets/screenshot_detail.png` – Packet detail popup

---

## 7. Project Structure

```
NetworkPacketAnalyzer/
│
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── LICENSE                    # MIT License
│
├── gui/                       # All Tkinter GUI components
│   ├── __init__.py
│   ├── main_window.py         # Main application window (wires everything together)
│   ├── toolbar.py             # Top toolbar (capture controls, export buttons)
│   ├── menu_bar.py            # Menu bar + keyboard shortcuts
│   ├── filter_panel.py        # Left-hand filter panel
│   ├── packet_table.py        # Central sortable packet table (Treeview)
│   ├── detail_panel.py        # Bottom detail panel + popup window
│   ├── status_bar.py          # Bottom status bar
│   ├── graphs_window.py       # Live statistics graphs window
│   └── theme.py                # Light / Dark theme definitions
│
├── capture/                   # Packet capture & parsing engine
│   ├── __init__.py
│   ├── packet_capture.py      # Threaded Scapy AsyncSniffer wrapper
│   ├── packet_parser.py       # Raw packet -> normalized dict
│   └── filters.py             # Protocol / IP / port / search filtering
│
├── database/                  # Persistence layer
│   ├── __init__.py
│   ├── db_manager.py          # SQLite session save/load
│   └── capture_history.db     # Created automatically on first run
│
├── graphs/                    # Data visualization
│   ├── __init__.py
│   └── stats_graphs.py        # Matplotlib pie/bar/timeline charts
│
├── utils/                     # Shared utilities
│   ├── __init__.py
│   ├── constants.py           # App-wide constants (columns, colors, ports)
│   ├── validators.py          # Filter input validation
│   └── exporters.py           # CSV / JSON export logic
│
├── assets/                    # Icons / screenshots (place your own here)
│
├── exports/                   # Default output folder for CSV/JSON exports
│
└── docs/                      # Project report & test documentation
    ├── REPORT.md
    └── TEST_CASES.md
```

---

## 8. Architecture Notes

- **Multithreading:** `capture/packet_capture.py` runs Scapy's `AsyncSniffer` on its own thread. Captured packets are parsed and pushed onto a `queue.Queue`. The GUI polls this queue every 200 ms via Tkinter's `after()` scheduler — the sniffing thread never touches Tkinter widgets directly, which is what keeps the interface responsive.
- **Separation of concerns:** parsing (`capture/packet_parser.py`), filtering (`capture/filters.py`), persistence (`database/db_manager.py`), and export (`utils/exporters.py`) are all independent, unit-testable modules with no GUI dependencies.
- **Error handling:** permission errors, missing/invalid network adapters, invalid filter input, empty-export attempts, and file I/O failures are all caught and surfaced to the user through friendly dialog boxes instead of crashing the app.

---

## 9. Future Enhancements

- Packet payload hex-dump viewer
- Custom BPF filter expression box (advanced users)
- VoIP / streaming traffic reconstruction
- Geo-IP lookups and a world-map traffic visualization
- Alerting rules (e.g. port-scan or ARP-spoofing detection)
- Multi-session comparison view
- PCAP file import/export (Wireshark-compatible format) via Scapy's `wrpcap`/`rdpcap`

---

## 10. License

Released under the MIT License — see `LICENSE` for details.
