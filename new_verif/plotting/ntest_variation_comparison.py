import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
num_iters = 10
fid = 999
f_threshold = 1 / (2 * (num_nodes**2))

gen_set_file = f"data/ntest_variation_gen_set_f{fid}.txt"
new_file = f"data/simul_variation_f{fid}.txt"

gen_x, gen_y = read_from_file(gen_set_file)
new_x, new_y = read_from_file(new_file)

# Modifying generator data set
gen_x = [x * 2 * num_nodes for x in gen_x[4:]]
gen_y = gen_y[4:]

fig, ax1 = plt.subplots()
ax1.plot(gen_x, gen_y, c="orange", label="Generator set protocol")
ax1.scatter(gen_x, gen_y, c="orange", marker='v')
ax1.plot(new_x, new_y, c="blue", label="New protocol")
ax1.scatter(new_x, new_y, c="blue", marker='o')

ax1.set_ylim(0, 0.25)
ax1.set_xlabel("Total number of GHZ copies")
ax1.set_ylabel("Average failure rate")
ax1.set_title(f"Verification comparison (n={num_nodes}, #iters={num_iters}) \nOptimistic devices, link fidelity={fid/1000}")

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.75))
fig.savefig(f"figures/ntest_variation_comparison_f{fid}.png")


