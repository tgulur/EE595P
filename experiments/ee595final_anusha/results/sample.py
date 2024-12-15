import numpy as np
import matplotlib.pyplot as plt

# List of MLD data files
dat_files = ['wifi-mld5.dat', 'wifi-mld6.dat', 'wifi-mld8.dat']  # Replace with actual file names

def load_data(file_name):
    # Load the data from the file
    data = np.loadtxt(file_name, delimiter=',')
    
    # Extract lambda and throughput values (adjust column indices as per the correct file structure)
    lambda_values = data[:, 29]  # Lambda (assumed column 34, index 33)
    throughput_values = data[:, 5]  # Throughput (assumed column 6, index 5)
    return lambda_values, throughput_values

def find_saturation_point(lambda_values, throughput_values):
    # Find the point where throughput stops increasing significantly
    for i in range(1, len(throughput_values)):
        # Check if throughput has plateaued (no significant increase)
        if throughput_values[i] <= throughput_values[i-1]:
            return lambda_values[i], throughput_values[i]  # Return saturation lambda and throughput value
    return lambda_values[-1], throughput_values[-1]  # In case throughput keeps increasing

# Plotting and analyzing each file
plt.figure(figsize=(10, 6))
for file_name in dat_files:
    # Load data from each file
    lambda_values, throughput_values = load_data(file_name)
    
    # Find the saturation point
    saturation_lambda, saturation_throughput = find_saturation_point(lambda_values, throughput_values)
    
    # Plot throughput vs lambda
    plt.plot(lambda_values, throughput_values, marker='o', label=f"{file_name} (Saturation at λ={saturation_lambda:.4f})")
    
    # Mark the saturation point
    plt.scatter([saturation_lambda], [saturation_throughput], color='red', zorder=5)
    plt.text(saturation_lambda, saturation_throughput, f" λ={saturation_lambda:.4f}", ha='right')

# Set x-axis to logarithmic scale
plt.xscale('log')

# Customize the plot
plt.title("Throughput vs Offered Load (λ) for Different MLD Files (Log Scale)")
plt.xlabel("Offered Load (λ) - Log Scale")
plt.ylabel("Throughput (Mbps)")
plt.legend()
plt.grid(True, which="both", ls="--")

# Save the plot as an image file
plt.savefig("throughput_vs_lambda_log.png", format="png")

# Display the plot
plt.show()
