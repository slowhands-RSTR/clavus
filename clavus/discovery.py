"""Clavus — LAN peer discovery via mDNS/DNS-SD.

Find other Clavus servers on the local network and advertise
your own server so others can find you.

Uses zeroconf (pure Python mDNS). Cross-platform: macOS, Linux, Windows.

Service type: _clavus._tcp
TXT records:
  project  = Current project name
  user     = Author name from config
  version  = Clavus version string
"""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass, field
from typing import Optional

import zeroconf

# ─── Service Definition ────────────────────────────────────────────────

SERVICE_TYPE = "_clavus._tcp.local."
SERVICE_NAME = "Clavus"

# ─── Models ────────────────────────────────────────────────────────────


@dataclass
class ClavusPeer:
    """A Clavus server discovered on the network."""

    name: str  # Machine hostname or friendly name
    host: str  # IP address
    port: int  # Server port
    project: str = ""  # Current project name
    user: str = ""  # Author name
    version: str = ""  # Clavus version
    last_seen: float = 0.0  # When discovered

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def __str__(self) -> str:
        proj = f"  {self.project}" if self.project else ""
        user = f"  [{self.user}]" if self.user else ""
        return f"{self.name:<20} {self.host:>15}:{self.port:<5}{proj}{user}"


# ─── Advertiser ────────────────────────────────────────────────────────


class ClavusAdvertiser:
    """Advertise this Clavus server on the LAN via mDNS.

    Call start(port, project, user) when the web server starts.
    Call stop() when shutting down.
    """

    def __init__(self):
        self._zc: Optional[zeroconf.Zeroconf] = None
        self._service: Optional[zeroconf.ServiceInfo] = None

    def start(self, port: int, project: str = "", user: str = "", version: str = ""):
        """Start advertising this Clavus server on the network.

        Args:
            port: The port Clavus web server is running on
            project: Name of the active project
            user: Author name from config
            version: Clavus version string
        """
        if self._zc:
            return  # Already advertising

        # Build TXT records
        txt = {
            "project": project or "none",
            "user": user or "anonymous",
            "version": version or "0.5.0",
        }
        txt_bytes = {k: v.encode("utf-8") for k, v in txt.items()}

        # Get hostname
        hostname = socket.gethostname()

        # Build full service name: "Hostname._clavus._tcp.local."
        fqdn = f"{hostname}.{SERVICE_TYPE}"
        server_name = f"{hostname}.local."

        # Resolve our IP
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip = "127.0.0.1"

        self._service = zeroconf.ServiceInfo(
            type_=SERVICE_TYPE,
            name=fqdn,
            addresses=[socket.inet_aton(ip)],
            port=port,
            properties=txt_bytes,
            server=server_name,
        )

        self._zc = zeroconf.Zeroconf()
        self._zc.register_service(self._service)
        print(f"📡 Advertising clavus on LAN: {hostname}:{port} ({project or 'no project'})")

    def update(self, project: str = "", user: str = "", version: str = ""):
        """Update TXT records (e.g., when project changes)."""
        if not self._zc or not self._service:
            return

        txt = {
            "project": project or "none",
            "user": user or "anonymous",
            "version": version or "0.5.0",
        }
        self._service.properties = {k: v.encode("utf-8") for k, v in txt.items()}
        try:
            self._zc.unregister_service(self._service)
            self._zc.register_service(self._service)
        except Exception:
            pass

    def stop(self):
        """Stop advertising."""
        if self._zc and self._service:
            try:
                self._zc.unregister_service(self._service)
            except Exception:
                pass
            self._zc.close()
            self._zc = None
            self._service = None
            print("📡 Stopped LAN advertising")


# ─── Discoverer ────────────────────────────────────────────────────────


class ClavusListener(zeroconf.ServiceListener):
    """Collects discovered Clavus peers from mDNS responses."""

    def __init__(self):
        self.peers: dict[str, ClavusPeer] = {}
        self._done = False

    def add_service(self, zc: zeroconf.Zeroconf, type_: str, name: str):
        info = zc.get_service_info(type_, name)
        if info:
            peer = self._info_to_peer(info)
            self.peers[peer.name] = peer
            self.peers[peer.name].last_seen = time.time()

    def update_service(self, zc: zeroconf.Zeroconf, type_: str, name: str):
        self.add_service(zc, type_, name)

    def remove_service(self, zc: zeroconf.Zeroconf, type_: str, name: str):
        # Extract hostname from service name
        host_part = name.split(".")[0]
        if host_part in self.peers:
            del self.peers[host_part]

    def _info_to_peer(self, info: zeroconf.ServiceInfo) -> ClavusPeer:
        txt = {}
        if info.properties:
            txt = {
                k.decode("utf-8") if isinstance(k, bytes) else k: (
                    v.decode("utf-8") if isinstance(v, bytes) else v
                )
                for k, v in info.properties.items()
            }

        # Get IP address
        ip = "0.0.0.0"
        if info.addresses:
            ip = socket.inet_ntoa(info.addresses[0])

        hostname = info.name.split(".")[0]
        return ClavusPeer(
            name=hostname,
            host=ip,
            port=info.port,
            project=txt.get("project", ""),
            user=txt.get("user", ""),
            version=txt.get("version", ""),
        )

    def done(self):
        self._done = True


def discover_peers(timeout: float = 3.0) -> list[ClavusPeer]:
    """Scan the LAN for Clavus servers.

    Args:
        timeout: Max seconds to wait for responses

    Returns:
        List of discovered ClavusPeer objects
    """
    listener = ClavusListener()
    zc = zeroconf.Zeroconf()

    try:
        browser = zeroconf.ServiceBrowser(zc, SERVICE_TYPE, listener)
        time.sleep(timeout)
        browser.cancel()
    finally:
        zc.close()

    return list(listener.peers.values())
