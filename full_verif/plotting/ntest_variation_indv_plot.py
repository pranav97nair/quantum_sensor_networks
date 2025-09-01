import numpy as np
import matplotlib.pyplot as plt
from utilsIO import *

num_nodes = 4
num_iters = 10
fid = 999
f_threshold = 1 / (2 * (num_nodes**2))
f_threshold_full = 1 / (2 * (2**(2*num_nodes)))

plot_target_fids = False
plot_ntotals = True
plot_data = {}

# Read full set data
full_file = f"data/ntest_variation_full_set_f{fid}.txt"
x, y, z, _, _, _ = read_from_file_multiy(full_file, num_y=2)
plot_data['full'] = z[4:] if plot_target_fids else y[4:]

# Read gen set data
gen_file = f"data/ntest_variation_gen_set_f{fid}.txt"
p, q, r, _, _, _ = read_from_file_multiy(gen_file, num_y=2)
plot_data['gen'] = r[4:] if plot_target_fids else q[4:]

# Read select set data
if not plot_ntotals:
    select_file = f"data/ntest_variation_select_set_f{fid}.txt"
    a, b, c, _, _, _ = read_from_file_multiy(select_file, num_y=2)
    plot_data['select'] = c[4:] if plot_target_fids else b[4:]

plot_data['ntest'] = x[4:]
plot_data['ntotal_gen'] = [int(2*ntest*num_nodes) for ntest in x[4:]]
plot_data['ntotal_full'] = [int(2*ntest*(2**num_nodes)) for ntest in x[4:]]

print(plot_data['ntest'])
print(plot_data['ntotal_full'])
print(plot_data['ntotal_gen'])

#yticks = np.arange(0, 0.3, 0.05)
color1 = 'tab:orange'
color2 = 'tab:green'
color3 = 'tab:blue'

# Plot combined fidelity and psuccess simulation results
fig, ax1 = plt.subplots()

if plot_ntotals:
    ax2 = ax1.twiny()
    ax1.set_xlabel("Number of total GHZ copies", color=color1)
    ax1.tick_params(axis='x', labelcolor=color1)
    ax2.set_xlabel("Number of total GHZ copies", color=color2)
    ax2.tick_params(axis='x', labelcolor=color2)

    ax1.set_ylabel('Average Failure Rate')
    line4 = ax1.axhline(y=f_threshold, c=color1, linestyle='--', alpha=0.5, label=f"Passing threshold (generators)")
    line5 = ax1.axhline(y=f_threshold_full, c=color2, linestyle='--', alpha=0.5, label=f"Passing threshold (full set)")
    ax1.set_ylim(top=0.3)

    line1, = ax1.plot(plot_data['ntotal_gen'], plot_data['gen'], color=color1, marker='o', label='Generator measurements')
    line2, = ax2.plot(plot_data['ntotal_full'], plot_data['full'], color=color2, marker='^', label='Full set measurements')

else:
    line1, = ax1.plot(plot_data['ntest'], plot_data['gen'], color=color1, marker='o', label='Generator measurements')
    line2, = ax1.plot(plot_data['ntest'], plot_data['full'], color=color2, marker='^', label='Full set measurements')
    line3, = ax1.plot(plot_data['ntest'], plot_data['select'], color=color3, marker='x', label='Random n measurements')


    if plot_target_fids:
        ax1.set_ylabel('Fidelity of Target copy')
        ax1.set_xlabel('Number of test copies per stabilizer')
        ax1.set_ylim(-0.05, 1.0)
    
    else:
        ax1.set_ylabel('Average Failure Rate')
        line4 = ax1.axhline(y=f_threshold, c=color1, linestyle='--', alpha=0.5, label=f"Passing threshold (generators)")
        line5 = ax1.axhline(y=f_threshold_full, c=color2, linestyle='--', alpha=0.5, label=f"Passing threshold (full set)")
        ax1.set_ylim(top=0.3)
        line6 = ax1.axhline(y=f_threshold, c=color3, linestyle=':', alpha=0.5, label=f"Passing threshold (random set)")

ax1.set_title(f"Verification comparison (n={num_nodes}, #iters={num_iters}) \nOptimistic devices, link fidelity={fid/1000}")

fig.legend(loc='upper right', bbox_to_anchor=(0.95, 0.75))
fig.tight_layout()
if plot_target_fids:
    fig.savefig(f"figures/ntest_vs_target_fids_comparison_f{fid}.png")
elif plot_ntotals:
    fig.savefig(f"figures/failure_rate_vs_ntotal_comparison_f{fid}.png")
else:
    fig.savefig(f"figures/ntest_variation_comparison_f{fid}.png")