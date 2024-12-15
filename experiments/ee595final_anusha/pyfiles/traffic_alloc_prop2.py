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
    mldPerNodeLambda = 0.001 # Set to 1.0 for saturated traffic
    nMldSta = 10
    mcs = 6  # For link 1
    mcs2 = 6  # Fixed MCS for link 2
    channelWidth_values = [40, 80]  # Different channel widths for link 2
    channelWidth = 20  # Fixed channel width for link 1
    mldProbLink1_values = [0.4, 0.6, 0.8, 0.9] 
    #mldProbLink1_values = [round(0.1 * i, 1) for i in range(1, 10)]  # 0.1 to 0.9

    # Initialize data structures to store results
    # delay_data: {channelWidth: {'mldProbLink1': [], 'e2e_delay': []}}
    delay_data = {}

    for cw in channelWidth_values:
        delay_data[cw] = {
            'mldProbLink1': [],
            'e2e_delay': []
        }

        # Run the ns3 simulation for each mldProbLink1
        for mldProbLink1 in mldProbLink1_values:
            cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --payloadSize={payload_size} --simulationTime={simulation_time} --nMldSta={nMldSta} --mldPerNodeLambda={mldPerNodeLambda} --channelWidth={channelWidth} --channelWidth2={cw} --mcs={mcs} --mcs2={mcs2} --mldProbLink1={mldProbLink1}'"
            print(f"Running simulation with channelWidth2={cw}, mldProbLink1={mldProbLink1}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Simulation failed with error:\n{result.stderr}")
                continue  # Skip to the next iteration

            # After each run, read the output data file and collect the e2e delay metrics
            if os.path.exists('wifi-mld.dat'):
                with open('wifi-mld.dat', 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]  # Assuming the last line contains the latest run data
                        tokens = last_line.strip().split(',')

                        try:
                            # Get the required e2e delay metric from the tokens
                            # Replace the index below with the correct one for e2e delay
                            # For example, if e2e delay is in column 6 (0-based index 5):
                            e2e_delay = float(tokens[6])
                        except (IndexError, ValueError) as e:
                            print(f"Error parsing e2e delay from line: {last_line}")
                            print(e)
                            continue  # Skip to the next iteration

                        # Store the results
                        delay_data[cw]['mldProbLink1'].append(mldProbLink1)
                        delay_data[cw]['e2e_delay'].append(e2e_delay)
                    else:
                        print("No data in wifi-mld.dat. The simulation might have failed.")
            else:
                print("wifi-mld.dat does not exist. The simulation might have failed.")

    # Now plot the e2e delay vs mldProbLink1 for each channelWidth
    plt.figure(figsize=(10, 6))
    for cw in channelWidth_values:
        mldProbLink1_vals = delay_data[cw]['mldProbLink1']
        e2e_delay_vals = delay_data[cw]['e2e_delay']

        if not mldProbLink1_vals:
            print(f"No data collected for channelWidth={cw}. Skipping plot for this configuration.")
            continue

        # Sort the data by mldProbLink1
        sorted_indices = np.argsort(mldProbLink1_vals)
        mldProbLink1_sorted = np.array(mldProbLink1_vals)[sorted_indices]
        e2e_delay_sorted = np.array(e2e_delay_vals)[sorted_indices]

        plt.plot(mldProbLink1_sorted, e2e_delay_sorted, marker='o', label=f"Channel Width2={cw} MHz")

    plt.xlabel('mldProbLink1')
    plt.ylabel('End-to-End Delay (ms)')
    plt.title('End-to-End Delay vs mldProbLink1 for Different Channel Widths')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_mldProbLink1.png'))
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
        if response in ['yes', 'y']:
            os.remove(filename)
            print(f"Removed {filename}")
        else:
            print("Exiting...")
            sys.exit(1)

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved {filename} to {destination_dir}")

if __name__ == "__main__":
    main()
