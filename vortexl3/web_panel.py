#!/usr/bin/env python3
"""
VortexL3 Web Panel

Browser-based tunnel management with a cyberpunk UI:
- View tunnel status (L2TPv3 or EasyTier, depending on tunnel mode)
- Start / restart / stop / delete tunnels
- Create new tunnels
- Manage port forwards

Security:
- Random username + password (generated on first run, stored hashed)
- Random free port (checked against listening sockets)
- Cookie session with server-side expiry (12h)
- Login rate limiting per IP
- Runs as root via systemd (needs it for tunnels/iptables)

Stdlib only (no extra dependencies).
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import yaml

from . import __version__
from . import cron_manager
from . import dns_manager
from .config import ConfigManager, GlobalConfig, TunnelConfig
from .tcp_optimizer import TCPOptimizer, setup_tcp_optimization
from .tunnel import TunnelManager
from .haproxy_manager import HAProxyManager

logger = logging.getLogger("vortexl3-panel")

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

PANEL_CONFIG_FILE = Path("/etc/vortexl3/panel.yaml")
PANEL_LOG_FILE = Path("/var/log/vortexl3/panel.log")
PANEL_SERVICE = "vortexl3-panel"
FORWARD_DAEMON_SERVICE = "vortexl3-forward-daemon"

SESSION_TTL = 12 * 3600
SESSION_COOKIE = "vortex3sess"
PORT_MIN = 20000
PORT_MAX = 45000
MAX_BODY = 512 * 1024

LOGIN_MAX_FAILS = 10
LOGIN_WINDOW = 300

_sessions: dict = {}
_sessions_lock = threading.Lock()
_login_fails: dict = {}


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def run_command(cmd: str, timeout: int = 15):
    """Run shell command, return (ok, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, (result.stdout or "").strip(), (result.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:  # noqa: BLE001
        return False, "", str(e)


def sanitize_name(name: str) -> str:
    """Sanitize tunnel name (same rule as the TUI)."""
    name = "".join(c if c.isalnum() or c == "-" else "-" for c in (name or "").lower())
    return name[:32]


def is_valid_ip(ip: str) -> bool:
    """Validate IPv4 address (CIDR suffix allowed)."""
    if not ip:
        return False
    parts = ip.split("/")[0].split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def is_valid_port(port: int) -> bool:
    return isinstance(port, int) and 1 <= port <= 65535


def parse_ports(ports_str: str):
    """Parse '80,443,1000-1005' into a sorted unique port list."""
    ports = set()
    for part in (ports_str or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            chunks = part.split("-")
            if len(chunks) != 2:
                raise ValueError(f"Invalid range: {part}")
            start, end = int(chunks[0]), int(chunks[1])
            if not (is_valid_port(start) and is_valid_port(end)) or end < start:
                raise ValueError(f"Invalid range: {part}")
            if end - start > 500:
                raise ValueError("Range too large (max 500 ports)")
            ports.update(range(start, end + 1))
        else:
            port = int(part)
            if not is_valid_port(port):
                raise ValueError(f"Invalid port: {part}")
            ports.add(port)
    if not ports:
        raise ValueError("No ports given")
    return sorted(ports)


def is_port_free(port: int) -> bool:
    """Check that nothing listens on this TCP port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", port))
        ok, out, _ = run_command(f"ss -tln 2>/dev/null | grep -E ':{port}\\b'")
        if ok and out:
            return False
        return True
    except OSError:
        return False


def find_free_port() -> int:
    """Pick a random free port in PORT_MIN..PORT_MAX."""
    for _ in range(100):
        port = secrets.randbelow(PORT_MAX - PORT_MIN + 1) + PORT_MIN
        if is_port_free(port):
            return port
    for port in range(PORT_MIN, PORT_MAX + 1):
        if is_port_free(port):
            return port
    raise RuntimeError("No free port available")


def get_server_ip() -> str:
    """Detect the server's primary IP address."""
    ok, out, _ = run_command("ip route get 8.8.8.8 2>/dev/null | grep -oP 'src \\K[0-9.]+'")
    if ok and out and is_valid_ip(out.split()[0]):
        return out.split()[0]
    ok, out, _ = run_command("hostname -I 2>/dev/null | awk '{print $1}'")
    if ok and out and is_valid_ip(out.split()[0]):
        return out.split()[0]
    return "SERVER-IP"


def ensure_panel_firewall(port: int) -> None:
    """Open the panel TCP port in iptables (idempotent, best-effort)."""
    ok, _, _ = run_command(f"iptables -C INPUT -p tcp --dport {port} -j ACCEPT 2>/dev/null")
    if not ok:
        run_command(f"iptables -I INPUT -p tcp --dport {port} -j ACCEPT 2>/dev/null")


# ----------------------------------------------------------------------------
# Panel configuration (credentials + port)
# ----------------------------------------------------------------------------

def _hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000).hex()


class PanelConfig:
    """Panel credentials/port stored in /etc/vortexl3/panel.yaml (0600)."""

    def __init__(self, path: Path = PANEL_CONFIG_FILE):
        self.path = Path(path)
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = yaml.safe_load(f) or {}
            except Exception as e:  # noqa: BLE001
                logger.warning("Could not load panel config: %s", e)
                self._data = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False)
        os.chmod(self.path, 0o600)

    @property
    def exists(self) -> bool:
        return bool(self._data.get("password_hash"))

    @property
    def port(self) -> int:
        try:
            return int(self._data.get("port", 0))
        except (TypeError, ValueError):
            return 0

    @property
    def username(self) -> str:
        return self._data.get("username", "")

    def ensure_initialized(self):
        """Generate port + credentials if missing. Returns (is_new, username, password|None)."""
        if self.exists and is_valid_port(self.port):
            return False, self.username, None
        port = find_free_port()
        username = "vortex-" + secrets.token_hex(3)
        password = secrets.token_urlsafe(18)
        salt = secrets.token_hex(16)
        self._data = {
            "port": port,
            "username": username,
            "salt": salt,
            "password_hash": _hash_password(password, salt),
            "session_secret": secrets.token_hex(32),
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return True, username, password

    def verify(self, username: str, password: str) -> bool:
        if not self.exists:
            return False
        if not username or not password:
            return False
        if not hmac.compare_digest(username, self.username):
            return False
        salt = self._data.get("salt", "")
        expected = self._data.get("password_hash", "")
        if not salt or not expected:
            return False
        return hmac.compare_digest(_hash_password(password, salt), expected)

    def regenerate_credentials(self):
        """Generate a new random username + password (port unchanged)."""
        username = "vortex-" + secrets.token_hex(3)
        password = secrets.token_urlsafe(18)
        salt = secrets.token_hex(16)
        self._data["username"] = username
        self._data["salt"] = salt
        self._data["password_hash"] = _hash_password(password, salt)
        self._save()
        return username, password

    def set_port(self, port: int) -> None:
        if not is_valid_port(port):
            raise ValueError("Invalid port")
        if not is_port_free(port):
            raise ValueError(f"Port {port} is already in use")
        self._data["port"] = port
        self._save()


# ----------------------------------------------------------------------------
# Tunnel operations (shared by API)
# ----------------------------------------------------------------------------

def get_mode() -> str:
    try:
        return GlobalConfig().tunnel_mode
    except Exception:  # noqa: BLE001
        return "l2tpv3"


def restart_forward_daemon() -> None:
    run_command(f"systemctl restart {FORWARD_DAEMON_SERVICE}")


class EasyTierForwardsAdapter:
    """HAProxy-compatible wrapper around an EasyTier config (mirrors TUI)."""

    def __init__(self, et_config):
        self.name = et_config.name
        self.remote_forward_ip = et_config.remote_forward_ip
        self._et_config = et_config

    @property
    def forwarded_ports(self):
        return self._et_config.forwarded_ports

    def add_port(self, port: int) -> None:
        self._et_config.add_port(port)

    def remove_port(self, port: int) -> None:
        self._et_config.remove_port(port)


def _l2tp_tunnel_info(config: TunnelConfig) -> dict:
    mgr = TunnelManager(config)
    running = mgr.check_tunnel_exists()
    forwards = []
    try:
        for fwd in HAProxyManager(config).list_forwards():
            if fwd.get("tunnel") == config.name:
                forwards.append({
                    "port": fwd.get("port"),
                    "remote": fwd.get("remote", "-"),
                    "active": bool(fwd.get("active")),
                })
    except Exception:  # noqa: BLE001
        pass
    return {
        "name": config.name,
        "type": "l2tpv3",
        "interface": config.interface_name,
        "local_ip": config.local_ip,
        "remote_ip": config.remote_ip,
        "interface_ip": config.interface_ip,
        "tunnel_id": config.tunnel_id,
        "encap": config.encap_type,
        "running": running,
        "status": "Running" if running else "Stopped",
        "forwards": sorted(forwards, key=lambda f: f["port"]),
    }


def _easytier_tunnel_info(config) -> dict:
    from .easytier_manager import EasyTierManager
    mgr = EasyTierManager(config)
    try:
        running, status = mgr.get_status()
    except Exception:  # noqa: BLE001
        running, status = False, "Unknown"
    peers = []
    if running:
        try:
            for peer in mgr.get_peer_info():
                peers.append({
                    "ipv4": peer.get("ipv4", "-"),
                    "hostname": peer.get("hostname", "-"),
                    "latency": peer.get("latency") or "-",
                    "loss": peer.get("loss") or "-",
                    "tunnel": peer.get("tunnel") or "-",
                })
        except Exception:  # noqa: BLE001
            pass
    forwards = []
    try:
        mode = GlobalConfig().forward_mode
        for port in config.forwarded_ports:
            forwards.append({
                "port": port,
                "remote": f"{config.remote_forward_ip}:{port}" if config.remote_forward_ip else str(port),
                "active": mode != "none",
            })
    except Exception:  # noqa: BLE001
        pass
    return {
        "name": config.name,
        "type": "easytier",
        "interface": config.interface_name,
        "local_ip": config.local_ip,
        "remote_ip": config.peer_ip,
        "port": config.port,
        "running": running,
        "status": status,
        "peers": peers,
        "forwards": sorted(forwards, key=lambda f: f["port"]),
    }


def list_tunnels() -> list:
    mode = get_mode()
    result = []
    if mode == "easytier":
        from .easytier_manager import EasyTierConfigManager
        for config in EasyTierConfigManager().get_all_tunnels():
            try:
                result.append(_easytier_tunnel_info(config))
            except Exception as e:  # noqa: BLE001
                result.append({"name": config.name, "type": "easytier",
                               "running": False, "status": f"Error: {e}",
                               "forwards": [], "peers": []})
    else:
        for config in ConfigManager().get_all_tunnels():
            try:
                result.append(_l2tp_tunnel_info(config))
            except Exception as e:  # noqa: BLE001
                result.append({"name": config.name, "type": "l2tpv3",
                               "running": False, "status": f"Error: {e}",
                               "forwards": []})
    return sorted(result, key=lambda t: t["name"])


def tunnel_action(name: str, action: str) -> tuple:
    """Start / restart / stop / delete a tunnel. Returns (ok, message)."""
    name = sanitize_name(name)
    if not name:
        return False, "Invalid tunnel name"
    mode = get_mode()
    try:
        if mode == "easytier":
            from .easytier_manager import EasyTierConfigManager, EasyTierManager
            manager = EasyTierConfigManager()
            config = manager.get_tunnel(name)
            if not config:
                return False, f"Tunnel '{name}' not found"
            mgr = EasyTierManager(config)
            if action == "start":
                return mgr.start_tunnel()
            if action == "restart":
                return mgr.restart_tunnel()
            if action == "stop":
                return mgr.stop_tunnel()
            if action == "delete":
                manager.delete_tunnel(name)
                return True, f"EasyTier tunnel '{name}' deleted"
            return False, f"Unknown action: {action}"

        manager = ConfigManager()
        config = manager.get_tunnel(name)
        if not config:
            return False, f"Tunnel '{name}' not found"
        tunnel = TunnelManager(config)
        if action == "start":
            return tunnel.full_setup()
        if action == "restart":
            tunnel.full_teardown()
            return tunnel.full_setup()
        if action == "stop":
            return tunnel.full_teardown()
        if action == "delete":
            forward = HAProxyManager(config)
            for port in list(config.forwarded_ports):
                try:
                    forward.remove_forward(port)
                except Exception:  # noqa: BLE001
                    pass
            tunnel.full_teardown()
            manager.delete_tunnel(name)
            return True, f"Tunnel '{name}' deleted"
        return False, f"Unknown action: {action}"
    except Exception as e:  # noqa: BLE001
        logger.exception("Tunnel action failed")
        return False, f"Error: {e}"


def _unique_or_error(used: set, value, label: str):
    if value in used:
        raise ValueError(f"{label} {value} is already used by another tunnel")


def create_l2tp_tunnel(data: dict) -> tuple:
    """Create + start an L2TPv3 tunnel from panel form data."""
    side = (data.get("side") or "IRAN").upper()
    if side not in ("IRAN", "KHAREJ"):
        return False, "Side must be IRAN or KHAREJ"
    name = sanitize_name(data.get("name", ""))
    if not name:
        return False, "Tunnel name is required"
    manager = ConfigManager()
    if manager.tunnel_exists(name):
        return False, f"Tunnel '{name}' already exists"

    local_ip = (data.get("local_ip") or "").strip()
    remote_ip = (data.get("remote_ip") or "").strip()
    if not is_valid_ip(local_ip):
        return False, "Valid Local Server Public IP is required"
    if not is_valid_ip(remote_ip):
        return False, "Valid Remote Server Public IP is required"

    encap = (data.get("encap") or "ip").lower()
    if encap not in ("ip", "udp"):
        return False, "Encapsulation must be ip or udp"

    try:
        used = manager.get_used_values(exclude_tunnel=name)

        interface_ip = (data.get("interface_ip") or "").strip() or manager.suggest_interface_ip(side)
        if not is_valid_ip(interface_ip):
            return False, "Invalid Interface IP"
        _unique_or_error(used.get("interface_ips", set()), interface_ip.split("/")[0], "Interface IP")
        if "/" not in interface_ip:
            interface_ip += "/30"

        if side == "IRAN":
            remote_forward = (data.get("remote_forward_ip") or "").strip()
            if not remote_forward:
                remote_forward = interface_ip.split("/")[0].rsplit(".", 1)[0] + ".2"
            if not is_valid_ip(remote_forward):
                return False, "Invalid Remote Forward Target IP"
        else:
            remote_forward = "10.30.30.1"

        base_tid = 1000 if side == "IRAN" else 2000
        base_peer = 2000 if side == "IRAN" else 1000
        base_sid = 10 if side == "IRAN" else 20
        base_psid = 20 if side == "IRAN" else 10

        def pick(raw, base, used_set, step, label):
            try:
                value = int((raw or "").strip() or base)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid {label}")
            while value in used_set:
                value += step
            return value

        tunnel_id = pick(data.get("tunnel_id"), base_tid, used.get("tunnel_ids", set()), 100, "Tunnel ID")
        peer_tunnel_id = pick(data.get("peer_tunnel_id"), base_peer, used.get("peer_tunnel_ids", set()), 100, "Peer Tunnel ID")
        session_id = pick(data.get("session_id"), base_sid, used.get("session_ids", set()), 10, "Session ID")
        peer_session_id = pick(data.get("peer_session_id"), base_psid, used.get("peer_session_ids", set()), 10, "Peer Session ID")

        udp_port = None
        if encap == "udp":
            try:
                udp_port = int((data.get("udp_port") or "").strip() or manager.suggest_udp_port())
            except (ValueError, AttributeError):
                return False, "Invalid UDP port"
            if not is_valid_port(udp_port):
                return False, "UDP port must be 1-65535"
            _unique_or_error(used.get("udp_ports", set()), udp_port, "UDP port")

        config = manager.create_tunnel(name)
        config.local_ip = local_ip
        config.remote_ip = remote_ip
        config.interface_ip = interface_ip
        config.remote_forward_ip = remote_forward
        config.tunnel_id = tunnel_id
        config.peer_tunnel_id = peer_tunnel_id
        config.session_id = session_id
        config.peer_session_id = peer_session_id
        config.encap_type = encap
        if udp_port is not None:
            config.udp_port = udp_port

        tunnel = TunnelManager(config)
        success, msg = tunnel.full_setup()
        if success:
            config.save()
            return True, f"Tunnel '{name}' created and started!\n{msg}"
        return False, f"Tunnel setup failed (not saved):\n{msg}"
    except ValueError as e:
        return False, str(e)
    except Exception as e:  # noqa: BLE001
        logger.exception("L2TP create failed")
        return False, f"Error: {e}"


def create_easytier_tunnel(data: dict) -> tuple:
    """Create + start an EasyTier tunnel from panel form data."""
    from .easytier_manager import EasyTierConfigManager, EasyTierManager

    side = (data.get("side") or "IRAN").upper()
    if side not in ("IRAN", "KHAREJ"):
        return False, "Side must be IRAN or KHAREJ"
    name = sanitize_name(data.get("name", ""))
    if not name:
        return False, "Tunnel name is required"
    manager = EasyTierConfigManager()
    if manager.tunnel_exists(name):
        return False, f"Tunnel '{name}' already exists"

    local_ip = (data.get("local_ip") or "").strip() or manager.suggest_local_ip(side)
    peer_ip = (data.get("peer_ip") or "").strip()
    if not is_valid_ip(local_ip):
        return False, "Invalid Tunnel Interface IP"
    if not peer_ip or not is_valid_ip(peer_ip):
        return False, "Valid peer Server Public IP is required"

    try:
        used = manager.get_used_values(exclude_tunnel=name)
        if local_ip.split("/")[0] in used.get("local_ips", set()):
            return False, f"IP {local_ip} is already used by another tunnel"

        try:
            port = int((data.get("port") or "").strip() or manager.suggest_listen_port())
        except (ValueError, AttributeError):
            return False, "Invalid Port"
        if not is_valid_port(port):
            return False, "Port must be 1-65535"
        _unique_or_error(used.get("listen_ports", set()), port, "Port")

        secret = (data.get("network_secret") or "").strip() or "vortexl2"
        hostname = (data.get("hostname") or "").strip() or name
        custom_net = (data.get("network_name") or "").strip()

        if side == "IRAN":
            remote_forward = (data.get("remote_forward_ip") or "").strip() or "10.155.155.2"
            if not is_valid_ip(remote_forward):
                return False, "Invalid Remote Forward IP"
        else:
            remote_forward = "10.155.155.1"

        config = manager.create_tunnel(name)
        config._config["local_ip"] = local_ip
        config._config["peer_ip"] = peer_ip
        config._config["port"] = port
        config._config["network_secret"] = secret
        config._config["hostname"] = hostname
        config._config["network_name"] = custom_net if custom_net else None
        config._config["remote_forward_ip"] = remote_forward
        config._config["latency_first"] = True
        config._config["compression"] = "zstd"
        config._config["enable_kcp"] = True
        config._config["mtu"] = 1380

        mgr = EasyTierManager(config)
        success, msg = mgr.start_tunnel()
        if success:
            config.save()
            return True, f"EasyTier tunnel '{name}' created and started!\n{msg}"
        return False, f"Tunnel setup failed (not saved):\n{msg}"
    except ValueError as e:
        return False, str(e)
    except Exception as e:  # noqa: BLE001
        logger.exception("EasyTier create failed")
        return False, f"Error: {e}"


def forwards_modify(name: str, ports_str: str, add: bool) -> tuple:
    """Add or remove port forwards for a tunnel. Returns (ok, message)."""
    name = sanitize_name(name)
    if not name:
        return False, "Invalid tunnel name"
    try:
        ports = parse_ports(ports_str)
    except ValueError as e:
        return False, str(e)
    mode = get_mode()
    try:
        if mode == "easytier":
            from .easytier_manager import EasyTierConfigManager
            from .haproxy_manager import HAProxyManager as Hap
            config = EasyTierConfigManager().get_tunnel(name)
            if not config:
                return False, f"Tunnel '{name}' not found"
            hap = Hap(EasyTierForwardsAdapter(config))
        else:
            config = ConfigManager().get_tunnel(name)
            if not config:
                return False, f"Tunnel '{name}' not found"
            hap = HAProxyManager(config)
        if add:
            ok, msg = hap.add_multiple_forwards(",".join(str(p) for p in ports))
        else:
            ok, msg = hap.remove_multiple_forwards(",".join(str(p) for p in ports))
        restart_forward_daemon()
        return ok, msg
    except Exception as e:  # noqa: BLE001
        logger.exception("Forwards modify failed")
        return False, f"Error: {e}"


# ----------------------------------------------------------------------------
# Logs
# ----------------------------------------------------------------------------

def allowed_log_services() -> list:
    """Services allowed for log viewing (strict allowlist)."""
    services = ["vortexl3-panel", "vortexl3-forward-daemon", "vortexl3-watchdog", "haproxy"]
    try:
        if get_mode() == "easytier":
            from .easytier_manager import EasyTierConfigManager
            for name in EasyTierConfigManager().list_tunnels():
                services.append(f"vortexl3-easytier-{sanitize_name(name)}")
        else:
            services.append("vortexl3-tunnel")
    except Exception:  # noqa: BLE001
        pass
    return services


def get_service_logs_any(service: str, lines: int = 100) -> tuple:
    """Return journal logs for an allowlisted service."""
    import re
    service = (service or "").strip()
    try:
        lines = max(10, min(500, int(lines)))
    except (TypeError, ValueError):
        lines = 100
    if not re.fullmatch(r"[a-z0-9@*._-]+", service) or service not in allowed_log_services():
        return False, "Unknown service"
    ok, out, err = run_command(f"journalctl -u {service} -n {lines} --no-pager 2>&1")
    text = (out or err or "").strip()
    return True, text if text else "No logs available (service may be inactive)"


# ----------------------------------------------------------------------------
# Forward mode
# ----------------------------------------------------------------------------

def get_forward_mode_info() -> str:
    from .forward import get_forward_mode
    try:
        return get_forward_mode()
    except Exception:  # noqa: BLE001
        return "none"


def set_forward_mode_api(mode: str) -> tuple:
    """Change forward mode (mirrors TUI transitions)."""
    from .forward import set_forward_mode, get_forward_mode
    mode = (mode or "").lower()
    if mode not in ("none", "haproxy", "socat"):
        return False, "Mode must be none, haproxy or socat"
    try:
        current = get_forward_mode()
        if mode == current:
            return True, f"Forward mode is already {mode.upper()}"
        if current == "haproxy":
            run_command("systemctl stop haproxy")
        elif current == "socat":
            try:
                from .socat_manager import stop_all_socat
                stop_all_socat()
            except Exception:  # noqa: BLE001
                run_command("pkill -f 'socat.*TCP-LISTEN'")
        set_forward_mode(mode)
        if mode != "none":
            run_command(f"systemctl restart {FORWARD_DAEMON_SERVICE}")
        else:
            run_command("systemctl stop haproxy")
        return True, f"Forward mode changed to {mode.upper()}"
    except Exception as e:  # noqa: BLE001
        logger.exception("Set forward mode failed")
        return False, f"Error: {e}"


def restart_forwards_api() -> tuple:
    run_command(f"systemctl restart {FORWARD_DAEMON_SERVICE}")
    return True, "Forward daemon restarted"


def validate_forwards_api() -> tuple:
    """Validate HAProxy config and reload (socat: no-op)."""
    try:
        from .forward import get_forward_manager, get_forward_mode
        mode = get_forward_mode()
        if mode == "none":
            return False, "Port forwarding is disabled (mode: none)"
        mgr = get_forward_manager(None)
        if not mgr:
            return False, "No forward manager available"
        return mgr.validate_and_reload()
    except Exception as e:  # noqa: BLE001
        logger.exception("Validate forwards failed")
        return False, f"Error: {e}"


# ----------------------------------------------------------------------------
# System health / services
# ----------------------------------------------------------------------------

BASE_HEALTH_SERVICES = [
    ("vortexl3-tunnel", "L2TPv3 Tunnel"),
    ("vortexl3-forward-daemon", "Port Forward Daemon"),
    ("vortexl3-panel", "Web Panel"),
    ("vortexl3-watchdog", "Watchdog"),
    ("haproxy", "HAProxy"),
]


def health_services() -> list:
    """All monitored services with live state."""
    services = list(BASE_HEALTH_SERVICES)
    try:
        if get_mode() == "easytier":
            from .easytier_manager import EasyTierConfigManager
            for name in EasyTierConfigManager().list_tunnels():
                services.append((f"vortexl3-easytier-{sanitize_name(name)}", f"EasyTier: {name}"))
    except Exception:  # noqa: BLE001
        pass
    result = []
    for unit, label in services:
        ok, out, _ = run_command(f"systemctl is-active {unit} 2>&1")
        state = (out or "").strip() if ok else "unknown"
        if not ok and not out:
            state = "unknown"
        result.append({"service": unit, "label": label, "state": state,
                       "active": state == "active"})
    return result


def service_action_api(service: str, action: str) -> tuple:
    """Start / restart / stop an allowlisted service."""
    service = (service or "").strip()
    action = (action or "").lower()
    allowed = [s for s, _ in BASE_HEALTH_SERVICES] + allowed_log_services()
    if service not in allowed:
        return False, "Unknown service"
    if action not in ("start", "restart", "stop"):
        return False, "Action must be start, restart or stop"
    ok, out, err = run_command(f"systemctl {action} {service}")
    if ok:
        return True, f"{service} {action}ed"
    return False, (err or out or "Command failed")[:500]


# ----------------------------------------------------------------------------
# Auto-restart cron
# ----------------------------------------------------------------------------

CRON_INTERVALS = (5, 15, 30, 60)


def cron_status_api() -> dict:
    try:
        fwd_on, fwd_sched = cron_manager.get_auto_restart_status()
    except Exception:  # noqa: BLE001
        fwd_on, fwd_sched = False, "Unknown"
    try:
        et_on, et_sched = cron_manager.get_easytier_cron_status()
    except Exception:  # noqa: BLE001
        et_on, et_sched = False, "Unknown"
    return {
        "forward": {"enabled": fwd_on, "schedule": fwd_sched},
        "easytier": {"enabled": et_on, "schedule": et_sched},
        "intervals": list(CRON_INTERVALS),
    }


def cron_set_api(kind: str, action: str, interval: int = 60) -> tuple:
    """Enable/disable auto-restart cron for 'forward' or 'easytier'."""
    action = (action or "").lower()
    try:
        interval = int(interval)
    except (TypeError, ValueError):
        interval = 60
    if interval not in CRON_INTERVALS:
        return False, f"Interval must be one of {list(CRON_INTERVALS)} minutes"
    try:
        if kind == "forward":
            if action == "enable":
                return cron_manager.add_auto_restart_cron(interval)
            if action == "disable":
                return cron_manager.remove_auto_restart_cron()
        elif kind == "easytier":
            if action == "enable":
                return cron_manager.add_easytier_cron(interval)
            if action == "disable":
                return cron_manager.remove_easytier_cron()
        return False, "Invalid kind/action"
    except Exception as e:  # noqa: BLE001
        logger.exception("Cron update failed")
        return False, f"Error: {e}"


# ----------------------------------------------------------------------------
# TCP optimization
# ----------------------------------------------------------------------------

TCP_STATUS_KEYS = [
    "net.ipv4.tcp_congestion_control",
    "net.core.rmem_max",
    "net.core.wmem_max",
    "net.ipv4.ip_forward",
    "net.ipv4.tcp_fastopen",
]


def tcp_status_api() -> dict:
    try:
        current = TCPOptimizer().get_current_params(TCP_STATUS_KEYS)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
    return {"ok": True, "params": current}


def tcp_apply_api() -> tuple:
    try:
        return setup_tcp_optimization()
    except Exception as e:  # noqa: BLE001
        logger.exception("TCP optimization failed")
        return False, f"Error: {e}"


# ----------------------------------------------------------------------------
# DNS manager (background scan with progress)
# ----------------------------------------------------------------------------

_dns_scan = {"running": False, "progress": [], "done": False,
             "success": None, "message": "", "best": None, "started": ""}
_dns_lock = threading.Lock()


def _dns_scan_worker() -> None:
    def callback(name, ip, status, score):
        with _dns_lock:
            if len(_dns_scan["progress"]) < 500:
                _dns_scan["progress"].append(
                    {"name": name, "ip": ip, "status": status, "score": score})
    try:
        ok, msg, best = dns_manager.scan_and_apply_best_dns(callback=callback)
    except Exception as e:  # noqa: BLE001
        logger.exception("DNS scan failed")
        ok, msg, best = False, f"Error: {e}", None
    with _dns_lock:
        _dns_scan.update({"running": False, "done": True,
                          "success": ok, "message": msg, "best": best})


def dns_scan_start_api() -> tuple:
    with _dns_lock:
        if _dns_scan["running"]:
            return False, "A scan is already running"
        _dns_scan.update({"running": True, "progress": [], "done": False,
                          "success": None, "message": "", "best": None,
                          "started": time.strftime("%Y-%m-%d %H:%M:%S")})
    thread = threading.Thread(target=_dns_scan_worker, daemon=True)
    thread.start()
    return True, "DNS scan started"


def dns_scan_state_api() -> dict:
    with _dns_lock:
        state = dict(_dns_scan)
    state["total"] = len(dns_manager.normalize_dns_list(dns_manager.RAW_DNS_LIST))
    return state


def dns_status_api() -> dict:
    try:
        current = dns_manager.get_current_system_dns()
    except Exception:  # noqa: BLE001
        current = None
    try:
        config = dns_manager.get_dns_config()
    except Exception:  # noqa: BLE001
        config = {}
    try:
        cron_on, cron_sched = dns_manager.get_dns_cron_status()
    except Exception:  # noqa: BLE001
        cron_on, cron_sched = False, "Unknown"
    return {
        "system_dns": current,
        "configured_dns": config.get("current_dns"),
        "configured_name": config.get("current_dns_name"),
        "last_check": config.get("last_check"),
        "interval_hours": config.get("check_interval_hours", 4),
        "auto_check": {"enabled": cron_on, "schedule": cron_sched},
    }


def dns_interval_api(hours) -> tuple:
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        return False, "Invalid interval"
    if not 1 <= hours <= 72:
        return False, "Interval must be 1-72 hours"
    try:
        return dns_manager.set_check_interval(hours)
    except Exception as e:  # noqa: BLE001
        return False, f"Error: {e}"


def dns_autocheck_api(action: str) -> tuple:
    action = (action or "").lower()
    try:
        if action == "enable":
            hours = dns_manager.get_check_interval()
            return dns_manager.update_dns_cron(hours)
        if action == "disable":
            return dns_manager.remove_dns_cron()
        return False, "Action must be enable or disable"
    except Exception as e:  # noqa: BLE001
        return False, f"Error: {e}"


# ----------------------------------------------------------------------------
# HTTP layer
# ----------------------------------------------------------------------------

def _json_response(handler: BaseHTTPRequestHandler, code: int, obj: dict, cookie: str = None) -> None:
    body = json.dumps(obj).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    if cookie:
        handler.send_header("Set-Cookie", cookie)
    handler.end_headers()
    handler.wfile.write(body)


class PanelHandler(BaseHTTPRequestHandler):
    server_version = "VortexL3-Panel"

    def log_message(self, fmt, *args):  # noqa: ANN001, ANN002
        logger.info("%s - %s", self.address_string(), fmt % args)

    # -- helpers ---------------------------------------------------------
    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            length = 0
        if length <= 0 or length > MAX_BODY:
            return None
        try:
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def _session_user(self):
        cookie = self.headers.get("Cookie") or ""
        token = ""
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith(SESSION_COOKIE + "="):
                token = part.split("=", 1)[1].strip()
                break
        if not token:
            return None
        now = time.time()
        with _sessions_lock:
            sess = _sessions.get(token)
            if not sess:
                return None
            if sess["expiry"] < now:
                _sessions.pop(token, None)
                return None
            return sess["username"]

    def _serve_page(self):
        from .panel_template import PAGE
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # -- routes ----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/login", "/dashboard"):
            self._serve_page()
            return
        if not self._session_user():
            _json_response(self, 401, {"ok": False, "error": "Unauthorized"})
            return
        try:
            if path == "/api/summary":
                _json_response(self, 200, {
                    "ok": True,
                    "mode": get_mode(),
                    "version": __version__,
                    "server_ip": get_server_ip(),
                    "tunnels": list_tunnels(),
                })
            elif path == "/api/panel/info":
                cfg = self.server.panel_config
                _json_response(self, 200, {
                    "ok": True,
                    "url": f"http://{get_server_ip()}:{cfg.port}",
                    "username": cfg.username,
                    "port": cfg.port,
                    "version": __version__,
                })
            elif path == "/api/logs":
                query = parse_qs(parsed.query)
                service = (query.get("service", [""])[0])
                lines = (query.get("lines", ["100"])[0])
                ok, output = get_service_logs_any(service, lines)
                _json_response(self, 200 if ok else 400,
                               {"ok": ok, "output": output, "services": allowed_log_services()})
            elif path == "/api/forward/mode":
                _json_response(self, 200, {"ok": True, "mode": get_forward_mode_info()})
            elif path == "/api/health":
                _json_response(self, 200, {"ok": True, "services": health_services()})
            elif path == "/api/cron/status":
                _json_response(self, 200, {"ok": True, **cron_status_api()})
            elif path == "/api/tcp/status":
                _json_response(self, 200, tcp_status_api())
            elif path == "/api/dns/status":
                _json_response(self, 200, {"ok": True, **dns_status_api()})
            elif path == "/api/dns/scan":
                _json_response(self, 200, {"ok": True, **dns_scan_state_api()})
            else:
                _json_response(self, 404, {"ok": False, "error": "Not found"})
        except Exception as e:  # noqa: BLE001
            logger.exception("GET API failed")
            _json_response(self, 500, {"ok": False, "error": str(e)})

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/login":
            self._handle_login()
            return
        if path == "/api/logout":
            self._logout()
            return
        if not self._session_user():
            _json_response(self, 401, {"ok": False, "error": "Unauthorized"})
            return
        data = self._read_json()
        if data is None:
            _json_response(self, 400, {"ok": False, "error": "Invalid JSON body"})
            return
        try:
            if path == "/api/tunnel/action":
                ok, msg = tunnel_action(data.get("name", ""), (data.get("action") or "").lower())
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/tunnel/create":
                if get_mode() == "easytier":
                    ok, msg = create_easytier_tunnel(data)
                else:
                    ok, msg = create_l2tp_tunnel(data)
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/forwards/add":
                ok, msg = forwards_modify(data.get("name", ""), data.get("ports", ""), True)
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/forwards/remove":
                ok, msg = forwards_modify(data.get("name", ""), data.get("ports", ""), False)
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/forward/mode":
                ok, msg = set_forward_mode_api(data.get("mode", ""))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/forward/restart":
                ok, msg = restart_forwards_api()
                _json_response(self, 200, {"ok": ok, "message": msg})
            elif path == "/api/forward/validate":
                ok, msg = validate_forwards_api()
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/service/action":
                ok, msg = service_action_api(data.get("service", ""), data.get("action", ""))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/cron/forward":
                ok, msg = cron_set_api("forward", data.get("action", ""), data.get("interval", 60))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/cron/easytier":
                ok, msg = cron_set_api("easytier", data.get("action", ""), data.get("interval", 60))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/tcp/apply":
                ok, msg = tcp_apply_api()
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/dns/scan":
                ok, msg = dns_scan_start_api()
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/dns/interval":
                ok, msg = dns_interval_api(data.get("hours"))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/dns/autocheck":
                ok, msg = dns_autocheck_api(data.get("action", ""))
                _json_response(self, 200 if ok else 400, {"ok": ok, "message": msg})
            elif path == "/api/panel/password":
                _json_response(self, *self._change_password(data))
            elif path == "/api/panel/port":
                _json_response(self, *self._change_port(data))
            else:
                _json_response(self, 404, {"ok": False, "error": "Not found"})
        except Exception as e:  # noqa: BLE001
            logger.exception("API failed")
            _json_response(self, 500, {"ok": False, "error": str(e)})

    # -- auth ------------------------------------------------------------
    def _client_ip(self) -> str:
        return (self.client_address[0] if self.client_address else "unknown")

    def _login_allowed(self) -> bool:
        now = time.time()
        with _sessions_lock:
            rec = _login_fails.get(self._client_ip())
            if not rec:
                return True
            if now - rec["first"] > LOGIN_WINDOW:
                _login_fails.pop(self._client_ip(), None)
                return True
            return rec["count"] < LOGIN_MAX_FAILS

    def _record_login_fail(self) -> None:
        now = time.time()
        with _sessions_lock:
            rec = _login_fails.get(self._client_ip())
            if not rec or now - rec["first"] > LOGIN_WINDOW:
                _login_fails[self._client_ip()] = {"count": 1, "first": now}
            else:
                rec["count"] += 1

    def _change_password(self, data: dict):
        """Change panel password. Returns (http_code, obj)."""
        cfg = self.server.panel_config
        cfg._load()  # pick up changes made from the TUI
        current = (data.get("current") or "")
        new = (data.get("new") or "")
        if not cfg.verify(self._session_user(), current):
            return 401, {"ok": False, "error": "Current password is wrong"}
        if len(new) < 8:
            return 400, {"ok": False, "error": "New password must be at least 8 characters"}
        if len(new) > 128:
            return 400, {"ok": False, "error": "New password is too long (max 128)"}
        salt = secrets.token_hex(16)
        cfg._data["salt"] = salt
        cfg._data["password_hash"] = _hash_password(new, salt)
        cfg._save()
        return 200, {"ok": True, "message": "Password changed. Use it on next login."}

    def _change_port(self, data: dict):
        """Change panel port (restarts service afterwards). Returns (http_code, obj)."""
        cfg = self.server.panel_config
        try:
            port = int(data.get("port", 0))
        except (TypeError, ValueError):
            return 400, {"ok": False, "error": "Invalid port"}
        if not is_valid_port(port):
            return 400, {"ok": False, "error": "Port must be 1-65535"}
        if port == cfg.port:
            return 400, {"ok": False, "error": "Already using this port"}
        if not is_port_free(port):
            return 400, {"ok": False, "error": f"Port {port} is already in use"}
        cfg.set_port(port)
        ensure_panel_firewall(port)
        reconnect = f"http://{get_server_ip()}:{port}"

        def _delayed_restart():
            time.sleep(2)
            run_command(f"systemctl restart {PANEL_SERVICE}")

        threading.Thread(target=_delayed_restart, daemon=True).start()
        return 200, {"ok": True,
                     "message": f"Port changed to {port}. Panel is restarting...",
                     "reconnect_url": reconnect}

    def _handle_login(self) -> None:
        if not self._login_allowed():
            _json_response(self, 429, {"ok": False, "error": "Too many attempts, try later"})
            return
        data = self._read_json()
        if not data:
            _json_response(self, 400, {"ok": False, "error": "Invalid JSON body"})
            return
        cfg = self.server.panel_config
        cfg._load()  # pick up credential changes made from the TUI
        if cfg.verify(data.get("username", ""), data.get("password", "")):
            token = secrets.token_hex(32)
            with _sessions_lock:
                _sessions[token] = {"username": cfg.username, "expiry": time.time() + SESSION_TTL}
                _login_fails.pop(self._client_ip(), None)
            cookie = f"{SESSION_COOKIE}={token}; HttpOnly; Path=/; SameSite=Lax"
            _json_response(self, 200, {"ok": True}, cookie=cookie)
        else:
            self._record_login_fail()
            _json_response(self, 401, {"ok": False, "error": "Invalid username or password"})

    def _logout(self) -> None:
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith(SESSION_COOKIE + "="):
                with _sessions_lock:
                    _sessions.pop(part.split("=", 1)[1].strip(), None)
        expired = f"{SESSION_COOKIE}=; HttpOnly; Path=/; Max-Age=0"
        _json_response(self, 200, {"ok": True}, cookie=expired)


class PanelServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host: str, port: int, panel_config: PanelConfig):
        self.panel_config = panel_config
        super().__init__((host, port), PanelHandler)


# ----------------------------------------------------------------------------
# Entry point (systemd: python3 -m vortexl3.web_panel)
# ----------------------------------------------------------------------------

def setup_logging() -> None:
    try:
        PANEL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(str(PANEL_LOG_FILE))
    except Exception:  # noqa: BLE001
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def main() -> int:
    setup_logging()
    config = PanelConfig()
    is_new, username, password = config.ensure_initialized()
    port = config.port
    if not is_valid_port(port) or not is_port_free(port):
        port = find_free_port()
        config.set_port(port)

    ensure_panel_firewall(port)

    try:
        server = PanelServer("0.0.0.0", port, config)
    except OSError as e:
        logger.error("Cannot bind panel port %s: %s", port, e)
        return 1

    url = f"http://{get_server_ip()}:{port}"
    logger.info("VortexL3 Web Panel listening on %s (user: %s)", url, username)
    print(f"VortexL3 Web Panel: {url}  user: {username}", flush=True)
    if is_new and password:
        logger.info("Panel credentials - username: %s password: %s", username, password)
        print(f"Panel username: {username}", flush=True)
        print(f"Panel password: {password}", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
