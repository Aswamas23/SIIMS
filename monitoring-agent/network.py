"""
Network status collection for SIIMS Monitoring Agent.
Uses subprocess ping for ICMP connectivity and psutil for interface details.
All functions return safe defaults on failure and never raise.
"""
import logging
import re
import subprocess
import sys
from urllib.parse import urlparse

import psutil

logger = logging.getLogger(__name__)


def _extract_hostname(url: str) -> str:
    """Extract the hostname from a URL string."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            return hostname
    except Exception:
        pass
    # Fallback: treat the whole string as a hostname if no scheme
    return url.split("/")[0].split(":")[0]


def parse_ping_output(stdout: str, platform: str = None) -> dict:
    """
    Parse ping command stdout to extract latency and packet loss.
    
    Supports Windows and Linux/macOS ping output formats.
    Returns dict with keys: latency_ms (float|None), packet_loss_percent (float|None).
    """
    if platform is None:
        platform = sys.platform

    latency_ms = None
    packet_loss_percent = None

    if not stdout:
        return {"latency_ms": None, "packet_loss_percent": None}

    if platform == "win32":
        # Windows: "Average = 12ms" or "Average = 12ms" (varies by locale)
        # Also handle: "Minimum = 10ms, Maximum = 15ms, Average = 12ms"
        avg_match = re.search(r"Average\s*=\s*(\d+)ms", stdout, re.IGNORECASE)
        if avg_match:
            try:
                latency_ms = float(avg_match.group(1))
            except ValueError:
                pass

        # Windows: "Lost = 2 (50% loss)"  or "(0% loss)"
        loss_match = re.search(r"\((\d+)%\s*loss\)", stdout, re.IGNORECASE)
        if loss_match:
            try:
                packet_loss_percent = float(loss_match.group(1))
            except ValueError:
                pass
    else:
        # Linux/macOS: "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.100 ms"
        rtt_match = re.search(
            r"rtt min/avg/max/m?dev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms",
            stdout, re.IGNORECASE
        )
        if rtt_match:
            try:
                latency_ms = float(rtt_match.group(1))
            except ValueError:
                pass

        # Linux/macOS: "2 packets transmitted, 2 received, 0% packet loss"
        loss_match = re.search(r"(\d+)%\s*packet loss", stdout, re.IGNORECASE)
        if loss_match:
            try:
                packet_loss_percent = float(loss_match.group(1))
            except ValueError:
                pass

    return {"latency_ms": latency_ms, "packet_loss_percent": packet_loss_percent}


def ping_host(hostname: str, count: int = 4) -> dict:
    """
    Ping a hostname and return connectivity metrics.
    
    Returns:
        dict with keys:
            is_online (bool), latency_ms (float|None), packet_loss_percent (float|None)
    """
    default = {"is_online": False, "latency_ms": None, "packet_loss_percent": None}

    if not hostname:
        return default

    try:
        if sys.platform == "win32":
            cmd = ["ping", "-n", str(count), "-w", "1000", hostname]
        else:
            cmd = ["ping", "-c", str(count), "-W", "1", hostname]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        stdout = result.stdout or ""
        parsed = parse_ping_output(stdout)

        # Online if the return code is 0 (all pings succeeded)
        # or if we got a valid average latency (some pings succeeded)
        is_online = result.returncode == 0 or parsed["latency_ms"] is not None

        return {
            "is_online": is_online,
            "latency_ms": parsed["latency_ms"],
            "packet_loss_percent": parsed["packet_loss_percent"],
        }

    except subprocess.TimeoutExpired:
        logger.warning("Ping timed out for host: %s", hostname)
        return default
    except FileNotFoundError:
        logger.warning("ping command not found")
        return default
    except Exception as e:
        logger.warning("Ping failed for %s: %s", hostname, e)
        return default


def get_interfaces() -> list[dict]:
    """
    Return network interface information using psutil.
    
    Returns:
        List of dicts with keys: name, is_up, speed_mbps, ip_addresses
    """
    interfaces = []
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for name, stat in stats.items():
            ip_addresses = []
            for addr in addrs.get(name, []):
                # AF_INET = IPv4, AF_INET6 = IPv6
                try:
                    import socket
                    if addr.family in (socket.AF_INET, socket.AF_INET6):
                        ip_addresses.append(addr.address)
                except Exception:
                    pass

            interfaces.append({
                "name": name,
                "is_up": stat.isup,
                "speed_mbps": stat.speed if stat.speed > 0 else None,
                "ip_addresses": ip_addresses,
            })

    except Exception as e:
        logger.warning("Could not collect network interface information: %s", e)

    return interfaces


def collect_network_status(server_url: str = "") -> dict:
    """
    Collect network status including server reachability and interface info.
    
    Args:
        server_url: The backend server URL to ping (hostname extracted automatically)
    
    Returns:
        dict with keys:
            is_online, latency_ms, packet_loss_percent,
            server_hostname, interfaces
    """
    result = {
        "is_online": False,
        "latency_ms": None,
        "packet_loss_percent": None,
        "server_hostname": None,
        "interfaces": [],
    }

    # Ping the backend server
    if server_url:
        hostname = _extract_hostname(server_url)
        result["server_hostname"] = hostname
        ping_result = ping_host(hostname)
        result["is_online"] = ping_result["is_online"]
        result["latency_ms"] = ping_result["latency_ms"]
        result["packet_loss_percent"] = ping_result["packet_loss_percent"]
    else:
        logger.warning("No server_url provided; skipping ping check")

    # Collect interface information
    result["interfaces"] = get_interfaces()

    return result


if __name__ == "__main__":
    import pprint
    logging.basicConfig(level=logging.INFO)
    print("Collecting network status...")
    status = collect_network_status("http://localhost:8000")
    pprint.pprint(status)
