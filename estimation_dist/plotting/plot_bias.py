import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

optim_highfid = False

if optim_highfid:
    postfix = "_optimhf"
else:
    postfix = "_perfect"

filename = f"data/estimation_x1000{postfix}.txt"
true_avg, inv_est, mle_est, _, _, _ = read_from_file_multiy(filename, num_y=2)

inv_bias = []
mle_bias = []
for (x, y1, y2) in zip(true_avg, inv_est, mle_est):
    # Standard bias
    inv_bias.append((x - y1))
    mle_bias.append((x - y2))

    # Circular square bias
    """ y1 = y1 % (2*np.pi)
    y2 = y2 % (2*np.pi)
    inv_bias2 = 2*np.sin((y1-x)/2)**2
    mle_bias2 = 2*np.sin((y2-x)/2)**2
    inv_bias.append(inv_bias2)
    mle_bias.append(mle_bias2) """

""" print(inv_bias)
print("")
print(mle_bias) """

data_max = max(max(inv_bias), max(mle_bias))
data_min = min(min(inv_bias), min(mle_bias))
data_range = data_max - data_min

num_bins = 32
bin_width = data_range / num_bins
bins = np.arange(data_min, data_max, bin_width)
print(bins)

inv_counts, edges = np.histogram(inv_bias, bins=bins)
mle_counts, _ = np.histogram(mle_bias, bins=bins)
inv_freq = inv_counts * 100 / len(inv_bias)
mle_freq = mle_counts * 100 / len(mle_bias)

""" plt.plot(bins[1:], inv_counts, label='Inverse cosine estimation')
plt.plot(bins[1:], mle_counts, label='Maximum likelihood estimation')
plt.legend()
plt.savefig("figures/lineplot_test.png") """


labels = [f"bin{i}" for i in range(1, len(edges))]
edges = [round(num, 3) for num in edges[1:]]

x = np.arange(len(labels))
width = 0.4  # Width of each bar
x_ticks = [i+width for i in x]
tick_labels = []
for i in x :
    if list(x).index(i) % 4 == 0:
        tick_labels.append(str(edges[i]))
    else:
        tick_labels.append("")


plt.bar(x - width/2, inv_freq, width=width, color='skyblue', edgecolor='black', label='Inverse cosine estimation')
plt.bar(x + width/2, mle_freq, width=width, color='orange', edgecolor='black', label='Maximum likelihood estimation')
plt.xticks(x_ticks, labels=tick_labels)
plt.ylabel("Proportion of results (%)")
plt.xlabel("Estimation bias (radians)")

if optim_highfid:
    plt.title("1000-round parameter estimation\n(Optimistic, high-fidelity parameters)")
    plt.ylim(top=10)
else:
    plt.title("1000-round parameter estimation\n(Perfect network parameters)")
    plt.ylim(top=16)
plt.legend()
plt.savefig(f"figures/barplot_bias{postfix}.png")
