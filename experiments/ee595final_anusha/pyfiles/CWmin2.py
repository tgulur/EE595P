import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
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

    # Define the CWmin values for both links
    cwmin_values = [16, 32, 64, 128, 256, 512, 1000]  # CWmin values for Link 1 and Link 2
    cwmin_combinations = list(itertools.product(cwmin_values, cwmin_values))  # All combinations

    # Fixed Parameters
    rng_run = 1                     # Single RNG run
    n_sta = 10                      # Number of MLD STAs
    mldPerNodeLambda = 0.001        # Traffic arrival rate
    simTime = 10                   # Simulation time in seconds

    # Initialize lists to store results
    results = []

    # Run simulations for each CWmin combination
    for cwmin1, cwmin2 in cwmin_combinations:
        print(f"\nRunning simulation for CWmin Link 1={cwmin1}, CWmin Link 2={cwmin2}...")
        cmd = (
            f"./ns3 run 'single-bss-mld "
            f"--rngRun={rng_run} "
            f"--nMldSta={n_sta} "
            f"--mldPerNodeLambda={mldPerNodeLambda} "
            f"--acBECwminLink1={cwmin1} "
            f"--acBECwminLink2={cwmin2} "
            f"--simulationTime={simTime}'"
        )
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for CWmin Link 1={cwmin1}, CWmin Link 2={cwmin2}. Check NS-3 logs for details.")
            continue

        # Move and rename the result file
        data_filename = f"wifi-mld_cwmin_L1_{cwmin1}_L2_{cwmin2}.dat"
        destination_path = os.path.join(results_dir, data_filename)
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation run for CWmin Link 1={cwmin1}, CWmin Link 2={cwmin2}")
            continue

        # Parse results
        parsed_data = parse_results(destination_path)
        if parsed_data:
            results.append((cwmin1, cwmin2, parsed_data['throughput_total'], parsed_data['e2e_delay_total']))
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots and heatmaps
    plot_results(results_dir, results)

    # Save git commit info
    save_git_commit_info(results_dir)

def check_and_remove(filename):
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Removed existing file: {filename}")

def parse_results(filepath):
    metrics = {
        'throughput_total': 0.0,
        'e2e_delay_total': 0.0
    }

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            valid_lines = 0
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 15:  # Ensure sufficient tokens in the result file
                    continue
                try:
                    metrics['throughput_total'] += float(tokens[5])  # Total throughput
                    metrics['e2e_delay_total'] += float(tokens[14])  # Total end-to-end delay
                    valid_lines += 1
                except ValueError:
                    continue

            # Average the metrics over valid lines
            if valid_lines > 0:
                for key in metrics:
                    metrics[key] /= valid_lines
            else:
                return None

    except FileNotFoundError:
        return None

    return metrics

def plot_results(results_dir, results):
    # Extract data
    cwmin1_values = sorted(set([r[0] for r in results]))
    cwmin2_values = sorted(set([r[1] for r in results]))
    throughput_matrix = np.zeros((len(cwmin1_values), len(cwmin2_values)))
    e2e_delay_matrix = np.zeros((len(cwmin1_values), len(cwmin2_values)))

    for cwmin1, cwmin2, throughput, e2e_delay in results:
        row = cwmin1_values.index(cwmin1)
        col = cwmin2_values.index(cwmin2)
        throughput_matrix[row, col] = throughput
        e2e_delay_matrix[row, col] = e2e_delay

    # Plot Throughput Heatmap
    plt.figure(figsize=(8, 6))
    plt.title('Throughput Heatmap')
    plt.imshow(throughput_matrix, cmap='Blues', interpolation='nearest')
    plt.xlabel('CWmin Link 2')
    plt.ylabel('CWmin Link 1')
    plt.xticks(range(len(cwmin2_values)), cwmin2_values)
    plt.yticks(range(len(cwmin1_values)), cwmin1_values)
    plt.colorbar(label='Throughput (Mbps)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'throughput_heatmap.png'))
    plt.close()

    # Plot E2E Delay Heatmap
    plt.figure(figsize=(8, 6))
    plt.title('End-to-End Delay Heatmap')
    plt.imshow(e2e_delay_matrix, cmap='Reds', interpolation='nearest')
    plt.xlabel('CWmin Link 2')
    plt.ylabel('CWmin Link 1')
    plt.xticks(range(len(cwmin2_values)), cwmin2_values)
    plt.yticks(range(len(cwmin1_values)), cwmin1_values)
    plt.colorbar(label='End-to-End Delay (ms)')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_heatmap.png'))
    plt.close()

def save_git_commit_info(results_dir):
    try:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if commit_info.returncode == 0:
            with open(os.path.join(results_dir, 'git-commit.txt'), 'w') as f:
                f.write(commit_info.stdout)
    except Exception as e:
        print(f"Error saving git commit info: {e}")

if __name__ == "__main__":
    main()
