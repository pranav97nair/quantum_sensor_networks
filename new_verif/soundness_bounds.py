from utils import *
from utilsIO import *
import numpy as np
import matplotlib.pyplot as plt
import math
from pprint import pprint

def calc_sum(delta, k):
    elements = []
    range_end = min(delta, k-1)
    for x in range(0, range_end+1):
        elements.append(math.comb(k-1, x))
    return np.sum(elements)

if __name__ == '__main__':  
    ntest = 50
    delta_list = np.arange(0, ntest, 2)
    k_list = np.arange(ntest+1)

    # Dictionary to hold soundness values for various deltas
    s = {}

    for delta in delta_list:
        elems = []
        for k in k_list:
            sum_x = calc_sum(delta, k)
            coeff = k / (2**(ntest-1) * ntest)
            result = coeff * sum_x
            elems.append(result)
        s[delta] = max(elems)

    # Figure
    fig, ax1 = plt.subplots()
    ax1.plot(s.keys(), s.values())
    ax1.set_xlabel(r"$\Delta$")
    ax1.set_ylabel(r"S($\Delta$, N)")
    ax1.set_title(f"Verification soundness for N=50")
    fig.savefig("figures/soundness_bounds_vs_delta_n50.png")

