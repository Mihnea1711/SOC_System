# Automated Incident Response Engine

The Incident Response (IR) Engine is a Python microservice that acts as the "muscle" of the SOC. While the Detection Engine passively monitors traffic and generates alerts, the IR Engine actively consumes those alerts and takes physical actions to stop attacks and contain breaches in real-time.

## Architecture

The IR Engine runs in its own Docker container (`incident_response`) and is connected to the central Kafka broker.

Crucially, this container is granted elevated privileges:
1. **Docker Socket Access:** It mounts the host's `/var/run/docker.sock`, allowing the Python script to use the Docker API to inspect, modify, and disconnect other containers on the host.
2. **Shared Volumes:** It shares a volume (`shared_nginx_config`) with the `nginx_server` (Nginx) container, allowing it to dynamically write firewall rules that Nginx immediately applies.

## The Event Loop

1. **Listen:** The engine subscribes to the `alerts.signatures` and `alerts.anomalies` Kafka topics.
2. **Parse:** When an alert is received, it extracts the `rule_name`, `severity`, and the `source_ip` (the attacker).
3. **Decide:** It uses a predefined mapping of rules (configured at the top of `incident_responder.py`) to determine the appropriate response strategy.
4. **Execute:** It executes one or both of the response strategies below.

---

## Response Strategies

### Strategy 1: Application-Layer Block (Nginx Dynamic Deny)
**Used for:** External attacks (SQLi, XSS, Brute Force, Path Traversal).

When an external attacker is detected, the goal is to block them at the edge without disrupting the service for legitimate users.
- The IR Engine appends `deny <attacker_ip>;` to the `blocklist.conf` file in the shared volume.
- It then uses the Docker API to execute `nginx -s reload` inside the Nginx container.
- **Result:** The attacker instantly receives `403 Forbidden` errors for all subsequent requests, while normal traffic continues uninterrupted.

### Strategy 2: Containment Layer (Docker Network Isolation)
**Used for:** Internal compromise (Data Exfiltration, DNS Tunneling, Suspicious MySQL Queries).

When an alert indicates that a container itself is compromised or is being used to exfiltrate data, blocking the external IP is insufficient (the attacker might have a backdoor or multiple IPs). The asset must be quarantined.
- The IR Engine uses the Docker API to scan the `monitored_net` network.
- It finds the specific container matching the compromised IP address.
- It forcefully executes a `network.disconnect()` on that container.
- **Result:** The compromised container is instantly severed from the network. It can no longer communicate with the internet or other internal containers, stopping the exfiltration dead in its tracks. The container is left running in memory so forensic analysts can investigate it later.

### Strategy 3: The "Nuclear" Option (Critical Breach)
**Used for:** High-severity ML Anomalies, Successful Logins after Brute Force.

If a critical breach is detected, the IR Engine executes **both** strategies simultaneously:
1. It blocks the attacker's IP at the Nginx edge (protecting the front door).
2. It isolates the targeted container (severing existing connections and protecting internal assets).

---

## Configuration

You can easily modify how the IR Engine reacts to different threats by editing the lists at the top of `incident_responder.py`:

```python
EXTERNAL_ATTACK_RULES = [ ... ]     # Triggers Strategy 1
INTERNAL_COMPROMISE_RULES = [ ... ] # Triggers Strategy 2
CRITICAL_BREACH_RULES = [ ... ]     # Triggers Both
```

## How to Test the Response Strategies

To verify that the Incident Responder is actively modifying the environment, you can run the attack scenarios and check the physical results.

### Testing Strategy 1: Nginx IP Blocking

**1. Trigger an External Attack:**
Run a scenario that uses HTTP attacks (which utilize spoofed IPs):
```bash
python app/attacks/scenario_runner.py app/attacks/scenarios/scenario_2_brute_xss.yaml
```

**2. Verify the Blocklist File:**
The IR Engine will extract the spoofed attacker IPs and write them to the shared volume. Verify this by reading the file inside the Nginx container:
```bash
docker exec nginx_server cat /etc/nginx/conf.d/shared/blocklist.conf
```
*Expected Output:* You should see lines like `deny 103.15.26.11;`

**3. Verify the 403 Forbidden Response:**
Because the attack used spoofed IPs, your real host machine is NOT blocked.
```bash
# This will succeed (200 OK or 404 Not Found)
curl -I http://localhost:8080/
```
To verify the block works, spoof your `curl` request to match the blocked attacker:
```bash
# This will be instantly dropped by Nginx (403 Forbidden)
curl -I -H "X-Forwarded-For: 45.133.1.22" http://localhost:8080/
```

**4. Clearing the blocklist**
To clear the blocklist, run
```bash
docker exec nginx_server sh -c '> /etc/nginx/conf.d/shared/blocklist.conf && nginx -s reload'
```

### Testing Strategy 2: Container Quarantine

**1. Trigger an Internal Compromise:**
Run a scenario that targets an internal service (like DNS Tunneling):
```bash
python app/attacks/scenario_runner.py app/attacks/scenarios/dns_tunneling.yaml
```
*Watch the IR logs: You should see it say `[Strategy 2] ISOLATING CONTAINER: dns_server`.*

**2. Verify the Network Disconnect:**
Check the network interfaces attached to the `dns_server` container:
```bash
docker inspect dns_server --format='{{json .NetworkSettings.Networks}}'
```
*Expected Output:* It should return `{}` (an empty JSON object). The container has been physically unplugged from the `monitored_net` virtual switch.

**3. Verify the Isolation:**
Try to make the DNS container talk to the outside world:
```bash
docker exec dns_server ping -c 2 8.8.8.8
```
*Expected Output:* `ping: connect: Network is unreachable`. The container is completely isolated. It is still running for forensic analysis, but it cannot send or receive any network traffic.

*(Note: To plug it back in, you can restart the container: `docker restart dns_server`)*