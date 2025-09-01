from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
filename = "data/num_iters_variation_perfect.txt"
x, y1, y2, y3, _, _ = read_from_file_multiy(filename, num_y=3)

# Calculate expected probability of 0 <=> +1 outcome from average phase
phase_average = y3[-1]
exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / (2 ** num_nodes)

fig1, ax1 = plt.subplots()
ax1.plot(x, y1, c='b', label=f"Observed frequency")
ax1.axhline(y=exp_prob0, c='r', linestyle='--', label=f"Expected probability")
ax1.fill_between(x, y1, exp_prob0, color='lightskyblue')
ax1.legend()
ax1.set_xlabel("Number of protocol iterations")
ax1.set_ylabel(f"Frequency of {'+'*num_nodes} outcome")
fig1.savefig("figures/num_iters_variation_probs.png")

fig2, ax2 = plt.subplots()
ax2.plot(x, y2, c='g', label="Estimation")
ax2.axhline(y=phase_average, c='orange', linestyle='--', label="Actual value")
ax2.fill_between(x, y2, phase_average, color='yellowgreen')
ax2.legend()
ax2.set_xlabel("Number of protocol iterations")
ax2.set_ylabel(r"Estimation of $\overline{\Theta}$")

fig2.savefig("figures/num_iters_variation_avg_phase.png")