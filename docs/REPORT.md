# Project Report: Network Packet Analyzer

## 1. Problem Statement

Network administrators, security analysts, and students need an accessible way to observe, understand, and analyze live network traffic without relying on expensive commercial tools or the steep learning curve of full-scale tools such as Wireshark. There is a need for a lightweight, transparent, and educational packet-analysis tool that captures traffic in real time, decodes it into human-readable form, and presents actionable statistics — all while remaining simple enough to be understood, extended, and maintained by a student developer.

## 2. Objectives

1. Capture live network packets using raw sockets (via Scapy) without freezing the user interface.
2. Decode and classify packets by protocol: TCP, UDP, ICMP, ARP, DNS, HTTP, and HTTPS.
3. Present captured data in a searchable, filterable, sortable table, similar in spirit to Wireshark.
4. Provide live statistics and visualizations (protocol distribution, bandwidth, packet rate).
5. Allow the user to persist and later reload capture sessions.
6. Allow the user to export capture data to portable formats (CSV, JSON) for further analysis.
7. Demonstrate sound software-engineering practice: modular design, multithreading, and robust error handling.

## 3. Scope

**In scope:**
- Live capture on a locally available network interface
- Classification of the most common Internet protocols
- A desktop GUI (Tkinter) with filtering, search, sorting, and detail views
- Local persistence (SQLite) and export (CSV/JSON)
- Basic traffic visualization (pie chart, bar chart, timeline)

**Out of scope:**
- Deep packet inspection / payload reconstruction of encrypted traffic (HTTPS payloads are not decrypted — TLS traffic is only classified, not inspected)
- Distributed / multi-host capture and aggregation
- Intrusion detection or automated threat response
- Support for capturing on remote or cloud network interfaces

## 4. Modules

| Module | Responsibility |
|---|---|
| `capture.packet_capture` | Runs Scapy's `AsyncSniffer` on a background thread; exposes a thread-safe queue of parsed packets |
| `capture.packet_parser` | Converts raw Scapy packet objects into normalized dictionaries |
| `capture.filters` | Applies protocol / IP / port / free-text filters to packet lists |
| `database.db_manager` | Persists and retrieves capture sessions using SQLite |
| `utils.exporters` | Exports packet lists to CSV and JSON |
| `utils.validators` | Validates user-entered filter values |
| `graphs.stats_graphs` | Builds and refreshes Matplotlib visualizations |
| `gui.*` | All Tkinter presentation-layer components (toolbar, menu, table, panels, windows) |

## 5. Methodology

The project follows a layered architecture that separates **capture**, **data/persistence**, and **presentation** concerns:

1. **Capture Layer** — `PacketCapture` starts a Scapy `AsyncSniffer` on a dedicated thread. Every captured packet is immediately parsed by `PacketParser` into a plain Python dictionary and placed on a `queue.Queue`. This is the only interaction point between the capture thread and the rest of the application, which avoids any race conditions on GUI widgets.

2. **Presentation Layer** — The Tkinter main loop polls the queue every 200 ms using `after()`. New packets are appended to the in-memory packet store and, if they satisfy any active filter, inserted into the visible table. This polling approach guarantees the GUI thread is never blocked waiting on network I/O.

3. **Filtering** — `PacketFilter` holds the current filter state (selected protocols, IP substring, port number, free-text search) and exposes a single `matches()` predicate, reused both for live incoming packets and for "Apply Filters" on the full history.

4. **Persistence** — `DatabaseManager` uses two related SQLite tables (`sessions` and `packets`) so a user can save an entire capture under a name and reload it later, including after closing the application.

5. **Visualization** — `StatsGraphs` embeds a Matplotlib `Figure` inside a `Toplevel` window via `FigureCanvasTkAgg`, and refreshes on a timer to show live protocol distribution and traffic-rate trends.

## 6. Flowchart (textual)

```
                     ┌────────────────────┐
                     │   User clicks       │
                     │  "Start Capture"    │
                     └─────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │ PacketCapture.start()    │
                  │ spawns AsyncSniffer      │
                  │ on a background thread   │
                  └─────────┬─────────────────┘
                            │  (background thread)
                            ▼
              ┌───────────────────────────────┐
              │  For each packet sniffed:      │
              │   PacketParser.parse(packet)   │
              │   -> normalized dict            │
              │   -> queue.put(dict)            │
              └─────────────┬───────────────────┘
                             │  (thread-safe queue)
                             ▼
        ┌─────────────────────────────────────────┐
        │  Tkinter main loop, every 200 ms:         │
        │   drain_queue() -> list of new packets    │
        │   append to in-memory store                │
        │   if matches active filter -> add to table │
        │   update live statistics + status bar       │
        └─────────────────┬───────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────────┐
              │  User interacts: filter,      │
              │  search, sort, save, export,   │
              │  view graphs, view details      │
              └─────────────────────────────────┘
```

## 7. Algorithms

- **Protocol classification** (`PacketParser.parse`): a priority-ordered check of packet layers — ARP → IP/IPv6 → ICMP → TCP (further split into HTTPS / HTTP / generic TCP by well-known port number) → UDP (further split into DNS / generic UDP by port 53) → fallback "OTHER".
- **Filtering** (`PacketFilter.matches`): a short-circuit conjunction of independent predicates (protocol membership, IP substring match, port equality, free-text substring match across all fields).
- **Table sorting** (`PacketTable._sort_by`): a stable sort using a numeric-first key function (numbers sort numerically, everything else falls back to case-insensitive string comparison), with sort direction toggled on repeated clicks of the same column header.
- **Bandwidth estimation** (`MainWindow._update_stats_loop`): computed as a discrete derivative — `(current_total - previous_total) / elapsed_seconds` — sampled once per second for both packet count and byte count.

## 8. Advantages

- Fully responsive UI, even under heavy traffic, due to the threaded producer/consumer (queue) design.
- Modular codebase — each concern (capture, filtering, persistence, export, visualization, GUI) lives in its own file and can be tested or replaced independently.
- No external services or accounts required; everything runs and stores data locally.
- Cross-platform (Windows/Linux/macOS), subject to the underlying packet-capture driver being installed.

## 9. Limitations

- Requires administrator/root privileges, which may not be available in all lab/classroom environments.
- HTTPS/TLS traffic is identified by port, not decrypted — payload content is not inspected.
- Capture performance is bounded by Python's GIL and Scapy's per-packet parsing cost; extremely high-throughput links (multi-Gbps) are not the target use case.
- No built-in PCAP (`.pcap`/`.pcapng`) import/export in the current version (see Future Enhancements).

## 10. Conclusion

Network Packet Analyzer demonstrates an end-to-end, real-world application of core computer networking concepts (protocol structure, ports, addressing) alongside practical software-engineering skills (multithreading, GUI design, persistence, data export, and error handling). The modular architecture keeps the codebase approachable for further extension, making it a solid foundation for a college major project and a realistic demonstration of applied networking and Python software development.

## 11. References

1. Python Software Foundation — *Python 3 Documentation*, https://docs.python.org/3/
2. Scapy Project — *Scapy Documentation*, https://scapy.readthedocs.io/
3. Python Software Foundation — *tkinter — Python interface to Tcl/Tk*, https://docs.python.org/3/library/tkinter.html
4. Matplotlib Development Team — *Matplotlib Documentation*, https://matplotlib.org/stable/
5. SQLite Consortium — *SQLite Documentation*, https://www.sqlite.org/docs.html
6. IETF — RFC 791 (Internet Protocol), RFC 793 (TCP), RFC 768 (UDP), RFC 792 (ICMP), RFC 826 (ARP), RFC 1035 (DNS)
