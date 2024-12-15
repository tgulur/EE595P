import csv
import matplotlib.pyplot as plt
from collections import defaultdict

def plot_total_throughput_vs_mldProbLink1(dat_file, output_image):
    """
    Reads the 'wifi-mld.dat' file and plots Total Throughput vs. mldProbLink1
    for both Link2 widths.

    Parameters:
    - dat_file (str): Path to the 'wifi-mld.dat' data file.
    - output_image (str): Filename for the saved plot image.
    """
    # Define column indices (0-based)
    mldProbLink1_idx = 30   # Column 31
    mldThptTotal_idx = 5    # Column 6
    channelWidth2_idx = 27   # Column 28

    # Initialize dictionaries to hold data for each Link2 width
    throughput_data = defaultdict(list)  # {channelWidth2: [(mldProbLink1, mldThptTotal), ...]}

    try:
        with open(dat_file, 'r') as file:
            reader = csv.reader(file)
            for row_num, row in enumerate(reader, start=1):
                # Ensure the row has enough columns
                if len(row) <= max(mldProbLink1_idx, mldThptTotal_idx, channelWidth2_idx):
                    print(f"Skipping row {row_num}: insufficient columns.")
                    continue

                try:
                    mldProbLink1 = float(row[mldProbLink1_idx])
                    mldThptTotal = float(row[mldThptTotal_idx])
                    channelWidth2 = float(row[channelWidth2_idx])
                except ValueError:
                    print(f"Skipping row {row_num}: invalid data.")
                    continue

                # Store the data
                throughput_data[channelWidth2].append((mldProbLink1, mldThptTotal))
    except FileNotFoundError:
        print(f"Error: The file '{dat_file}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading '{dat_file}': {e}")
        return

    if not throughput_data:
        print("No valid data found to plot.")
        return

    # Prepare plot
    plt.figure(figsize=(10, 6))

    # Define markers and colors for different Link2 widths
    markers = ['o', 's']  # Add more markers if more Link2 widths exist
    colors = ['lightblue', 'orange']  # Add more colors if more Link2 widths exist

    # Sort the Link2 widths for consistent plotting
    sorted_link2_widths = sorted(throughput_data.keys())

    for idx, link2_width in enumerate(sorted_link2_widths):
        data_points = throughput_data[link2_width]
        if not data_points:
            print(f"No data for Link2 Width = {link2_width}. Skipping.")
            continue

        # Separate mldProbLink1 and mldThptTotal
        mldProbLink1 = [point[0] for point in data_points]
        mldThptTotal = [point[1] for point in data_points]

        # Scatter plot for individual data points
        plt.scatter(mldProbLink1, mldThptTotal, 
                    color=colors[idx % len(colors)], 
                    marker=markers[idx % len(markers)], 
                    alpha=0.6, edgecolors='w', 
                    s=100, label=f'Link2 Width = {link2_width} MHz')

        # Calculate average throughput for each mldProbLink1
        avg_throughput = defaultdict(list)
        for prob, thpt in data_points:
            avg_throughput[prob].append(thpt)
        
        # Compute the mean for each probability
        sorted_probs = sorted(avg_throughput.keys())
        mean_throughput = [sum(avg_throughput[prob])/len(avg_throughput[prob]) for prob in sorted_probs]

        # Line plot for average throughput
        plt.plot(sorted_probs, mean_throughput, 
                 color=colors[idx % len(colors)], 
                 marker=markers[idx % len(markers)], 
                 linestyle='-', 
                 linewidth=2)

    # Customize the plot
    plt.xlabel('mldProbLink1', fontsize=14)
    plt.ylabel('Total Throughput (Mbps)', fontsize=14)
    plt.title('Total Throughput vs. mldProbLink1 for Different Link2 Widths', fontsize=16)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    # Save and display the plot
    plt.savefig(output_image)
    print(f"Plot saved as '{output_image}'")
    plt.show()

if __name__ == "__main__":
    # Define the path to your data file and the desired output image filename
    dat_file = 'wifi-mld.dat'  # Ensure this file is in the same directory or provide the full path
    output_image = 'Total_Throughput_vs_mldProbLink1_Link2Widths.png'

    # Call the plotting function
    plot_total_throughput_vs_mldProbLink1(dat_file, output_image)
