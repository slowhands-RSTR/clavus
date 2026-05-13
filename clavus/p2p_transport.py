"""
Clavus P2P Transport Layer

Provides:
  - TCPTransport: raw socket P2P, direct machine-to-machine sync
  - HTTPTransport: wraps existing SyncClient, for relay/hub mode

Frame format: [4-byte uint32 length][JSON payload]
Payload always has a "type" field: MANIFEST, PING, WANT, GIVE, GOT, DONE, ERROR

Smoke test: python3 clavus/p2p_transport.py
"""

from __future__ import annotations

import base64
import json
import socket
import struct
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

# ─── Frame Format ────────────────────────────────────────────────────────────

FRAME_HEADER = struct.Struct("!I")  # big-endian uint32


def recv_frame(sock: socket.socket) -> Optional[dict]:
    """Receive one JSON frame from a socket. Returns None on disconnect."""
    try:
        header = sock.recv(FRAME_HEADER.size)
        if not header:
            return None
        length, = FRAME_HEADER.unpack(header)
        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk
        return json.loads(data.decode("utf-8"))
    except (ConnectionResetError, BrokenPipeError, OSError):
        return None
    except json.JSONDecodeError:
        return None


def send_frame(sock: socket.socket, payload: dict) -> bool:
    """Send one JSON frame to a socket. Returns False on error."""
    try:
        body = json.dumps(payload).encode("utf-8")
        sock.sendall(FRAME_HEADER.pack(len(body)) + body)
        return True
    except (ConnectionResetError, BrokenPipeError, OSError):
        return False


# ─── Retry Constants ─────────────────────────────────────────────────────────

_RETRYABLE = (ConnectionError, TimeoutError, OSError)
_MAX_RETRIES = 3
_RETRY_BACKOFF = [1.0, 2.0, 4.0]

# ─── Peer Manifest ──────────────────────────────────────────────────────────

@dataclass
class PeerManifest:
    """What a peer has."""
    project: str
    snapshots: list[str]
    blobs: list[str]


# ─── Transport Protocol ─────────────────────────────────────────────────────

class SyncTransport(ABC):
    """Abstract sync transport."""

    @abstractmethod
    def connect(self, host: str, port: int) -> tuple[Optional[PeerManifest], Optional[socket.socket]]:
        """Connect and exchange manifests. Returns (peer_manifest, socket) or (None, None)."""
        ...

    @abstractmethod
    def listen(self, port: int, callback: Callable[[str, socket.socket], None]) -> None:
        """Start TCP server. callback(project, client_sock) called per connection."""
        ...

    @abstractmethod
    def close(self) -> None:
        ...


# ─── TCP Transport ──────────────────────────────────────────────────────────

class TCPTransport(SyncTransport):
    """Raw-socket P2P transport. No HTTP, no relay."""

    def __init__(self, project: str, snapshots: list[str], blobs: list[str]):
        self.project = project
        self.snapshots = snapshots
        self.blobs = blobs
        self._server_sock: Optional[socket.socket] = None
        self._server_thread: Optional[threading.Thread] = None
        self._running = False
        self._callback: Optional[Callable[[str, socket.socket], None]] = None

    def connect(self, host: str, port: int) -> tuple[Optional[PeerManifest], Optional[socket.socket]]:
        """Connect to a peer, exchange manifests. Caller closes returned socket."""
        sock = None
        for attempt in range(_MAX_RETRIES):
            try:
                sock = socket.create_connection((host, port), timeout=10)
                break
            except _RETRYABLE as e:
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF[attempt])
                continue

        if sock is None:
            return (None, None)

        try:
            if not send_frame(sock, {
                "type": "MANIFEST",
                "project": self.project,
                "snapshots": self.snapshots,
                "blobs": self.blobs,
            }):
                sock.close()
                return (None, None)

            peer_frame = recv_frame(sock)
            if not peer_frame or peer_frame.get("type") != "MANIFEST":
                sock.close()
                return (None, None)

            return (
                PeerManifest(
                    project=peer_frame.get("project", ""),
                    snapshots=peer_frame.get("snapshots", []),
                    blobs=peer_frame.get("blobs", []),
                ),
                sock,
            )
        except Exception:
            try:
                sock.close()
            except Exception:
                pass
            return (None, None)

    def listen(self, port: int, callback: Callable[[str, socket.socket], None]) -> None:
        """Start TCP server."""
        self._running = True
        self._callback = callback
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind(("0.0.0.0", port))
        self._server_sock.listen(4)
        self._server_sock.settimeout(2.0)
        self._server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._server_thread.start()

    def _accept_loop(self) -> None:
        while self._running:
            try:
                client_sock, _ = self._server_sock.accept()
                t = threading.Thread(target=self._handle, args=(client_sock,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle(self, sock: socket.socket) -> None:
        """Handle one incoming connection."""
        try:
            peer_frame = recv_frame(sock)
            if not peer_frame or peer_frame.get("type") != "MANIFEST":
                return

            peer = PeerManifest(
                project=peer_frame.get("project", ""),
                snapshots=peer_frame.get("snapshots", []),
                blobs=peer_frame.get("blobs", []),
            )

            if not send_frame(sock, {
                "type": "MANIFEST",
                "project": self.project,
                "snapshots": self.snapshots,
                "blobs": self.blobs,
            }):
                return

            if self._callback:
                self._callback(peer.project, sock)
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def close(self) -> None:
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        if self._server_thread:
            self._server_thread.join(timeout=3)


# ─── Frame Helpers ──────────────────────────────────────────────────────────

def frame_want(sock: socket.socket, hashes: list[str]) -> None:
    send_frame(sock, {"type": "WANT", "hashes": hashes})

def frame_give(sock: socket.socket, h: str, data: bytes) -> None:
    send_frame(sock, {"type": "GIVE", "hash": h, "data": base64.b64encode(data).decode("ascii")})

def frame_got(sock: socket.socket, h: str) -> None:
    send_frame(sock, {"type": "GOT", "hash": h})

def frame_done(sock: socket.socket) -> None:
    send_frame(sock, {"type": "DONE"})

def frame_error(sock: socket.socket, message: str) -> None:
    send_frame(sock, {"type": "ERROR", "message": message})


# ─── P2P Sync ───────────────────────────────────────────────────────────────

def p2p_sync(
    sock: socket.socket,
    store,                    # BlobStore
    local_snapshots: list[str],
    local_blobs: list[str],
    local_has: Callable[[str], bool],
    peer_snapshots: list[str],
    peer_blobs: list[str],
    peer_has: Callable[[str], bool],
    on_progress: Callable[[str, str], None] | None = None,
) -> dict:
    """
    Bidirectional blob sync over a live TCP socket.

    Both sides run this identically. Protocol:
      1. Both send MANIFEST (transport layer handles this)
      2. Both compute diff: what they need
      3. Both send WANT for blobs they need
      4. Both respond to peer's WANT with GIVE
      5. DONE when exchange complete

    Returns {"downloaded": [...], "uploaded": [...], "error": ""}
    """
    result = {"downloaded": [], "uploaded": [], "error": ""}

    # What we need from peer (they have, we don't)
    we_want = [h for h in peer_blobs if not local_has(h)]
    # What peer needs from us (we have, they don't)
    they_want = [h for h in local_blobs if not peer_has(h)]

    print(f"  [P2P] need from peer: {len(we_want)}  |  peer needs from us: {len(they_want)}")

    pending_uploads = set(they_want)
    pending_downloads = set(we_want)

    # Send our wants first
    if we_want:
        frame_want(sock, we_want)

    # Exchange loop
    while pending_uploads or pending_downloads:
        frame = recv_frame(sock)
        if not frame:
            result["error"] = "Connection closed"
            break

        t = frame.get("type")

        if t == "WANT":
            for h in (frame.get("hashes") or []):
                if h in pending_uploads and local_has(h):
                    data = store.get_object(h)
                    if data:
                        frame_give(sock, h, data)
                        pending_uploads.discard(h)
                        result["uploaded"].append(h)
                        if on_progress:
                            on_progress("upload", h)

        elif t == "GIVE":
            h = frame.get("hash", "")
            data_b64 = frame.get("data", "")
            if h in pending_downloads and data_b64:
                try:
                    data = base64.b64decode(data_b64)
                    store.put_object(data, h)
                    pending_downloads.discard(h)
                    result["downloaded"].append(h)
                    frame_got(sock, h)
                    if on_progress:
                        on_progress("download", h)
                except Exception:
                    pass

        elif t == "GOT":
            pending_uploads.discard(frame.get("hash", ""))

        elif t == "DONE":
            break

        elif t == "ERROR":
            result["error"] = frame.get("message", "peer error")
            break

    frame_done(sock)
    return result


# ─── Peer Discovery ─────────────────────────────────────────────────────────

def discover_peers() -> list[dict]:
    """
    Discover Clavus peers on the tailnet via `tailscale status --json`.
    Returns [{"name", "dns", "ip", "online"}, ...]. Excludes self.
    """
    import subprocess

    try:
        r = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            return []
        data = json.loads(r.stdout)
    except Exception:
        return []

    peers = []
    self_name = data.get("Self", {}).get("HostName", "")
    for node in data.get("Peer", {}).values():
        dns = node.get("DNSName", "").rstrip(".")
        ip = node.get("TailscaleIPs", [None])[0] or ""
        peers.append({
            "name": node.get("HostName", dns),
            "dns": dns,
            "ip": ip,
            "online": node.get("Online", False),
        })

    return [p for p in peers if p["name"] != self_name]


# ─── Mock BlobStore for Testing ─────────────────────────────────────────────

class MockStore:
    def __init__(self, blobs: dict[str, bytes]):
        self._d = blobs

    def get_object(self, h: str) -> Optional[bytes]:
        return self._d.get(h)

    def put_object(self, data: bytes, h: str) -> None:
        self._d[h] = data

    def has_object(self, h: str) -> bool:
        return h in self._d


# ─── Smoke Tests ────────────────────────────────────────────────────────────

def _smoke_manifest():
    """Test: two TCPTransport instances exchange manifests."""
    print("\n=== P2P Manifest Exchange ===\n")

    host = TCPTransport("test-project", ["snap_a", "snap_b"], ["blob_1", "blob_2"])
    client = TCPTransport("test-project", ["snap_b", "snap_c"], ["blob_2", "blob_3"])

    connected = {}

    def handler(project: str, sock: socket.socket):
        connected["project"] = project
        sock.close()

    host.listen(7950, handler)
    time.sleep(0.2)

    peer_manifest, sock = client.connect("127.0.0.1", 7950)
    time.sleep(0.3)

    host.close()
    client.close()

    ok = True
    checks = {
        "peer_manifest_received": peer_manifest is not None,
        "host_got_project": connected.get("project") == "test-project",
        "peer_snapshots_correct": list(peer_manifest.snapshots) == ["snap_a", "snap_b"] if peer_manifest else False,
        "peer_blobs_correct": list(peer_manifest.blobs) == ["blob_1", "blob_2"] if peer_manifest else False,
    }
    for name, result in checks.items():
        print(f"  {'PASS' if result else 'FAIL'} {name}")
        if not result:
            ok = False

    print(f"\n  {'ALL PASS' if ok else 'FAILURES'}\n")
    return ok


def _smoke_full_sync():
    """Test: bidirectional blob sync between two peers."""
    print("\n=== P2P Full Blob Sync ===\n")

    # Host has blobs 1,2  |  Client has blobs 2,3
    # After sync: both should have 1,2,3
    host_store = MockStore({
        "blob1": b"HOST_blob1",
        "blob2": b"HOST_blob2",
    })
    client_store = MockStore({
        "blob2": b"CLIENT_blob2",
        "blob3": b"CLIENT_blob3",
    })

    host_snapshots = ["snap_a", "snap_b"]
    client_snapshots = ["snap_b", "snap_c"]
    host_blobs = ["blob1", "blob2"]
    client_blobs = ["blob2", "blob3"]

    results: dict[str, dict] = {}
    done = threading.Event()

    def host_handler(project: str, sock: socket.socket):
        r = p2p_sync(
            sock=sock,
            store=host_store,
            local_snapshots=host_snapshots,
            local_blobs=host_blobs,
            local_has=host_store.has_object,
            peer_snapshots=client_snapshots,
            peer_blobs=client_blobs,
            peer_has=client_store.has_object,
        )
        results["host"] = r

    host = TCPTransport("test-project", host_snapshots, host_blobs)
    host.listen(7951, host_handler)
    time.sleep(0.3)

    # Client
    client = TCPTransport("test-project", client_snapshots, client_blobs)
    peer_manifest, sock = client.connect("127.0.0.1", 7951)
    if peer_manifest and sock:
        r = p2p_sync(
            sock=sock,
            store=client_store,
            local_snapshots=client_snapshots,
            local_blobs=client_blobs,
            local_has=client_store.has_object,
            peer_snapshots=peer_manifest.snapshots,
            peer_blobs=peer_manifest.blobs,
            peer_has=host_store.has_object,
        )
        results["client"] = r
        sock.close()
    client.close()

    time.sleep(0.5)
    host.close()

    # Verify both stores now have all blobs
    ok = True
    all_blobs = ["blob1", "blob2", "blob3"]

    host_has_all = all(host_store.has_object(b) for b in all_blobs)
    client_has_all = all(client_store.has_object(b) for b in all_blobs)

    checks = {
        "host_got_blob1": host_store.has_object("blob1"),
        "host_got_blob3": host_store.has_object("blob3"),
        "client_got_blob1": client_store.has_object("blob1"),
        "client_got_blob3": client_store.has_object("blob3"),
        "host_has_all": host_has_all,
        "client_has_all": client_has_all,
        "client_uploaded": len(results.get("client", {}).get("uploaded", [])) > 0,
        "client_downloaded": len(results.get("client", {}).get("downloaded", [])) > 0,
        "host_uploaded": len(results.get("host", {}).get("uploaded", [])) > 0,
        "host_downloaded": len(results.get("host", {}).get("downloaded", [])) > 0,
    }

    for name, result in checks.items():
        print(f"  {'PASS' if result else 'FAIL'} {name}")
        if not result:
            ok = False

    print(f"\n  {'ALL PASS' if ok else 'FAILURES'}\n")
    return ok


def _smoke_test():
    a = _smoke_manifest()
    b = _smoke_full_sync()
    print(f"\n=== Results: {'ALL PASS' if (a and b) else 'FAILURES'} ===\n")
    return a and b


if __name__ == "__main__":
    _smoke_test()
