import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

optim_highfid = False

if optim_highfid:
    postfix = "_optimhf"
else:
    postfix = "_perfect"

filename = f"data/estimation_seeded_x1000{postfix}.txt"
true_avg, inv_est, mle_est, _, _, _ = read_from_file_multiy(filename, num_y=2)

inv_bias = []
mle_bias = []
""" for (x, y1, y2) in zip(true_avg, inv_est, mle_est):
        # Standard bias
        inv_bias.append(abs(x - y1))
        mle_bias.append(abs(x - y2)) """

# Circular square bias (adapted from Sean's circStats.m)
# sum of sin and cos angles
r1 = sum(np.exp([1j*pos for pos in inv_est]))
r2 = sum(np.exp([1j*pos for pos in mle_est]))

# mean direction
mu1 = np.angle(r1) % (2*np.pi)
mu2 = np.angle(r2) % (2*np.pi)

# mean resultant length
rBar1 = abs(r1) / len(inv_est)
rBar2 = abs(r2) / len(mle_est)

# dispersion
nu1 = np.sqrt(-2*np.log(rBar1))
nu2 = np.sqrt(-2*np.log(rBar2))

mse1 = sum((1-np.cos([pos-true_avg for pos in inv_est]))/len(inv_est))
mse2 = sum((1-np.cos([pos-true_avg for pos in mle_est]))/len(mle_est))

var1 = 1 - rBar1
var2 = 1 - rBar2

inv_bias2 = 2*rBar1*(np.sin((mu1-true_avg)/2)**2)
mle_bias2 = 2*rBar2*(np.sin((mu2-true_avg)/2)**2)


data_max = max(max(inv_est), max(mle_est))
data_max = max(data_max, true_avg[0])
data_min = min(min(inv_est), min(mle_est))
data_min = min(data_min, true_avg[0])
num_bins = 36
bin_width = (data_max - data_min) / num_bins
bins = np.arange(data_min, data_max, bin_width)
print(bins)

inv_counts, edges = np.histogram(inv_est, bins=bins)
mle_counts, _ = np.histogram(mle_est, bins=bins)
inv_freq = inv_counts * 100 / len(inv_est)
mle_freq = mle_counts * 100 / len(mle_est)

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
plt.axvline(x=x_ticks[true_edge], ymin=0, ymax=1, color='green', label=f"True value - {round(true_avg[0], 5)}")
plt.xticks(x_ticks, labels=tick_labels)
plt.ylabel("Proportion of results (%)")
plt.xlabel("Estimated values")

if optim_highfid:
    plt.title("1000-round parameter estimation\n(Optimistic, high-fidelity parameters)")
    plt.legend(loc='upper right')
    plt.ylim(top=30)
else:
    plt.title("1000-round parameter estimation\n(Perfect network parameters)")
    plt.legend(loc='upper left')
    plt.ylim(top=15)
plt.savefig(f"figures/barplot_seeded{postfix}.png")
