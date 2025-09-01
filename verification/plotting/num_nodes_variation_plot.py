import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
from utilsIO import *

# Read data from two files
filename = "data/failure_rate_comparison_optim_perfect_v2_n3-7.txt"
filenamep = "data/failure_rate_comparison_optim_perfect_v2_n8-10.txt"
num_nodes, y1, y2, y3, y4, _ = read_from_file_multiy(filename, num_y=4)
nump, y1p, y2p, y3p, y4p, _ = read_from_file_multiy(filenamep, num_y=4)

# Combine data from two files
num_nodes = np.append(num_nodes, nump)
y1 = np.append(y1, y1p)
y2 = np.append(y2, y2p)
y3 = np.append(y3, y3p)
y4 = np.append(y4, y4p)

# Print results
""" print(f"Results 1: {y1}\n")
print(f"Results 2: {y2}\n")
print(f"Results 3: {y3}\n")
print(f"Results 4: {y4}\n") """

# Plot single data set with scatter plus dashed line plot
""" plt.plot(num_nodes_list, average_failures, c='r', ls='--', alpha=0.5)
plt.scatter(num_nodes_list, average_failures, c='g')
plt.xlabel('Number of nodes in the network')
plt.ylabel('Average failure rate')
plt.title('Verification simulation (ntest=10)')
plt.savefig('failure_rate_vs_num_nodes_optim_highfid_v2.png') """

# Plot multiple data sets with bar chart
labels = [str(int(n)) for n in num_nodes]
x = np.arange(len(labels))
width = 0.2
yticks = np.arange(0, 0.55, 0.05)

fig, ax = plt.subplots()
rects1 = ax.bar(x - 1.5*width, y1, width, label="Optimistic links and devices")
rects2 = ax.bar(x - 0.5*width, y2, width, label="Optimistic links, perfect devices")
rects3 = ax.bar(x + 0.5*width, y3, width, label="Perfect links, optimistic devices")
rects4 = ax.bar(x + 1.5*width, y4, width, label="Perfect links and devices")

ax.set_ylabel("Average failure rate")
ax.set_xlabel("Number of nodes")
ax.set_title("Verification simulation (ntest=10)")
ax.set_xticks(x)
ax.set_xticklabels(labels)
""" ax.set_yticks(yticks)
ax.grid(axis='y', color='grey', linestyle='-', linewidth=1, alpha=0.3) """
ax.set_ylim(0, 0.6)
ax.legend(loc='upper left')

fig.tight_layout()
plt.savefig("figures/failure_rate_comparison_optim_perfect_v2.png")