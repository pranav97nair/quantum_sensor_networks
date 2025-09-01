import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
ntest = 10
num_iters = 1000
sim_number = 1

filename = f"data/{num_iters}_iters_optim_highfid_({ntest})_thresh01/sim{sim_number}.txt"
x, y1, y2, y3, _, _ = read_from_file_multiy(filename, num_y=3)

# Calculate expected probability of 0 <=> +1 outcome from average phase
phase_average = y3[-1]
exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2 

color1 = 'tab:red'
color2 = 'tab:blue'
color3 = 'tab:green'
color4 = 'tab:orange'
color5 = (0, 0, 0)

fig, ax1 = plt.subplots()
ax1.set_xlabel('Protocol iteration')
ax1.set_ylabel(r'Running estimation of $\overline{\theta}$')

ax1.plot(x, y2, color=color1, label='Running estimation')
ax1.axhline(y=phase_average, c=color3, linestyle='--', alpha=0.5, label=f"Actual value")
""" ax1.scatter(x2, y2, s=15, color=color2, marker='x', label='Optimistic parameters')
ax1.scatter(x3, y3, s=15, color=color3, marker='v', label='Current parameters')
ax1.scatter(x4, y4, s=15, color=color4, marker='d', label='Current, high-fidelity parameters') """

#ax1.set_ylim(0, 0.5)
#ax1.set_yticks(yticks)
#ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)
ax1.set_title(f"Network sensing (n={num_nodes}, ntest={ntest})\nOptimistic, high-fidelity parameters")

x_sensing = np.arange(1, len(x)+1, 1)
ax2 = ax1.twiny()
ax2.tick_params(axis='x', labelcolor=color5)
ax2.set_xlabel('Sensing iteration', color=color5)
ax2.scatter(x_sensing, y2, marker='x', s=5, color=color5, alpha=0)

fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.4))
fig.tight_layout()
fig.savefig(f"figures/running_estimation_{ntest}_tests_x1000_thresh01.png")