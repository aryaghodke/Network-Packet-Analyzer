"""
Live packet capture engine.

Wraps Scapy's sniffing capability and runs it on a background thread
so the Tkinter GUI never freezes.
"""

import threading
import queue
import time

from scapy.all import AsyncSniffer, get_if_list

from capture.packet_parser import PacketParser


class PacketCaptureError(Exception):
    pass


class PacketCapture:

    def __init__(self, on_error=None):
        self.sniffer = None
        self.packet_queue = queue.Queue()
        self.is_capturing = False
        self.on_error = on_error

        self._lock = threading.Lock()
        self._packet_count = 0
        self._byte_count = 0
        self._start_time = None

    @staticmethod
    def list_interfaces():
        try:
            return get_if_list()
        except Exception as e:
            raise PacketCaptureError(str(e))

    def start(self, interface=None, bpf_filter=None):

        with self._lock:

            if self.is_capturing:
                return

            PacketParser.reset_counter()

            self._packet_count = 0
            self._byte_count = 0
            self._start_time = time.time()

            print("=" * 60)
            print("Starting Packet Capture")
            print("Interface :", interface)
            print("Filter    :", bpf_filter)
            print("=" * 60)

            try:

                self.sniffer = AsyncSniffer(
                    iface=interface if interface else None,
                    filter=bpf_filter if bpf_filter else None,
                    prn=self._on_packet,
                    store=False,
                )

                self.sniffer.start()

                self.is_capturing = True

                print("✓ Capture Started Successfully")

            except Exception as e:
                raise PacketCaptureError(f"Unable to start capture:\n{e}")

    def stop(self):

        with self._lock:

            if not self.is_capturing:
                return

            try:

                if self.sniffer is not None:
                    self.sniffer.stop()

            except Exception as e:
                print("Stop Error :", e)

            self.is_capturing = False

            print("✓ Capture Stopped")

    def _on_packet(self, packet):
        """
        Called automatically whenever Scapy captures a packet.
        """

        print("\n" + "=" * 60)
        print("PACKET RECEIVED")
        print(packet.summary())
        print("=" * 60)

        try:

            parsed = PacketParser.parse(packet)

            if parsed is None:
                print("Parser returned None")
                return

            print("PARSED PACKET:")
            print(parsed)

            self._packet_count += 1
            self._byte_count += parsed.get("length", 0)

            self.packet_queue.put(parsed)

            print("Queue Size :", self.packet_queue.qsize())
            print("Total Packets :", self._packet_count)

        except Exception as e:

            print("Packet Parse Error :", e)

            if self.on_error:
                self.on_error(str(e))

    def drain_queue(self, max_items=500):

        packets = []

        for _ in range(max_items):

            try:
                packets.append(self.packet_queue.get_nowait())

            except queue.Empty:
                break

        if packets:
            print(f"GUI fetched {len(packets)} packet(s) from queue.")

        return packets

    def get_elapsed_seconds(self):

        if self._start_time is None:
            return 0

        return time.time() - self._start_time

    def get_totals(self):

        return self._packet_count, self._byte_count