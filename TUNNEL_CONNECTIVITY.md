# VortexL3 Tunnel Connectivity Troubleshooting Guide

## Common Issue: "Destination Host Unreachable" on Ping

### Problem
```bash
$ ping 10.30.30.2
PING 10.30.30.2 (10.30.30.2) 56(84) bytes of data.
From 10.30.30.1 icmp_seq=1 Destination Host Unreachable
```

This happens after tunnel is UP and IP is assigned, but ICMP packets can't be delivered.

---

## Root Causes & Solutions

### Cause 1: Reverse Path Filtering (rp_filter) Blocking Traffic
**Symptom:** One-way ping (you can ping remote, but remote can't ping you)

**Solution:**
```bash
# Disable rp_filter completely (most permissive)
sudo sysctl -w net.ipv4.conf.l2tpeth0.rp_filter=0

# Or use loose mode (2) - recommended
sudo sysctl -w net.ipv4.conf.l2tpeth0.rp_filter=2

# Make persistent
echo "net.ipv4.conf.l2tpeth0.rp_filter=2" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Cause 2: IP Forwarding Disabled
**Symptom:** Can't forward traffic through tunnel

**Solution:**
```bash
# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Make persistent
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Cause 3: Interface Not in Promiscuous Mode
**Symptom:** Interface is UP but not receiving all traffic

**Solution:**
```bash
# Set interface to promiscuous mode
sudo ip link set l2tpeth0 promisc on

# Verify
ip link show l2tpeth0
```

### Cause 4: ARP Not Enabled on Interface
**Symptom:** No ARP replies, neighbors can't find the interface

**Solution:**
```bash
# Enable ARP
sudo ip link set l2tpeth0 arp on

# Check ARP table
ip neigh show dev l2tpeth0

# Add static ARP entry if needed
sudo ip neigh add 10.30.30.2 dev l2tpeth0 lladdr aa:bb:cc:dd:ee:ff
```

---

## Diagnostic Commands

### 1. Check Tunnel Status
```bash
# List all L2TP tunnels
ip l2tp show tunnel

# Expected output:
# Tunnel 1000, encap IP
#   From 203.0.113.1 to 203.0.113.2
#   Carrier up, 1 session(s)

# List sessions
ip l2tp show session

# Expected output:
# Session 10 in tunnel 1000
#   Peer session 20
#   PPPIFL ppp0 (up)
```

### 2. Check Interface Status
```bash
# Show interface details
ip addr show l2tpeth0

# Expected output:
# inet 10.30.30.1/30 scope global l2tpeth0

# Check MTU
ip link show l2tpeth0 | grep mtu

# Expected: mtu 1280 or 1500
```

### 3. Check Routing
```bash
# Show routes on tunnel interface
ip route show dev l2tpeth0

# Show default routes
ip route show

# Add route if missing (example)
sudo ip route add 10.30.30.0/30 dev l2tpeth0
```

### 4. Check ARP Table
```bash
# Show ARP entries for interface
ip neigh show dev l2tpeth0

# Expected: 10.30.30.2 dev l2tpeth0 lladdr aa:bb:cc:dd:ee:ff

# If empty, try to ping remote and check again
ping -c 1 10.30.30.2
ip neigh show dev l2tpeth0
```

### 5. Check rp_filter Settings
```bash
# Show rp_filter for interface
cat /proc/sys/net/ipv4/conf/l2tpeth0/rp_filter

# Show global setting
cat /proc/sys/net/ipv4/conf/default/rp_filter

# All interfaces
cat /proc/sys/net/ipv4/conf/all/rp_filter
```

### 6. Test with tcpdump
```bash
# Monitor interface in another terminal
sudo tcpdump -i l2tpeth0 -n icmp

# In another terminal, ping
ping -c 1 10.30.30.2

# You should see ICMP packets in first terminal
```

### 7. Check IP Forwarding
```bash
# Show current setting
cat /proc/sys/net/ipv4/ip_forward

# 0 = disabled, 1 = enabled

# Check with sysctl
sysctl net.ipv4.ip_forward
```

---

## Complete Tunnel Verification Script

```bash
#!/bin/bash

echo "=== VortexL3 Tunnel Connectivity Check ==="

# Check tunnel exists
echo -e "\n[1] Tunnel Status:"
ip l2tp show tunnel | head -5

# Check interface
echo -e "\n[2] Interface Status:"
ip link show l2tpeth0

# Check IP
echo -e "\n[3] IP Address:"
ip addr show l2tpeth0

# Check rp_filter
echo -e "\n[4] Reverse Path Filter:"
echo "l2tpeth0: $(cat /proc/sys/net/ipv4/conf/l2tpeth0/rp_filter)"

# Check IP forwarding
echo -e "\n[5] IP Forwarding:"
cat /proc/sys/net/ipv4/ip_forward

# Check ARP
echo -e "\n[6] ARP Table:"
ip neigh show dev l2tpeth0

# Check routes
echo -e "\n[7] Routes on Interface:"
ip route show dev l2tpeth0

# Try ping
echo -e "\n[8] Ping Test (1 packet):"
ping -c 1 -W 2 10.30.30.2 && echo "SUCCESS" || echo "FAILED"
```

---

## Manual Fix (All-in-One)

```bash
#!/bin/bash
IFNAME="l2tpeth0"
REMOTE_IP="10.30.30.2"

echo "Fixing tunnel connectivity for $IFNAME..."

# 1. Disable rp_filter
sudo sysctl -w net.ipv4.conf.$IFNAME.rp_filter=2
sudo sysctl -w net.ipv4.conf.all.rp_filter=2
echo "✓ Reverse path filter configured"

# 2. Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
echo "✓ IP forwarding enabled"

# 3. Ensure interface is up
sudo ip link set $IFNAME up
echo "✓ Interface is UP"

# 4. Enable ARP
sudo ip link set $IFNAME arp on
echo "✓ ARP enabled"

# 5. Add route if needed
if ! ip route show | grep -q "$IFNAME"; then
    sudo ip route add 10.30.30.0/30 dev $IFNAME
    echo "✓ Route added"
fi

# 6. Make settings persistent
cat <<EOF | sudo tee -a /etc/sysctl.conf
# VortexL3 Tunnel Settings
net.ipv4.conf.$IFNAME.rp_filter=2
net.ipv4.conf.all.rp_filter=2
net.ipv4.ip_forward=1
EOF

sudo sysctl -p
echo "✓ Settings saved to /etc/sysctl.conf"

# 7. Test
echo -e "\nTesting connectivity..."
ping -c 1 -W 2 $REMOTE_IP && echo "✓ SUCCESS" || echo "✗ FAILED"
```

---

## Prevention: VortexL3 Integration

The latest VortexL3 update includes automatic routing configuration in `tunnel.py`:

- **Automatically disables rp_filter** during tunnel setup
- **Enables IP forwarding** for TCP/IP stack
- **Sets interface to promiscuous mode** for traffic capture
- **Enables ARP** for neighbor discovery

This is applied in the `configure_routing()` method during `full_setup()`.

---

## Still Having Issues?

### Check these in order:
1. **Is tunnel interface UP?** → `ip link show l2tpeth0`
2. **Does it have an IP?** → `ip addr show l2tpeth0`
3. **Is rp_filter = 0 or 2?** → `cat /proc/sys/net/ipv4/conf/l2tpeth0/rp_filter`
4. **Is IP forwarding on?** → `cat /proc/sys/net/ipv4/ip_forward`
5. **Can you see ICMP packets?** → `sudo tcpdump -i l2tpeth0 icmp`

### Advanced Debugging:
```bash
# Enable kernel logging
sudo sysctl -w kernel.printk="7 4 1 7"

# Monitor kernel messages
sudo journalctl -f

# Check for dropped packets
netstat -s | grep -i icmp

# Monitor interface stats
watch -n 1 'ip -s link show l2tpeth0'
```

---

## References
- [IPv4 Routing Documentation](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html)
- [Reverse Path Filtering](https://en.wikipedia.org/wiki/Anti-spoofing#Reverse_path_filtering)
- [L2TP Protocol](https://tools.ietf.org/html/rfc2661)
