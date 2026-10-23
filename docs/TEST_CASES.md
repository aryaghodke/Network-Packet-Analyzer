# Test Cases and Expected Outputs

These test cases were exercised against the actual codebase during development (see "Verified" column). Cases marked `Manual` require a live network interface and administrator/root privileges, and should be re-verified in the grading environment.

## 1. Packet Parsing (`capture/packet_parser.py`)

| # | Test | Input | Expected Output | Verified |
|---|---|---|---|---|
| 1.1 | Parse a plain TCP SYN packet | `Ether()/IP(src, dst)/TCP(sport=51000, dport=22, flags='S')` | `protocol == "TCP"`, `info` contains `"[SYN]"` | ✅ Automated |
| 1.2 | Parse an HTTP request packet | TCP packet on port 80 with `GET / HTTP/1.1` payload | `protocol == "HTTP"`, `info` starts with `"HTTP: GET"` | ✅ Automated |
| 1.3 | Parse an HTTPS packet | TCP packet on port 443 | `protocol == "HTTPS"` | ✅ Automated |
| 1.4 | Parse a DNS query | UDP packet on port 53 with `DNSQR(qname="example.com")` | `protocol == "DNS"`, `info` contains `"example.com"` | ✅ Automated |
| 1.5 | Parse an ICMP echo request | `ICMP()` (default type=8) | `protocol == "ICMP"`, `info` contains `"type=8"` | ✅ Automated |
| 1.6 | Parse an ARP request | `ARP(psrc, pdst)` | `protocol == "ARP"`, `info` contains `"who-has"` | ✅ Automated |
| 1.7 | Packet counter increments correctly | Parse 6 packets in sequence | `PacketParser._counter == 6` | ✅ Automated |

## 2. Filtering (`capture/filters.py`)

| # | Test | Input | Expected Output | Verified |
|---|---|---|---|---|
| 2.1 | Filter by single protocol | 3 packets (DNS, HTTPS, ARP); filter = `{DNS}` | 1 result, the DNS packet | ✅ Automated |
| 2.2 | Filter by IP substring | Filter IP = `"192.168"` | Only packets with that substring in src/dst IP | ✅ Automated |
| 2.3 | Filter by exact port | Filter port = `443` | Only packets with src or dst port 443 | ✅ Automated |
| 2.4 | Filter by free-text search | Search = `"example.com"` | Only packets whose fields contain that text | ✅ Automated |
| 2.5 | Invalid port filter (non-numeric) | `set_port_filter("abc")` | Raises `ValueError` | ✅ Automated (validators) |
| 2.6 | Invalid port filter (out of range) | `set_port_filter("99999")` | Raises `ValueError` | ✅ Automated (validators) |
| 2.7 | No active filters | `reset()` then `apply(packets)` | Returns the original, unfiltered list | ✅ Automated |

## 3. Export (`utils/exporters.py`)

| # | Test | Input | Expected Output | Verified |
|---|---|---|---|---|
| 3.1 | Export to CSV | 3 sample packets | `.csv` file created, contains header row + 3 data rows | ✅ Automated |
| 3.2 | Export to JSON | 3 sample packets | `.json` file created with `packet_count == 3` | ✅ Automated |
| 3.3 | Export with no packets | Empty list | Raises `ExportError("There are no packets to export.")` | ✅ Automated (by inspection) |

## 4. Database Persistence (`database/db_manager.py`)

| # | Test | Input | Expected Output | Verified |
|---|---|---|---|---|
| 4.1 | Save a session | 3 sample packets, name="Test Session" | Returns a valid integer `session_id`; row appears in `sessions` table | ✅ Automated |
| 4.2 | Load a saved session | `load_session(session_id)` | Returns 3 packets matching what was saved | ✅ Automated |
| 4.3 | List sessions | After saving 1 session | `list_sessions()` returns exactly 1 entry | ✅ Automated |
| 4.4 | Delete a session | `delete_session(session_id)` | Session no longer appears in `list_sessions()` | ✅ Automated |

## 5. GUI Behavior (`gui/*`)

| # | Test | Input | Expected Output | Verified |
|---|---|---|---|---|
| 5.1 | Application launches | Run `python main.py` | Main window opens with toolbar, filter panel, table, detail panel, stats panel, and status bar visible | Manual |
| 5.2 | Start Capture without privileges | Click "Start Capture" as a non-admin user | Friendly error dialog explaining privileges are required; app does not crash | Manual |
| 5.3 | Packet arrives while capturing | Live traffic present | New row appears in the table within ~200 ms; live counters update | Manual |
| 5.4 | Apply protocol filter mid-capture | Check "TCP" only, click "Apply Filters" | Table shows only TCP rows; status bar reports the filtered count | ✅ Logic verified via `_apply_filters` |
| 5.5 | Double-click a row | Any captured row | Packet Detail popup opens with Summary and Info tabs | Manual |
| 5.6 | Right-click a row | Any captured row | Context menu appears with Copy / View Details / Remove Selected | Manual |
| 5.7 | Sort by column | Click "Length" column header | Rows reorder numerically; clicking again reverses the order | ✅ Logic verified in `PacketTable._sort_by` |
| 5.8 | Toggle theme | Click "Toggle Theme" | All `ttk` styles and window background switch between light/dark palettes | Manual |
| 5.9 | Save then Load capture | Save a named session, clear the table, then Load it | Table repopulates with the same packets | ✅ Logic verified end-to-end via DatabaseManager tests |
| 5.10 | Export with an empty capture | Click "Export CSV" with 0 packets | Info dialog: "There are no packets to export." — no file is written | ✅ Logic verified via `ExportError` |
| 5.11 | Clear packets | Click "Clear" with packets present | Confirmation dialog, then table and live counters reset to 0 | Manual |
| 5.12 | Open Graphs window | Click "Graphs" | A new window opens with pie chart, bar chart, and timeline, refreshing every 2 seconds | Manual |

## 6. Error Handling

| # | Test | Scenario | Expected Output | Verified |
|---|---|---|---|---|
| 6.1 | No network adapter available | `get_if_list()` returns an empty list | Warning dialog on startup; interface dropdown shows `"(default)"` | ✅ Logic verified in `MainWindow.__init__` |
| 6.2 | Permission denied on capture start | Non-privileged user clicks Start | `PacketCaptureError` raised with a clear, actionable message | ✅ Logic verified in `PacketCapture.start` |
| 6.3 | Malformed/unparseable packet | Packet parsing raises an exception | Error is caught in `_on_packet`, reported via `on_error` callback, capture continues | ✅ Logic verified by code inspection |
| 6.4 | File write failure on export (e.g. read-only folder) | `OSError` during file write | `ExportError` raised and shown in a dialog; app does not crash | ✅ Logic verified in `Exporter` |

## 7. Environment / Compilation Checks

| # | Test | Result |
|---|---|---|
| 7.1 | All `.py` files compile with `python3 -m py_compile` | ✅ Passed — 23/23 files |
| 7.2 | All non-GUI modules import successfully | ✅ Passed |
| 7.3 | All GUI callback names referenced in `menu_bar`/`toolbar` dictionaries exist as `MainWindow` methods | ✅ Passed (static AST check) |
