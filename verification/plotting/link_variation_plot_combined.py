import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

filename = "data/failure_rate_vs_link_params_combined_optim_v2.txt"
x1, x2, y = read_from_file2x(filename)

""" print(f"x1: {x1}")
print(f"x2: {x2}")
print(f"y: {y}") """
yticks = np.arange(0, 0.55, 0.05)

# Plot combined fidelity and psuccess simulation results
fig, ax1 = plt.subplots()
ax1.set_xlabel('Link Fidelity')
ax1.set_ylabel('Average Failure Rate')
ax1.plot(x1, y, color='tab:green')
ax1.set_ylim(0, 0.5)
ax1.set_yticks(yticks)
ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)

ax2 = ax1.twiny()
ax2.set_xlabel('Link Probability of Success')
#ax2.scatter(x2, y, marker='x', color='tab:red', alpha=0.8, s=12)

fig.tight_layout()
fig.savefig("figures/failure_rate_vs_link_params_combined_optim_v2.png")

