import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

def control_c(signum, frame):
    print("Exiting...")
    sys.exit(1)

signal.signal(signal.SIGINT, control_c)

def main():
    # Define the directory for results
    dirname = '11be-mlo'
    ns3_path = os.path.join('../../../../ns3')

    # Check if the ns3 directory exists
    if not os.path.exists(ns3_path):
        print(f"Please run this program from within the correct directory.")
        sys.exit(1)

    # Create a results directory with a timestamp
    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(results_dir, exist_ok=True)

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Experiment parameters
    rng_run = 1
    payload_size = 1500
    simulation_time = 10  # seconds
    mldPerNodeLambda = 0.001  # Set close to 1 for saturated traffic
    nMldSta = 5
    mcs = 6  # For Link 1
    channelWidth = 40  # For Link 1
    mcs2_values = [ 4, 8]  # MCS values for Link 2
    channelWidth2 = 40  # Fixed channel width for Link 2
    mldProbLink1_values = [0.2, 0.4, 0.6, 0.8, 0.9]  # 0.1 to 0.9

    # Initialize data structures to store results
    # throughput_data: {mcs2: {'mldProbLink1': [], 'throughput_total': []}}
    throughput_data = {}

    for mcs2 in mcs2_values:
        throughput_data[mcs2] = {
            'mldProbLink1': [],
            'throughput_total': []
        }

        # Run the ns-3 simulation for each mldProbLink1
        for mldProbLink1 in mldProbLink1_values:
            cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --payloadSize={payload_size} --simulationTime={simulation_time} --nMldSta={nMldSta} --mldPerNodeLambda={mldPerNodeLambda} --channelWidth={channelWidth} --channelWidth2={channelWidth2} --mcs={mcs} --mcs2={mcs2} --mldProbLink1={mldProbLink1}'"
            print(f"Running simulation with mcs2={mcs2}, mldProbLink1={mldProbLink1}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Simulation failed with error:\n{result.stderr}")
                continue  # Skip to the next iteration

            # After each run, read the output data file and collect the throughput metrics
            if os.path.exists('wifi-mld.dat'):
                with open('wifi-mld.dat', 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]  # Assuming the last line contains the latest run data
                        tokens = last_line.strip().split(',')

                        # Get the required throughput metric from the tokens
                        # Index 5: mldThptTotal
                        throughput_total = float(tokens[5])

                        # Store the results
                        throughput_data[mcs2]['mldProbLink1'].append(mldProbLink1)
                        throughput_data[mcs2]['throughput_total'].append(throughput_total)
                    else:
                        print("No data in wifi-mld.dat. The simulation might have failed.")
            else:
                print("wifi-mld.dat does not exist. The simulation might have failed.")

    # Now plot the throughput vs mldProbLink1 for each mcs2 value
    plt.figure(figsize=(10, 6))
    for mcs2 in mcs2_values:
        mldProbLink1_vals = throughput_data[mcs2]['mldProbLink1']
        throughput_vals = throughput_data[mcs2]['throughput_total']

        # Sort the data by mldProbLink1
        sorted_indices = np.argsort(mldProbLink1_vals)
        mldProbLink1_vals = np.array(mldProbLink1_vals)[sorted_indices]
        throughput_vals = np.array(throughput_vals)[sorted_indices]

        plt.plot(mldProbLink1_vals, throughput_vals, marker='o', label=f"Link2 MCS={mcs2}")

    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Throughput (Mbps)')
    plt.title('Total Throughput vs mldProbLink1 for Different Link2 MCS')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(results_dir, 'throughput_vs_mldProbLink1.png'))
    plt.close()

    # Move result files to the experiment directory
    move_file('wifi-mld.dat', results_dir)

    # Save the git commit information
    with open(os.path.join(results_dir, 'git-commit.txt'), 'w') as f:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE)
        f.write(commit_info.stdout.decode())

def check_and_remove(filename):
    if os.path.exists(filename):
        response = input(f"Remove existing file {filename}? [Yes/No]: ").strip().lower()
        if response == 'yes':
            os.remove(filename)
            print(f"Removed {filename}")
        else:
            print("Exiting...")
            sys.exit(1)

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)

if __name__ == "__main__":
    main()
