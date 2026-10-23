"""
Export utilities: CSV and JSON export of captured packets.
"""

import csv
import json
import os
import datetime


class ExportError(Exception):
    """Raised when an export operation cannot be completed."""
    pass


class Exporter:
    """Handles exporting a list of parsed packet dictionaries to disk."""

    FIELD_ORDER = [
        "no", "timestamp", "src_ip", "dst_ip", "src_port", "dst_port",
        "protocol", "length", "src_mac", "dst_mac", "info",
    ]

    HEADER = [
        "No.", "Timestamp", "Source IP", "Destination IP", "Source Port",
        "Destination Port", "Protocol", "Length", "Source MAC",
        "Destination MAC", "Info",
    ]

    @classmethod
    def to_csv(cls, packets: list, filepath: str):
        if not packets:
            raise ExportError("There are no packets to export.")
        try:
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cls.HEADER)
                for pkt in packets:
                    writer.writerow([pkt.get(field, "-") for field in cls.FIELD_ORDER])
        except OSError as exc:
            raise ExportError(f"Could not write CSV file: {exc}") from exc

    @classmethod
    def to_json(cls, packets: list, filepath: str):
        if not packets:
            raise ExportError("There are no packets to export.")
        try:
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            export_data = {
                "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "packet_count": len(packets),
                "packets": packets,
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
        except OSError as exc:
            raise ExportError(f"Could not write JSON file: {exc}") from exc
