"""
VortexL3 L2TPv3 Tunnel Management

Handles L2TPv3 tunnel and session creation/deletion using iproute2.
"""

from asyncio.log import logger
import subprocess
import re
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a shell command execution."""
    success: bool
    stdout: str
    stderr: str
    returncode: int


def run_command(cmd: str, check: bool = False) -> CommandResult:
    """Execute a shell command and return result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return CommandResult(
            success=(result.returncode == 0),
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            success=False,
            stdout="",
            stderr="Command timed out",
            returncode=-1
        )
    except Exception as e:
        return CommandResult(
            success=False,
            stdout="",
            stderr=str(e),
            returncode=-1
        )


class TunnelManager:
    """Manages L2TPv3 tunnel and session operations for a specific tunnel config."""
    
    def __init__(self, config):
        """
        Initialize with a TunnelConfig instance.

        Args:
            config: TunnelConfig instance for the tunnel to manage
        """
        self.config = config
        self._actual_interface: Optional[str] = None

    @property
    def interface_name(self) -> str:
        """Get the interface name for this tunnel."""
        return self.config.interface_name

    @property
    def effective_interface(self) -> str:
        """Interface actually used by the kernel (auto-detected after setup)."""
        return self._actual_interface or self.config.interface_name

    def _list_l2tp_interfaces(self) -> List[str]:
        """List existing l2tpeth interfaces."""
        result = run_command("ip -o link show | grep -o 'l2tpeth[0-9]*'")
        if not result.success or not result.stdout:
            return []
        return sorted(set(result.stdout.split()))

    def _detect_new_interface(self, before: List[str]) -> Optional[str]:
        """Find the l2tpeth interface created by the last session setup."""
        after = self._list_l2tp_interfaces()
        new_ifaces = [i for i in after if i not in before]
        if len(new_ifaces) == 1:
            return new_ifaces[0]
        if self.config.interface_name in after:
            return self.config.interface_name
        return new_ifaces[0] if new_ifaces else None
    
    def install_prerequisites(self) -> Tuple[bool, str]:
        """Install required packages and load kernel modules."""
        steps = []
        
        # Get kernel version
        result = run_command("uname -r")
        if not result.success:
            return False, "Failed to get kernel version"
        kernel_version = result.stdout.strip()
        
        # Install linux-modules-extra
        steps.append(f"Installing linux-modules-extra-{kernel_version}...")
        result = run_command(f"apt-get install -y linux-modules-extra-{kernel_version}")
        if not result.success:
            # Try without specific version as fallback
            result = run_command("apt-get install -y linux-modules-extra-$(uname -r)")
            if not result.success:
                steps.append(f"Warning: Could not install modules package: {result.stderr}")
        else:
            steps.append("Package installed successfully")
        
        # Install iproute2 with l2tp support
        result = run_command("apt-get install -y iproute2")
        if not result.success:
            steps.append(f"Warning: Could not install iproute2: {result.stderr}")
        
        # Load kernel modules
        modules = ["l2tp_core", "l2tp_netlink", "l2tp_eth"]
        for module in modules:
            steps.append(f"Loading module {module}...")
            result = run_command(f"modprobe {module}")
            if not result.success:
                return False, f"Failed to load module {module}: {result.stderr}"
            steps.append(f"Module {module} loaded")
        
        # Verify modules are loaded
        result = run_command("lsmod | grep l2tp")
        if "l2tp" not in result.stdout:
            return False, "L2TP modules not found in lsmod"
        
        steps.append("All prerequisites installed successfully!")
        return True, "\n".join(steps)
    
    def check_tunnel_exists(self, tunnel_id: int = None) -> bool:
        """Check if L2TP tunnel exists."""
        if tunnel_id is None:
            tunnel_id = self.config.tunnel_id
        
        result = run_command("ip l2tp show tunnel")
        if not result.success:
            return False
        
        # Parse output for tunnel_id
        pattern = rf"Tunnel\s+{tunnel_id},"
        return bool(re.search(pattern, result.stdout))
    
    def check_session_exists(self, tunnel_id: int = None, session_id: int = None) -> bool:
        """Check if L2TP session exists."""
        if tunnel_id is None:
            tunnel_id = self.config.tunnel_id
        if session_id is None:
            session_id = self.config.session_id
        
        result = run_command("ip l2tp show session")
        if not result.success:
            return False
        
        # Parse output for session_id in tunnel
        pattern = rf"Session\s+{session_id}\s+in\s+tunnel\s+{tunnel_id}"
        return bool(re.search(pattern, result.stdout))
    
    def create_tunnel(self) -> Tuple[bool, str]:
        """Create L2TP tunnel based on configuration."""
        if not self.config.local_ip or not self.config.remote_ip:
            return False, "IPs not configured. Please configure tunnel first."
        
        ids = self.config.get_tunnel_ids()
        
        if self.check_tunnel_exists():
            return False, f"Tunnel {ids['tunnel_id']} already exists. Delete it first or use recreate."
        
        # Build command based on encapsulation type
        cmd_parts = [
            "ip l2tp add tunnel",
            f"tunnel_id {ids['tunnel_id']}",
            f"peer_tunnel_id {ids['peer_tunnel_id']}",
        ]
        
        # Add encapsulation-specific parameters
        if self.config.encap_type == "udp":
            cmd_parts.extend([
                "encap udp",
                f"local {self.config.local_ip}",
                f"remote {self.config.remote_ip}",
                f"udp_sport {self.config.udp_port}",
                f"udp_dport {self.config.udp_port}",
            ])
        else:  # ip (default)
            cmd_parts.extend([
                "encap ip",
                f"local {self.config.local_ip}",
                f"remote {self.config.remote_ip}",
            ])
        
        cmd = " ".join(cmd_parts)
        
        result = run_command(cmd)
        if not result.success:
            return False, f"Failed to create tunnel: {result.stderr}"
        
        return True, f"Tunnel {ids['tunnel_id']} created successfully ({self.config.encap_type.upper()} mode)"
    
    def create_session(self) -> Tuple[bool, str]:
        """Create L2TP session in existing tunnel."""
        ids = self.config.get_tunnel_ids()

        if not self.check_tunnel_exists():
            return False, "Tunnel does not exist. Create tunnel first."

        if self.check_session_exists():
            return False, f"Session {ids['session_id']} already exists"

        # Snapshot interfaces: the kernel auto-names the session interface
        # (l2tpethN) and it may differ from our configured index when several
        # tunnels exist, so detect the newly created one afterwards.
        before = self._list_l2tp_interfaces()

        cmd = (
            f"ip l2tp add session "
            f"tunnel_id {ids['tunnel_id']} "
            f"session_id {ids['session_id']} "
            f"peer_session_id {ids['peer_session_id']}"
        )

        result = run_command(cmd)
        if not result.success:
            return False, f"Failed to create session: {result.stderr}"

        detected = self._detect_new_interface(before)
        if detected:
            self._actual_interface = detected
            if detected != self.config.interface_name:
                return True, (
                    f"Session {ids['session_id']} created successfully "
                    f"(kernel interface: {detected})"
                )

        return True, f"Session {ids['session_id']} created successfully"
    
    def bring_up_interface(self) -> Tuple[bool, str]:
        """Bring up the tunnel interface."""
        # Wait a moment for interface to appear
        import time
        time.sleep(0.5)

        iface = self.effective_interface
        result = run_command(f"ip link set {iface} up")
        if not result.success:
            # Fall back: re-detect in case the kernel named it differently
            # (multi-tunnel setups) and retry once.
            detected = self._detect_new_interface([])
            if detected and detected != iface:
                self._actual_interface = detected
                iface = detected
                result = run_command(f"ip link set {iface} up")
            if not result.success:
                return False, f"Failed to bring up interface: {result.stderr}"

        return True, f"Interface {iface} is up"

    def assign_ip(self) -> Tuple[bool, str]:
        """Assign IP address to tunnel interface with optimized MTU."""
        ip_cidr = self.config.interface_ip
        iface = self.effective_interface

        # Check if IP already assigned
        result = run_command(f"ip addr show {iface}")
        if ip_cidr.split('/')[0] in result.stdout:
            # Still set MTU even if IP exists
            pass
        else:
            result = run_command(f"ip addr add {ip_cidr} dev {iface}")
            if not result.success:
                # Check if it's because address exists
                if "RTNETLINK answers: File exists" in result.stderr:
                    pass  # Continue to MTU setting
                else:
                    return False, f"Failed to assign IP: {result.stderr}"

        # Set optimized MTU for better performance
        # UDP: 1280 (leave room for L2TP/UDP headers)
        # IP: 1500 (standard Ethernet MTU, L2TP encapsulation has low overhead)
        mtu = 1280 if self.config.encap_type == "udp" else 1500
        result = run_command(f"ip link set dev {iface} mtu {mtu}")
        if not result.success:
            return False, f"Failed to set MTU: {result.stderr}"

        # Enable TCP window scaling for better throughput
        result = run_command(f"sysctl -w net.ipv4.tcp_window_scaling=1")
        if not result.success:
            logger.warning(f"Could not enable TCP window scaling: {result.stderr}")

        return True, f"IP {ip_cidr} assigned to {iface} (MTU: {mtu})"

    def configure_routing(self) -> Tuple[bool, str]:
        """Configure routing for the tunnel interface."""
        steps = []
        iface = self.effective_interface

        # Loose reverse path filtering on tunnel interface so forwarded
        # traffic (which did not originate locally) is not dropped.
        result = run_command(f"sysctl -w net.ipv4.conf.{iface}.rp_filter=2")
        if result.success:
            steps.append(f"Set rp_filter to loose mode on {iface}")
        else:
            steps.append(f"Warning: Could not set rp_filter: {result.stderr}")

        # Enable ARP on the interface
        result = run_command(f"ip link set {iface} arp on")
        if result.success:
            steps.append(f"Enabled ARP on {iface}")

        # Ensure the interface is in UP and RUNNING state
        result = run_command(f"ip link set {iface} up")
        if result.success:
            steps.append(f"Interface {iface} is UP")

        # Configure IP forwarding to allow traffic through tunnel
        result = run_command("sysctl -w net.ipv4.ip_forward=1")
        if result.success:
            steps.append("IP forwarding enabled")

        return True, "\n".join(steps)

    def configure_firewall(self) -> Tuple[bool, str]:
        """Configure firewall rules for UDP encapsulation (idempotent)."""
        if self.config.encap_type != "udp":
            return True, "Firewall rules not needed for IP encapsulation"

        port = self.config.udp_port

        # Add iptables rules only if missing (multi-tunnel safe)
        commands = [
            f"iptables -C INPUT -p udp --dport {port} -j ACCEPT 2>/dev/null || iptables -I INPUT -p udp --dport {port} -j ACCEPT",
            f"iptables -C OUTPUT -p udp --sport {port} -j ACCEPT 2>/dev/null || iptables -I OUTPUT -p udp --sport {port} -j ACCEPT",
        ]

        for cmd in commands:
            result = run_command(cmd)
            if not result.success:
                return False, f"Failed to add firewall rule: {result.stderr}"

        return True, f"Firewall configured for UDP port {port}"
    def delete_session(self) -> Tuple[bool, str]:
        """Delete L2TP session."""
        ids = self.config.get_tunnel_ids()
        
        if not self.check_session_exists():
            return True, "Session does not exist (already deleted)"
        
        cmd = f"ip l2tp del session tunnel_id {ids['tunnel_id']} session_id {ids['session_id']}"
        result = run_command(cmd)
        if not result.success:
            return False, f"Failed to delete session: {result.stderr}"
        
        return True, f"Session {ids['session_id']} deleted"
    
    def delete_tunnel(self) -> Tuple[bool, str]:
        """Delete L2TP tunnel (must delete session first)."""
        ids = self.config.get_tunnel_ids()
        
        # First delete session if exists
        if self.check_session_exists():
            success, msg = self.delete_session()
            if not success:
                return False, f"Failed to delete session first: {msg}"
        
        if not self.check_tunnel_exists():
            return True, "Tunnel does not exist (already deleted)"
        
        cmd = f"ip l2tp del tunnel tunnel_id {ids['tunnel_id']}"
        result = run_command(cmd)
        if not result.success:
            return False, f"Failed to delete tunnel: {result.stderr}"
        
        return True, f"Tunnel {ids['tunnel_id']} deleted"
    
    def full_setup(self) -> Tuple[bool, str]:
        """Perform full tunnel setup: create tunnel, session, bring up interface, assign IP."""
        steps = []
        tunnel_name = self.config.name
        
        steps.append(f"=== Setting up tunnel: {tunnel_name} ===")
        
        # Create tunnel
        success, msg = self.create_tunnel()
        steps.append(f"Create tunnel: {msg}")
        if not success and "already exists" not in msg:
            return False, "\n".join(steps)
        
        # Create session
        success, msg = self.create_session()
        steps.append(f"Create session: {msg}")
        if not success and "already exists" not in msg:
            return False, "\n".join(steps)
        
        # Bring up interface
        success, msg = self.bring_up_interface()
        steps.append(f"Bring up interface: {msg}")
        if not success:
            return False, "\n".join(steps)
        
        # Assign IP
        success, msg = self.assign_ip()
        steps.append(f"Assign IP: {msg}")
        if not success:
            return False, "\n".join(steps)
        
        # Configure routing for tunnel interface
        success, msg = self.configure_routing()
        steps.append(f"Configure routing: {msg}")
        if not success:
            steps.append(f"Warning: Routing configuration had issues")
        
        # Configure firewall if needed (UDP mode)
        if self.config.encap_type == "udp":
            success, msg = self.configure_firewall()
            steps.append(f"Configure firewall: {msg}")
            if not success:
                return False, "\n".join(steps)
        
        # NOTE: DPI evasion (tc netem artificial delay) is intentionally NOT
        # applied automatically: it adds ~25ms latency to every packet.
        # Enable it manually only on networks with active DPI throttling:
        #   from vortexl3.dpi_evasion import setup_dpi_evasion
        #   setup_dpi_evasion("<iface>", "<encap>")
        steps.append("DPI evasion: skipped (opt-in only, adds latency)")
        
        # Setup connection pooling to reduce signatures
        try:
            from .connection_pool import setup_connection_pooling
            success, msg = setup_connection_pooling(tunnel_name, pool_size=8)
            steps.append(f"Connection pooling: {msg}")
        except Exception as e:
            steps.append(f"Connection pooling (optional): Skipped - {e}")
        
        steps.append(f"\n✓ Tunnel '{tunnel_name}' setup complete!")
        return True, "\n".join(steps)
    
    def full_teardown(self) -> Tuple[bool, str]:
        """Perform full tunnel teardown: delete session and tunnel."""
        steps = []
        tunnel_name = self.config.name

        steps.append(f"=== Tearing down tunnel: {tunnel_name} ===")

        # Delete session
        success, msg = self.delete_session()
        steps.append(f"Delete session: {msg}")

        # Delete tunnel
        success, msg = self.delete_tunnel()
        steps.append(f"Delete tunnel: {msg}")

        # Best-effort cleanup of per-tunnel firewall/qdisc state (UDP mode)
        if self.config.encap_type == "udp":
            port = self.config.udp_port
            run_command(f"iptables -D INPUT -p udp --dport {port} -j ACCEPT 2>/dev/null")
            run_command(f"iptables -D OUTPUT -p udp --sport {port} -j ACCEPT 2>/dev/null")
            run_command(f"tc qdisc del dev {self.effective_interface} root 2>/dev/null")

        steps.append(f"\n✓ Tunnel '{tunnel_name}' teardown complete!")
        return True, "\n".join(steps)
    
    def get_status(self) -> Dict[str, any]:
        """Get comprehensive tunnel status."""
        status = {
            "tunnel_name": self.config.name,
            "configured": self.config.is_configured(),
            "local_ip": self.config.local_ip,
            "remote_ip": self.config.remote_ip,
            "interface_name": self.interface_name,
            "tunnel_exists": False,
            "session_exists": False,
            "interface_up": False,
            "interface_ip": None,
            "tunnel_info": "",
            "session_info": "",
            "interface_info": "",
        }
        
        # Check tunnel
        result = run_command("ip l2tp show tunnel")
        status["tunnel_info"] = result.stdout if result.success else result.stderr
        status["tunnel_exists"] = self.check_tunnel_exists()
        
        # Check session
        result = run_command("ip l2tp show session")
        status["session_info"] = result.stdout if result.success else result.stderr
        status["session_exists"] = self.check_session_exists()
        
        # Check interface
        result = run_command(f"ip addr show {self.interface_name} 2>/dev/null")
        if result.success and result.stdout:
            status["interface_info"] = result.stdout
            status["interface_up"] = "UP" in result.stdout
            # Extract IP
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+/\d+)', result.stdout)
            if ip_match:
                status["interface_ip"] = ip_match.group(1)
        
        return status
