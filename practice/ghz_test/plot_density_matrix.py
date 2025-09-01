import numpy as np
import scipy.linalg as sci
import matplotlib.pyplot as plt
from utils import *
from plot_bar3D import plot_3d_bar

from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.run.stack.run import run # type: ignore
from squidasm.util.util import create_complete_graph_network # type: ignore

num_nodes = 4
num_iters = 1

def calculate_fidelities(ideal_state: np.ndarray, noisy_states: List[np.ndarray]):
    fidelities = list(
        np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
        for noisy_state in noisy_states
    )
    return fidelities

# Test simulation with full state
programs, node_names = init_GHZ_programs(num_nodes, measure_qubits=False, full_state=True)
cfg1 = configure_network(node_names, use_high_fidelity=False, use_optimistic=True)
#cfg2 = configure_perfect_network(node_names)

for k in range(num_iters):
    #print(f"Iteration: {k+1}")
    results1 = run(config=cfg1, programs=programs)
    full_state = results1[num_nodes-1][0]["state"]
    """ results2 = run(config=cfg2, programs=programs, num_times=1)
    ideal_state = results2[num_nodes-1][k]["state"] """

    #print(f"Ideal GHZ state between {num_nodes} nodes: \n{ideal_state}")
    #print(f"Dimensions: {len(ideal_state)}x{len(ideal_state[0])}")

    plot_3d_bar(full_state,"density_mat_optim_n4.png")
    