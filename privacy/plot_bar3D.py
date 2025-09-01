import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go

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


def plot_3d_bar_with_gradient(matrix, filename=None, layers=30):
    matrix = np.array(matrix)
    dim = matrix.shape[0]

    x, y = np.meshgrid(np.arange(dim), np.arange(dim))
    x = x.flatten()
    y = y.flatten()
    heights = matrix.flatten()

    dx = dy = 0.8
    traces = []

    for layer in range(layers):
        frac = layer / layers
        next_frac = (layer + 1) / layers
        dz = (next_frac - frac) * heights
        z = frac * heights

        color = next_frac  # Normalized height to simulate gradient
        colors = np.repeat(color, len(heights))

        trace = go.Bar3d(
            x=x,
            y=y,
            z=z,
            dx=dx,
            dy=dy,
            dz=dz,
            opacity=1.0,
            surfacecolor=colors,
            colorscale='Viridis',
            showscale=False
        )
        traces.append(trace)

    fig = go.Figure(data=traces)

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Value'),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
    )

    if filename:
        fig.write_html(filename)
    else:
        fig.savefig("figures/test.png")


if __name__ == '__main__':
    # Example usage
    matrix = np.random.rand(8, 8)
    plot_3d_bar_with_gradient(matrix, "figures/test")