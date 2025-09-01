import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

optim_highfid = False
version = 1

if optim_highfid:
    postfix = "_optimhf"
else:
    postfix = "_perfect"

if version < 2:
    filename = f"data/estimation_seeded_x1000{postfix}.txt"
else:
    filename = f"data/estimation_seeded_x1000{postfix}_{version}.txt"

true_avg, inv_est, mle_est, _, _, _ = read_from_file_multiy(filename, num_y=2)

inv_bias = []
mle_bias = []
for (x, y1, y2) in zip(true_avg, inv_est, mle_est):
        # Standard bias
        inv_bias.append((x - y1))
        mle_bias.append((x - y2))

data_max = max(max(inv_bias), max(mle_bias))
data_min = min(min(inv_bias), min(mle_bias))
num_bins = 32
bin_width = (data_max - data_min) / num_bins
bins = np.arange(data_min, data_max, bin_width)
print(bins)

inv_counts, edges = np.histogram(inv_bias, bins=bins)
mle_counts, _ = np.histogram(mle_bias, bins=bins)
inv_freq = inv_counts * 100 / len(inv_bias)
mle_freq = mle_counts * 100 / len(mle_bias)

print(inv_counts)
print(mle_counts)

labels = [f"bin{i}" for i in range(1, len(edges))]
edges = [round(num, 4) for num in edges[1:]]

x = np.arange(len(labels))
width = 0.4  # Width of each bar
x_ticks = [i+width for i in x]
tick_labels = []
for i in x :
    if list(x).index(i) % 5 == 0:
        tick_labels.append(str(edges[i]))
    else:
        tick_labels.append("")

#print(true_avg[0])
delta = true_avg[0]
true_edge = 0
for i in range(len(edges)):
    diff = abs(true_avg[0] - edges[i])
    if diff < delta:
        delta = diff
        true_edge = i

#print(true_edge)


plt.bar(x - width/2, inv_freq, width=width, color='skyblue', edgecolor='black', label='Inverse cosine estimation')
plt.bar(x + width/2, mle_freq, width=width, color='orange', edgecolor='black', label='Maximum likelihood estimation')
plt.xticks(x_ticks, labels=tick_labels)
plt.ylabel("Proportion of results (%)")
plt.xlabel("Estimation bias")

if optim_highfid:
    plt.title("1000-round parameter estimation\n(Optimistic, high-fidelity parameters)")
    plt.legend(loc='upper right')
    plt.ylim(top=15)
else:
    plt.title("1000-round parameter estimation\n(Perfect network parameters)")
    plt.legend(loc='upper left')
    plt.ylim(top=13)

if version < 2:
    plt.savefig(f"figures/barplot_seeded_bias{postfix}.png")
else:
    plt.savefig(f"figures/barplot_seeded_bias{postfix}_{version}.png")