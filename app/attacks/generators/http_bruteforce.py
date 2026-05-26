import requests
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor

def send_brute_force_request(target_url, username, password):
    """Sends a single login attempt."""
    try:
        # We simulate a POST request to a login endpoint
        login_url = f"{target_url}/login"
        data = {'username': username, 'password': password}
        
        # Using a suspicious User-Agent to trigger potential rules
        headers = {'User-Agent': 'Hydra/0.1 (Brute Force Tool)'}
        
        response = requests.post(login_url, data=data, headers=headers, timeout=5)
        
        # In a real app, 401/403 means failure, 200/302 means success.
        # Since Nginx doesn't have a /login endpoint by default, it will return 404.
        # Our detection engine will look for rapid 404s or 401s from the same IP.
        print(f"[BRUTE-FORCE] Tried {username}:{password} | Status: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"[BRUTE-FORCE] Request failed: {e}")

def simulate_brute_force(target_url, username, password_list, threads):
    """Simulates a rapid brute force attack using multiple threads."""
    print(f"Starting Brute Force Simulation against {target_url}/login")
    print(f"Target Username: {username}")
    print(f"Passwords to try: {len(password_list)}")
    print(f"Threads: {threads}")
    print("-" * 50)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to send requests concurrently (rapid fire)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for password in password_list:
            executor.submit(send_brute_force_request, target_url, username, password)
            
    elapsed = time.time() - start_time
    print("-" * 50)
    print(f"Simulation complete. Sent {len(password_list)} requests in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate HTTP Brute Force Attack")
    parser.add_argument("--target", type=str, default="http://localhost:8080", help="Target URL")
    parser.add_argument("--user", type=str, default="admin", help="Username to brute force")
    parser.add_argument("--count", type=int, default=100, help="Number of passwords to try")
    parser.add_argument("--threads", type=int, default=10, help="Number of concurrent threads")
    
    args = parser.parse_args()
    
    # Generate a dummy password list
    passwords = [f"password{i}" for i in range(args.count)]
    # Add some common passwords
    passwords.extend(["admin", "123456", "qwerty", "root"])
    
    simulate_brute_force(args.target, args.user, passwords, args.threads)