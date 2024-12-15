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

    # Define the CWmin values to test for both links
    cwmin_values = [16, 32, 64]  # Possible CWmin values
    cwmin_combinations = list(itertools.product(cwmin_values, cwmin_values))  # All combinations

    # Fixed Parameters
    rng_run = 1                     # Single RNG run
    n_sta = 10                      # Fixed number of MLD STAs
    mldPerNodeLambda = 0.001        # Fixed traffic arrival rate
    mldProbLink1 = 0.5              # Fixed traffic allocation probability
    simTime = 20                    # Simulation time in seconds

    # Initialize lists to store results
    cwminLink1_list = []
    cwminLink2_list = []
    throughput_total = []
    queue_delay_total = []
    access_delay_total = []
    e2e_delay_total = []

    # Run simulations for each CWmin combination
    for cwmin1, cwmin2 in cwmin_combinations:
        print(f"\nRunning simulation for acBECwminLink1={cwmin1}, acBECwminLink2={cwmin2}...")
        cmd = (
            f"./ns3 run 'single-bss-mld "
            f"--rngRun={rng_run} "
            f"--nMldSta={n_sta} "
            f"--mldPerNodeLambda={mldPerNodeLambda} "
            f"--mldProbLink1={mldProbLink1} "
            f"--acBECwminLink1={cwmin1} "
            f"--acBECwminLink2={cwmin2} "
            f"--simulationTime={simTime}'"
        )
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for acBECwminLink1={cwmin1}, acBECwminLink2={cwmin2}. Check NS-3 logs for details.")
            continue

        # Define a unique filename for the current run's data
        data_filename = f"wifi-mld_cwmin_L1_{cwmin1}_L2_{cwmin2}.dat"
        destination_path = os.path.join(results_dir, data_filename)

        # Move the 'wifi-mld.dat' to the results directory with the unique filename
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation run for acBECwminLink1={cwmin1}, acBECwminLink2={cwmin2}")
            continue

        # Parse results from the moved data file
        parsed_data = parse_results(destination_path)
        if parsed_data:
            # Aggregate the metrics
            cwminLink1_list.append(cwmin1)
            cwminLink2_list.append(cwmin2)
            throughput_total.append(parsed_data['throughput_total'])
            queue_delay_total.append(parsed_data['queue_delay_total'])
            access_delay_total.append(parsed_data['access_delay_total'])
            e2e_delay_total.append(parsed_data['e2e_delay_total'])
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots
    plot_results(results_dir, cwminLink1_list, cwminLink2_list, throughput_total,
                queue_delay_total, access_delay_total, e2e_delay_total)

    # Final cleanup: Move any remaining 'wifi-mld.dat' if exists
    move_file('wifi-mld.dat', results_dir)

    # Save git commit info
    save_git_commit_info(results_dir)

def check_and_remove(filename):
    """
    Checks if a file exists and prompts the user to remove it.
    """
    if os.path.exists(filename):
        response = input(f"Remove existing file '{filename}'? [Yes/No]: ").strip().lower()
        if response == 'yes':
            os.remove(filename)
            print(f"Removed '{filename}'")
        else:
            print("Exiting to prevent data contamination.")
            sys.exit(1)

def parse_results(filepath):
    """
    Parses the given 'wifi-mld_cwmin_L1_X_L2_Y.dat' file and extracts relevant metrics.
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
                if len(tokens) < 21:  # Adjust based on actual number of tokens in your .dat file
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

def plot_results(results_dir, cwminLink1_list, cwminLink2_list, throughput_total,
                queue_delay_total, access_delay_total, e2e_delay_total):
    """
    Generates and saves plots for throughput and delay metrics against CWmin settings.
    """
    # Prepare data for plotting
    combinations = list(zip(cwminLink1_list, cwminLink2_list))
    labels = [f"L1={cw1}, L2={cw2}" for cw1, cw2 in combinations]

    # Plot Throughput vs. CWmin Combinations
    plt.figure(figsize=(12, 8))
    plt.bar(labels, throughput_total, color='skyblue')
    plt.title('Total Throughput for Different CWmin Combinations')
    plt.xlabel('CWmin Link1 and Link2 Combinations')
    plt.ylabel('Total Throughput (Mbps)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_cwmin_combinations.png'))
    plt.close()
    print(f"Saved plot: throughput_vs_cwmin_combinations.png")

    # Plot End-to-End Delay vs. CWmin Combinations
    plt.figure(figsize=(12, 8))
    plt.bar(labels, e2e_delay_total, color='salmon')
    plt.title('Total End-to-End Delay for Different CWmin Combinations')
    plt.xlabel('CWmin Link1 and Link2 Combinations')
    plt.ylabel('Total End-to-End Delay (ms)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_cwmin_combinations.png'))
    plt.close()
    print(f"Saved plot: e2e_delay_vs_cwmin_combinations.png")

    # Additional Plots: Separate Throughput and Delay by Link1 or Link2 CWmin
    # Example: Throughput Heatmap

    import numpy as np

    # Create matrices for heatmaps
    cwmin_unique = sorted(set(cwminLink1_list))
    throughput_matrix = np.zeros((len(cwmin_unique), len(cwmin_unique)))
    e2e_delay_matrix = np.zeros((len(cwmin_unique), len(cwmin_unique)))

    for idx, (cw1, cw2, throughput, delay) in enumerate(zip(cwminLink1_list, cwminLink2_list, throughput_total, e2e_delay_total)):
        row = cwmin_unique.index(cw1)
        col = cwmin_unique.index(cw2)
        throughput_matrix[row, col] = throughput
        e2e_delay_matrix[row, col] = delay

    # Plot Throughput Heatmap
    plt.figure(figsize=(8, 6))
    plt.imshow(throughput_matrix, cmap='Blues', interpolation='nearest')
    plt.title('Throughput Heatmap')
    plt.xlabel('acBECwminLink2')
    plt.ylabel('acBECwminLink1')
    plt.xticks(ticks=range(len(cwmin_unique)), labels=cwmin_unique)
    plt.yticks(ticks=range(len(cwmin_unique)), labels=cwmin_unique)
    plt.colorbar(label='Throughput (Mbps)')
    for i in range(len(cwmin_unique)):
        for j in range(len(cwmin_unique)):
            plt.text(j, i, throughput_matrix[i, j], ha='center', va='center', color='black')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'throughput_heatmap.png'))
    plt.close()
    print(f"Saved plot: throughput_heatmap.png")

    # Plot End-to-End Delay Heatmap
    plt.figure(figsize=(8, 6))
    plt.imshow(e2e_delay_matrix, cmap='Reds', interpolation='nearest')
    plt.title('End-to-End Delay Heatmap')
    plt.xlabel('acBECwminLink2')
    plt.ylabel('acBECwminLink1')
    plt.xticks(ticks=range(len(cwmin_unique)), labels=cwmin_unique)
    plt.yticks(ticks=range(len(cwmin_unique)), labels=cwmin_unique)
    plt.colorbar(label='End-to-End Delay (ms)')
    for i in range(len(cwmin_unique)):
        for j in range(len(cwmin_unique)):
            plt.text(j, i, e2e_delay_matrix[i, j], ha='center', va='center', color='black')
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_heatmap.png'))
    plt.close()
    print(f"Saved plot: e2e_delay_heatmap.png")

def move_file(filename, destination_dir):
    """
    Moves the specified file to the destination directory.
    """
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved '{filename}' to '{destination_dir}'")
    else:
        print(f"File '{filename}' does not exist. Skipping move operation.")

def save_git_commit_info(results_dir):
    """
    Saves the current git commit information to a file in the results directory.
    """
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
