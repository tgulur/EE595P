import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import itertools

def control_c(signum, frame):
    print("\nExiting gracefully...")
    sys.exit(1)

signal.signal(signal.SIGINT, control_c)

def main():
    # Define the directory for results
    dirname = '11be-mlo'
    ns3_path = os.path.join('../../../../ns3')  # Adjust this path based on your directory structure

    # Check if the ns3 executable exists
    if not os.path.exists(ns3_path):
        print(f"Please ensure the ns3 directory exists at: {ns3_path}")
        sys.exit(1)

    # Create a results directory with a timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    print(f"Results will be stored in: {results_dir}")

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Define the payload sizes and mldProbLink1 values to test
    payload_sizes = [512, 1024, 2048, 4096]  # in Bytes
    mldProbLink1_values = [0.2, 0.4, 0.6, 0.8]  # Probabilities for Link1

    # Fixed Parameters
    rng_run = 1                     # Single RNG run
    mldPerNodeLambda = 0.0001       # Fixed traffic arrival rate
    n_sta = 10                      # Fixed number of STAs
    simTime = 20                    # Simulation time in seconds

    # Initialize dictionaries to store results
    results = {
        'payload_size': [],
        'mldProbLink1': [],
        'throughput_total': [],
        'queue_delay_total': [],
        'access_delay_total': [],
        'e2e_delay_total': []
    }

    # Generate all combinations of payload_sizes and mldProbLink1_values
    experiment_combinations = list(itertools.product(payload_sizes, mldProbLink1_values))

    # Run simulations for each combination
    for payload_size, mldProbLink1 in experiment_combinations:
        print(f"\nRunning simulation for payloadSize={payload_size} Bytes, mldProbLink1={mldProbLink1}...")
        cmd = (
            f"./ns3 run 'single-bss-mld "
            f"--rngRun={rng_run} "
            f"--nMldSta={n_sta} "
            f"--mldPerNodeLambda={mldPerNodeLambda} "
            f"--mldProbLink1={mldProbLink1} "
            f"--payloadSize={payload_size} "
            f"--simulationTime={simTime}'"
        )
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for payloadSize={payload_size} Bytes, mldProbLink1={mldProbLink1}. Check NS-3 logs for details.")
            continue

        # Define a unique filename for the current run's data
        data_filename = f"wifi-mld_payload_{payload_size}_mldProbLink1_{mldProbLink1}.dat"
        destination_path = os.path.join(results_dir, data_filename)

        # Move the 'wifi-mld.dat' to the results directory with the unique filename
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation run for payloadSize={payload_size} Bytes, mldProbLink1={mldProbLink1}")
            continue

        # Parse results from the moved data file
        parsed_data = parse_results(destination_path)
        if parsed_data:
            # Aggregate the metrics
            results['payload_size'].append(payload_size)
            results['mldProbLink1'].append(mldProbLink1)
            results['throughput_total'].append(parsed_data['throughput_total'])
            results['queue_delay_total'].append(parsed_data['queue_delay_total'])
            results['access_delay_total'].append(parsed_data['access_delay_total'])
            results['e2e_delay_total'].append(parsed_data['e2e_delay_total'])
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots
    plot_results(results_dir, results)

    # Final cleanup: Move any remaining 'wifi-mld.dat' if exists
    move_file('wifi-mld.dat', results_dir)

    # Save git commit info
    save_git_commit_info(results_dir)

def check_and_remove(filename):
    if os.path.exists(filename):
        response = input(f"Remove existing file '{filename}'? [Yes/No]: ").strip().lower()
        if response == 'yes':
            os.remove(filename)
            print(f"Removed '{filename}'")
        else:
            print("Exiting to prevent data contamination.")
            sys.exit(1)

def parse_results(filepath):
    metrics = {
        'throughput_total': 0.0,
        'queue_delay_total': 0.0,
        'access_delay_total': 0.0,
        'e2e_delay_total': 0.0
    }

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            valid_lines = 0
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 21:  # Adjust based on actual number of tokens in your .dat file
                    print(f"Skipping incomplete line in {filepath}: {line.strip()}")
                    continue
                try:
                    metrics['throughput_total'] += float(tokens[5])
                    metrics['queue_delay_total'] += float(tokens[8])
                    metrics['access_delay_total'] += float(tokens[11])
                    metrics['e2e_delay_total'] += float(tokens[14])
                    valid_lines += 1
                except ValueError as e:
                    print(f"Error parsing line in {filepath}: {line.strip()} - {e}")
                    continue

            if valid_lines > 0:
                for key in metrics:
                    metrics[key] /= valid_lines
            else:
                print(f"No valid data found in {filepath}.")
                return None

    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    return metrics

def plot_results(results_dir, results):
    unique_payloads = sorted(set(results['payload_size']))
    plt.figure(figsize=(10, 6))
    for payload in unique_payloads:
        filtered_mldProbLink1 = [results['mldProbLink1'][i] for i in range(len(results['payload_size'])) if results['payload_size'][i] == payload]
        filtered_throughput = [results['throughput_total'][i] for i in range(len(results['payload_size'])) if results['payload_size'][i] == payload]
        plt.plot(filtered_mldProbLink1, filtered_throughput, marker='o', label=f'Payload {payload} Bytes')
    plt.title('Total Throughput vs. mldProbLink1 for Different Payload Sizes')
    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Throughput (Mbps)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_mldProbLink1_payload.png'))
    plt.close()
    print(f"Saved plot: throughput_vs_mldProbLink1_payload.png")

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved '{filename}' to '{destination_dir}'")
    else:
        print(f"File '{filename}' does not exist. Skipping move operation.")

def save_git_commit_info(results_dir):
    try:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if commit_info.returncode == 0:
            with open(os.path.join(results_dir, 'git-commit.txt'), 'w') as f:
                f.write(commit_info.stdout)
            print(f"Saved git commit info to '{os.path.join(results_dir, 'git-commit.txt')}'")
        else:
            print(f"Git command failed: {commit_info.stderr}")
    except Exception as e:
        print(f"Error saving git commit info: {e}")

if __name__ == "__main__":
    main()
