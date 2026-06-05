import os
import json
import docker
from confluent_kafka import Consumer, KafkaError
from utils.logger import logger

# --- Configuration Constants ---
KAFKA_GROUP_ID = "incident-responder-group"
NGINX_BLOCKLIST_PATH = "/etc/nginx/conf.d/shared/blocklist.conf"
NGINX_CONTAINER_NAME = "nginx_server"
MONITORED_NETWORK_NAME = "monitored_net"

# Safe list of container names that should NEVER be isolated
SAFE_CONTAINERS = [
    "kafka", 
    "elasticsearch", 
    "kibana", 
    "detection_engine", 
    "incident_response"
]

# Rule mappings for Response Strategies
EXTERNAL_ATTACK_RULES = [
    "SQL Injection Detected", 
    "Cross-Site Scripting (XSS) Detected", 
    "Path Traversal Detected",
    "Failed Web Login Brute Force",
    "SSH Brute Force Detected"
]

COMPROMISED_TARGET_RULES = [
    "Malicious MySQL Query (Data Exfiltration)",
    "Suspicious MySQL Query (Unbounded SELECT)"
]

COMPROMISED_SOURCE_RULES = [
    "Suspicious DNS Query (Potential Tunneling)"
]

CRITICAL_BREACH_RULES = [
    "Successful Web Login After Brute Force (Compromised Account)",
    "Successful SSH Login After Brute Force (Compromised Account)"
]
# -------------------------------

class IncidentResponder:
    def __init__(self):
        self.kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.alert_topics = ["alerts.signatures", "alerts.anomalies"]
        
        # Initialize Docker client (uses the mounted /var/run/docker.sock)
        try:
            self.docker_client = docker.from_env()
            logger.info("Successfully connected to Docker daemon.")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise
        
        # Keep track of blocked IPs to avoid duplicate entries
        self.blocked_ips = set()
        self._load_existing_blocklist()

    def _load_existing_blocklist(self):
        """Loads already blocked IPs from the file if it exists."""
        if os.path.exists(NGINX_BLOCKLIST_PATH):
            try:
                with open(NGINX_BLOCKLIST_PATH, 'r') as f:
                    for line in f:
                        if line.startswith("deny "):
                            ip = line.split(" ")[1].strip(";\n")
                            self.blocked_ips.add(ip)
                logger.info(f"Loaded {len(self.blocked_ips)} existing IPs from blocklist.")
            except Exception as e:
                logger.error(f"Error loading blocklist: {e}")

    def run(self):
        """Starts the Kafka consumer loop."""
        logger.info(f"Connecting to Kafka at {self.kafka_bootstrap}...")
        try:
            consumer_config = {
                'bootstrap.servers': self.kafka_bootstrap,
                'group.id': KAFKA_GROUP_ID,
                'auto.offset.reset': 'latest'
            }
            consumer = Consumer(consumer_config)
            consumer.subscribe(self.alert_topics)
            
            logger.info(f"Listening for alerts on topics: {self.alert_topics}")
            
            while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        break
                
                try:
                    alert = json.loads(msg.value().decode('utf-8'))
                    self.process_alert(alert)
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from Kafka message")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            if 'consumer' in locals():
                consumer.close()

    def process_alert(self, alert: dict):
        """Decision engine: Determines which action to take based on the alert."""
        rule_name = alert.get("rule_name", "")
        severity = alert.get("severity", "LOW")
        source_ip = alert.get("source_ip")
        destination_ip = alert.get("destination_ip")
        
        if not source_ip:
            return

        logger.info(f"Received {severity} alert: '{rule_name}' from {source_ip} to {destination_ip}")

        # ML Anomalies (Determine action based on severity)
        if rule_name == "ML Anomaly Detected":
            self.strategy_1_nginx_block(source_ip)
            if severity == "HIGH":
                # For high severity anomalies, try to isolate the internal asset involved
                if source_ip and (source_ip.startswith("172.") or source_ip.startswith("192.168.")):
                    self.strategy_2_isolate_container(source_ip)
                if destination_ip and (destination_ip.startswith("172.") or destination_ip.startswith("192.168.")):
                    self.strategy_2_isolate_container(destination_ip)
            return

        # Signature Rule Routing
        if rule_name in CRITICAL_BREACH_RULES:
            # Scenarios 2 & 4: Block attacker, isolate compromised target
            self.strategy_1_nginx_block(source_ip)
            if destination_ip:
                self.strategy_2_isolate_container(destination_ip)
                
        elif rule_name in COMPROMISED_TARGET_RULES:
            # Scenario 5: Block attacker, isolate compromised database
            self.strategy_1_nginx_block(source_ip)
            if destination_ip:
                self.strategy_2_isolate_container(destination_ip)
                
        elif rule_name in COMPROMISED_SOURCE_RULES:
            # Scenario 6: Isolate the container making the outbound tunneling requests
            self.strategy_2_isolate_container(source_ip)
            
        elif rule_name in EXTERNAL_ATTACK_RULES:
            # Scenarios 1 & 3: Just block the external attacker
            self.strategy_1_nginx_block(source_ip)

    def strategy_1_nginx_block(self, ip_address: str):
        """Appends the IP to the Nginx blocklist and reloads Nginx."""
        if ip_address in self.blocked_ips:
            logger.debug(f"IP {ip_address} is already blocked. Skipping.")
            return

        # Don't block our own Docker gateway or internal network
        if ip_address.startswith("172.") or ip_address.startswith("192.168.") or ip_address == "127.0.0.1":
            # logger.warning(f"Refusing to block internal IP: {ip_address} at Nginx level.")
            return

        # Handle spoofed IPs from our attack scenarios
        # If the IP is from our spoofed ranges (e.g., 103.x, 45.x, 185.x), it won't actually
        # affect your real host machine's access, but it WILL successfully write to the blocklist.
        # This is perfect for demonstration purposes without locking you out of your own project!

        try:
            # 1. Write to shared volume
            with open(NGINX_BLOCKLIST_PATH, 'a') as f:
                f.write(f"deny {ip_address};\n")
            self.blocked_ips.add(ip_address)
            logger.info(f"[Strategy 1] Added {ip_address} to Nginx blocklist.")

            # 2. Reload Nginx via Docker API
            nginx_container = self._get_container_by_name(NGINX_CONTAINER_NAME)
            if nginx_container:
                exit_code, output = nginx_container.exec_run("nginx -s reload")
                if exit_code == 0:
                    logger.info("[Strategy 1] Successfully reloaded Nginx.")
                else:
                    logger.error(f"[Strategy 1] Failed to reload Nginx: {output.decode('utf-8')}")
            else:
                logger.error(f"[Strategy 1] Could not find Nginx container ('{NGINX_CONTAINER_NAME}').")

        except Exception as e:
            logger.error(f"[Strategy 1] Error blocking IP {ip_address}: {e}")

    def strategy_2_isolate_container(self, target_ip: str):
        """Finds the container with the given IP (or container name) and disconnects it from the monitored network."""
        try:
            # First, see if the target_ip is actually a container name (e.g. passed from Filebeat normalizer)
            target_container = self._get_container_by_name(target_ip) or None
            
            # If not found by name, search by IP
            if not target_container:
                for container in self.docker_client.containers.list():
                    networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
                    if MONITORED_NETWORK_NAME in networks:
                        ip = networks[MONITORED_NETWORK_NAME].get("IPAddress")
                        if ip == target_ip:
                            target_container = container
                            break
            
            if not target_container:
                # Only log error if it's an internal IP that SHOULD be a container
                if target_ip.startswith("172."):
                    logger.debug(f"[Strategy 2] Could not find a container with IP {target_ip} on network '{MONITORED_NETWORK_NAME}'. It may have already been isolated.")
                return

            # Prevent isolating critical infrastructure
            if target_container.name in SAFE_CONTAINERS:
                logger.warning(f"[Strategy 2] Refusing to isolate critical infrastructure container: {target_container.name}")
                return

            # 2. Disconnect from network
            logger.warning(f"[Strategy 2] ISOLATING CONTAINER: {target_container.name} (IP: {target_ip})")
            network = self.docker_client.networks.get(MONITORED_NETWORK_NAME)
            network.disconnect(target_container, force=True)
            logger.info(f"[Strategy 2] Successfully disconnected {target_container.name} from {MONITORED_NETWORK_NAME}.")

        except Exception as e:
            logger.error(f"[Strategy 2] Error isolating container for IP {target_ip}: {e}")

    def _get_container_by_name(self, name: str):
        """Helper to find a container object by its name."""
        try:
            return self.docker_client.containers.get(name)
        except docker.errors.NotFound:
            return None

if __name__ == "__main__":
    responder = IncidentResponder()
    responder.run()