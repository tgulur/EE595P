import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt
from itertools import product  # For generating parameter combinations

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

    # Define the reduced parameter space
    lambda_values = sorted([0.0000001, 0.000001, 0.00001, 0.0001, 0.001, 0.01])       
    bandwidth_values_bw2 = [20, 40, 80]  # Varying BW2 while fixing BW1
    mcs_values = [6]  # Reduced MCS values
    fixed_bw1 = 20  # Fixed BW1 value
    fixed_mcs1 = 6 # Keep MCS1 constant

    # Initialize dictionaries to store results
    throughput_data = {bw2: [] for bw2 in bandwidth_values_bw2}
    e2e_delay_data = {bw2: [] for bw2 in bandwidth_values_bw2}
    combinations_tested = []

    # Run simulations for each subset of parameters
    for lambda_val, bw2, mcs2 in product(lambda_values, bandwidth_values_bw2, mcs_values):
        print(f"\nRunning simulation for Lambda={lambda_val}, BW1={fixed_bw1}, BW2={bw2}, MCS1={fixed_mcs1}, MCS2={mcs2}...")
        cmd = f"./ns3 run 'single-bss-mld --rngRun=1 --nMldSta=5 --mldPerNodeLambda={lambda_val} --channelWidth={fixed_bw1} --channelWidth2={bw2} --mcs={fixed_mcs1} --mcs2={mcs2}'"
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for Lambda={lambda_val}, BW1={fixed_bw1}, BW2={bw2}, MCS1={fixed_mcs1}, MCS2={mcs2}.")
            continue

        # Define a unique filename for the current run's data
        data_filename = f"wifi-mld_lambda_{lambda_val}_bw2_{bw2}_mcs1_{fixed_mcs1}_mcs2_{mcs2}.dat"
        destination_path = os.path.join(results_dir, data_filename)

        # Move the 'wifi-mld.dat' to the results directory with the unique filename
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation for Lambda={lambda_val}, BW2={bw2}.")
            continue

        # Parse results from the moved data file
        parsed_data = parse_results(destination_path)
        if parsed_data:
            # Store the results
            throughput_data[bw2].append(parsed_data['throughput_total'])
            e2e_delay_data[bw2].append(parsed_data['e2e_delay_total'])
            combinations_tested.append((lambda_val, fixed_bw1, bw2, fixed_mcs1, mcs2))
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots
    plot_results(results_dir, lambda_values, bandwidth_values_bw2, throughput_data, e2e_delay_data)

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
        'throughput_total': 0.0,
        'e2e_delay_total': 0.0
    }

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            valid_lines = 0
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 15:
                    print(f"Skipping incomplete line in {filepath}: {line.strip()}")
                    continue
                try:
                    metrics['throughput_total'] += float(tokens[5])          # Total Throughput
                    metrics['e2e_delay_total'] += float(tokens[14])          # Total End-to-End Delay
                    valid_lines += 1
                except ValueError as e:
                    print(f"Error parsing line in {filepath}: {line.strip()} - {e}")
                    continue

        if valid_lines > 0:
            # Average the metrics if there are multiple entries
            metrics['throughput_total'] /= valid_lines
            metrics['e2e_delay_total'] /= valid_lines
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

def plot_results(results_dir, lambda_values, bandwidth_values_bw2, throughput_data, e2e_delay_data):
    """
    Generates line plots for Throughput and E2E Delay against Lambda for different BW2 values.
    Saves the plots in the specified results directory.
    """
    # Plot Throughput vs Lambda for different BW2 values
    plt.figure(figsize=(10, 6))
    for bw2 in bandwidth_values_bw2:
        if bw2 in throughput_data and len(throughput_data[bw2]) == len(lambda_values):
            plt.plot(lambda_values, throughput_data[bw2], marker='o', label=f'BW2={bw2} MHz')
        else:
            print(f"Insufficient data for BW2={bw2} MHz. Skipping in throughput plot.")
    plt.title('Throughput vs Lambda for Different BW2 Values')
    plt.xlabel('Lambda (λ)')
    plt.ylabel('Throughput (Mbps)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    throughput_plot_path = os.path.join(results_dir, 'throughput_vs_lambda.png')
    plt.savefig(throughput_plot_path)
    print(f"Throughput plot saved to {throughput_plot_path}")
    plt.close()

    # Plot End-to-End Delay vs Lambda for different BW2 values
    plt.figure(figsize=(10, 6))
    for bw2 in bandwidth_values_bw2:
        if bw2 in e2e_delay_data and len(e2e_delay_data[bw2]) == len(lambda_values):
            plt.plot(lambda_values, e2e_delay_data[bw2], marker='o', label=f'BW2={bw2} MHz')
        else:
            print(f"Insufficient data for BW2={bw2} MHz. Skipping in E2E Delay plot.")
    plt.title('End-to-End Delay vs Lambda for Different BW2 Values')
    plt.xlabel('Lambda (λ)')
    plt.ylabel('E2E Delay (ms)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    e2e_delay_plot_path = os.path.join(results_dir, 'e2e_delay_vs_lambda.png')
    plt.savefig(e2e_delay_plot_path)
    print(f"E2E Delay plot saved to {e2e_delay_plot_path}")
    plt.close()

def save_git_commit_info(results_dir):
    """
    Saves the current git commit information to a text file in the results directory.
    """
    try:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if commit_info.returncode == 0:
            git_commit_path = os.path.join(results_dir, 'git-commit.txt')
            with open(git_commit_path, 'w') as f:
                f.write(commit_info.stdout)
            print(f"Saved git commit info to {git_commit_path}")
        else:
            print(f"Git command failed: {commit_info.stderr}")
    except Exception as e:
        print(f"Error saving git commit info: {e}")

if __name__ == "__main__":
    main()
