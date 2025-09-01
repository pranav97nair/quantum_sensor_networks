from matplotlib import pyplot as plt
from utilsIO import *
import numpy as np
import math

num_nodes = 4
filename = "data/kraus_noise_fidelities.txt"

x, y1, y2, y3, y4, _ = read_from_file_multiy(filename, num_y=4)

""" plt.plot(x, y1, label="Amplitude damping")
plt.plot(x, y2, label="Phase damping")
plt.plot(x, y3, label="Depolarizing noise")
plt.plot(x, y4, label="Dephasing noise")
plt.xlabel(r"Noise parameter $\eta$")
plt.ylabel("Fidelity of state to perfect GHZ")
plt.legend()
plt.savefig("figures/kraus_noise_fidelities.png") """

norm_H = 0.5

for i in range(len(y1)):
    eps1 = 8 * norm_H * math.sqrt(1 - y1[i]**2)
    eps2 = 8 * norm_H * math.sqrt(1 - y2[i]**2)
    eps3 = 8 * norm_H * math.sqrt(1 - y3[i]**2)
    eps4 = 8 * norm_H * math.sqrt(1 - y4[i]**2)

    y1[i] = eps1
    y2[i] = eps2
    y3[i] = eps3
    y4[i] = eps4

plt.plot(x, y1, label="Amplitude damping")
plt.plot(x, y2, label="Phase damping")
plt.plot(x, y3, label="Depolarizing noise")
plt.plot(x, y4, label="Dephasing noise")
plt.xlabel(r"Noise parameter $\eta$")
plt.ylabel(r"Upper bound of $\epsilon$")
plt.legend()
plt.savefig("figures/kraus_noise_epsilon_bounds.png")
