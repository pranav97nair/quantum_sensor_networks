import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
ntest = 10
f_threshold = 1 / (2 * num_nodes**2)

filename = "data/link_variation_multi_fom_x50.txt"
x, y1, y2, _, _, _ = read_from_file_multiy(filename, num_y=2)

""" print(f"x1: {x1}")
print(f"x2: {x2}")
print(f"y: {y}") """
yticks = np.arange(0, 0.55, 0.05)
color1 = 'tab:red'
color2 = 'tab:blue'

# Plot combined fidelity and psuccess simulation results
fig, ax1 = plt.subplots()
ax1.set_xlabel('EPR Link Fidelity')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_ylabel('Average Failure Rate', color=color1)
ax1.scatter(x, y1, s=20, color=color1)

ax1.axhline(y=f_threshold, c=color1, linestyle='--', alpha=0.5, label=f"Failure rate threshold for sensing")
#ax1.set_ylim(0, 0.5)
#ax1.set_yticks(yticks)
#ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)
ax1.set_title(f"Full set verification (n={num_nodes}, ntest={ntest})")

ax2 = ax1.twinx()
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylabel('Average fidelity of target copy', color=color2)
ax2.scatter(x, y2, marker='x', s=20, color=color2)

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.92))
fig.tight_layout()
fig.savefig("figures/link_variation_multi_fom_x50.png")