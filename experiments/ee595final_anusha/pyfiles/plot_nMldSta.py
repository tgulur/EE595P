import os
import matplotlib.pyplot as plt

def parse_dat_file(filepath):
    """
    Parses the given .dat file to extract STA count, throughput, and channel configuration.
    Adjust column indices based on the actual `.dat` file structure.
    """
    sta_values = []
    throughput_link1 = []
    throughput_link2 = []
    total_throughput = []
    channel_configs = []

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                tokens = line.strip().split(',')
                if len(tokens) < 15:  # Ensure enough columns exist
                    print(f"Skipping incomplete line: {line.strip()}")
                    continue
                try:
                    # Adjust indices based on your `.dat` structure
                    sta_value = int(float(tokens[0]))  # nMldSta
                    link1_throughput = float(tokens[3])  # Throughput on Link 1
                    link2_throughput = float(tokens[4])  # Throughput on Link 2
                    total = float(tokens[5])            # Total throughput
                    channel_width1 = int(float(tokens[10]))  # ChannelWidth1
                    channel_width2 = int(float(tokens[11]))  # ChannelWidth2

                    sta_values.append(sta_value)
                    throughput_link1.append(link1_throughput)
                    throughput_link2.append(link2_throughput)
                    total_throughput.append(total)
                    channel_configs.append((channel_width1, channel_width2))
                except ValueError as e:
                    print(f"Error parsing line {i}: {line.strip()} - {e}")
                    continue
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None, None, None, None, None
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None, None, None, None, None

    return sta_values, throughput_link1, throughput_link2, total_throughput, channel_configs


def plot_results(results_dir, sta_values, throughput_link1, throughput_link2, total_throughput, channel_configs):
    """
    Generates meaningful plots for throughput analysis.
    """
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    # Extract unique channel configurations
    unique_configs = sorted(set(channel_configs))

    # 1. Total Throughput vs. STA Count for Each Channel Configuration
    plt.figure(figsize=(10, 6))
    plt.title("Total Throughput vs. Number of STAs")
    plt.xlabel("Number of MLD STAs")
    plt.ylabel("Total Throughput (Mbps)")
    plt.grid(True)
    for config in unique_configs:
        config_throughput = [total_throughput[i] for i in range(len(sta_values)) if channel_configs[i] == config]
        config_sta = [sta_values[i] for i in range(len(sta_values)) if channel_configs[i] == config]
        plt.plot(config_sta, config_throughput, marker='o', label=f"BW1={config[0]}, BW2={config[1]}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "total_throughput_vs_sta.png"))
    plt.close()

    # 2. Throughput Ratio (Link1/Link2) vs. STA Count
    throughput_ratio = [
        l1 / l2 if l2 > 0 else 0 for l1, l2 in zip(throughput_link1, throughput_link2)
    ]
    plt.figure(figsize=(10, 6))
    plt.title("Throughput Ratio (Link1/Link2) vs. Number of STAs")
    plt.xlabel("Number of MLD STAs")
    plt.ylabel("Throughput Ratio (Link1/Link2)")
    plt.grid(True)
    plt.plot(sta_values, throughput_ratio, marker='o', color='purple', label="Throughput Ratio")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, "throughput_ratio_vs_sta.png"))
    plt.close()


def main():
    # Path to the .dat file
    dat_file = "/homes/anukashi/ns-3-dev/contrib/uwee595/experiments/11be-mlo/results/nMldSta/wifi-mld.dat"  # Update this with your .dat file path
    results_dir = "/homes/anukashi/ns-3-dev/contrib/uwee595/experiments/11be-mlo/results/nMldSta"  # Directory for saving plots

    # Parse the .dat file
    (sta_values, throughput_link1, throughput_link2, 
     total_throughput, channel_configs) = parse_dat_file(dat_file)

    if not all([sta_values, throughput_link1, throughput_link2, total_throughput, channel_configs]):
        print("Failed to parse data. Exiting...")
        return

    # Generate plots
    plot_results(results_dir, sta_values, throughput_link1, throughput_link2, total_throughput, channel_configs)


if __name__ == "__main__":
    main()
