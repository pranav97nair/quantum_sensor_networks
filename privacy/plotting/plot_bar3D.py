import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def plot_3d_bar(matrix, filename):
    dim = len(matrix[0])
    
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    x, y = np.meshgrid(np.arange(dim), np.arange(dim))
    x = x.flatten()
    y = y.flatten()
    z = np.zeros_like(x)  # Bottom starts at zero
    
    dx = dy = 0.8  # Width of bars
    #print(matrix)
    dz = matrix.flatten()

    ax.bar3d(x[::-1], y, z, dx, dy, dz, shade=True, cmap='viridis')

    ax.set_xticks(x)
    ax.set_yticks(y)
    if dim <= 8:
        x_labels = [f"<{i}|" for i in x[::-1]]
        y_labels = [f"|{i}>" for i in y]
        ax.set_xticklabels(x_labels)
        ax.set_yticklabels(y_labels)
    else:
        ax.set_xticklabels([])
        ax.set_yticklabels([])
    ax.view_init(elev=30, azim=60)
    plt.savefig(filename)

# Example usage
matrix = np.random.rand(8, 8)
plot_3d_bar(matrix, "test.png")