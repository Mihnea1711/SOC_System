import yaml
import time
import subprocess
import argparse
import os

def run_scenario(scenario_file):
    """Parses a YAML scenario file and executes the steps."""
    if not os.path.exists(scenario_file):
        print(f"Error: Scenario file '{scenario_file}' not found.")
        return

    with open(scenario_file, 'r') as f:
        try:
            scenario = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return

    print(f"=== Starting Scenario: {scenario.get('name', 'Unnamed')} ===")
    print(f"Description: {scenario.get('description', 'No description provided.')}")
    print("=" * 50)

    steps = scenario.get('steps', [])
    if not steps:
        print("No steps found in the scenario.")
        return

    generators_dir = os.path.join(os.path.dirname(__file__), 'generators')

    for i, step in enumerate(steps):
        step_name = step.get('name', f"Step {i+1}")
        print(f"\n[+] Executing: {step_name}")

        if 'delay' in step:
            delay_seconds = step['delay']
            print(f"    Waiting for {delay_seconds} seconds...")
            time.sleep(delay_seconds)
            continue

        if 'generator' in step:
            generator_script = step['generator']
            script_path = os.path.join(generators_dir, generator_script)
            
            if not os.path.exists(script_path):
                print(f"    Error: Generator script '{generator_script}' not found in {generators_dir}")
                continue

            # Build the command
            cmd = ["python", script_path]
            args = step.get('args', {})
            
            for key, value in args.items():
                # Handle boolean flags (e.g. --success without a value) or specific formatting if needed
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"--{key}")
                        cmd.append("true")
                    else:
                        cmd.append(f"--{key}")
                        cmd.append("false")
                else:
                    cmd.append(f"--{key}")
                    cmd.append(str(value))

            print(f"    Running command: {' '.join(cmd)}")
            
            # Use subprocess.Popen instead of subprocess.run to stream output in real-time
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                print("    Output:")
                for line in process.stdout:
                    print(f"      {line.strip()}")
                
                process.wait()
                if process.returncode != 0:
                    print(f"    Error executing script. Return code: {process.returncode}")
            except Exception as e:
                print(f"    Unexpected error: {e}")

    print("\n" + "=" * 50)
    print(f"=== Scenario '{scenario.get('name', 'Unnamed')}' Complete ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Attack Scenario Runner")
    parser.add_argument("scenario", help="Path to the YAML scenario file to run")
    
    args = parser.parse_args()
    run_scenario(args.scenario)
