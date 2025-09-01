import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
ntest = 10
f_threshold = 1 / (2 * num_nodes**2)

filename = "data/failure_rate_vs_link_fidelity_optim_x50.txt"
x, y = read_from_file(filename)

filename2 = "data/failure_rate_vs_link_fidelity_optim_x50_(2).txt"
x2, y2 = read_from_file(filename2)

filename3 = "data/failure_rate_vs_link_fidelity_optim_x50_(3).txt"
x2, y3 = read_from_file(filename3)

""" print(f"x1: {x1}")
print(f"x2: {x2}")
print(f"y: {y}") """
yticks = np.arange(0, 0.55, 0.05)

# Plot combined fidelity and psuccess simulation results
fig, ax1 = plt.subplots()
ax1.set_xlabel('Link Fidelity')
ax1.set_ylabel('Average Failure Rate')
ax1.scatter(x, y, s=15, color='tab:green', label="10 iterations")
#ax1.scatter(x, y2, s=15, color='tab:blue', label="20 iterations")
#ax1.scatter(x, y3, s=15, color='tab:orange', label="30 iterations")

ax1.axhline(y=f_threshold, c='r', linestyle='--', alpha=0.7, label=f"Failure threshold for sensing")
ax1.set_ylim(0, 0.5)
ax1.set_yticks(yticks)
ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)
ax1.set_title(f"Verification simulation (n={num_nodes}, ntest={ntest})")

""" ax2 = ax1.twiny()
ax2.set_xlabel('Link Probability of Success') """
#ax2.scatter(x2, y, marker='x', color='tab:red', alpha=0.8, s=12)

fig.legend(loc='upper right', bbox_to_anchor=(0.98, 0.92))
fig.tight_layout()
fig.savefig("figures/failure_rate_vs_link_fidelity_optim_x50.png")