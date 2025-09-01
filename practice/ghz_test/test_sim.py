import numpy as np
import scipy.linalg as sci
import matplotlib.pyplot as plt
from utils import *

from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.run.stack.run import run # type: ignore
from squidasm.util.util import create_complete_graph_network # type: ignore
from squidasm.util.util import get_qubit_state # type: ignore

num_nodes = 3
num_iters = 1

def calculate_fidelities(ideal_state: np.ndarray, noisy_states: List[np.ndarray]):
    fidelities = list(
        np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
        for noisy_state in noisy_states
    )
    return fidelities

# Test simulation with full state
programs, node_names = init_GHZ_programs(num_nodes, measure_qubits=False, full_state=True)
#cfg1 = configure_network(node_names, use_high_fidelity=False, use_optimistic=False)
cfg2 = configure_perfect_network(node_names)

for k in range(num_iters):
    #print(f"Iteration: {k+1}")
    """ results1 = run(config=cfg1, programs=programs)
    full_state = results1[num_nodes-1][0]["state"] """
    results2 = run(config=cfg2, programs=programs, num_times=1)
    ideal_state = results2[num_nodes-1][k]["state"]

    print(f"Ideal GHZ state between {num_nodes} nodes: \n{ideal_state}")
    print(f"Dimensions: {len(ideal_state)}x{len(ideal_state[0])}")
    print("")
    """ print(f"Simulated GHZ state between {num_nodes} nodes: \n{full_state}")
    print(f"Dimensions: {len(full_state)}x{len(full_state[0])}")
    print("") """

    """ fidelities = calculate_fidelities(ideal_state, [full_state])
    print(f"Fidelity: {fidelities[0]}") """

# Test simulation with reduced states
""" programs, node_names = init_GHZ_programs(num_nodes, measure_qubits=False)
cfg = configure_network(node_names, False, False)

for k in range(num_iters):
    print(f"Iteration: {k+1}")
    results = run(config=cfg, programs=programs)
    for j in range(num_nodes):
            node_state = results[j][0]["state"]
            print(f"{node_names[j]} has reduced state: \n{node_state}")
    print("") """

# Test simulation with measurements
""" programs, node_names = init_GHZ_programs(num_nodes)
cfg = configure_perfect_network(node_names)
results = run(config=cfg, programs=programs, num_times=num_iters)

measurements = []
for k in range(num_iters):
        reference_result = results[0][k]["result"]
        for j in range(num_nodes):
            node_result = results[j][k]["result"]
            assert node_result == reference_result # All nodes should measure the same result
            print(f"Iteration {k}: Node {j+1} measures {node_result}")
        measurements.append(reference_result)
        print("")
print(measurements) """



