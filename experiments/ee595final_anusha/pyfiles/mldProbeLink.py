import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt

def control_c(signum, frame):
    print("Exiting gracefully...")
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
    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(results_dir, exist_ok=True)
    print(f"Results will be stored in: {results_dir}")

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Define the mldProbLink1 values to test
    mldProbLink1_values = [0.3, 0.5, 0.7]
    rng_run = 1          # Single RNG run
    n_sta = 10           # Fixed number of MLD STAs
    mldPerNodeLambda = 0.001  # Fixed traffic arrival rate
    simTime = 20

    # Initialize lists to store results
    mldProbLink1_list = []
    throughput_total = []
    queue_delay_total = []
    access_delay_total = []
    e2e_delay_total = []

    # Run simulations for each mldProbLink1 value
    for prob_val in mldProbLink1_values:
        print(f"\nRunning simulation for mldProbLink1={prob_val}...")
        cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --nMldSta={n_sta} --mldPerNodeLambda={mldPerNodeLambda} --mldProbLink1={prob_val} --simulationTime={simTime}'"
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for mldProbLink1={prob_val}. Check NS-3 logs for details.")
            continue

        # Define a unique filename for the current run's data
        data_filename = f"wifi-mld_probLink1_{prob_val}.dat"
        destination_path = os.path.join(results_dir, data_filename)

        # Move the 'wifi-mld.dat' to the results directory with the unique filename
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation run for mldProbLink1={prob_val}")
            continue

        # Parse results from the moved data file
        parsed_data = parse_results(destination_path)
        if parsed_data:
            # Aggregate the metrics
            mldProbLink1_list.append(prob_val)
            throughput_total.append(parsed_data['throughput_total'])
            queue_delay_total.append(parsed_data['queue_delay_total'])
            access_delay_total.append(parsed_data['access_delay_total'])
            e2e_delay_total.append(parsed_data['e2e_delay_total'])
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots
    plot_results(results_dir, mldProbLink1_list, throughput_total,
                queue_delay_total, access_delay_total, e2e_delay_total)

    # Save results
    move_file('wifi-mld.dat', results_dir)

    # Save git commit info
    save_git_commit_info(results_dir)

def check_and_remove(filename):
    if os.path.exists(filename):
        response = input(f"Remove existing file {filename}? [Yes/No]: ").strip().lower()
        if response == 'yes':
            os.remove(filename)
            print(f"Removed {filename}")
        else:
            print("Exiting...")
            sys.exit(1)

def parse_results(filepath):
    """
    Parses the given 'wifi-mld_probLink1_X.dat' file and extracts relevant metrics.
    Returns a dictionary of averaged metrics.
    """
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
                if len(tokens) < 21:  # Adjust based on actual number of tokens
                    print(f"Skipping incomplete line in {filepath}: {line.strip()}")
                    continue
                try:
                    # Aggregate the metrics by summing them up
                    metrics['throughput_total'] += float(tokens[5])          # Total Throughput
                    metrics['queue_delay_total'] += float(tokens[8])         # Total Queue Delay
                    metrics['access_delay_total'] += float(tokens[11])       # Total Access Delay
                    metrics['e2e_delay_total'] += float(tokens[14])          # Total End-to-End Delay
                    valid_lines += 1
                except ValueError as e:
                    print(f"Error parsing line in {filepath}: {line.strip()} - {e}")
                    continue

            if valid_lines > 0:
                for key in metrics:
                    metrics[key] /= valid_lines  # Calculate average
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

def plot_results(results_dir, mldProbLink1_list, throughput_total,
                queue_delay_total, access_delay_total, e2e_delay_total):
    
    # Plot Throughput vs mldProbLink1
    plt.figure(figsize=(8,6))
    plt.title('Total Throughput vs. mldProbLink1')
    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Throughput (Mbps)')
    plt.grid(True)
    plt.plot(mldProbLink1_list, throughput_total, label='Total Throughput', marker='o', linestyle='-')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_mldProbLink1.png'))
    plt.close()
    print(f"Saved plot: throughput_vs_mldProbLink1.png")

    # Plot Queue Delay vs mldProbLink1
    plt.figure(figsize=(8,6))
    plt.title('Total Queue Delay vs. mldProbLink1')
    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Queue Delay (ms)')
    plt.grid(True)
    plt.plot(mldProbLink1_list, queue_delay_total, label='Total Queue Delay', marker='x', linestyle='-')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'queue_delay_vs_mldProbLink1.png'))
    plt.close()
    print(f"Saved plot: queue_delay_vs_mldProbLink1.png")

    # Plot Access Delay vs mldProbLink1
    plt.figure(figsize=(8,6))
    plt.title('Total Access Delay vs. mldProbLink1')
    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Access Delay (ms)')
    plt.grid(True)
    plt.plot(mldProbLink1_list, access_delay_total, label='Total Access Delay', marker='^', linestyle='-')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'access_delay_vs_mldProbLink1.png'))
    plt.close()
    print(f"Saved plot: access_delay_vs_mldProbLink1.png")

    # Plot End-to-End Delay vs mldProbLink1
    plt.figure(figsize=(8,6))
    plt.title('Total End-to-End Delay vs. mldProbLink1')
    plt.xlabel('mldProbLink1')
    plt.ylabel('Total End-to-End Delay (ms)')
    plt.grid(True)
    plt.plot(mldProbLink1_list, e2e_delay_total, label='Total End-to-End Delay', marker='s', linestyle='-')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_mldProbLink1.png'))
    plt.close()
    print(f"Saved plot: e2e_delay_vs_mldProbLink1.png")

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved {filename} to {destination_dir}")
    else:
        print(f"File {filename} does not exist. Skipping move operation.")

def save_git_commit_info(results_dir):
    try:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if commit_info.returncode == 0:
            with open(os.path.join(results_dir, 'git-commit.txt'), 'w') as f:
                f.write(commit_info.stdout)
            print(f"Saved git commit info to {os.path.join(results_dir, 'git-commit.txt')}")
        else:
            print(f"Git command failed: {commit_info.stderr}")
    except Exception as e:
        print(f"Error saving git commit info: {e}")

if __name__ == "__main__":
    main()
