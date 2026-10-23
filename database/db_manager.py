"""
SQLite-backed storage for captured packet sessions.

Allows the user to persist an entire capture session (all packets +
metadata) to disk and reload it later via "Save Capture" / "Load
Capture" in the GUI.
"""

import sqlite3
import os
import datetime


class DatabaseManager:
    """Handles all SQLite interactions for saving/loading capture sessions."""

    def __init__(self, db_path="database/capture_history.db"):
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    packet_count INTEGER NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS packets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    packet_no INTEGER,
                    timestamp TEXT,
                    src_ip TEXT,
                    dst_ip TEXT,
                    src_port TEXT,
                    dst_port TEXT,
                    protocol TEXT,
                    length INTEGER,
                    src_mac TEXT,
                    dst_mac TEXT,
                    info TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            conn.commit()

    def save_session(self, name: str, packets: list) -> int:
        """Save a full capture session, returns the new session id."""
        created_at = datetime.datetime.now().isoformat(timespec="seconds")
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO sessions (name, created_at, packet_count) VALUES (?, ?, ?)",
                (name, created_at, len(packets)),
            )
            session_id = cur.lastrowid

            rows = [
                (
                    session_id, p.get("no"), p.get("timestamp"), p.get("src_ip"),
                    p.get("dst_ip"), str(p.get("src_port")), str(p.get("dst_port")),
                    p.get("protocol"), p.get("length"), p.get("src_mac"),
                    p.get("dst_mac"), p.get("info"),
                )
                for p in packets
            ]
            cur.executemany("""
                INSERT INTO packets (
                    session_id, packet_no, timestamp, src_ip, dst_ip,
                    src_port, dst_port, protocol, length, src_mac, dst_mac, info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
        return session_id

    def list_sessions(self) -> list:
        """Return a list of (id, name, created_at, packet_count) tuples."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, created_at, packet_count FROM sessions ORDER BY created_at DESC"
            )
            return cur.fetchall()

    def load_session(self, session_id: int) -> list:
        """Return the list of parsed-packet dictionaries for a saved session."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT packet_no, timestamp, src_ip, dst_ip, src_port, dst_port,
                       protocol, length, src_mac, dst_mac, info
                FROM packets WHERE session_id = ? ORDER BY packet_no ASC
            """, (session_id,))
            rows = cur.fetchall()

        packets = []
        for row in rows:
            (no, timestamp, src_ip, dst_ip, src_port, dst_port,
             protocol, length, src_mac, dst_mac, info) = row
            packets.append({
                "no": no, "timestamp": timestamp, "src_ip": src_ip, "dst_ip": dst_ip,
                "src_port": self._maybe_int(src_port), "dst_port": self._maybe_int(dst_port),
                "protocol": protocol, "length": length, "src_mac": src_mac,
                "dst_mac": dst_mac, "info": info, "raw_summary": info,
            })
        return packets

    def delete_session(self, session_id: int):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM packets WHERE session_id = ?", (session_id,))
            cur.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    @staticmethod
    def _maybe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return "-"
