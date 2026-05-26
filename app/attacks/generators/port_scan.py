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

def simulate_port_scan(target_ip, start_port, end_port, threads, timeout):
    """Simulates a rapid TCP SYN/Connect scan across a range of ports."""
    print(f"Starting Port Scan Simulation against {target_ip}")
    print(f"Scanning ports {start_port} to {end_port}...")
    print(f"Threads: {threads}")
    print("-" * 50)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to scan ports concurrently
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for port in range(start_port, end_port + 1):
            executor.submit(scan_port, target_ip, port, timeout)
            
    elapsed = time.time() - start_time
    print("-" * 50)
    scanned_count = end_port - start_port + 1
    print(f"Simulation complete. Scanned {scanned_count} ports in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate TCP Port Scan (Reconnaissance)")
    parser.add_argument("--target", type=str, default="127.0.0.1", help="Target IP address (e.g., 127.0.0.1 for localhost mapped ports, or the container IP)")
    parser.add_argument("--start", type=int, default=1, help="Start port")
    parser.add_argument("--end", type=int, default=1000, help="End port")
    parser.add_argument("--threads", type=int, default=50, help="Number of concurrent threads")
    parser.add_argument("--timeout", type=float, default=0.5, help="Socket timeout in seconds")
    
    args = parser.parse_args()
    
    simulate_port_scan(args.target, args.start, args.end, args.threads, args.timeout)