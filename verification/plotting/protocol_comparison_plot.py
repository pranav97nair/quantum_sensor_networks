import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

filename = "data/protocol_comparison_optim.txt"
x, y1, y2, _, _, _ = read_from_file_multiy(filename, num_y=2)

""" print(x)
print(y1)
print(y2) """

yticks = np.arange(0, 0.85, 0.05)
xticks = list(int(x[i]) for i in range(len(x)) if (i+1) % 2 == 0)

plt.plot(x, y1, c='b', label='Original protocol')
plt.plot(x, y2, c='g', label='Modified protocol')
plt.xlabel('Number of tests per stabilizer')
plt.ylabel('Average failure rate')
plt.title('Verification simulation (n=4)')
plt.legend()
plt.ylim(0, 0.8)
plt.yticks(yticks)
plt.xticks(xticks)
plt.grid(axis='y', color='grey', linestyle=':', linewidth=1, alpha=0.45)
plt.savefig('figures/protocol_comparison_optim.png')