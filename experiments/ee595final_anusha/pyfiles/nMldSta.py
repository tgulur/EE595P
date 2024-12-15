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

    # Move to ns3 top-level directory
    os.chdir('../../../../')

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Experiment Parameters
    lambda_val = 0.001
    rng_run = 1
    min_sta = 5
    max_sta = 30
    step_sta = 5
    sta_counts = range(min_sta, max_sta + 1, step_sta)
    channel_widths = [(20, 80), (40, 80), (20, 40)]  # (channelWidth, channelWidth2)

    # Run simulations for each combination of STA count and channel widths
    for channel_width, channel_width2 in channel_widths:
        for n_sta in sta_counts:
            print(f"Running simulation for nMldSta={n_sta}, ChannelWidth={channel_width}, ChannelWidth2={channel_width2}...")
            cmd = (f"./ns3 run 'single-bss-mld --rngRun={rng_run} --nMldSta={n_sta} "
                   f"--mldPerNodeLambda={lambda_val} --channelWidth={channel_width} "
                   f"--channelWidth2={channel_width2}'")
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                print(f"Simulation failed for nMldSta={n_sta}, ChannelWidth={channel_width}, ChannelWidth2={channel_width2}.")
                continue

    # Parse results
    sta_values, throughput_total = parse_results()

    # Generate plots
    plot_results(results_dir, sta_values, throughput_total)

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

def parse_results():
    sta_values = []
    throughput_total = []

    with open('wifi-mld.dat', 'r') as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.strip().split(',')
            if len(tokens) < 15:  # Adjust based on the actual data structure
                print(f"Skipping incomplete line: {line.strip()}")
                continue
            try:
                sta_values.append(int(float(tokens[0])))       # nMldSta value
                throughput_total.append(float(tokens[5]))      # Total Throughput
            except ValueError as e:
                print(f"Error parsing line: {line.strip()} - {e}")
                continue

    return sta_values, throughput_total

def plot_results(results_dir, sta_values, throughput_total):
    # Plot Throughput vs STA count
    plt.figure()
    plt.title('Throughput vs. Number of STAs')
    plt.xlabel('Number of MLD STAs')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.plot(sta_values, throughput_total, label='Total Throughput', marker='o')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_sta.png'))
    plt.close()

def move_file(filename, destination_dir):
    if os.path.exists(filename):
        shutil.move(filename, destination_dir)
        print(f"Moved {filename} to {destination_dir}")

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
