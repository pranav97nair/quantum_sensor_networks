import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *
from pprint import pprint

num_nodes = 4
num_iters = 10
fidelity_set = [95, 97, 99]
f_threshold = 1 / (2 * (num_nodes**2))
f_threshold_full = 1 / (2 * (2**(2*num_nodes)))

full_set_data = {}
gen_set_data = {}

for f in fidelity_set:
    # Read full set data
    full_file = f"data/ntest_variation_full_set_f{f}.txt"
    x, y, _, _, _, _ = read_from_file_multiy(full_file, num_y=1)
    full_set_data[f] = y[4:]
    # Read gen set data
    gen_file = f"data/ntest_variation_gen_set_f{f}.txt"
    p, q, _, _, _, _ = read_from_file_multiy(gen_file, num_y=1)
    gen_set_data[f] = q[4:]

x = x[4:]

""" pprint(full_set_data)
print()
pprint(gen_set_data)
print(x) """


yticks = np.arange(0, 0.3, 0.05)
color1 = 'tab:orange'
color2 = 'tab:green'

# Plot combined fidelity and psuccess simulation results
fig, ax1 = plt.subplots()
ax1.set_xlabel('Number of test copies per stabilizer')
#ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_ylabel('Average Failure Rate')

marker_set = ['^', '+', 'o']
for i in range(len(fidelity_set)):
    f = fidelity_set[i]
    m = marker_set[i]
    ax1.scatter(x, gen_set_data[f], marker=m, s=20, color=color1)
    line1, = ax1.plot(x, gen_set_data[f], color=color1, label='Generator measurements')
    ax1.scatter(x, full_set_data[f], marker=m, s=20, color=color2)
    line2, = ax1.plot(x, full_set_data[f], color=color2, label='Full set measurements')


line3 = ax1.axhline(y=f_threshold, c=color1, linestyle='--', alpha=0.5, label=f"Passing threshold (generators)")
line4 = ax1.axhline(y=f_threshold_full, c=color2, linestyle='--', alpha=0.5, label=f"Passing threshold (full set)")
ax1.set_ylim(0, 0.25)
ax1.set_yticks(yticks)
#ax1.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.35)
ax1.set_title(f"Verification comparison (n={num_nodes}, #iters={num_iters}) \nOptimistic, high-fidelity parameters")

fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.85), handles=[line1, line2, line3, line4])
fig.tight_layout()
fig.savefig("figures/ntest_variation_comparison.png")