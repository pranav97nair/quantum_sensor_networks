from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
sim_number = 3
num_dishonest = 1
action_labels = {}

postfix1 = f"dishonest{num_dishonest}_action1"
dis_file = f"data/sim{sim_number}/running_est_{postfix1}.txt"
x, _, y2, y3, _, _ = read_from_file_multiy(dis_file, num_y=3)

postfix2 = f"dishonest{num_dishonest}_action2"
dis_file2 = f"data/sim{sim_number}/running_est_{postfix2}.txt"
j, _, k2, k3, _, _ = read_from_file_multiy(dis_file2, num_y=3)

postfix3 = f"dishonest{num_dishonest}_action3"
dis_file3 = f"data/sim{sim_number}/running_est_{postfix3}.txt"
p, _, q2, q3, _, _ = read_from_file_multiy(dis_file3, num_y=3)


# Get actual phase average
phase_average = y3[-1]
assert(phase_average == q3[-1] == k3[-1])               

# Select data to plot
start, end = 0, len(x)
x = x[start:end]
y2 = y2[start:end]
k2 = k2[start:end]
q2 = q2[start:end]

# Define dishonest action labels
action_labels[1] = "No rotation"
action_labels[2] = "Incorrect basis"
action_labels[3] = "Incorrect rotation"

# Plot comparison
fig, ax1 = plt.subplots()
ax1.plot(x, y2, c='g', label=f"{action_labels[1]}")
ax1.plot(x, k2, c='r', label=f"{action_labels[2]}")
ax1.plot(x, q2, c='b', label=f"{action_labels[3]}")
ax1.axhline(y=phase_average, c='orange', linestyle='--', label="Actual value")

ax1.legend(loc='lower right')
ax1.set_xlabel("Protocol iteration")
ax1.set_ylabel(r"Estimation of $\overline{\Theta}$")
ax1.set_title(f"Running estimation of parameter average\n(n={num_nodes}, dishonest_nodes={num_dishonest})")

fig.savefig(f"figures/running_est_comparison_dishonest{num_dishonest}_sim{sim_number}.png")