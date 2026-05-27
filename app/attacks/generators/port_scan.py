import socket
import time
import argparse
from concurrent.futures import ThreadPoolExecutor

def scan_port(target_ip, port, timeout):
    """Attempts to connect to a single TCP port."""
    try:
        # Create a TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Attempt connection
        result = sock.connect_ex((target_ip, port))
        
        if result == 0:
            print(f"[PORT SCAN] Port {port} is OPEN")
        # We don't print closed ports to avoid flooding the console,
        # but Packetbeat will still capture the SYN packets!
        
        sock.close()
    except Exception:
        pass

def simulate_port_scan(target_ip, ports_to_scan, threads, timeout):
    """Simulates a rapid TCP SYN/Connect scan across a list of ports."""
    print(f"Starting Port Scan Simulation against {target_ip}")
    print(f"Scanning {len(ports_to_scan)} ports...")
    print(f"Threads: {threads}")
    print("-" * 50)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to scan ports concurrently
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for port in ports_to_scan:
            executor.submit(scan_port, target_ip, port, timeout)
            
    elapsed = time.time() - start_time
    print("-" * 50)
    print(f"Simulation complete. Scanned {len(ports_to_scan)} ports in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate TCP Port Scan (Reconnaissance)")
    parser.add_argument("--target", type=str, default="127.0.0.1", help="Target IP address (e.g., 127.0.0.1 for localhost mapped ports, or the container IP)")
    parser.add_argument("--ports", type=str, default="", help="Comma-separated list of ports to scan")
    parser.add_argument("--start", type=int, default=1, help="Start port (if --ports is not used)")
    parser.add_argument("--end", type=int, default=1000, help="End port (if --ports is not used)")
    parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")
    parser.add_argument("--timeout", type=float, default=0.5, help="Socket timeout in seconds")
    
    args = parser.parse_args()
    
    if args.ports:
        ports_to_scan = [int(p.strip()) for p in args.ports.split(",")]
    else:
        ports_to_scan = list(range(args.start, args.end + 1))
        
    simulate_port_scan(args.target, ports_to_scan, args.threads, args.timeout)