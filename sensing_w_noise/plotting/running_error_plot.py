from utilsIO import *
from matplotlib import pyplot as plt
import numpy as np

num_nodes = 4
num_iters = 1000
ntest = 10
num_sims = 10

size = 1000
sim = 0
running_errors = []
for i in range(1, num_sims+1):
    # Read ith simulation results from file
    filename = f"data/{num_iters}_iters_optim_highfid_({ntest})/sim{i}.txt"
    x, _, estimations, avg_phases, _, _ = read_from_file_multiy(filename, num_y=3)

    # Identify smallest data set size
    if len(x) < size:
        size = len(x)
        sim = i
    
    # Get phase average and calculate running bias / mean squared error at each iteration
    phase_average = avg_phases[-1]
    bias = [abs(estimations[k]-phase_average) for k in range(size)]
    mean_sq_error = [(estimations[k]-phase_average)**2 for k in range(size)]

    running_errors.append(mean_sq_error)

# Ensure we only keep the smallest dataset size from each simulation run
for j in range(len(running_errors)):
    if len(running_errors[j]) > size:
        running_errors[j] = running_errors[j][:size]

# Transpose error array so the rows correspond to the iteration and columns to the simulation
running_errors = np.array(running_errors).transpose()

# Calculate error averages and variances for each simulation
average_errors = []
variance = []
for k in range(size):
    average_errors.append(np.mean(running_errors[k]))
    variance.append(np.var(running_errors[k]))

iterations = list(range(1, size+1))

# Find minimum error
min_err = min(average_errors)
print(min_err)
min_idx = average_errors.index(min_err)
print(min_idx+1)


fig, ax1 = plt.subplots()
color1 = 'red'
color2 = 'orange'
ax1.plot(iterations, average_errors, color=color1)
ax1.set_xticks(np.arange(2, size, 2))
ax1.set_xlabel("Sensing iteration")
ax1.set_ylabel(r"Mean squared error of $\overline{\theta}$")
ax1.axhline(y=min_err, linestyle='--', color=color1, alpha=0.7, label="Minimum MSE")
ax1.legend()

ax1.set_title(f"Noisy parameter estimation (n={num_nodes}, ntest={ntest})\nOptimistic, high-fidelity parameters")
fig.tight_layout()
fig.savefig("figures/running_estimation_MSE_optim_highfid_x1000_(10).png")

""" fig, ax1 = plt.subplots()
color1 = 'green'
color2 = 'orange'
ax1.plot(iterations, average_errors, color=color1)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xlabel("Sensing iteration")
ax1.set_ylabel(r"Average estimation bias of $\overline{\theta}$", color=color1)
ax1.axhline(y=min_err, linestyle='--', color=color1, alpha=0.8, label="Minimum average bias")
ax1.legend()

ax2 = ax1.twinx()
ax2.plot(iterations, variance, color=color2, alpha=0.8)
ax2.set_xticks(np.arange(2, size, 2))
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylabel(f"Variance of estimation bias", color=color2)

ax1.set_title(f"Noisy parameter estimation (n={num_nodes}, ntest={ntest})\nOptimistic, high-fidelity parameters")
fig.tight_layout()
fig.savefig("figures/running_estimation_bias_optim_highfid_x1000_(10).png") """