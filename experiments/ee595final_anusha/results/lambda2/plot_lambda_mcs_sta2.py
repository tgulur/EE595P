import os
import matplotlib.pyplot as plt
from collections import defaultdict

def parse_dat_files(results_dir):
    """Parse .dat files to extract throughput and E2E delay metrics."""
    files = [f for f in os.listdir(results_dir) if f.endswith('.dat')]
    results = {}

    for file in files:
        filepath = os.path.join(results_dir, file)
        try:
            # Extract parameters from the filename
            tokens = file.split('_')
            lambda_val = tokens[2]
            bw2 = tokens[4]
            mcs1 = tokens[6]
            mcs2 = tokens[8].split('.')[0]

            # Create a unique key for this combination
            key = (lambda_val, bw2, mcs1, mcs2)

            # Initialize metrics
            throughput_total = 0.0
            e2e_delay_total = 0.0
            valid_lines = 0

            # Read the file and process data
            with open(filepath, 'r') as f:
                for line in f:
                    tokens = line.strip().split(',')
                    if len(tokens) < 15:  # Ensure sufficient data
                        continue
                    try:
                        throughput_total += float(tokens[5])  # Throughput
                        e2e_delay_total += float(tokens[14])  # E2E delay
                        valid_lines += 1
                    except ValueError:
                        continue

            if valid_lines > 0:
                # Calculate averages
                throughput_avg = throughput_total / valid_lines
                e2e_delay_avg = e2e_delay_total / valid_lines
                results[key] = (throughput_avg, e2e_delay_avg)
        except Exception as e:
            print(f"Error parsing {file}: {e}")

    return results

def plot_results(results_dir, combinations_tested, throughput_total, e2e_delay_total):
    # Extract unique λ, BW2, and MCS2 values
    lambda_values = sorted(set(combo[0] for combo in combinations_tested))
    bw2_values = sorted(set(combo[2] for combo in combinations_tested))
    mcs2_values = sorted(set(combo[4] for combo in combinations_tested))

    # Convert results into dictionaries for easier plotting
    throughput_dict = {combo: throughput_total[i] for i, combo in enumerate(combinations_tested)}
    e2e_delay_dict = {combo: e2e_delay_total[i] for i, combo in enumerate(combinations_tested)}

    # 1. Throughput vs. BW2 for Different λ Values
    plt.figure()
    for λ in lambda_values:
        throughput_bw2 = [throughput_dict[(λ, 20, bw2, 4, 4)] for bw2 in bw2_values]
        plt.plot(bw2_values, throughput_bw2, marker='o', label=f"λ={λ}")
    plt.title('Throughput vs. BW2 for Different λ Values')
    plt.xlabel('BW2 (MHz)')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_bw2_lambda.png'))
    plt.close()

    # 2. E2E Delay vs. BW2 for Different λ Values
    plt.figure()
    for λ in lambda_values:
        e2e_delay_bw2 = [e2e_delay_dict[(λ, 20, bw2, 4, 4)] for bw2 in bw2_values]
        plt.plot(bw2_values, e2e_delay_bw2, marker='o', label=f"λ={λ}")
    plt.title('E2E Delay vs. BW2 for Different λ Values')
    plt.xlabel('BW2 (MHz)')
    plt.ylabel('End-to-End Delay (ms)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_bw2_lambda.png'))
    plt.close()

    # 3. Throughput vs. MCS2 for Fixed λ and BW2
    plt.figure()
    for bw2 in bw2_values:
        throughput_mcs2 = [throughput_dict[(0.001, 20, bw2, 4, mcs2)] for mcs2 in mcs2_values]
        plt.plot(mcs2_values, throughput_mcs2, marker='o', label=f"BW2={bw2} MHz")
    plt.title('Throughput vs. MCS2 for λ=0.001 and Different BW2')
    plt.xlabel('MCS2')
    plt.ylabel('Throughput (Mbps)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'throughput_vs_mcs2_bw2.png'))
    plt.close()

    # 4. E2E Delay vs. MCS2 for Fixed λ and BW2
    plt.figure()
    for bw2 in bw2_values:
        e2e_delay_mcs2 = [e2e_delay_dict[(0.001, 20, bw2, 4, mcs2)] for mcs2 in mcs2_values]
        plt.plot(mcs2_values, e2e_delay_mcs2, marker='o', label=f"BW2={bw2} MHz")
    plt.title('E2E Delay vs. MCS2 for λ=0.001 and Different BW2')
    plt.xlabel('MCS2')
    plt.ylabel('End-to-End Delay (ms)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(results_dir, 'e2e_delay_vs_mcs2_bw2.png'))
    plt.close()
