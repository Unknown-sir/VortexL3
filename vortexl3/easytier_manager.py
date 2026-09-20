"""
VortexL3 EasyTier Tunnel Manager

Manages EasyTier mesh tunnel configuration and operations.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import yaml

logger = logging.getLogger(__name__)

# Paths
EASYTIER_BIN = Path("/usr/local/bin/easytier-core")
EASYTIER_CLI = Path("/usr/local/bin/easytier-cli")
CONFIG_DIR = Path("/etc/vortexl3")
TUNNELS_DIR = CONFIG_DIR / "tunnels"

# Port allocation ranges (per-tunnel uniqueness for multi-tunnel support)
DEFAULT_LISTEN_PORT = 2070
RPC_PORT_BASE = 15888
RPC_PORT_MAX = 15987

# easytier-core --help cache for CLI feature detection.
# New flags are only passed when the installed binary supports them, so old
# bundled binaries keep working instead of exiting on unknown arguments
# (which leaves no TUN interface and no local IP behind).
_HELP_CACHE: Dict[str, str] = {}


def _get_help_text() -> str:
    """Return `easytier-core --help` output (cached per process)."""
    if "help" not in _HELP_CACHE:
        try:
            result = subprocess.run(
                [str(EASYTIER_BIN), "--help"],
                capture_output=True, text=True, timeout=15,
            )
            _HELP_CACHE["help"] = (result.stdout or "") + "\n" + (result.stderr or "")
        except Exception:
            _HELP_CACHE["help"] = ""
    return _HELP_CACHE["help"]


def _supports(flag: str) -> bool:
    """Check if the installed easytier-core binary supports a CLI flag."""
    return flag in _get_help_text()


def get_binary_version() -> str:
    """Return easytier-core version string (best-effort)."""
    try:
        result = subprocess.run(
            [str(EASYTIER_BIN), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        out = ((result.stdout or "") + " " + (result.stderr or "")).strip()
        return out.split("\n")[0][:120] if out else "unknown"
    except Exception:
        return "unknown"


class EasyTierConfig:
    """Configuration for an EasyTier tunnel."""
    
    DEFAULTS = {
        "name": "tunnel1",
        "tunnel_type": "easytier",
        "network_name": None,          # Defaults to f"vortex-{name}" (must match on both sides)
        "local_ip": "10.155.155.1",  # Interface IP
        "peer_ip": None,              # Remote server IP
        "port": 2070,                 # Listen/connect port (auto-allocated per tunnel)
        "rpc_port": None,             # RPC portal port (auto-allocated per tunnel)
        "network_secret": "vortexl2",  # NOTE: kept for compat with existing peers; do not rename
        "interface_name": "tun1",
        "hostname": "node1",
        "forwarded_ports": [],
        "remote_forward_ip": None,    # For port forwarding target
        # Performance tuning (latency / packet-loss fixes)
        "mtu": 1380,
        "latency_first": True,
        "compression": "zstd",
        "enable_kcp": True,
        "disable_ipv6": False,
        # Command profile: "auto" tries full features then falls back to
        # "minimal" (old-binary compatible). Set automatically on success.
        "cmd_profile": "auto",
    }
    
    def __init__(self, name: str, config_data: Dict[str, Any] = None, auto_save: bool = True):
        self._name = name
        self._config: Dict[str, Any] = {}
        self._file_path = TUNNELS_DIR / f"{name}.yaml"
        self._auto_save = auto_save
        
        if config_data:
            self._config = config_data
        else:
            self._load()
        
        # Apply defaults
        for key, default in self.DEFAULTS.items():
            if key not in self._config:
                self._config[key] = default
        
        self._config["name"] = name
        self._config["tunnel_type"] = "easytier"
    
    def _load(self) -> None:
        if self._file_path.exists():
            try:
                with open(self._file_path, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception:
                self._config = {}
    
    def _save(self) -> None:
        if not self._auto_save:
            return
        TUNNELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
        os.chmod(self._file_path, 0o600)
    
    def save(self) -> None:
        """Force save configuration."""
        TUNNELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
        os.chmod(self._file_path, 0o600)
        self._auto_save = True
    
    def delete(self) -> bool:
        if self._file_path.exists():
            self._file_path.unlink()
            return True
        return False
    
    # Properties
    @property
    def name(self) -> str:
        return self._config.get("name", self._name)
    
    @property
    def local_ip(self) -> str:
        return self._config.get("local_ip", "10.155.155.1")
    
    @local_ip.setter
    def local_ip(self, value: str) -> None:
        self._config["local_ip"] = value
        self._save()
    
    @property
    def peer_ip(self) -> Optional[str]:
        return self._config.get("peer_ip")
    
    @peer_ip.setter
    def peer_ip(self, value: str) -> None:
        self._config["peer_ip"] = value
        self._save()
    
    @property
    def port(self) -> int:
        return self._config.get("port", 2070)
    
    @port.setter
    def port(self, value: int) -> None:
        self._config["port"] = value
        self._save()
    
    @property
    def network_secret(self) -> str:
        return self._config.get("network_secret", "vortexl2")

    @network_secret.setter
    def network_secret(self, value: str) -> None:
        self._config["network_secret"] = value
        self._save()

    @property
    def network_name(self) -> str:
        """Mesh network name. Must be identical on both sides of a tunnel pair."""
        name = self._config.get("network_name")
        if not name:
            name = f"vortex-{self._name}"
        return name

    @network_name.setter
    def network_name(self, value: str) -> None:
        self._config["network_name"] = value
        self._save()

    @property
    def rpc_port(self) -> int:
        """Unique RPC portal port for this tunnel (multi-tunnel support)."""
        port = self._config.get("rpc_port")
        if port is None:
            return RPC_PORT_BASE
        return int(port)

    @rpc_port.setter
    def rpc_port(self, value: int) -> None:
        self._config["rpc_port"] = int(value)
        self._save()

    @property
    def mtu(self) -> int:
        return int(self._config.get("mtu", 1380))

    @mtu.setter
    def mtu(self, value: int) -> None:
        self._config["mtu"] = int(value)
        self._save()

    @property
    def latency_first(self) -> bool:
        return bool(self._config.get("latency_first", True))

    @latency_first.setter
    def latency_first(self, value: bool) -> None:
        self._config["latency_first"] = bool(value)
        self._save()

    @property
    def compression(self) -> str:
        return self._config.get("compression", "zstd") or "none"

    @compression.setter
    def compression(self, value: str) -> None:
        self._config["compression"] = value
        self._save()

    @property
    def enable_kcp(self) -> bool:
        return bool(self._config.get("enable_kcp", True))

    @enable_kcp.setter
    def enable_kcp(self, value: bool) -> None:
        self._config["enable_kcp"] = bool(value)
        self._save()

    @property
    def disable_ipv6(self) -> bool:
        return bool(self._config.get("disable_ipv6", False))

    @disable_ipv6.setter
    def disable_ipv6(self, value: bool) -> None:
        self._config["disable_ipv6"] = bool(value)
        self._save()

    @property
    def cmd_profile(self) -> str:
        """Command profile: 'auto', 'full' or 'minimal'."""
        profile = self._config.get("cmd_profile", "auto")
        return profile if profile in ("auto", "full", "minimal") else "auto"

    @cmd_profile.setter
    def cmd_profile(self, value: str) -> None:
        if value in ("auto", "full", "minimal"):
            self._config["cmd_profile"] = value
            self._save()
    
    @property
    def interface_name(self) -> str:
        return self._config.get("interface_name", "tun1")
    
    @interface_name.setter
    def interface_name(self, value: str) -> None:
        self._config["interface_name"] = value
        self._save()
    
    @property
    def hostname(self) -> str:
        return self._config.get("hostname", "node1")
    
    @hostname.setter
    def hostname(self, value: str) -> None:
        self._config["hostname"] = value
        self._save()
    
    @property
    def forwarded_ports(self) -> List[int]:
        return self._config.get("forwarded_ports", [])
    
    @forwarded_ports.setter
    def forwarded_ports(self, value: List[int]) -> None:
        self._config["forwarded_ports"] = value
        self._save()
    
    @property
    def remote_forward_ip(self) -> Optional[str]:
        return self._config.get("remote_forward_ip")
    
    @remote_forward_ip.setter
    def remote_forward_ip(self, value: str) -> None:
        self._config["remote_forward_ip"] = value
        self._save()
    
    def add_port(self, port: int) -> None:
        ports = self.forwarded_ports
        if port not in ports:
            ports.append(port)
            self.forwarded_ports = ports
    
    def remove_port(self, port: int) -> None:
        ports = self.forwarded_ports
        if port in ports:
            ports.remove(port)
            self.forwarded_ports = ports
    
    def is_configured(self) -> bool:
        return bool(self.peer_ip)
    
    def to_dict(self) -> Dict[str, Any]:
        return self._config.copy()
    
    def get_command_args(self, profile: str = "full") -> List[str]:
        """Generate command line arguments for easytier-core.

        Profiles:
        - "full": all performance flags, each included only if the installed
          binary advertises it in `--help` (UDP listeners/peers, latency-first,
          zstd, MTU, KCP, network-name, instance-name).
        - "minimal": v4-compatible set (TCP only) + per-tunnel RPC port.
          Used automatically when the binary is old or the full profile
          fails to bring the TUN interface up.

        Performance notes (latency / packet-loss fixes):
        - Listen on BOTH tcp and udp so P2P can use UDP (lowest latency).
          TCP-only mode causes TCP-over-TCP meltdown under load.
        - Peers are added as both tcp:// and udp:// URLs.
        - --latency-first routes via the lowest-latency path.
        - --compression zstd reduces bytes on the wire.
        - --mtu 1380 avoids fragmentation with encryption overhead.
        - --enable-kcp-proxy protects TCP streams on lossy links.
        - --rpc-portal is unique per tunnel so multiple tunnels can coexist.
        - --network-name isolates each tunnel pair into its own mesh.
        """
        minimal = (profile == "minimal")

        def has(flag: str) -> bool:
            return (not minimal) and _supports(flag)

        args = [str(EASYTIER_BIN), "-i", self.local_ip]

        if has("--network-name"):
            args.extend(["--network-name", self.network_name])

        args.extend(["--hostname", self.hostname])

        if has("--instance-name"):
            args.extend(["-m", self.name])

        args.extend(["--network-secret", self.network_secret])

        if has("--default-protocol"):
            args.extend(["--default-protocol", "udp"])

        args.extend(["--listeners", f"tcp://0.0.0.0:{self.port}"])
        if has("udp://"):
            args.extend(["--listeners", f"udp://0.0.0.0:{self.port}"])

        if has("--multi-thread"):
            args.append("--multi-thread")

        args.extend(["--dev-name", self.interface_name])

        if has("--mtu"):
            args.extend(["--mtu", str(self.mtu)])

        args.extend(["--rpc-portal", f"127.0.0.1:{self.rpc_port}"])

        if self.latency_first and has("--latency-first"):
            args.append("--latency-first")

        if self.compression and self.compression != "none" and has("--compression"):
            args.extend(["--compression", self.compression])

        if self.enable_kcp and has("--enable-kcp-proxy"):
            args.append("--enable-kcp-proxy")

        if self.disable_ipv6 and has("--disable-ipv6"):
            args.append("--disable-ipv6")

        if self.peer_ip:
            args.extend(["--peers", f"tcp://{self.peer_ip}:{self.port}"])
            if has("udp://"):
                args.extend(["--peers", f"udp://{self.peer_ip}:{self.port}"])

        return args

    def get_command_string(self, profile: str = "full") -> str:
        """Get full command as string."""
        return " ".join(self.get_command_args(profile=profile))


class EasyTierManager:
    """Manages EasyTier tunnel operations."""
    
    def __init__(self, config: EasyTierConfig):
        self.config = config
        self._service_name = f"vortexl3-easytier-{config.name}"
    
    def _run_command(self, cmd: str) -> Tuple[bool, str, str]:
        """Execute shell command."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_easytier_installed(self) -> bool:
        """Check if EasyTier binary is installed."""
        return EASYTIER_BIN.exists() and os.access(EASYTIER_BIN, os.X_OK)

    def _ensure_firewall(self) -> None:
        """Open the tunnel listen port for TCP+UDP (idempotent, best-effort)."""
        for proto in ("tcp", "udp"):
            check = subprocess.run(
                f"iptables -C INPUT -p {proto} --dport {self.config.port} -j ACCEPT",
                shell=True, capture_output=True, timeout=10,
            )
            if check.returncode != 0:
                subprocess.run(
                    f"iptables -I INPUT -p {proto} --dport {self.config.port} -j ACCEPT",
                    shell=True, capture_output=True, timeout=10,
                )
    
    def check_tunnel_exists(self) -> bool:
        """Check if tunnel interface exists."""
        success, stdout, _ = self._run_command(f"ip link show {self.config.interface_name}")
        return success

    def check_interface(self) -> Tuple[bool, bool, bool]:
        """Check TUN interface state.

        Returns:
            (exists, has_any_ip, has_configured_ip)
        """
        success, stdout, _ = self._run_command(f"ip addr show {self.config.interface_name}")
        if not success or not stdout:
            return False, False, False
        has_ip = "inet " in stdout
        want = self.config.local_ip.split('/')[0] if self.config.local_ip else ""
        has_ours = bool(want) and want in stdout
        return True, has_ip, has_ours

    def wait_for_interface(self, timeout: int = 20) -> Tuple[bool, bool, bool]:
        """Wait until the TUN interface exists and has an IP (poll each second)."""
        import time
        state: Tuple[bool, bool, bool] = (False, False, False)
        for _ in range(max(1, timeout)):
            state = self.check_interface()
            if state[0] and state[1]:
                return state
            time.sleep(1)
        return state

    def get_service_logs(self, lines: int = 25) -> str:
        """Return recent journal logs for this tunnel's service (diagnostics)."""
        success, stdout, stderr = self._run_command(
            f"journalctl -u {self._service_name} -n {lines} --no-pager 2>&1"
        )
        out = (stdout or "") + (stderr or "")
        return out.strip()[-3000:] if out.strip() else "No journal logs available"

    def _create_service_file(self, cmd: str = None) -> Tuple[bool, str]:
        """Create systemd service file for this tunnel."""
        if cmd is None:
            cmd = self.config.get_command_string()

        service_content = f"""[Unit]
Description=VortexL3 EasyTier Tunnel - {self.config.name}
After=network.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={cmd}
Restart=always
RestartSec=3
StartLimitIntervalSec=120
StartLimitBurst=10
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        try:
            service_path = Path(f"/etc/systemd/system/{self._service_name}.service")
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            self._run_command("systemctl daemon-reload")
            return True, f"Service file created: {self._service_name}"
        except Exception as e:
            return False, f"Failed to create service: {e}"
    
    def start_tunnel(self) -> Tuple[bool, str]:
        """Start the EasyTier tunnel.

        Writes the service file, starts it, then VERIFIES that the TUN
        interface actually came up with our local IP. If the full-featured
        command fails (e.g. old binary without new flags), it automatically
        retries with the minimal v4-compatible profile.
        """
        if not self.check_easytier_installed():
            return False, "EasyTier binary not found at /usr/local/bin/easytier-core"

        if not self.config.is_configured():
            return False, "Tunnel not fully configured (missing peer IP)"

        # Open firewall for both TCP and UDP listeners (idempotent)
        self._ensure_firewall()

        version = get_binary_version()
        pinned = self.config.cmd_profile
        order = ["full", "minimal"] if pinned in ("auto", "full") else ["minimal", "full"]

        last_logs = ""
        for profile in order:
            cmd = self.config.get_command_string(profile=profile)
            success, msg = self._create_service_file(cmd)
            if not success:
                return False, msg

            # Enable and (re)start service
            self._run_command(f"systemctl enable {self._service_name}")
            success, _, stderr = self._run_command(f"systemctl restart {self._service_name}")
            if not success:
                success, _, stderr = self._run_command(f"systemctl start {self._service_name}")
                if not success:
                    last_logs = self.get_service_logs()
                    continue  # try next profile

            exists, has_ip, has_ours = self.wait_for_interface(timeout=20)
            if exists and has_ip:
                self.config.cmd_profile = profile
                detail = (
                    f"Interface {self.config.interface_name} is UP "
                    f"({self.config.local_ip} {'assigned' if has_ours else 'present (IP differs from config!)'})"
                )
                note = "" if profile == "full" else (
                    " [compatibility profile: binary lacks new flags, consider upgrading easytier-core]"
                )
                return True, (
                    f"EasyTier tunnel '{self.config.name}' started "
                    f"(binary: {version}, profile: {profile}){note}\n{detail}"
                )
            last_logs = self.get_service_logs()

        return False, (
            f"EasyTier tunnel '{self.config.name}' failed: TUN interface "
            f"'{self.config.interface_name}' did not come up with IP {self.config.local_ip} "
            f"(binary: {version}).\n"
            f"--- service logs ---\n{last_logs}\n"
            f"Hint: check that UDP/TCP port {self.config.port} is free, the binary is executable, "
            f"and TUN device creation is allowed on this host."
        )
    
    def stop_tunnel(self) -> Tuple[bool, str]:
        """Stop the EasyTier tunnel."""
        self._run_command(f"systemctl stop {self._service_name}")
        self._run_command(f"systemctl disable {self._service_name}")
        return True, f"EasyTier tunnel '{self.config.name}' stopped"
    
    def restart_tunnel(self) -> Tuple[bool, str]:
        """Restart the EasyTier tunnel (regenerates service file, verifies interface)."""
        return self.start_tunnel()

    def get_status(self) -> Tuple[bool, str]:
        """Get tunnel status (service state + TUN interface state)."""
        success, stdout, stderr = self._run_command(f"systemctl is-active {self._service_name}")
        is_active = success and "active" in stdout

        exists, has_ip, has_ours = self.check_interface()

        if is_active and exists and has_ip:
            return True, "Running"
        if is_active and exists and not has_ip:
            return False, "Service active but TUN has no IP"
        if is_active:
            return False, "Service active but TUN interface missing"
        else:
            return False, "Stopped"
    
    def get_peer_info(self) -> List[Dict[str, Any]]:
        """Get peer information from easytier-cli peer command.
        
        Returns list of peers with their stats:
        - ipv4: IP address
        - hostname: peer hostname
        - cost: connection cost (Local, p2p, etc.)
        - latency: latency in ms
        - loss: packet loss percentage
        - rx: received bytes
        - tx: transmitted bytes
        - tunnel: tunnel type (tcp, udp, etc.)
        - nat: NAT type
        """
        if not EASYTIER_CLI.exists():
            return []

        # Query this tunnel's own RPC portal (unique per tunnel for multi-tunnel).
        # Fall back to the default portal for configs created before rpc_port existed.
        commands = [
            f"{EASYTIER_CLI} --rpc-portal 127.0.0.1:{self.config.rpc_port} peer",
            f"{EASYTIER_CLI} peer",
        ]
        stdout = ""
        for cmd in commands:
            success, out, stderr = self._run_command(cmd)
            if success and out:
                stdout = out
                break
        if not stdout:
            return []
        
        peers = []
        lines = stdout.strip().split('\n')
        
        # Parse table with Unicode box-drawing characters
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip header and separator lines (contain ┌ ├ └ ─ or header text)
            if any(c in line for c in '┌├└─┬┴┼'):
                continue
            if 'ipv4' in line.lower() or 'hostname' in line.lower():
                continue
            
            # Data lines start with │
            if not line.startswith('│'):
                continue
            
            # Parse pipe-separated values (using Unicode │)
            parts = [p.strip() for p in line.split('│') if p.strip()]
            
            if len(parts) >= 7:
                try:
                    peer = {
                        'ipv4': parts[0],
                        'hostname': parts[1],
                        'cost': parts[2],
                        'latency': parts[3] if parts[3] != '-' else None,
                        'loss': parts[4] if parts[4] != '-' else None,
                        'rx': parts[5] if parts[5] != '-' else None,
                        'tx': parts[6] if parts[6] != '-' else None,
                        'tunnel': parts[7] if len(parts) > 7 and parts[7] != '-' else None,
                        'nat': parts[8] if len(parts) > 8 else None,
                    }
                    peers.append(peer)
                except (IndexError, ValueError):
                    continue
        
        return peers
    
    def full_setup(self) -> Tuple[bool, str]:
        """Full tunnel setup (create and start)."""
        return self.start_tunnel()
    
    def full_teardown(self) -> Tuple[bool, str]:
        """Full tunnel teardown (stop and remove service)."""
        self.stop_tunnel()
        
        # Remove service file
        service_path = Path(f"/etc/systemd/system/{self._service_name}.service")
        if service_path.exists():
            service_path.unlink()
            self._run_command("systemctl daemon-reload")
        
        return True, f"EasyTier tunnel '{self.config.name}' removed"


class EasyTierConfigManager:
    """Manages multiple EasyTier tunnel configurations."""
    
    def __init__(self):
        self._ensure_dirs()
    
    def _ensure_dirs(self) -> None:
        TUNNELS_DIR.mkdir(parents=True, exist_ok=True)
    
    def list_tunnels(self) -> List[str]:
        """List all EasyTier tunnel names."""
        if not TUNNELS_DIR.exists():
            return []
        
        tunnels = []
        for f in TUNNELS_DIR.glob("*.yaml"):
            try:
                with open(f, 'r') as file:
                    data = yaml.safe_load(file) or {}
                    if data.get("tunnel_type") == "easytier":
                        tunnels.append(f.stem)
            except Exception:
                pass
        return sorted(tunnels)
    
    def get_tunnel(self, name: str) -> Optional[EasyTierConfig]:
        file_path = TUNNELS_DIR / f"{name}.yaml"
        if file_path.exists():
            return EasyTierConfig(name)
        return None
    
    def get_all_tunnels(self) -> List[EasyTierConfig]:
        return [EasyTierConfig(name) for name in self.list_tunnels()]
    
    def create_tunnel(self, name: str) -> EasyTierConfig:
        """Create new EasyTier tunnel config (not saved yet).

        Allocates resources that must be unique per tunnel on one machine:
        listen port, RPC portal port, interface name, hostname and network name.
        """
        tunnel = EasyTierConfig(name, auto_save=False)
        # Use tunnel name as interface name (Linux allows up to 15 chars)
        iface_name = name[:15] if len(name) > 15 else name
        if iface_name in self.get_used_interface_names():
            suffix = 1
            base = name[:13] if len(name) > 13 else name
            while f"{base}-{suffix}" in self.get_used_interface_names():
                suffix += 1
            iface_name = f"{base}-{suffix}"
        tunnel._config["interface_name"] = iface_name
        tunnel._config["hostname"] = name
        tunnel._config["network_name"] = f"vortex-{name}"
        tunnel._config["port"] = self.suggest_listen_port()
        tunnel._config["rpc_port"] = self.suggest_rpc_port()
        return tunnel

    def get_used_values(self, exclude_tunnel: str = None) -> Dict[str, Any]:
        """Collect values already used by other EasyTier tunnels."""
        used: Dict[str, Any] = {
            "listen_ports": set(),
            "rpc_ports": set(),
            "interface_names": set(),
            "local_ips": set(),
            "hostnames": set(),
        }
        for tunnel in self.get_all_tunnels():
            if exclude_tunnel and tunnel.name == exclude_tunnel:
                continue
            used["listen_ports"].add(int(tunnel.port))
            used["rpc_ports"].add(int(tunnel.rpc_port))
            used["interface_names"].add(tunnel.interface_name)
            if tunnel.local_ip:
                used["local_ips"].add(tunnel.local_ip.split('/')[0])
            if tunnel.hostname:
                used["hostnames"].add(tunnel.hostname)
        return used

    def get_used_interface_names(self) -> set:
        return self.get_used_values().get("interface_names", set())

    def suggest_listen_port(self, exclude_tunnel: str = None) -> int:
        """Suggest the first free listen port starting at 2070."""
        used = self.get_used_values(exclude_tunnel).get("listen_ports", set())
        port = DEFAULT_LISTEN_PORT
        while port in used and port < 65535:
            port += 1
        return port

    def suggest_rpc_port(self, exclude_tunnel: str = None) -> int:
        """Suggest the first free RPC portal port starting at 15888."""
        used = self.get_used_values(exclude_tunnel).get("rpc_ports", set())
        port = RPC_PORT_BASE
        while port in used and port <= RPC_PORT_MAX:
            port += 1
        return port

    def suggest_local_ip(self, side: str, exclude_tunnel: str = None) -> str:
        """Suggest a free tunnel IP in 10.155.155.0/24 (.1 for IRAN, .2 for KHAREJ...)."""
        used = self.get_used_values(exclude_tunnel).get("local_ips", set())
        start = 1 if side == "IRAN" else 2
        for host in list(range(start, 255, 2)) + list(range(1, 255)):
            candidate = f"10.155.155.{host}"
            if candidate not in used:
                return candidate
        return "10.155.155.1" if side == "IRAN" else "10.155.155.2"
    
    def delete_tunnel(self, name: str) -> bool:
        tunnel = self.get_tunnel(name)
        if tunnel:
            # Stop tunnel first
            manager = EasyTierManager(tunnel)
            manager.full_teardown()
            return tunnel.delete()
        return False
    
    def tunnel_exists(self, name: str) -> bool:
        return (TUNNELS_DIR / f"{name}.yaml").exists()
