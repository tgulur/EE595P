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
    min_lambda_exp = -5
    max_lambda_exp = -2
    step_size = 1
    channel_width2_values = [40, 80]  # Channel widths for link 2
    lambdas = [10 ** exp for exp in range(min_lambda_exp, max_lambda_exp + 1, step_size)]

    # Initialize data structures to store results
    # delays_data: {channel_width2: {'lambda': [], 'queuing_delay_link1': [], ... }}
    delays_data = {}

    for channel_width2 in channel_width2_values:
        delays_data[channel_width2] = {
            'lambda': [],
            'queuing_delay_link1': [],
            'queuing_delay_link2': [],
            'queuing_delay_total': [],
            'access_delay_link1': [],
            'access_delay_link2': [],
            'access_delay_total': [],
            'e2e_delay_link1': [],
            'e2e_delay_link2': [],
            'e2e_delay_total': []
        }

        # Run the ns3 simulation for each lambda
        for lambda_val in lambdas:
            cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --payloadSize={payload_size} --mldPerNodeLambda={lambda_val} --channelWidth2={channel_width2} --channelWidth=20 --mcs=6 --mcs2=6'"
            print(f"Running simulation with channelWidth2={channel_width2}, lambda={lambda_val}")
            subprocess.run(cmd, shell=True)

            # After each run, read the output data file and collect the delay metrics
            with open('wifi-mld.dat', 'r') as f:
                lines = f.readlines()
                last_line = lines[-1]  # Assuming the last line contains the latest run data
                tokens = last_line.strip().split(',')

                # Get the required delay metrics from the tokens
                # Column indices based on your data file structure
                # Index 6: mldMeanQueDelayLink1
                # Index 7: mldMeanQueDelayLink2
                # Index 8: mldMeanQueDelayTotal
                # Index 9: mldMeanAccDelayLink1
                # Index 10: mldMeanAccDelayLink2
                # Index 11: mldMeanAccDelayTotal
                # Index 12: mldMeanE2eDelayLink1
                # Index 13: mldMeanE2eDelayLink2
                # Index 14: mldMeanE2eDelayTotal

                queuing_delay_link1 = float(tokens[6])
                queuing_delay_link2 = float(tokens[7])
                queuing_delay_total = float(tokens[8])

                access_delay_link1 = float(tokens[9])
                access_delay_link2 = float(tokens[10])
                access_delay_total = float(tokens[11])

                e2e_delay_link1 = float(tokens[12])
                e2e_delay_link2 = float(tokens[13])
                e2e_delay_total = float(tokens[14])

                # Store the results
                delays_data[channel_width2]['lambda'].append(lambda_val)
                delays_data[channel_width2]['queuing_delay_link1'].append(queuing_delay_link1)
                delays_data[channel_width2]['queuing_delay_link2'].append(queuing_delay_link2)
                delays_data[channel_width2]['queuing_delay_total'].append(queuing_delay_total)
                delays_data[channel_width2]['access_delay_link1'].append(access_delay_link1)
                delays_data[channel_width2]['access_delay_link2'].append(access_delay_link2)
                delays_data[channel_width2]['access_delay_total'].append(access_delay_total)
                delays_data[channel_width2]['e2e_delay_link1'].append(e2e_delay_link1)
                delays_data[channel_width2]['e2e_delay_link2'].append(e2e_delay_link2)
                delays_data[channel_width2]['e2e_delay_total'].append(e2e_delay_total)

    # Now plot the delays vs lambda for each channel_width2 value
    for delay_type in ['queuing_delay', 'access_delay', 'e2e_delay']:
        for link in ['link1', 'link2', 'total']:
            plt.figure(figsize=(10, 6))
            for channel_width2 in channel_width2_values:
                lambda_values = delays_data[channel_width2]['lambda']
                delay_values = delays_data[channel_width2][f'{delay_type}_{link}']

                # Sort the data by lambda
                sorted_indices = np.argsort(lambda_values)
                lambda_values = np.array(lambda_values)[sorted_indices]
                delay_values = np.array(delay_values)[sorted_indices]

                plt.plot(lambda_values, delay_values, marker='o', label=f"Link2 Width={channel_width2} MHz")

            plt.xscale('log')
            plt.xlabel('Offered Load (λ) - Log Scale')
            plt.ylabel('Delay (ms)')
            plt.title(f'{delay_type.replace("_", " ").title()} ({link}) vs Offered Load')
            plt.legend()
            plt.grid(True, which='both', ls='--')

            # Save the plot
            plot_filename = f'{delay_type}_{link}_vs_lambda.png'
            plt.savefig(os.path.join(results_dir, plot_filename))
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
