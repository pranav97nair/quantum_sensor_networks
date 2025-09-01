import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

# Select simulation parameters
plot_perfect = True
plot_optim = False
plot_highfid = False
if plot_perfect:
    postfix = "perfect"
else:
    postfix = "optim" if plot_optim else "current"
    if plot_highfid:
        postfix += "highfid"

# Read data from files
ghz_filename = f"data/fidelity_variation_ghz_{postfix}.txt"
plus_filename = f"data/fidelity_variation_plus_{postfix}.txt"
bell_filename = f"data/fidelity_variation_bell_{postfix}.txt"
x, ghz_y = read_from_file(ghz_filename)
_, plus_y = read_from_file(plus_filename)
_, bell_y = read_from_file(bell_filename)

yticks = np.arange(0, 0.85, 0.05)
xticks = np.arange(0.6, 1.05, 0.05)

plt.plot(x, ghz_y, c='b', marker='o', label='GHZ state')
plt.plot(x, bell_y, c='g', marker='^', label='Two Bell pairs')
plt.plot(x, plus_y, c='r', marker='v', label='Four Plus states')
plt.xlabel('EPR link fidelity')
plt.ylabel('Average failure rate')
plt.title('Verification simulation (n=4)')
plt.legend()
plt.ylim(0, 0.8)
plt.yticks(yticks)
plt.xticks(xticks)
plt.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.45)
plt.savefig(f'figures/state_comparison_vs_fidelity_{postfix}.png')

