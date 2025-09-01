import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

filename1 = "data/failure_rate_vs_link_fidelity_optim_v2.txt"
filename2 = "data/failure_rate_vs_link_psuccess_optim_v2.txt"
fidelity, y1 = read_from_file(filename1)
psuccess, y2 = read_from_file(filename2)

yticks = np.arange(0, 0.55, 0.05)

# Plot separate fidelity and psuccess simulation results
fig, ax1 = plt.subplots()
color = 'tab:red'
ax1.set_xlabel('Link Fidelity', color=color)
ax1.set_ylabel('Average Failure Rate')
ax1.plot(fidelity, y1, color=color, alpha=1)
#ax1.scatter(fidelity, y1, color='green', alpha=1)
ax1.tick_params(axis='x', labelcolor=color)
ax1.set_ylim(0, 0.5)
ax1.set_yticks(yticks)
ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)

ax2 = ax1.twiny()
color = 'tab:blue'
ax2.set_xlabel('Link Probability of Success', color=color)
ax2.plot(psuccess, y2, color=color, alpha=1)
#ax2.scatter(psuccess, y2, color='pink', alpha=1)
ax2.tick_params(axis='x', labelcolor=color)

fig.tight_layout()
fig.savefig("figures/failure_rate_vs_link_params_separate_optim_v2.png")