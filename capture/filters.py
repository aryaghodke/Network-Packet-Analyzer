"""
Filtering logic for captured packets (protocol, IP, port, free-text search).
"""


class PacketFilter:
    """
    Encapsulates the current filter configuration and applies it to a
    list of parsed packet dictionaries.
    """

    def __init__(self):
        self.protocols = set()   # empty set == no protocol filter (show all)
        self.ip_filter = ""      # substring match on src or dst IP
        self.port_filter = None  # int port, matches src or dst port
        self.search_text = ""    # free text search across all fields

    def reset(self):
        self.protocols = set()
        self.ip_filter = ""
        self.port_filter = None
        self.search_text = ""

    def set_protocols(self, protocols):
        self.protocols = set(protocols)

    def set_ip_filter(self, ip_text: str):
        self.ip_filter = ip_text.strip()

    def set_port_filter(self, port_text: str):
        port_text = port_text.strip()
        if not port_text:
            self.port_filter = None
            return
        if not port_text.isdigit():
            raise ValueError("Port filter must be a number between 0 and 65535.")
        port = int(port_text)
        if not (0 <= port <= 65535):
            raise ValueError("Port filter must be a number between 0 and 65535.")
        self.port_filter = port

    def set_search_text(self, text: str):
        self.search_text = text.strip().lower()

    def is_active(self) -> bool:
        return bool(self.protocols or self.ip_filter or self.port_filter or self.search_text)

    def matches(self, pkt: dict) -> bool:
        """Return True if the given parsed packet dict passes all active filters."""
        if self.protocols and pkt.get("protocol") not in self.protocols:
            return False

        if self.ip_filter:
            if self.ip_filter not in str(pkt.get("src_ip", "")) and \
               self.ip_filter not in str(pkt.get("dst_ip", "")):
                return False

        if self.port_filter is not None:
            src_port = pkt.get("src_port")
            dst_port = pkt.get("dst_port")
            if src_port != self.port_filter and dst_port != self.port_filter:
                return False

        if self.search_text:
            haystack = " ".join(str(v) for v in pkt.values()).lower()
            if self.search_text not in haystack:
                return False

        return True

    def apply(self, packets: list) -> list:
        if not self.is_active():
            return packets
        return [p for p in packets if self.matches(p)]
