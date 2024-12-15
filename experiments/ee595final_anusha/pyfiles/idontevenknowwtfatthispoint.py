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
    rng_run = 6
    payload_size = 1500
    simulation_time = 10  # seconds
    mldPerNodeLambda = 0.001
    nMldSta = 5
    mcs = 6
    mcs2 = 6
    channelWidth = 20
    channelWidth2 = 20
    mldProbLink1_values = [0.1, 0.3, 0.5, 0.7, 0.9]

    # EDCA Parameters to Vary
    acBECwminLink1_values = [16, 32]
    acBECwStageLink1_values = [6, 7]

    # Initialize data structures for combined variation
    delay_data_combined = {
        (cwmin, cwstage): {'mldProbLink1': [], 'e2e_delay': []}
        for cwmin in acBECwminLink1_values
        for cwstage in acBECwStageLink1_values
    }

    # Run simulations varying both acBECwminLink1 and acBECwStageLink1
    for cwmin in acBECwminLink1_values:
        for cwstage in acBECwStageLink1_values:
            for mldProbLink1 in mldProbLink1_values:
                cmd = (
                    f"./ns3 run 'single-bss-mld --rngRun={rng_run} "
                    f"--payloadSize={payload_size} --simulationTime={simulation_time} "
                    f"--nMldSta={nMldSta} --mldPerNodeLambda={mldPerNodeLambda} "
                    f"--channelWidth={channelWidth} --channelWidth2={channelWidth2} "
                    f"--mcs={mcs} --mcs2={mcs2} --mldProbLink1={mldProbLink1} "
                    f"--acBECwminLink1={cwmin} --acBECwStageLink1={cwstage}'"
                )
                print(f"Running simulation with acBECwminLink1={cwmin}, acBECwStageLink1={cwstage}, mldProbLink1={mldProbLink1}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Simulation failed with error:\n{result.stderr}")
                    continue  # Skip to the next iteration

                # Read the output data file
                if os.path.exists('wifi-mld.dat'):
                    with open('wifi-mld.dat', 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1]
                            tokens = last_line.strip().split(',')

                            try:
                                e2e_delay = float(tokens[6])
                            except (IndexError, ValueError) as e:
                                print(f"Error parsing e2e delay from line: {last_line}")
                                print(e)
                                continue

                            # Store the results
                            delay_data_combined[(cwmin, cwstage)]['mldProbLink1'].append(mldProbLink1)
                            delay_data_combined[(cwmin, cwstage)]['e2e_delay'].append(e2e_delay)
                        else:
                            print("No data in wifi-mld.dat. The simulation might have failed.")
                else:
                    print("wifi-mld.dat does not exist. The simulation might have failed.")

    # Plotting Combined Graph: Varying both acBECwminLink1 and acBECwStageLink1
    plt.figure(figsize=(12, 8))
    markers = ['o', 's', '^', 'D']  # Different markers for combinations
    linestyles = ['-', '--', '-.', ':']  # Different linestyles for combinations
    color_map = plt.cm.get_cmap('tab10')

    for idx, ((cwmin, cwstage), data) in enumerate(delay_data_combined.items()):
        mldProb = data['mldProbLink1']
        delays = data['e2e_delay']

        if not mldProb:
            print(f"No data collected for acBECwminLink1={cwmin}, acBECwStageLink1={cwstage}. Skipping plot for this configuration.")
            continue

        # Sort the data by mldProbLink1
        sorted_indices = np.argsort(mldProb)
        mldProb_sorted = np.array(mldProb)[sorted_indices]
        delays_sorted = np.array(delays)[sorted_indices]

        label = f"cwmin={cwmin}, cwstage={cwstage}"
        marker = markers[idx % len(markers)]
        linestyle = linestyles[idx % len(linestyles)]
        color = color_map(idx % color_map.N)

        plt.plot(mldProb_sorted, delays_sorted, marker=marker, linestyle=linestyle, color=color, label=label)

    plt.xlabel('mldProbLink1')
    plt.ylabel('End-to-End Delay (ms)')
    plt.title('E2E Delay vs mldProbLink1 for Different acBECwminLink1 and acBECwStageLink1')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_mldProbLink1_acBECwminLink1_acBECwStageLink1.png'))
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
