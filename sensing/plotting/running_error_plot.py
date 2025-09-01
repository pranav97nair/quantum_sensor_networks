from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
num_iters = 3000
num_sims = 12

running_errors = []
for i in range(1, num_sims+1):
    # Read ith simulation results from file
    filename = f"data/{num_iters}_iteration_sims/sim{i}.txt"
    _, _, estimations, avg_phases, _, _ = read_from_file_multiy(filename, num_y=3)

    # Get phase average and calculate running error at each iteration
    phase_average = avg_phases[-1]
    running_errors.append([(estimations[k]-phase_average)**2 for k in range(num_iters)])

# Transpose error array so the rows correspond to the iteration and columns to the simulation
running_errors = np.array(running_errors).transpose()

average_errors = []
variance = []
for k in range(num_iters):
    average_errors.append(np.mean(running_errors[k]))
    variance.append(np.var(running_errors[k]))

iterations = list(range(1, num_iters+1))

# Find minimum error
min_err = min(average_errors)
print(min_err)
min_idx = average_errors.index(min_err)
print(min_idx+1)

# Select data to plot
start, end = 50, 3000
x = iterations[start:end]
y1 = average_errors[start:end]
y2 = variance[start:end]

fig, ax1 = plt.subplots()
color1 = 'red'
color2 = 'orange'
ax1.plot(x, y1, color=color1)
ax1.set_xlabel("Protocol iteration")
ax1.set_ylabel(r"Mean squared error of $\overline{\Theta}$")
ax1.axhline(y=min_err, linestyle='--', color=color1, alpha=0.7, label="Minimum MSE")
ax1.legend()

""" fig, ax1 = plt.subplots()
color1 = 'green'
color2 = 'orange'
ax1.loglog(x, y1, color=color1)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xlabel("Protocol iteration")
ax1.set_ylabel(r"Average estimation bias of $\overline{\Theta}$", color=color1)
ax1.axhline(y=min_err, linestyle='--', color=color1, alpha=0.8, label="Minimum average bias")
ax1.legend()

ax2 = ax1.twinx()
ax2.loglog(x, y2, color=color2, alpha=0.8)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylabel(f"Variance of estimation bias", color=color2) """

ax1.set_title(f"Parameter estimation (n={num_nodes}, #sims={num_sims})")
fig.tight_layout()
fig.savefig("figures/running_estimation_MSE_3000.png")