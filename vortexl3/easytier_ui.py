"""
VortexL3 EasyTier UI Components

UI functions for EasyTier tunnel management.
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from .easytier_manager import EasyTierConfig, EasyTierManager, EasyTierConfigManager


console = Console()


def show_easytier_main_menu() -> str:
    """Display EasyTier main menu."""
    menu_items = [
        ("1", "TCP Optimization"),
        ("2", "Create EasyTier Tunnel"),
        ("3", "Delete Tunnel"),
        ("4", "List Tunnels"),
        ("5", "Restart Tunnel"),
        ("6", "Port Forwards"),
        ("7", "Tunnel Auto-Restart"),
        ("8", "View Logs"),
        ("9", "DNS Manager"),
        ("0", "Exit"),
    ]
    
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Option", style="bold cyan", width=4)
    table.add_column("Description", style="white")
    
    for opt, desc in menu_items:
        table.add_row(f"[{opt}]", desc)
    
    console.print(Panel(table, title="[bold white]EasyTier Menu[/]", border_style="green"))
    
    return Prompt.ask("\n[bold cyan]Select option[/]", default="0")


def show_easytier_tunnel_list(manager: EasyTierConfigManager):
    """Display list of EasyTier tunnels with peer info."""
    tunnels = manager.get_all_tunnels()
    
    if not tunnels:
        console.print("[yellow]No EasyTier tunnels configured.[/]")
        return
    
    # Basic tunnel info table
    table = Table(title="EasyTier Tunnels", box=box.ROUNDED)
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="magenta")
    table.add_column("Interface", style="yellow")
    table.add_column("Local IP", style="green")
    table.add_column("Peer IP", style="cyan")
    table.add_column("Port", style="white")
    table.add_column("Status", style="white")
    
    for i, config in enumerate(tunnels, 1):
        mgr = EasyTierManager(config)
        is_running, status = mgr.get_status()
        status_display = f"[green]{status}[/]" if is_running else f"[red]{status}[/]"
        
        table.add_row(
            str(i),
            config.name,
            config.interface_name,
            config.local_ip or "-",
            config.peer_ip or "-",
            str(config.port),
            status_display
        )
    
    console.print(table)
    
    # Get peer info for running tunnels
    for config in tunnels:
        mgr = EasyTierManager(config)
        is_running, _ = mgr.get_status()
        
        if is_running:
            peers = mgr.get_peer_info()
            if peers:
                console.print(f"\n[bold cyan]Peer Stats for {config.name}:[/]")
                
                peer_table = Table(box=box.SIMPLE)
                peer_table.add_column("IP", style="green")
                peer_table.add_column("Host", style="magenta")
                peer_table.add_column("Type", style="yellow")
                peer_table.add_column("Latency", style="cyan")
                peer_table.add_column("Loss", style="red")
                peer_table.add_column("RX", style="blue")
                peer_table.add_column("TX", style="blue")
                peer_table.add_column("Tunnel", style="white")
                
                for peer in peers:
                    # Color latency based on value
                    lat = peer.get('latency', '-') or '-'
                    if lat != '-':
                        try:
                            lat_val = float(lat.replace('ms', '').strip())
                            if lat_val < 50:
                                lat = f"[green]{lat}[/]"
                            elif lat_val < 100:
                                lat = f"[yellow]{lat}[/]"
                            else:
                                lat = f"[red]{lat}[/]"
                        except:
                            pass
                    
                    # Color loss
                    loss = peer.get('loss', '-') or '-'
                    if loss != '-' and loss != '0.0%':
                        loss = f"[red]{loss}[/]"
                    elif loss == '0.0%':
                        loss = f"[green]{loss}[/]"
                    
                    peer_table.add_row(
                        peer.get('ipv4', '-'),
                        peer.get('hostname', '-'),
                        peer.get('cost', '-'),
                        lat,
                        loss,
                        peer.get('rx', '-') or '-',
                        peer.get('tx', '-') or '-',
                        peer.get('tunnel', '-') or '-'
                    )
                
                console.print(peer_table)


def prompt_easytier_side() -> Optional[str]:
    """Prompt for EasyTier tunnel side."""
    console.print("\n[bold white]Select Server Role:[/]")
    console.print("  [bold cyan][1][/] [green]IRAN[/]")
    console.print("  [bold cyan][2][/] [magenta]KHAREJ[/]")
    console.print("  [bold cyan][0][/] Cancel")
    
    choice = Prompt.ask("\n[bold cyan]Select role[/]", default="1")
    
    if choice == "1":
        return "IRAN"
    elif choice == "2":
        return "KHAREJ"
    return None


def prompt_easytier_config(config: EasyTierConfig, side: str, manager: EasyTierConfigManager = None) -> bool:
    """Prompt for EasyTier tunnel configuration."""
    from .easytier_manager import DEFAULT_LISTEN_PORT

    console.print(f"\n[bold white]Configure EasyTier Tunnel: {config.name}[/]")
    console.print(f"[bold]Role: [{'green' if side == 'IRAN' else 'magenta'}]{side}[/][/]")
    console.print("[dim]Enter configuration values. Press Enter for defaults.[/]\n")

    used = manager.get_used_values(exclude_tunnel=config.name) if manager else {}

    # Local IP (tunnel interface IP) - must be unique per tunnel on this machine
    if side == "IRAN":
        default_ip = "10.155.155.1"
    else:
        default_ip = "10.155.155.2"
    if manager:
        default_ip = manager.suggest_local_ip(side, exclude_tunnel=config.name)
    elif config.local_ip:
        default_ip = config.local_ip
    console.print("[dim]This is the IP for the tunnel interface (not your server's public IP)[/]")
    while True:
        local_ip = Prompt.ask("[bold yellow]Tunnel Interface IP[/]", default=default_ip)
        if used and local_ip.split('/')[0] in used.get("local_ips", set()):
            console.print(f"[red]IP {local_ip} is already used by another tunnel! Enter a different one.[/]")
            continue
        break
    config._config["local_ip"] = local_ip
    
    # Peer IP (remote server's PUBLIC IP)
    if side == "IRAN":
        console.print("\n[dim]Enter the PUBLIC IP of the Kharej server[/]")
        peer_label = "[bold cyan]Kharej Server Public IP[/]"
    else:
        console.print("\n[dim]Enter the PUBLIC IP of the Iran server[/]")
        peer_label = "[bold cyan]Iran Server Public IP[/]"
    
    peer_ip = Prompt.ask(peer_label)
    if not peer_ip:
        console.print("[red]Peer IP is required![/]")
        return False
    config._config["peer_ip"] = peer_ip
    
    # Port - must be unique per tunnel on this machine
    console.print("\n[dim]Port for EasyTier mesh (same on both sides of a pair, unique per tunnel on this server)[/]")
    default_port = str(getattr(config, "port", None) or DEFAULT_LISTEN_PORT)
    if manager:
        default_port = str(manager.suggest_listen_port(exclude_tunnel=config.name))
    while True:
        port_str = Prompt.ask("[bold yellow]Port[/]", default=default_port)
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                console.print("[red]Port must be between 1 and 65535[/]")
                continue
            if used and port in used.get("listen_ports", set()):
                console.print(f"[red]Port {port} is already used by another tunnel! Enter a different one.[/]")
                continue
            config._config["port"] = port
            break
        except ValueError:
            console.print("[red]Invalid port number[/]")
            return False

    # Network secret FIRST: the mesh network name is auto-derived from it,
    # so both servers always land in the same mesh.
    console.print("\n[dim]Shared secret for the mesh network (must match on all nodes)[/]")
    secret = Prompt.ask("[bold yellow]Network Secret[/]", default="vortexl2")
    config._config["network_secret"] = secret

    # Mesh network name - auto from secret (recommended) or custom.
    # Custom value MUST be identical on both servers of the pair.
    from .easytier_manager import derive_network_name
    auto_net = derive_network_name(secret)
    console.print(f"\n[dim]Mesh network name (auto from secret: [green]{auto_net}[/])[/]")
    custom_net = Prompt.ask("[bold yellow]Network Name (Enter=auto)[/]", default="")
    if custom_net.strip():
        config._config["network_name"] = custom_net.strip()
        console.print("[yellow]⚠ Custom name must be IDENTICAL on both servers, or peering will fail![/]")
    else:
        config._config["network_name"] = None
        console.print(f"[green]✓ Auto network name: {auto_net}[/]")

    # Hostname - defaults to tunnel name so multiple tunnels stay unique
    console.print("\n[dim]Hostname for this node (unique per tunnel recommended)[/]")
    default_hostname = config._config.get("hostname") or config.name
    hostname = Prompt.ask("[bold yellow]Hostname[/]", default=default_hostname)
    config._config["hostname"] = hostname

    # Performance tuning
    console.print("\n[dim]Performance: latency-first routing + compression + KCP (recommended ON)[/]")
    perf = Prompt.ask("[bold yellow]Enable performance tuning?[/] (yes/no)", default="yes")
    enable_perf = perf.strip().lower() in ("yes", "y", "1", "true")
    config._config["latency_first"] = enable_perf
    config._config["compression"] = "zstd" if enable_perf else "none"
    config._config["enable_kcp"] = enable_perf
    config._config["mtu"] = 1380
    
    # Remote forward IP (for port forwarding, IRAN only)
    if side == "IRAN":
        console.print("\n[dim]IP to forward ports to (usually the Kharej tunnel IP)[/]")
        remote_forward = Prompt.ask("[bold yellow]Remote Forward IP[/]", default="10.155.155.2")
        config._config["remote_forward_ip"] = remote_forward
    else:
        config._config["remote_forward_ip"] = "10.155.155.1"
    
    console.print("\n[green]✓ Configuration complete![/]")
    return True


def prompt_select_easytier_tunnel(manager: EasyTierConfigManager) -> Optional[str]:
    """Prompt to select an EasyTier tunnel."""
    tunnels = manager.list_tunnels()
    
    if not tunnels:
        console.print("[yellow]No EasyTier tunnels available.[/]")
        return None
    
    console.print("\n[bold white]Available Tunnels:[/]")
    for i, name in enumerate(tunnels, 1):
        console.print(f"  [bold cyan][{i}][/] {name}")
    console.print(f"  [bold cyan][0][/] Cancel")
    
    choice = Prompt.ask("\n[bold cyan]Select tunnel[/]", default="0")
    
    try:
        idx = int(choice)
        if idx == 0:
            return None
        if 1 <= idx <= len(tunnels):
            return tunnels[idx - 1]
    except ValueError:
        if choice in tunnels:
            return choice
    
    console.print("[red]Invalid selection[/]")
    return None


def prompt_tunnel_name() -> Optional[str]:
    """Prompt for tunnel name."""
    console.print("\n[dim]Enter a unique name for the tunnel (alphanumeric and dashes only)[/]")
    name = Prompt.ask("[bold magenta]Tunnel Name[/]", default="tunnel1")
    
    # Sanitize
    name = "".join(c if c.isalnum() or c == "-" else "-" for c in name.lower())
    return name if name else None
