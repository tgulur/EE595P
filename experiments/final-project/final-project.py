import os
import subprocess
import shutil
import signal
import sys
from datetime import datetime
import matplotlib.pyplot as plt

def control_c(signum, frame):
    print("exiting")
    sys.exit(1)

signal.signal(signal.SIGINT, control_c)

def main():
    dirname = 'final-project'
    ns3_path = os.path.join('../../../../ns3')
    
    # Check if the ns3 executable exists
    if not os.path.exists(ns3_path):
        print(f"Please run this program from within the correct directory.")
        sys.exit(1)

    results_dir = os.path.join(os.getcwd(), 'results', f"{dirname}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    os.system('mkdir -p ' + results_dir)


    # Move to ns3 top-level directory
    os.chdir('../../../../')
    

    # Check for existing data files and prompt for removal
    check_and_remove('wifi-mld.dat')

    # Experiment parameters
    rng_run = 5
    max_packets = 1500
    min_lambda = -10
    max_lambda = -1
    step_size = 1
    lambdas = []
    nStas = 10  
    # lambda_val = 10 ** max_lambda # Use for saturation
    mcs1 = 4
    mcs2 = 8
    channelWidth = 20
    channelWidth2 = 20
    # cwmin_values = [3, 7, 15, 31, 63, 127, 255, 511, 1023]
    # Run the ns3 simulation for each distance
    # --acBECwminLink2={cwmin_values[i]}
    # --acBECwminLink1={cwmin_values[i]}  


    # edit the values here as necessary 
    for lam in range(min_lambda, max_lambda+1, step_size):
        lambda_val = 10 ** lam
        lambdas.append(lambda_val)
        cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --payloadSize={max_packets} --mldPerNodeLambda={lambda_val} --nMldSta={nStas} --mcs={mcs1} --mcs2={mcs2} --channelWidth={channelWidth} --channelWidth2={channelWidth2} --acBECwminLink1={255} --acBECwminLink2={255}'"
        subprocess.run(cmd, shell=True)

    # for i in range(9):
    #     cmd = f"./ns3 run 'single-bss-mld --rngRun={rng_run} --payloadSize={max_packets} --mldPerNodeLambda={lambda_val} --nMldSta={nStas} --mcs={mcs1} --mcs2={mcs2} --channelWidth={channelWidth} --channelWidth2={channelWidth2}'"
    #     subprocess.run(cmd, shell=True)

    # draw plots
    plt.figure(1)
    plt.figure(figsize=(8,6), dpi=80)
    plt.title('Throughput vs. CWMin (CW1 = 20, CW2 = 20, MCS1 = 4, MCS2 = 8)') # Change the title for each graph
    plt.xlabel('CWMin')
    plt.ylabel('Throughput (Mbps)')
    # plt.legend(loc="upper left")
    plt.grid()
    plt.xscale('log')
    throughput_l1 = []
    throughput_l2 = []
    throughput_total = []

    e2edelay_l1 = []
    e2edelay_l2 = []
    e2e_delay_total = []

    queuedelay_l1 = []
    queuedelay_l2 = []
    queuedelay_total = []

    accdelay_l1 = []
    accdelay_l2 = []
    accdelay_total = []

    with open('wifi-mld.dat', 'r') as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.split(',')
            throughput_l1.append(float(tokens[3]))
            throughput_l2.append(float(tokens[4]))
            throughput_total.append(float(tokens[5]))

            e2edelay_l1.append(float(tokens[12]))
            e2edelay_l2.append(float(tokens[13]))
            e2e_delay_total.append(float(tokens[14]))

            queuedelay_l1.append(float(tokens[6]))
            queuedelay_l2.append(float(tokens[7]))
            queuedelay_total.append(float(tokens[8]))

            accdelay_l1.append(float(tokens[9]))       
            accdelay_l2.append(float(tokens[10]))
            accdelay_total.append(float(tokens[11]))     

    # Change the plot titles and axis as necessary for each run
    plt.plot(lambdas, throughput_l1, marker='o', label="L1 throughput")
    plt.plot(lambdas, throughput_l2, marker='x', label="L2 throughput")
    plt.plot(lambdas, throughput_total, marker='^', label="Total Throughput")
    plt.savefig(os.path.join(results_dir, 'wifi-CW2020-MCS14-MCS28.png')) 

    plt.figure(2)
    plt.figure(figsize=(8,6), dpi=80)
    # plt.legend(loc="upper left")
    plt.title('E2E Delay vs. Offered Load (CW1 = 20, CW2 = 40, MCS1 = 4, MCS2 = 8)')
    plt.xlabel('Offered Load')
    plt.ylabel('E2E Delay')
    plt.grid()
    plt.xscale('log')
    plt.plot(lambdas, e2edelay_l1, marker = 'o')
    plt.plot(lambdas, e2edelay_l2, marker='x')
    plt.plot(lambdas, e2e_delay_total, marker='^')
    plt.savefig(os.path.join(results_dir,'wifi-e2e-CW2020-MCS14-MCS28.png'))

    plt.figure(3)
    plt.figure(figsize=(8,6), dpi=80)
    # plt.legend(loc="upper left")
    plt.title('Queue Delay vs. Offered Load (CW1 = 20, CW2 = 40, MCS1 = 4, MCS2 = 8)')
    plt.xlabel('Offered Load')
    plt.ylabel('Queue Delay')
    plt.grid()
    plt.xscale('log')
    plt.plot(lambdas, queuedelay_l1, marker = 'o')
    plt.plot(lambdas, queuedelay_l2, marker='x')
    plt.plot(lambdas, queuedelay_total, marker='^')
    plt.savefig(os.path.join(results_dir,'wifi-queue-CW2020-MCS14-MCS28.png'))

    plt.figure(4)
    plt.figure(figsize=(8,6), dpi=80)
    # plt.legend(loc="upper left")
    plt.title('Access Delay vs. Offered Load (CW1 = 20, CW2 = 40, MCS1 = 4, MCS2 = 8)')
    plt.xlabel('Offered Load')
    plt.ylabel('Access Delay')
    plt.grid()
    plt.xscale('log')
    plt.plot(lambdas, accdelay_l1, marker = 'o')
    plt.plot(lambdas, accdelay_l2, marker='x')
    plt.plot(lambdas, accdelay_total, marker='^')
    plt.savefig(os.path.join(results_dir,'wifi-acc-CW2020-MCS14-MCS28.png'))



    

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
