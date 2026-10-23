"""
Constants used throughout the Network Packet Analyzer application.
"""

# ---------------------------------------------------------------------------
# Protocol labels used across parsing, filtering, GUI, and exports
# ---------------------------------------------------------------------------
PROTO_TCP = "TCP"
PROTO_UDP = "UDP"
PROTO_ICMP = "ICMP"
PROTO_ARP = "ARP"
PROTO_DNS = "DNS"
PROTO_HTTP = "HTTP"
PROTO_HTTPS = "HTTPS"
PROTO_OTHER = "OTHER"

ALL_PROTOCOLS = [
    PROTO_TCP, PROTO_UDP, PROTO_ICMP, PROTO_ARP,
    PROTO_DNS, PROTO_HTTP, PROTO_HTTPS, PROTO_OTHER,
]

# Well known ports used to classify application-layer protocols
HTTP_PORTS = (80, 8080, 8000)
HTTPS_PORTS = (443, 8443)
DNS_PORT = 53

# Packet table columns
TABLE_COLUMNS = (
    "No.", "Timestamp", "Source IP", "Destination IP",
    "Src Port", "Dst Port", "Protocol", "Length", "Src MAC", "Dst MAC", "Info",
)

COLUMN_WIDTHS = {
    "No.": 55,
    "Timestamp": 150,
    "Source IP": 130,
    "Destination IP": 130,
    "Src Port": 70,
    "Dst Port": 70,
    "Protocol": 70,
    "Length": 70,
    "Src MAC": 130,
    "Dst MAC": 130,
    "Info": 260,
}

# Protocol -> accent color (kept in sync with gui/theme.py's PROTOCOL_COLORS,
# used for Treeview row text color-coding)
PROTOCOL_COLORS = {
    PROTO_TCP: "#3B82F6",
    PROTO_UDP: "#A855F7",
    PROTO_ICMP: "#EF4444",
    PROTO_ARP: "#EC4899",
    PROTO_DNS: "#F59E0B",
    PROTO_HTTP: "#10B981",
    PROTO_HTTPS: "#06B6D4",
    PROTO_OTHER: "#94A3B8",
}

DB_PATH = "database/capture_history.db"
DEFAULT_EXPORT_DIR = "exports"

APP_TITLE = "Network Packet Analyzer"
APP_VERSION = "1.0.0"
