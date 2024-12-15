import csv
import matplotlib.pyplot as plt
from collections import defaultdict

def plot_delay_vs_mldProbLink1(dat_file, output_image):
    """
    Reads the 'wifi-mld.dat' file and plots End-to-End Delay vs. mldProbLink1
    for multiple Link2 MCS values.

    Parameters:
    - dat_file (str): Path to the 'wifi-mld.dat' data file.
    - output_image (str): Filename for the saved plot image.
    """
    # Define column indices (0-based)
    mldProbLink1_idx = 30          # Column 31
    mldMeanE2eDelayTotal_idx = 14  # Column 15
    mcs2_idx = 25                   # Column 26

    # Initialize dictionaries to hold data for each Link2 MCS
    delay_data = defaultdict(list)  # {mcs2: [(mldProbLink1, mldMeanE2eDelayTotal), ...]}

    try:
        with open(dat_file, 'r') as file:
            reader = csv.reader(file)
            for row_num, row in enumerate(reader, start=1):
                # Ensure the row has enough columns
                if len(row) <= max(mldProbLink1_idx, mldMeanE2eDelayTotal_idx, mcs2_idx):
                    print(f"Skipping row {row_num}: insufficient columns.")
                    continue

                try:
                    mldProbLink1 = float(row[mldProbLink1_idx])
                    mldMeanE2eDelayTotal = float(row[mldMeanE2eDelayTotal_idx])
                    mcs2 = row[mcs2_idx].strip()
                except ValueError:
                    print(f"Skipping row {row_num}: invalid data.")
                    continue

                # Store the data
                delay_data[mcs2].append((mldProbLink1, mldMeanE2eDelayTotal))
    except FileNotFoundError:
        print(f"Error: The file '{dat_file}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading '{dat_file}': {e}")
        return

    if not delay_data:
        print("No valid data found to plot.")
        return

    # Prepare plot
    plt.figure(figsize=(12, 8))

    # Define markers and colors for different Link2 MCS values
    markers = ['o', 's', '^', 'D', 'v', '>', '<', 'p', '*', 'h']  # Extend as needed
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'cyan', 'magenta', 'yellow', 'brown', 'pink']  # Extend as needed

    # Sort the MCS values for consistent plotting
    sorted_mcs2 = sorted(delay_data.keys())

    for idx, mcs2 in enumerate(sorted_mcs2):
        data_points = delay_data[mcs2]
        if not data_points:
            print(f"No data for Link2 MCS = {mcs2}. Skipping.")
            continue

        # Separate mldProbLink1 and mldMeanE2eDelayTotal
        mldProbLink1 = [point[0] for point in data_points]
        mldMeanE2eDelayTotal = [point[1] for point in data_points]

        # Scatter plot for individual data points
        plt.scatter(mldProbLink1, mldMeanE2eDelayTotal, 
                    color=colors[idx % len(colors)], 
                    marker=markers[idx % len(markers)], 
                    alpha=0.6, edgecolors='w', 
                    s=100, label=f'MCS2 = {mcs2}')

        # Calculate average delay for each mldProbLink1
        avg_delay = defaultdict(list)
        for prob, delay in data_points:
            avg_delay[prob].append(delay)

        # Compute the mean for each probability
        sorted_probs = sorted(avg_delay.keys())
        mean_delay = [sum(avg_delay[prob])/len(avg_delay[prob]) for prob in sorted_probs]

        # Line plot for average delay
        plt.plot(sorted_probs, mean_delay, 
                 color=colors[idx % len(colors)], 
                 marker=markers[idx % len(markers)], 
                 linestyle='-', 
                 linewidth=2)

    # Customize the plot
    plt.xlabel('mldProbLink1', fontsize=14)
    plt.ylabel('End-to-End Delay (ms)', fontsize=14)
    plt.title('End-to-End Delay vs. mldProbLink1 for Different Link2 MCS Values', fontsize=16)
    plt.legend(title='Link2 MCS')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    # Save and display the plot
    plt.savefig(output_image)
    print(f"Plot saved as '{output_image}'")
    plt.show()

if __name__ == "__main__":
    # Define the path to your data file and the desired output image filename
    dat_file = 'wifi-mld.dat'  # Ensure this file is in the same directory or provide the full path
    output_image = 'Delay_vs_mldProbLink1_Link2MCS.png'

    # Call the plotting function
    plot_delay_vs_mldProbLink1(dat_file, output_image)
