import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from itertools import product

def control_c(signum, frame):
    print("Exiting gracefully...")
    sys.exit(1)

signal.signal(signal.SIGINT, control_c)

def main():
    # Define the directory for results
    dirname = '11be-mlo'
    ns3_path = os.path.join('../../../../ns3')

    # Check if the ns3 executable exists
    if not os.path.exists(ns3_path):
        print(f"Please run this program from within the correct directory.")
        sys.exit(1)

    # Create a results directory with a timestamp
    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(results_dir, exist_ok=True)
    print(f"Results will be stored in: {results_dir}")

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Define parameter ranges
    lambda_values = [0.001, 0.005, 0.01, 0.05, 0.1]
    bandwidth_values = [20, 40, 80]
    mcs_values = [4, 6, 8]

    # Initialize storage for results
    results = {}

    # Iterate over combinations of lambda, bandwidth, and MCS values
    for lambda_val in lambda_values:
        results[lambda_val] = []
        for bw1, bw2, mcs1, mcs2 in product(bandwidth_values, bandwidth_values, mcs_values, mcs_values):
            print(f"\nRunning simulation for Lambda={lambda_val}, BW1={bw1}, BW2={bw2}, MCS1={mcs1}, MCS2={mcs2}...")
            cmd = (
                f"./ns3 run 'single-bss-mld --rngRun=1 --nMldSta=5 "
                f"--mldPerNodeLambda={lambda_val} --channelWidth={bw1} --channelWidth2={bw2} "
                f"--mcs={mcs1} --mcs2={mcs2}'"
            )
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                print(f"Simulation failed for Lambda={lambda_val}, BW1={bw1}, BW2={bw2}, MCS1={mcs1}, MCS2={mcs2}")
                continue

            # Move and parse the results
            data_filename = f"wifi-mld_lambda_{lambda_val}_bw1_{bw1}_bw2_{bw2}_mcs1_{mcs1}_mcs2_{mcs2}.dat"
            destination_path = os.path.join(results_dir, data_filename)
            if os.path.exists('wifi-mld.dat'):
                shutil.move('wifi-mld.dat', destination_path)
                parsed_data = parse_results(destination_path)
                if parsed_data:
                    results[lambda_val].append({
                        'bw1': bw1, 'bw2': bw2, 'mcs1': mcs1, 'mcs2': mcs2, **parsed_data
                    })
                else:
                    print(f"Failed to parse results for Lambda={lambda_val}, BW1={bw1}, BW2={bw2}, MCS1={mcs1}, MCS2={mcs2}")
            else:
                print(f"'wifi-mld.dat' not found for Lambda={lambda_val}, BW1={bw1}, BW2={bw2}, MCS1={mcs1}, MCS2={mcs2}")

    # Generate plots
    for lambda_val, data in results.items():
        if data:
            plot_results(results_dir, lambda_val, data)

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
    Parses the given 'wifi-mld.dat' file and extracts relevant metrics.
    Returns a dictionary of metrics.
    """
    metrics = {
        'throughput_l1': 0.0,
        'throughput_l2': 0.0,
        'throughput_total': 0.0,
        'e2e_delay_l1': 0.0,
        'e2e_delay_l2': 0.0,
        'e2e_delay_total': 0.0
    }

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 15:
                    print(f"Skipping incomplete line in {filepath}: {line.strip()}")
                    continue
                metrics['throughput_l1'] += float(tokens[3])
                metrics['throughput_l2'] += float(tokens[4])
                metrics['throughput_total'] += float(tokens[5])
                metrics['e2e_delay_l1'] += float(tokens[12])
                metrics['e2e_delay_l2'] += float(tokens[13])
                metrics['e2e_delay_total'] += float(tokens[14])

        # Average the metrics
        for key in metrics:
            metrics[key] /= len(lines)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None

    return metrics

def plot_results(results_dir, lambda_val, data):
    # Extract values for plotting
    bw1_values = [item['bw1'] for item in data]
    bw2_values = [item['bw2'] for item in data]
    throughput_total = [item['throughput_total'] for item in data]
    e2e_delay_total = [item['e2e_delay_total'] for item in data]

    # Plot Throughput
    plt.figure()
    plt.title(f'Throughput for Lambda={lambda_val}')
    plt.xlabel('Bandwidth Combination (BW1, BW2)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.bar(range(len(throughput_total)), throughput_total, tick_label=[f"{bw1}-{bw2}" for bw1, bw2 in zip(bw1_values, bw2_values)])
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(results_dir, f'throughput_lambda_{lambda_val}.png'))
    plt.close()

    # Plot End-to-End Delay
    plt.figure()
    plt.title(f'End-to-End Delay for Lambda={lambda_val}')
    plt.xlabel('Bandwidth Combination (BW1, BW2)')
    plt.ylabel('End-to-End Delay (ms)')
    plt.grid(True)
    plt.bar(range(len(e2e_delay_total)), e2e_delay_total, tick_label=[f"{bw1}-{bw2}" for bw1, bw2 in zip(bw1_values, bw2_values)])
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(results_dir, f'e2e_delay_lambda_{lambda_val}.png'))
    plt.close()

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
