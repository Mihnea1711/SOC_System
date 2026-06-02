import argparse
import time
import paramiko
import logging

# Disable paramiko logging to keep output clean
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

def run_compromise(target_ip: str, target_port: int, username: str, correct_password: str, failures: int, delay: float):
    print(f"[*] Starting SSH Compromise Scenario against {target_ip}:{target_port} for user '{username}'")
    print(f"[*] Will simulate {failures} failed attempts followed by a successful login.\n")

    # 1. Simulate Failed Attempts
    for i in range(1, failures + 1):
        wrong_password = f"wrongpass{i}"
        print(f"[{i}/{failures}] Attempting incorrect password: {wrong_password}")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(hostname=target_ip, port=target_port, username=username, password=wrong_password, timeout=5, banner_timeout=5)
            client.close()
        except paramiko.AuthenticationException:
            # Expected
            pass
        except Exception as e:
            print(f"[-] Connection error: {e}")
        finally:
            client.close()

        if delay > 0:
            time.sleep(delay)

    # 2. Simulate Successful Login
    print(f"\n[*] Executing successful login with correct password: {correct_password}")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=target_ip, port=target_port, username=username, password=correct_password, timeout=5, banner_timeout=5)
        print(f"[+] SUCCESS! Logged in as {username}:{correct_password}")
        
        # Optionally run a quick command to prove we are in
        stdin, stdout, stderr = client.exec_command("whoami")
        print(f"[+] Executed 'whoami' on server. Result: {stdout.read().decode().strip()}")
        
    except Exception as e:
        print(f"[-] Failed to login with correct credentials: {e}")
    finally:
        client.close()

    print("\n[*] Scenario completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSH Compromise Scenario Generator")
    parser.add_argument("--target", required=True, help="Target IP address")
    parser.add_argument("--port", type=int, default=2222, help="Target SSH port (default: 2222)")
    parser.add_argument("--user", required=True, help="Username to target")
    parser.add_argument("--password", required=True, help="The correct password to finally login with")
    parser.add_argument("--failures", type=int, default=6, help="Number of failed attempts before success (default: 6)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between attempts in seconds (default: 0.5)")

    args = parser.parse_args()
    
    run_compromise(args.target, args.port, args.user, args.password, args.failures, args.delay)
