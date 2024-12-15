import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

def control_c(signum, frame):
    print("\nExiting gracefully...")
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
    print(f"Results will be saved to: {results_dir}")

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Experiment parameters
    rng_run = 1
    payload_size = 1500
    simulation_time = 10  # seconds
    # Expanded lambda values from 0.1 to 1.0 with 0.1 increments
    mldPerNodeLambda_values = [0.00001, 0.0001, 0.001]  # 0.1, 0.2, ..., 1.0
    nMldSta = 10
    mcs = 4  # For Link 1
    mcs2=8
    channelWidth = 40  # For Link 1
    channelWidth2 = 40  # Fixed channel width for Link 2
    mldProbLink1_values = [round(0.1 * i, 1) for i in range(1, 10)]  # 0.1 to 0.9

    # Initialize data structures to store results
    # throughput_data: {lambda_val: {'mldProbLink1': [], 'throughput_total': []}}
    throughput_data = {lambda_val: {'mldProbLink1': [], 'throughput_total': []} for lambda_val in mldPerNodeLambda_values}

    total_simulations = len(mldPerNodeLambda_values) * len(mldProbLink1_values)
    print(f"Total simulations to run: {total_simulations}")

    simulation_count = 0  # To track progress

    for lambda_val in mldPerNodeLambda_values:
        print(f"\nRunning simulations for λ={lambda_val}")
        for mldProbLink1 in mldProbLink1_values:
            simulation_count += 1
            print(f"Simulation {simulation_count}/{total_simulations}: λ={lambda_val}, mldProbLink1={mldProbLink1}")

            cmd = (
                f"./ns3 run 'single-bss-mld "
                f"--rngRun={rng_run} "
                f"--payloadSize={payload_size} "
                f"--simulationTime={simulation_time} "
                f"--nMldSta={nMldSta} "
                f"--mldPerNodeLambda={lambda_val} "
                f"--channelWidth={channelWidth} "
                f"--channelWidth2={channelWidth2} "
                f"--mcs={mcs} "
                f"--mcs2={mcs2} "
                f"--mldProbLink1={mldProbLink1}'"
            )

            # Execute the simulation command
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

                        try:
                            # Get the required throughput metric from the tokens
                            # Index 5: mldThptTotal
                            throughput_total = float(tokens[5])

                            # Store the results
                            throughput_data[lambda_val]['mldProbLink1'].append(mldProbLink1)
                            throughput_data[lambda_val]['throughput_total'].append(throughput_total)
                            print(f"Throughput recorded: {throughput_total} Mbps")
                        except (IndexError, ValueError) as e:
                            print(f"Error parsing line: {last_line}. Error: {e}")
                    else:
                        print("No data in wifi-mld.dat. The simulation might have failed.")
            else:
                print("wifi-mld.dat does not exist. The simulation might have failed.")

    # Now plot the throughput vs mldProbLink1 for each lambda value
    plt.figure(figsize=(12, 8))
    color_map = plt.cm.get_cmap('viridis', len(mldPerNodeLambda_values))  # Use a colormap with enough distinct colors

    for idx, lambda_val in enumerate(mldPerNodeLambda_values):
        mldProbLink1_vals = throughput_data[lambda_val]['mldProbLink1']
        throughput_vals = throughput_data[lambda_val]['throughput_total']

        if not mldProbLink1_vals:
            print(f"No data to plot for λ={lambda_val}. Skipping...")
            continue

        # Sort the data by mldProbLink1 for better visualization
        sorted_indices = np.argsort(mldProbLink1_vals)
        mldProbLink1_sorted = np.array(mldProbLink1_vals)[sorted_indices]
        throughput_sorted = np.array(throughput_vals)[sorted_indices]

        plt.plot(
            mldProbLink1_sorted,
            throughput_sorted,
            marker='o',
            color=color_map(idx),
            label=f"λ={lambda_val}"
        )

    plt.xlabel('mldProbLink1')
    plt.ylabel('Total Throughput (Mbps)')
    plt.title('Total Throughput vs mldProbLink1 for Different Lambda Values')
    plt.legend(title='Lambda Values', bbox_to_anchor=(1.05, 1), loc='upper left')  # Place legend outside the plot
    plt.grid(True)
    plt.tight_layout()
    plot_path = os.path.join(results_dir, 'throughput_vs_mldProbLink1.png')
    plt.savefig(plot_path)
    plt.close()
    print(f"Throughput plot saved to: {plot_path}")

    # Move result files to the experiment directory
    move_file('wifi-mld.dat', results_dir)

    # Save the git commit information
    git_commit_path = os.path.join(results_dir, 'git-commit.txt')
    try:
        commit_info = subprocess.run(['git', 'show', '--name-only'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        with open(git_commit_path, 'w') as f:
            f.write(commit_info.stdout)
        print(f"Git commit information saved to: {git_commit_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to retrieve git commit information: {e.stderr}")

def check_and_remove(filename):
    if os.path.exists(filename):
        while True:
            response = input(f"Remove existing file {filename}? [Yes/No]: ").strip().lower()
            if response in ['yes', 'y']:
                try:
                    os.remove(filename)
                    print(f"Removed {filename}")
                except Exception as e:
                    print(f"Error removing {filename}: {e}")
                break
            elif response in ['no', 'n']:
                print("Exiting as per user request.")
                sys.exit(1)
            else:
                print("Please respond with 'Yes' or 'No'.")

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        try:
            shutil.move(filename, destination_dir)
            print(f"Moved {filename} to {destination_dir}")
        except Exception as e:
            print(f"Error moving {filename}: {e}")
    else:
        print(f"File {filename} does not exist. Skipping move.")

if __name__ == "__main__":
    main()
