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

    # Define the lambda values to test
    lambda_values = [0.001, 0.005, 0.01, 0.05, 0.1]
    rng_run = 1  # Single RNG run
    n_sta = 5    # Fixed number of MLD STAs
    

    # Initialize lists to store results
    throughput_l1 = []
    throughput_l2 = []
    throughput_total = []
    queue_delay_l1 = []
    queue_delay_l2 = []
    queue_delay_total = []
    access_delay_l1 = []
    access_delay_l2 = []
    access_delay_total = []
    e2e_delay_l1 = []
    e2e_delay_l2 = []
    e2e_delay_total = []

    # Run simulations for each lambda value
    for lambda_val in lambda_values:
        print(f"\nRunning simulation for mldPerNodeLambda={lambda_val}...")
        cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --nMldSta={n_sta} --mldPerNodeLambda={lambda_val}'"
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for mldPerNodeLambda={lambda_val}. Check NS-3 logs for details.")
            continue

        # Define a unique filename for the current run's data
        data_filename = f"wifi-mld_lambda_{lambda_val}.dat"
        destination_path = os.path.join(results_dir, data_filename)

        # Move the 'wifi-mld.dat' to the results directory with the unique filename
        if os.path.exists('wifi-mld.dat'):
            shutil.move('wifi-mld.dat', destination_path)
            print(f"Moved 'wifi-mld.dat' to '{destination_path}'")
        else:
            print(f"'wifi-mld.dat' not found after simulation run for mldPerNodeLambda={lambda_val}")
            continue

        # Parse results from the moved data file
        parsed_data = parse_results(destination_path)
        if parsed_data:
            # Aggregate the metrics
            throughput_l1.append(parsed_data['throughput_l1'])
            throughput_l2.append(parsed_data['throughput_l2'])
            throughput_total.append(parsed_data['throughput_total'])
            queue_delay_l1.append(parsed_data['queue_delay_l1'])
            queue_delay_l2.append(parsed_data['queue_delay_l2'])
            queue_delay_total.append(parsed_data['queue_delay_total'])
            access_delay_l1.append(parsed_data['access_delay_l1'])
            access_delay_l2.append(parsed_data['access_delay_l2'])
            access_delay_total.append(parsed_data['access_delay_total'])
            e2e_delay_l1.append(parsed_data['e2e_delay_l1'])
            e2e_delay_l2.append(parsed_data['e2e_delay_l2'])
            e2e_delay_total.append(parsed_data['e2e_delay_total'])
        else:
            print(f"Parsing failed for data file: {destination_path}")

    # Generate plots
    plot_results(results_dir, lambda_values, throughput_l1, throughput_l2, throughput_total,
                queue_delay_l1, queue_delay_l2, queue_delay_total,
                access_delay_l1, access_delay_l2, access_delay_total,
                e2e_delay_l1, e2e_delay_l2, e2e_delay_total)

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
    Parses the given 'wifi-mld.dat' file and extracts relevant metrics.
    Returns a dictionary of metrics.
    """
    metrics = {
        'throughput_l1': 0.0,
        'throughput_l2': 0.0,
        'throughput_total': 0.0,
        'queue_delay_l1': 0.0,
        'queue_delay_l2': 0.0,
        'queue_delay_total': 0.0,
        'access_delay_l1': 0.0,
        'access_delay_l2': 0.0,
        'access_delay_total': 0.0,
        'e2e_delay_l1': 0.0,
        'e2e_delay_l2': 0.0,
        'e2e_delay_total': 0.0
    }

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 49:
                    print(f"Skipping incomplete line in {filepath}: {line.strip()}")
                    continue
                try:
                    # Aggregate the metrics by summing them up
                    metrics['throughput_l1'] += float(tokens[3])             # Throughput Link 1
                    metrics['throughput_l2'] += float(tokens[4])             # Throughput Link 2
                    metrics['throughput_total'] += float(tokens[5])          # Total Throughput
                    metrics['queue_delay_l1'] += float(tokens[6])            # Queue Delay Link 1
                    metrics['queue_delay_l2'] += float(tokens[7])            # Queue Delay Link 2
                    metrics['queue_delay_total'] += float(tokens[8])         # Total Queue Delay
                    metrics['access_delay_l1'] += float(tokens[9])           # Access Delay Link 1
                    metrics['access_delay_l2'] += float(tokens[10])          # Access Delay Link 2
                    metrics['access_delay_total'] += float(tokens[11])       # Total Access Delay
                    metrics['e2e_delay_l1'] += float(tokens[12])             # End-to-End Delay Link 1
                    metrics['e2e_delay_l2'] += float(tokens[13])             # End-to-End Delay Link 2
                    metrics['e2e_delay_total'] += float(tokens[14])          # Total End-to-End Delay
                except ValueError as e:
                    print(f"Error parsing line in {filepath}: {line.strip()} - {e}")
                    continue

        # Average the metrics if there are multiple entries
        for key in metrics:
            metrics[key] /= len(lines)
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    return metrics

def plot_results(results_dir, lambda_values, throughput_l1, throughput_l2, throughput_total,
                queue_delay_l1, queue_delay_l2, queue_delay_total,
                access_delay_l1, access_delay_l2, access_delay_total,
                e2e_delay_l1, e2e_delay_l2, e2e_delay_total):
    
    # Plot Throughput vs Lambda
    plt.figure()
    plt.title('Throughput vs. mldPerNodeLambda')
    plt.xlabel('mldPerNodeLambda')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.plot(lambda_values, throughput_l1, label='Throughput Link 1', marker='o')
    plt.plot(lambda_values, throughput_l2, label='Throughput Link 2', marker='x')
    plt.plot(lambda_values, throughput_total, label='Total Throughput', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_lambda.png'))
    plt.close()

    # Plot Queue Delay vs Lambda
    plt.figure()
    plt.title('Queue Delay vs. mldPerNodeLambda')
    plt.xlabel('mldPerNodeLambda')
    plt.ylabel('Queue Delay (ms)')
    plt.grid(True)
    plt.plot(lambda_values, queue_delay_l1, label='Queue Delay Link 1', marker='o')
    plt.plot(lambda_values, queue_delay_l2, label='Queue Delay Link 2', marker='x')
    plt.plot(lambda_values, queue_delay_total, label='Total Queue Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'queue_delay_vs_lambda.png'))
    plt.close()

    # Plot Access Delay vs Lambda
    plt.figure()
    plt.title('Access Delay vs. mldPerNodeLambda')
    plt.xlabel('mldPerNodeLambda')
    plt.ylabel('Access Delay (ms)')
    plt.grid(True)
    plt.plot(lambda_values, access_delay_l1, label='Access Delay Link 1', marker='o')
    plt.plot(lambda_values, access_delay_l2, label='Access Delay Link 2', marker='x')
    plt.plot(lambda_values, access_delay_total, label='Total Access Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'access_delay_vs_lambda.png'))
    plt.close()

    # Plot End-to-End Delay vs Lambda
    plt.figure()
    plt.title('End-to-End Delay vs. mldPerNodeLambda')
    plt.xlabel('mldPerNodeLambda')
    plt.ylabel('End-to-End Delay (ms)')
    plt.grid(True)
    plt.plot(lambda_values, e2e_delay_l1, label='E2E Delay Link 1', marker='o')
    plt.plot(lambda_values, e2e_delay_l2, label='E2E Delay Link 2', marker='x')
    plt.plot(lambda_values, e2e_delay_total, label='Total End-to-End Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_lambda.png'))
    plt.close()

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
