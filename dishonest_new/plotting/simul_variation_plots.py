import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *
import sys

num_nodes = 4
num_iters = 10
network = sys.argv[1]   # 'perfect' or 'optimhf'


d1_a1_file = f"data/simul_variation_{network}_dishonest1_action1.txt"
d1_a2_file = f"data/simul_variation_{network}_dishonest1_action2.txt"
d2_a1_file = f"data/simul_variation_{network}_dishonest2_action1.txt"
d2_a2_file = f"data/simul_variation_{network}_dishonest2_action2.txt"

x, d1_a1_data = read_from_file(d1_a1_file)
_, d1_a2_data = read_from_file(d1_a2_file)
_, d2_a1_data = read_from_file(d2_a1_file)
_, d2_a2_data = read_from_file(d2_a2_file)

fig, ax1 = plt.subplots()
ax1.plot(x, d1_a1_data, c="orange", label="Phase flip applied by 1 node")
#ax1.scatter(x, d1_a1_data, c="orange", marker='v')
ax1.plot(x, d1_a2_data, c="blue", label="Bit flip applied by 1 node")
#ax1.scatter(x, d1_a2_data, c="blue", marker='o')
ax1.plot(x, d2_a1_data, c="green", label="Phase flip applied by 2 nodes")
#ax1.scatter(x, d2_a1_data, c="green", marker='v')
ax1.plot(x, d2_a2_data, c="red", label="Bit flip applied by 2 nodes")
#ax1.scatter(x, d2_a2_data, c="red", marker='o')

ax1.set_ylim(-0.05, 0.7)
ax1.set_xlabel("Total number of GHZ copies")
ax1.set_ylabel("Average failure rate")
ax1.set_title(f"Verification comparison (n={num_nodes}, #iters={num_iters}) \nDishonest actions")

fig.legend(loc='upper right', bbox_to_anchor=(0.9, 0.55))
fig.savefig(f"figures/simul_variation_plot_{network}.png")


