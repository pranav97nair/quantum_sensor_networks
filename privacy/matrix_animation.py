import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

def plot_3d_bar_animation(matrices, title="Test", filename="test_animation.mp4", fps=2, min_eta=0, max_eta=1):
    matrices = [np.array(m) for m in matrices]
    dim = matrices[0].shape[0]
    x, y = np.meshgrid(np.arange(dim), np.arange(dim))
    x = x.flatten()
    y = y.flatten()
    dx = dy = 0.8
    z_base = np.zeros_like(x)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    norm = Normalize(vmin=min(np.min(m) for m in matrices),
                     vmax=max(np.max(m) for m in matrices))
    cmap = plt.get_cmap('viridis')

    bars = None

    def update(frame):
        nonlocal bars
        ax.clear()
        dz = matrices[frame].flatten()
        colors = cmap(norm(dz))
        bars = ax.bar3d(x[::-1], y, z_base, dx, dy, dz, color=colors, shade=True)

        ax.set_zlim(0, norm.vmax)

        eta_range = max_eta - min_eta
        eta_val = round(min_eta + frame*eta_range/len(matrices), 2)
        ax.set_title(title + "\n" + r"$\eta$: " + f"{eta_val}")

        labels_x, labels_y = [], []
        for i in range(dim):
            if i == 0:
                labels_x.append(r"<$\overline{0}$|")
                labels_y.append(r"|$\overline{0}$>")
            elif i == dim-1:
                labels_x.append(r"<$\overline{1}$|")
                labels_y.append(r"|$\overline{1}$>")
            else:
                labels_x.append("")
                labels_y.append("")

        ax.set_xticks(np.arange(dim))
        ax.set_yticks(np.arange(dim))
        ax.set_xticklabels(labels_x[::-1])
        ax.set_yticklabels(labels_y)

        ax.view_init(elev=30, azim=60)

    anim = FuncAnimation(fig, update, frames=len(matrices), interval=1000/fps)

    # Save to file
    if filename.endswith(".gif"):
        anim.save(filename, writer=PillowWriter(fps=fps))
    elif filename.endswith(".mp4"):
        anim.save(filename, writer=FFMpegWriter(fps=fps))
    else:
        raise ValueError("Unsupported file type. Use '.gif' or '.mp4'")

    plt.close(fig)
    print(f"Animation saved to {filename}")

if __name__ == '__main__':
    matrices = [np.random.rand(8, 8) * (i + 1) for i in range(30)]
    plot_3d_bar_animation(matrices, filename="animations/test_animation.gif", fps=10)

