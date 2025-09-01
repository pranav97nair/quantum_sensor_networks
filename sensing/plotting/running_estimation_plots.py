from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
sim_number = 12
filename = f"data/3000_iteration_sims/sim{sim_number}.txt"
x, y1, y2, y3, _, _ = read_from_file_multiy(filename, num_y=3)

# Calculate expected probability of 0 <=> +1 outcome from average phase
phase_average = y3[-1]
#exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / (2 ** num_nodes)    # for +^d outcome
exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2                   # for overall +1 parity

# Select data to plot
start, end = 0, 3000
x = x[start:end]
y1 = y1[start:end]
y2 = y2[start:end]

fig1, ax1 = plt.subplots()
ax1.plot(x, y1, c='b', label=f"Running frequency")
ax1.axhline(y=exp_prob0, c='r', linestyle='--', label=f"Expected probability")
#ax1.fill_between(x, y1, exp_prob0, color='lightskyblue')
ax1.legend()
ax1.set_xlabel("Protocol iteration")
ax1.set_ylabel(f"Frequency of +1 overall parity")               # for overall +1 parity
#ax1.set_ylabel(f"Frequency of {'+'*num_nodes} outcome")        # for +^d outcome
ax1.set_title(f"Network sensing (n={num_nodes})")
fig1.savefig(f"figures/3000_iteration_plots/sim{sim_number}_probs.png")

fig2, ax2 = plt.subplots()
ax2.plot(x, y2, c='g', label="Running estimation")
ax2.axhline(y=phase_average, c='orange', linestyle='--', label="Actual value")
#ax2.fill_between(x, y2, phase_average, color='yellowgreen')
ax2.legend()
ax2.set_xlabel("Protocol iteration")
ax2.set_ylabel(r"Estimation of $\overline{\Theta}$")
ax2.set_title(f"Network sensing (n={num_nodes})")

fig2.savefig(f"figures/3000_iteration_plots/sim{sim_number}_avg_phase.png")