import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
ntest = 10
f_threshold = 1 / (2 * num_nodes**2)

filename = "data/fid_vs_pos_optim_highfid_x100.txt"
x, y = read_from_file(filename)
filename2 = "data/fid_vs_pos_optim_x100.txt"
x2, y2 = read_from_file(filename2)
filename3 = "data/fid_vs_pos_current_x100.txt"
x3, y3 = read_from_file(filename3)
filename4 = "data/fid_vs_pos_current_x100.txt"
x4, y4 = read_from_file(filename4)

color1 = 'tab:red'
color2 = 'tab:blue'
color3 = 'tab:green'
color4 = 'tab:orange'

fig, ax1 = plt.subplots()
ax1.set_xlabel('Target copy position')
#ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_ylabel('Target copy fidelity to GHZ')
ax1.scatter(x, y, s=15, color=color1, label='Optimistic, high-fidelity parameters')
ax1.scatter(x2, y2, s=15, color=color2, marker='x', label='Optimistic parameters')
ax1.scatter(x3, y3, s=15, color=color3, marker='v', label='Current parameters')
ax1.scatter(x4, y4, s=15, color=color4, marker='d', label='Current, high-fidelity parameters')

#ax1.axhline(y=f_threshold, c=color1, linestyle='--', alpha=0.5, label=f"Failure rate threshold for sensing")
#ax1.set_ylim(0, 0.5)
#ax1.set_yticks(yticks)
#ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)
ax1.set_title(f"Verification simulation (n={num_nodes}, ntest={ntest})")

""" ax2 = ax1.twinx()
ax2.tick_params(axis='y', labelcolor=color2)
ax2.set_ylabel('Average fidelity of target copy', color=color2)
ax2.scatter(x, y2, marker='x', s=20, color=color2) """

fig.legend(loc='upper right', bbox_to_anchor=(0.97, 0.4))
fig.tight_layout()
fig.savefig("figures/target_fid_vs_pos_x100.png")