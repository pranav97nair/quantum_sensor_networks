import matplotlib.pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

n = 4                   # number of nodes
f = 1 / (2 * n**2)      # verification failure rate
epsilon = 1e-06         # difference to be set between max_c and (n-1)^2/4
num_m = 10

# Set values of c
min_c = 1e-05
max_c = ((n-1)**2)/4 - epsilon
num_c = 5
c_list = np.linspace(min_c, max_c, num_c)

# Calculate fidelity bounds
fid_list = [1 - 2*np.sqrt(c)/n - 2*n*f for c in c_list]

""" print(c_list)
print(fid_list) """

for i in range(num_c):
    c = c_list[i]
    fid = fid_list[i]

    # Set values of m
    min_m = 3 / (2 * c-epsilon)
    max_m = 3 / (2 * 1e-06)
    m_list = np.linspace(min_m, max_m, num_m)
    
    # Calculate soundness (probability of fidelity lower bound)
    p_list = [1 - n**(1 - 2*m*c/3) for m in m_list]

    # Calculate ntest
    ntest_list = [np.rint(m*(n**4)*np.log(n)) for m in m_list]

    print(f"c : {c}")
    print(f"min fidelity: {fid}")
    print(f"m list: {m_list}")
    print(f"p list: {p_list}")
    print(f"ntests: {ntest_list}")
    


