from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
seed = 13579
num_iters = 250
network = 'perfect'
action_labels = {1: "Phase flip", 
                 2: "Bit flip"}

filename = f"data/running_multifunc_estimation/s{seed}_{network}_{num_iters}_iters.txt"
x, y0, y1, y2, _, _ = read_from_file_multiy(filename, num_y=3)

x, y0, y1, y2 = x[10:], y0[10:], y1[10:], y2[10:]


# Get actual phase average and difference
true_val_avg = np.nan
true_val_func1 = np.nan
true_val_func2 = np.nan
with open(filename, 'r') as f:
    line_num = 0
    for line in f:
        line_num += 1
        if line_num < 4:
            continue
        if line_num == 4:
            true_val_avg = float(line.split("=")[1])
        elif line_num == 5:
            true_val_func1 = float(line.split("=")[1])
        elif line_num == 6:
            true_val_func2 = float(line.split("=")[1])
        else:
            break

#print(true_val_avg, true_val_func1, true_val_func2)

# Plot comparison
fig, ax1 = plt.subplots()
# Running estimations
ax1.plot(x, y0, c='r', label="Phase average estimation")
ax1.plot(x, y1, c='g', label="Alternate function 1 estimation")
ax1.plot(x, y2, c='b', label="Alternate function 2 estimation")
# True values
ax1.axhline(y=true_val_avg, c='r', linestyle='--')
ax1.axhline(y=true_val_func1, c='g', linestyle='--')
ax1.axhline(y=true_val_func2, c='b', linestyle='--')

#ax1.set_xlim(0, len(x))

ax1.legend(loc='best')
ax1.set_xlabel("Sensing iteration")
ax1.set_ylabel(r"Running estimation")
ax1.set_title(f"Multi-function estimation (n={num_nodes})\n Perfect network parameters")

fig.savefig(f"figures/running_multifunc_est_s{seed}__{network}.png")