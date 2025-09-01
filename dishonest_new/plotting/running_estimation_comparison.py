from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
seed = 68024
num_dishonest = 2
dishonest_action = 2
action_labels = {1: "Phase flip", 
                 2: "Bit flip"}

postfix = f"dishonest{num_dishonest}_action{dishonest_action}"
file_perf = f"data/running_estimation/s{seed}_perfect_{postfix}.txt"
x, y1, y2, _, _, _ = read_from_file_multiy(file_perf, num_y=2)
file_opt = f"data/running_estimation/s{seed}_optimhf_{postfix}.txt"
_, z1, z2, _, _, _ = read_from_file_multiy(file_opt, num_y=2)


# Get actual phase average and difference
true_val = np.nan
with open(file_perf, 'r') as f:
    line_num = 0
    for line in f:
        line_num += 1
        if line_num < 5:
            continue
        true_val = float(line.split("=")[1])
        break


# Plot comparison
fig, ax1 = plt.subplots()
ax1.plot(x, y2, c='g', label="Perfect network")
ax1.plot(x, z2, c='b', label="Optimistic, highfid network")
if dishonest_action == 1:
    ax1.axhline(y=true_val, c='orange', linestyle='--', label="True value of average")
else:
    ax1.axhline(y=true_val, c='orange', linestyle='--', label="True value of difference")

ax1.legend(loc='best')
ax1.set_xlabel("Protocol iteration")
ax1.set_ylabel(r"Running estimation")
ax1.set_title(f"Network sensing (n={num_nodes})\n Dishonest nodes={num_dishonest}, Action={action_labels[dishonest_action]}")

fig.savefig(f"figures/running_estimation_s{seed}_dishonest{num_dishonest}_action{dishonest_action}.png")