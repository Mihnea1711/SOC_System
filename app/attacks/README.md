# SOC Attack Simulators

This directory contains the tools necessary to generate synthetic traffic and simulate cyber attacks against the monitored environment. This is crucial for testing the Detection Engine and training the Machine Learning model.

## Directory Structure

The simulation framework is divided into three parts:

1. **Generators (`generators/`):** Python scripts that execute specific types of network traffic or attacks (e.g., `sqli.py`. `xss.py`, `web_traffic.py`, `brute_force.py`, `dns_tunneling.py`, ...).
2. **Scenarios (`scenarios/`):** YAML files that define a sequence of actions, specifying which generator to run, with what arguments, and for how long.
3. **Scenario Runner (`scenario_runner.py`):** The orchestrator script that reads a YAML scenario and executes the defined steps.

## The Scenario Runner (`scenario_runner.py`)

The Scenario Runner is a lightweight orchestration tool. Instead of manually running multiple Python scripts with different arguments, you define the entire attack sequence in a single YAML file.

### How it works:
1. It parses the provided YAML file.
2. It iterates through the `steps` defined in the scenario.
3. For each step, it uses Python's `subprocess` module to execute the specified generator script.
4. It streams the output of the generator to the console in real-time.
5. It waits for the specified `delay_after` before moving to the next step.

### Usage:
```bash
python scenario_runner.py scenarios/scenario_name.yaml
```

## How to Run

1.  **Activate the Virtual Environment:**
    Ensure you are in the `app/attacks` directory and have activated the virtual environment where the depen    dencies (`requests`, `PyYAML`) are installed.

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
   
## How to Create a New Scenario

Scenarios are defined in YAML format. To create a new scenario, create a new `.yaml` file in the `scenarios/` directory.

### Scenario Structure:
```yaml
name: "Name of your scenario"
description: "What this scenario is trying to achieve"
steps:
  - name: "Step 1: Description of the step"
    script: "generators/name_of_script.py"
    args:
      --arg1: "value1"
      --arg2: "value2"
    delay_after: 5  # Seconds to wait before the next step

  - name: "Step 2: Description of the next step"
    script: "generators/another_scrip t.py"
    args:
      --target: "http://localhost:8080/login"
    delay_after: 0
```

---

## How to Create a New Attack Generator

If you want to simulate a new type of attack (e.g., Command Injection), you need to create a new generator script.

1. **Create the script:** Create a new Python file in the `generators/` directory (e.g., `generators/cmd_injection.py`).
2. **Use `argparse`:** Your script MUST use Python's `argparse` module to accept configuration from the command line. This is how the `scenario_runner.py` passes the `args` defined in the YAML file to your script.
3. **Generate Traffic:** Use python libraries to send requests to the target application.

---

## Included Generators

- **`warmup.py`**: Generates normal, benign HTTP GET requests to simulate legitimate user activity. Used to "warm up" the ML model so it learns what normal looks like.
- **`http_bruteforce.py`**: Simulates a high-volume credential stuffing attack against a web login endpoint.
- **`sqli_attack.py`**: Sends HTTP requests containing common SQLi payloads in the URL parameters.
- **`xss_attack.py`**: Sends HTTP requests containing Cross-Site Scripting payloads.
- **`path_traversal.py`**: Sends HTTP requests attempting to access restricted files (e.g., `../../../etc/passwd`).
- **`port_scan.py`**: Simulates a network reconnaissance scan across multiple ports to trigger threshold-based alerts.
- **`ssh_compromise.py`**: Simulates an SSH brute-force attack against the monitored SSH server.
- **`mysql_exfiltration.py`**: Simulates a database attack by connecting to MySQL and executing large data extraction queries.
- **`dns_tunneling.py`**: Simulates data exfiltration by hex-encoding dummy sensitive data and sending it as long subdomains in DNS queries to the monitored DNS server.