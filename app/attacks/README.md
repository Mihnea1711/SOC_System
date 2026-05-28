# SOC Attack Simulators

This directory contains the attack simulation framework for the Distributed Intrusion Detection and Response System. It is designed to generate realistic, multi-step attack traffic that will be captured by our collectors (Filebeat and Packetbeat), routed through Kafka, and ultimately analyzed by the Python Detection Engine.

## Architecture & Concept

The simulation framework is split into two main components: **Generators** and **Scenarios**.

### 1. Generators (`/generators`)
Generators are standalone Python scripts that perform a single, specific type of attack. They are the "primitives" or building blocks of our simulations.
*   `port_scan.py`: Simulates a rapid TCP SYN/Connect scan across a range of ports to trigger network anomalies.
*   `http_bruteforce.py`: Simulates rapid HTTP POST requests to a login endpoint, using a dictionary of passwords. It includes a `--success` flag that forces sequential execution of failed attempts, followed by a 3-second delay, and finally a successful login. This guarantees the correct event order for testing stateful "Compromised Account" detection rules.
*   `sqli_attack.py`: Injects common SQL Injection payloads into URL parameters.
*   `xss_attack.py`: Injects Cross-Site Scripting payloads into URL parameters.
*   `path_traversal.py`: Attempts to access restricted files (like `/etc/passwd`) using directory traversal payloads.

Each generator accepts command-line arguments (target IP, ports, delays, counts) so they can be easily customized or automated.

### 2. Scenarios (`/scenarios`)
Real-world attacks are rarely a single event; they are a sequence of actions. Scenarios are YAML files that orchestrate multiple generators in a specific order, with defined delays between them. This allows us to test the **correlation** capabilities of our Detection Engine.

*   `scenario_1_recon_brute.yaml`: Simulates an attacker scanning for open ports (Reconnaissance) and, upon finding a web server, launching a Brute Force attack. This tests the engine's ability to correlate network data (Packetbeat) with log data (Filebeat).
*   `scenario_2_brute_xss.yaml`: Simulates a Brute Force attack that eventually succeeds, immediately followed by an XSS injection. This tests the engine's stateful tracking (remembering the brute force) and logical progression (escalating the XSS severity because the account was just compromised).
*   `scenario_3_web_exfil.yaml`: Simulates a Path Traversal attack followed by an SQL Injection, representing an attacker trying multiple web vectors to exfiltrate data.

### 3. The Runner (`scenario_runner.py`)
The runner is the execution engine for the scenarios. It parses the YAML files, handles the timing (delays), and spawns the generator scripts as subprocesses with the correct arguments.

## How to Run

1.  **Activate the Virtual Environment:**
    Ensure you are in the `app/attacks` directory and have activated the virtual environment where the dependencies (`requests`, `PyYAML`) are installed.

2.  **Run a Scenario:**
    Use the `scenario_runner.py` script and pass the path to the YAML scenario you want to execute.
    ```bash
    python scenario_runner.py scenarios/scenario_1_recon_brute.yaml
    ```

## What Should Happen

When you run a scenario:
1.  The runner will print out the steps it is taking.
2.  The generator scripts will send network traffic (TCP connections, HTTP requests) to the target (usually `localhost` or the Nginx container).
3.  **Packetbeat** will capture the network flows (e.g., the port scan).
4.  **Filebeat** will capture the Nginx access/error logs (e.g., the 404s from the brute force, or the malicious URLs from SQLi).
5.  Both Beats will ship this data to **Kafka**.
6.  The **Detection Engine** will consume the data, route it, and evaluate it against its rules.
7.  If the engine successfully correlates the events as defined in the scenario, it will generate a high-severity alert and send it to **Elasticsearch** (for Kibana dashboards) and back to Kafka (for the Response Service).