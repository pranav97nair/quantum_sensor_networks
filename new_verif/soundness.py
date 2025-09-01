from utils import *
from utilsIO import *
import numpy as np
import matplotlib.pyplot as plt
import math

def calc_sum(delta, k):
    elements = []
    range_end = min(delta, k-1)
    for x in range(0, range_end+1):
        elements.append(math.comb(k-1, x))
    return np.sum(elements)

if __name__ == '__main__':  

    ntest = 50
    delta_list = [1, 5, 7, 10]
    k_list = np.arange(ntest+1)
    #print(k_list)

    # Dictionary to hold soundness values for various deltas
    s = {}

    for delta in delta_list:
        s[delta] = []
        for k in k_list:
            sum_x = calc_sum(delta, k)
            coeff = k / (2**(ntest-1) * ntest)
            result = coeff * sum_x
            s[delta].append(result)
        
    # Figure
    fig, ax1 = plt.subplots()
    ax1.set_yscale("log")
    ax1.plot(k_list, s[1], label=r'$\Delta$=5%')
    ax1.plot(k_list, s[5], label=r'$\Delta$=10%')
    ax1.plot(k_list, s[7], label=r'$\Delta$=15%')
    ax1.plot(k_list, s[10], label=r'$\Delta$=20%')
    ax1.legend()
    ax1.set_xlabel(r"$k$")
    ax1.set_ylabel("Soundness")
    ax1.set_title(f"Verification soundness for various threshold failure rates")
    fig.savefig("figures/soundness_test_multithresh_logy.png")
