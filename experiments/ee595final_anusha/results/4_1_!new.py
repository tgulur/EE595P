import numpy as np
import matplotlib.pyplot as plt

def load_data(file_name):
    # Load the data from the file
    data = np.loadtxt(file_name, delimiter=',')

    # Extract lambda and delay values (adjust column indices as per the correct file structure)
    lambda_values = data[:, 29]          # Lambda (column 30, index 29)
    queuing_delay_values = data[:, 8]    # Queuing Delay Total (column 9, index 8)
    access_delay_values = data[:, 11]    # Access Delay Total (column 12, index 11)
    e2e_delay_values = data[:, 14]       # E2E Delay Total (column 15, index 14)
    return lambda_values, queuing_delay_values, access_delay_values, e2e_delay_values

# Load data from the file
file_name = 'wifi-mld5.dat'  # Replace with your actual file name
lambda_values, queuing_delay_values, access_delay_values, e2e_delay_values = load_data(file_name)

# Sort the data by lambda for better plotting
sorted_indices = np.argsort(lambda_values)
lambda_values = lambda_values[sorted_indices]
queuing_delay_values = queuing_delay_values[sorted_indices]
access_delay_values = access_delay_values[sorted_indices]
e2e_delay_values = e2e_delay_values[sorted_indices]

# Plot the delays vs lambda
plt.figure(figsize=(10, 6))
plt.plot(lambda_values, queuing_delay_values, marker='o', label='Queuing Delay')
plt.plot(lambda_values, access_delay_values, marker='s', label='Access Delay')
plt.plot(lambda_values, e2e_delay_values, marker='^', label='End-to-End Delay')

# Set x-axis to logarithmic scale if needed
plt.xscale('log')

# Customize the plot
plt.title(f"Delay vs Offered Load (λ) for {file_name}")
plt.xlabel("Offered Load (λ) - Log Scale")
plt.ylabel("Delay (ms)")
plt.legend()
plt.grid(True, which="both", ls="--")

# Save the plot as an image file
plt.savefig(f"delay_vs_lambda_{file_name}.png", format="png")

# Display the plot
plt.show()
