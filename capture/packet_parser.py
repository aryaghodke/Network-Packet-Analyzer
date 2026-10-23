"""
Packet parsing utilities.

Converts raw Scapy packet objects into normalized Python dictionaries
that the rest of the application (GUI, database, exporters) can work
with, without needing to know anything about Scapy internals.
"""

import datetime

from scapy.all import (
    IP,
    IPv6,
    TCP,
    UDP,
    ICMP,
    ARP,
    DNS,
    Ether,
    Raw,
)

from utils.constants import (
    PROTO_TCP,
    PROTO_UDP,
    PROTO_ICMP,
    PROTO_ARP,
    PROTO_DNS,
    PROTO_HTTP,
    PROTO_HTTPS,
    PROTO_OTHER,
    HTTP_PORTS,
    HTTPS_PORTS,
    DNS_PORT,
)


class PacketParser:
    """Parses Scapy packets into normalized dictionaries."""

    _counter = 0

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    @classmethod
    def parse(cls, packet):
        """
        Parse a Scapy packet into a dictionary.
        """

        print("=" * 60)
        print("PacketParser.parse() called")
        print("Packet Summary:", packet.summary())
        print("=" * 60)

        cls._counter += 1

        info = {
            "no": cls._counter,
            "timestamp": cls._get_timestamp(packet),
            "src_ip": "-",
            "dst_ip": "-",
            "src_port": "-",
            "dst_port": "-",
            "protocol": PROTO_OTHER,
            "length": len(packet),
            "src_mac": "-",
            "dst_mac": "-",
            "info": "",
            "raw_summary": packet.summary(),
        }

        try:

            # ---------------- Ethernet ----------------

            if packet.haslayer(Ether):
                eth = packet[Ether]
                info["src_mac"] = eth.src
                info["dst_mac"] = eth.dst

            # ---------------- ARP ----------------

            if packet.haslayer(ARP):
                arp = packet[ARP]

                info["protocol"] = PROTO_ARP
                info["src_ip"] = arp.psrc
                info["dst_ip"] = arp.pdst

                if arp.op == 1:
                    operation = "Who Has"
                elif arp.op == 2:
                    operation = "Is At"
                else:
                    operation = str(arp.op)

                info["info"] = f"ARP {operation} {arp.pdst}"

                print("Parsed ARP Packet")
                return info

            # ---------------- IP / IPv6 ----------------

            if packet.haslayer(IP):

                ip = packet[IP]

                info["src_ip"] = ip.src
                info["dst_ip"] = ip.dst

            elif packet.haslayer(IPv6):

                ip = packet[IPv6]

                info["src_ip"] = ip.src
                info["dst_ip"] = ip.dst

            # ---------------- ICMP ----------------

            if packet.haslayer(ICMP):

                icmp = packet[ICMP]

                info["protocol"] = PROTO_ICMP
                info["info"] = f"ICMP Type={icmp.type} Code={icmp.code}"

                print("Parsed ICMP Packet")
                return info

            # ---------------- TCP ----------------

            if packet.haslayer(TCP):

                tcp = packet[TCP]

                info["src_port"] = int(tcp.sport)
                info["dst_port"] = int(tcp.dport)

                if tcp.sport in HTTPS_PORTS or tcp.dport in HTTPS_PORTS:

                    info["protocol"] = PROTO_HTTPS
                    info["info"] = "TLS / HTTPS Traffic"

                elif tcp.sport in HTTP_PORTS or tcp.dport in HTTP_PORTS:

                    info["protocol"] = PROTO_HTTP
                    info["info"] = cls._http_info(packet)

                else:

                    info["protocol"] = PROTO_TCP
                    flags = cls._tcp_flags(tcp)
                    info["info"] = (
                        f"{tcp.sport} → {tcp.dport} "
                        f"[{flags}] Seq={tcp.seq}"
                    )

                print("Parsed TCP Packet")
                print(info)
                return info

            # ---------------- UDP ----------------

            if packet.haslayer(UDP):

                udp = packet[UDP]

                info["src_port"] = int(udp.sport)
                info["dst_port"] = int(udp.dport)

                if (
                    packet.haslayer(DNS)
                    or udp.sport == DNS_PORT
                    or udp.dport == DNS_PORT
                ):

                    info["protocol"] = PROTO_DNS
                    info["info"] = cls._dns_info(packet)

                else:

                    info["protocol"] = PROTO_UDP
                    info["info"] = (
                        f"{udp.sport} → {udp.dport} "
                        f"Length={udp.len}"
                    )

                print("Parsed UDP Packet")
                print(info)
                return info

            # ---------------- Other ----------------

            info["protocol"] = PROTO_OTHER
            info["info"] = packet.summary()

            print("Parsed OTHER Packet")
            print(info)

            return info

        except Exception as e:

            print("Packet Parsing Failed")
            print(e)

            return info

    # ==========================================================
    # Helper Functions
    # ==========================================================

    @staticmethod
    def _get_timestamp(packet):

        try:
            ts = float(packet.time)
        except Exception:
            ts = datetime.datetime.now().timestamp()

        return datetime.datetime.fromtimestamp(
            ts
        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    @staticmethod
    def _tcp_flags(tcp):

        mapping = {
            "F": "FIN",
            "S": "SYN",
            "R": "RST",
            "P": "PSH",
            "A": "ACK",
            "U": "URG",
            "E": "ECE",
            "C": "CWR",
        }

        flags = str(tcp.flags)

        if not flags:
            return "-"

        return ",".join(mapping.get(f, f) for f in flags)

    @staticmethod
    def _http_info(packet):

        try:

            if packet.haslayer(Raw):

                payload = bytes(packet[Raw].load)

                text = payload.decode(errors="ignore")

                first_line = text.split("\r\n")[0]

                if first_line.strip():
                    return "HTTP: " + first_line[:80]

        except Exception:
            pass

        return "HTTP Traffic"

    @staticmethod
    def _dns_info(packet):

        try:

            if packet.haslayer(DNS):

                dns = packet[DNS]

                if dns.qr == 0 and dns.qd:

                    qname = dns.qd.qname.decode(errors="ignore")

                    return f"DNS Query: {qname}"

                elif dns.qr == 1:

                    return "DNS Response"

        except Exception:
            pass

        return "DNS Traffic"