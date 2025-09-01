from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np

num_nodes = 4
num_iters = 1000
seed = 7200

file1 = f"data/t1/{num_iters}_iteration_sim_optimhf_{seed}.txt"
file2 = f"data/t2/{num_iters}_iteration_sim_optimhf_{seed}.txt"
#file05 = f"data/t05/{num_iters}_iteration_sim_optimhf_{seed}.txt"
file15 = f"data/t15/{num_iters}_iteration_sim_optimhf_{seed}.txt"
file_perf = f"data/t1/{num_iters}_iteration_sim_perfect_{seed}.txt"

x, _, y1, _, _, _ = read_from_file_multiy(file1, num_y=2)
_, _, y2, _, _, _ = read_from_file_multiy(file2, num_y=2)
#_, _, y05, _, _, _ = read_from_file_multiy(file05, num_y=2)
_, _, y15, _, _, _ = read_from_file_multiy(file15, num_y=2)
_, _, y_perf, _, _, _ = read_from_file_multiy(file_perf, num_y=2)


phase_average = 2.1115347763547287

fig2, ax2 = plt.subplots()
ax2.plot(x, y2, label="Failure threshold = 0.2")
ax2.plot(x, y15, label="Failure threshold = 0.15")
ax2.plot(x, y1, label="Failure threshold = 0.1")
#ax2.plot(x, y05, label="Failure threshold = 0.05")
ax2.plot(x, y_perf, label="Perfect network")
ax2.axhline(y=phase_average, c='pink', linestyle='--', label="Actual value")

ax2.legend()
ax2.set_xlabel("Sensing iteration")
ax2.set_ylabel(r"Running estimation of $\overline{\Theta}$")
ax2.set_title(f"Network sensing (n={num_nodes})\nVerification threshold comparison")

fig2.savefig(f"figures/threshold_variation_x{num_iters}_{seed}.png")