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

    # Number of MLD STAs to test
    lambda_val = 0.0001
    rng_run = 1
    min_sta = 5
    max_sta = 30
    step_sta = 5
    sta_counts = range(min_sta, max_sta + 1, step_sta)
    mcs =6
    mcs2=6
    bw1 = 80
    bw2 = 80

    # Run simulations for each STA count
    for n_sta in sta_counts:
        print(f"Running simulation for nMldSta={n_sta}...")
        cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --nMldSta={n_sta} --mldPerNodeLambda={lambda_val}'"
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Simulation failed for nMldSta={n_sta}. Check NS-3 logs for details.")
            continue

    # Parse results
    sta_values, throughput_l1, throughput_l2, throughput_total, queue_delay_l1, queue_delay_l2, queue_delay_total, access_delay_l1, access_delay_l2, access_delay_total, e2e_delay_l1, e2e_delay_l2, e2e_delay_total = parse_results()

    # Generate plots
    plot_results(results_dir, sta_values, throughput_l1, throughput_l2, throughput_total, queue_delay_l1, queue_delay_l2, queue_delay_total, access_delay_l1, access_delay_l2, access_delay_total, e2e_delay_l1, e2e_delay_l2, e2e_delay_total)

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

    with open('wifi-mld.dat', 'r') as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.strip().split(',')
            if len(tokens) < 49:
                print(f"Skipping incomplete line: {line.strip()}")
                continue
            try:
                sta_values.append(int(float(tokens[28])))          # nMldSta value
                throughput_l1.append(float(tokens[3]))             # Throughput Link 1
                throughput_l2.append(float(tokens[4]))             # Throughput Link 2
                throughput_total.append(float(tokens[5]))          # Total Throughput
                queue_delay_l1.append(float(tokens[6]))            # Queue Delay Link 1
                queue_delay_l2.append(float(tokens[7]))            # Queue Delay Link 2
                queue_delay_total.append(float(tokens[8]))         # Total Queue Delay
                access_delay_l1.append(float(tokens[9]))           # Access Delay Link 1
                access_delay_l2.append(float(tokens[10]))          # Access Delay Link 2
                access_delay_total.append(float(tokens[11]))       # Total Access Delay
                e2e_delay_l1.append(float(tokens[12]))             # End-to-End Delay Link 1
                e2e_delay_l2.append(float(tokens[13]))             # End-to-End Delay Link 2
                e2e_delay_total.append(float(tokens[14]))          # Total End-to-End Delay
            except ValueError as e:
                print(f"Error parsing line: {line.strip()} - {e}")
                continue

    return (sta_values, throughput_l1, throughput_l2, throughput_total,
            queue_delay_l1, queue_delay_l2, queue_delay_total,
            access_delay_l1, access_delay_l2, access_delay_total,
            e2e_delay_l1, e2e_delay_l2, e2e_delay_total)

def plot_results(results_dir, sta_values, throughput_l1, throughput_l2, throughput_total,
                queue_delay_l1, queue_delay_l2, queue_delay_total,
                access_delay_l1, access_delay_l2, access_delay_total,
                e2e_delay_l1, e2e_delay_l2, e2e_delay_total):
    
    # Plot Throughput vs STA count
    plt.figure()
    plt.title('Throughput vs. Number of STAs')
    plt.xlabel('Number of MLD STAs')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.plot(sta_values, throughput_l1, label='Throughput Link 1', marker='o')
    plt.plot(sta_values, throughput_l2, label='Throughput Link 2', marker='x')
    plt.plot(sta_values, throughput_total, label='Total Throughput', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_sta.png'))
    plt.close()

    # Plot Queue Delay vs STA count
    plt.figure()
    plt.title('Queue Delay vs. Number of STAs')
    plt.xlabel('Number of MLD STAs')
    plt.ylabel('Queue Delay (ms)')
    plt.grid(True)
    plt.plot(sta_values, queue_delay_l1, label='Queue Delay Link 1', marker='o')
    plt.plot(sta_values, queue_delay_l2, label='Queue Delay Link 2', marker='x')
    plt.plot(sta_values, queue_delay_total, label='Total Queue Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'queue_delay_vs_sta.png'))
    plt.close()

    # Plot Access Delay vs STA count
    plt.figure()
    plt.title('Access Delay vs. Number of STAs')
    plt.xlabel('Number of MLD STAs')
    plt.ylabel('Access Delay (ms)')
    plt.grid(True)
    plt.plot(sta_values, access_delay_l1, label='Access Delay Link 1', marker='o')
    plt.plot(sta_values, access_delay_l2, label='Access Delay Link 2', marker='x')
    plt.plot(sta_values, access_delay_total, label='Total Access Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'access_delay_vs_sta.png'))
    plt.close()

    # Plot End-to-End Delay vs STA count
    plt.figure()
    plt.title('End-to-End Delay vs. Number of STAs')
    plt.xlabel('Number of MLD STAs')
    plt.ylabel('End-to-End Delay (ms)')
    plt.grid(True)
    plt.plot(sta_values, e2e_delay_l1, label='E2E Delay Link 1', marker='o')
    plt.plot(sta_values, e2e_delay_l2, label='E2E Delay Link 2', marker='x')
    plt.plot(sta_values, e2e_delay_total, label='Total End-to-End Delay', marker='^')
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_sta.png'))
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
