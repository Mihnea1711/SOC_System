import requests
import time
import argparse
import random

# A list of normal-looking paths that a regular user might visit
# We only use paths that actually exist on our default Nginx server 
# so we don't generate 404 errors (which the ML model would flag as anomalies).
NORMAL_PATHS = [
    "/",
    "/index.html",
    "/search",
    "/download",
    "/about",
    "/contact"
]

# Normal-looking User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
]

def send_normal_request(base_url, spoof_ip=None):
    """Sends a single normal-looking GET request."""
    path = random.choice(NORMAL_PATHS)
    target_url = f"{base_url.rstrip('/')}{path}"
    
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    if spoof_ip:
        headers['X-Forwarded-For'] = spoof_ip
        
    try:
        # We expect 200s for most of these since we added mock endpoints to Nginx.
        # This gives the ML model a baseline of normal traffic with 0 errors.
        response = requests.get(target_url, headers=headers, timeout=5)
        print(f"[NORMAL] GET {path} | Status: {response.status_code} | IP: {spoof_ip or 'Local'}")
    except requests.exceptions.RequestException as e:
        print(f"[NORMAL] Request failed: {e}")

def generate_normal_traffic(base_url, count, delay_min, delay_max, spoof_ips=None):
    """Generates a steady stream of normal traffic."""
    print(f"Starting Normal Traffic Generation against {base_url}")
    print(f"Total Requests to send: {count}")
    print(f"Delay between requests: {delay_min}s - {delay_max}s")
    print("-" * 50)
    
    for _ in range(count):
        # Pick a random IP if a list was provided
        ip = random.choice(spoof_ips) if spoof_ips else None
        
        send_normal_request(base_url, ip)
        
        # Sleep for a random amount of time to simulate human browsing
        sleep_time = random.uniform(delay_min, delay_max)
        time.sleep(sleep_time)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Normal HTTP Traffic for ML Warmup")
    parser.add_argument("--target", type=str, default="http://localhost:8080", help="Base Target URL")
    parser.add_argument("--count", type=int, default=150, help="Number of requests to send (should be > warmup_observations)")
    parser.add_argument("--delay_min", type=float, default=0.5, help="Minimum delay between requests (seconds)")
    parser.add_argument("--delay_max", type=float, default=2.0, help="Maximum delay between requests (seconds)")
    parser.add_argument("--spoof_ips", type=str, default="192.168.1.10,192.168.1.11,192.168.1.12", help="Comma-separated list of normal IPs to spoof")
    
    args = parser.parse_args()
    
    ip_list = [ip.strip() for ip in args.spoof_ips.split(",")] if args.spoof_ips else None
    
    generate_normal_traffic(args.target, args.count, args.delay_min, args.delay_max, ip_list)
    
    print("-" * 50)
    print("Warmup complete! The ML model should now have a baseline of normal traffic.")