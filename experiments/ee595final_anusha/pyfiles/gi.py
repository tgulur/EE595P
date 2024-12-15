import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt

def control_c(signum, frame):
    print("\nExiting...")
    sys.exit(1)

signal.signal(signal.SIGINT, control_c)

def main():
    dirname = 'gi-experiment'
    ns3_path = os.path.join('../../../../ns3')  # Adjust the path as needed

    # Check if the ns3 executable exists
    if not os.path.exists(ns3_path):
        print("NS-3 executable not found. Please ensure the path is correct.")
        sys.exit(1)

    # Create a unique results directory with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{timestamp}")
    os.makedirs(results_dir, exist_ok=True)

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Define GI values to test (in nanoseconds)
    gi_values = [3200]  # Adjust or expand as needed

    # Initialize result storage
    results = {
        'gi': [],
        'throughput_l1': [],
        'throughput_l2': [],
        'throughput_total': [],
        'delay_l1': [],
        'delay_l2': [],
        'delay_total': []
    }

    # Fixed parameters for this experiment
    rng_run = 1
    max_packets = 1500
    lambda_val = 1e-3  # Fixed traffic load
    mcs = 6  # Fixed MCS for Link 1
    mcs2 = 6  # Fixed MCS for Link 2
    channelWidth = 40  # Fixed channel width for Link 1
    channelWidth2 = 40  # Fixed channel width for Link 2
    nMldSta = 10  # Fixed number of STAs

    for gi in gi_values:
        print(f"\nRunning simulation with Guard Interval = {gi} ns")

        # Remove existing data file before each run
        check_and_remove('wifi-mld.dat')

        # Construct the simulation command with the current GI
        cmd = (
            f"./ns3 run \"single-bss-mld --rngRun={rng_run} "
            f"--payloadSize={max_packets} "
            f"--mldPerNodeLambda={lambda_val} "
            f"--gi={gi} "
            f"--mcs={mcs} "
            f"--mcs2={mcs2} "
            f"--channelWidth={channelWidth} "
            f"--channelWidth2={channelWidth2} "
            f"--nMldSta={nMldSta}\""
        )
        print(f"Executing command: {cmd}")

        # Run the simulation
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Simulation failed for GI={gi} ns. Error: {e}")
            continue

        # Parse the output data
        if not os.path.exists('wifi-mld.dat'):
            print("Data file 'wifi-mld.dat' not found after simulation run.")
            continue

        with open('wifi-mld.dat', 'r') as f:
            lines = f.readlines()
            for line in lines:
                tokens = line.strip().split(',')
                if len(tokens) < 15:
                    print(f"Skipping malformed line: {line.strip()}")
                    continue  # Ensure the line has enough tokens
                try:
                    # Extract relevant metrics based on your data format
                    # Adjust the indices if necessary
                    throughput_l1 = float(tokens[3])
                    throughput_l2 = float(tokens[4])
                    throughput_total = float(tokens[5])
                    delay_l1 = float(tokens[12])  # Mean Access Delay Link1
                    delay_l2 = float(tokens[13])  # Mean Access Delay Link2
                    delay_total = float(tokens[14])  # Mean End-to-End Delay Total

                    # Store the results
                    results['gi'].append(gi)
                    results['throughput_l1'].append(throughput_l1)
                    results['throughput_l2'].append(throughput_l2)
                    results['throughput_total'].append(throughput_total)
                    results['delay_l1'].append(delay_l1)
                    results['delay_l2'].append(delay_l2)
                    results['delay_total'].append(delay_total)
                except ValueError:
                    print(f"Invalid data format in line: {line.strip()}")
                    continue

        # Move the data file to results directory for record-keeping
        move_file('wifi-mld.dat', results_dir)

    # Plotting Throughput vs. Guard Interval
    plt.figure(figsize=(10, 6))
    plt.title('Throughput vs. Guard Interval')
    plt.xlabel('Guard Interval (ns)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.plot(results['gi'], results['throughput_l1'], marker='o', label='Link 1 Throughput')
    plt.plot(results['gi'], results['throughput_l2'], marker='x', label='Link 2 Throughput')
    plt.plot(results['gi'], results['throughput_total'], marker='^', label='Total Throughput')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'Throughput_vs_GI.png'))
    plt.close()
    print(f"Saved plot 'Throughput_vs_GI.png' in {results_dir}")

    # Plotting Delay vs. Guard Interval
    plt.figure(figsize=(10, 6))
    plt.title('Delay vs. Guard Interval')
    plt.xlabel('Guard Interval (ns)')
    plt.ylabel('Delay (ms)')
    plt.grid(True)
    plt.plot(results['gi'], results['delay_l1'], marker='o', label='Link 1 Delay')
    plt.plot(results['gi'], results['delay_l2'], marker='x', label='Link 2 Delay')
    plt.plot(results['gi'], results['delay_total'], marker='^', label='Total Delay')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'Delay_vs_GI.png'))
    plt.close()
    print(f"Saved plot 'Delay_vs_GI.png' in {results_dir}")

    # Save git commit information for reproducibility
    with open(os.path.join(results_dir, 'git-commit.txt'), 'w') as f:
        try:
            commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, check=True)
            f.write(commit_info.stdout.decode())
        except subprocess.CalledProcessError as e:
            print(f"Failed to retrieve git commit info. Error: {e}")

    print(f"\nExperiments completed. Results are saved in {results_dir}")

def check_and_remove(filename):
    if os.path.exists(filename):
        while True:
            response = input(f"Remove existing file '{filename}'? [Yes/No]: ").strip().lower()
            if response == 'yes':
                os.remove(filename)
                print(f"Removed '{filename}'.")
                break
            elif response == 'no':
                print("Exiting...")
                sys.exit(1)
            else:
                print("Please respond with 'Yes' or 'No'.")

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved '{filename}' to '{destination_dir}'.")
    else:
        print(f"File '{filename}' does not exist and cannot be moved.")

if __name__ == "__main__":
    main()
