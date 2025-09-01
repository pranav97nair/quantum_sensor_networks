import numpy as np
import matplotlib.pyplot as plt
from application import GHZProgram

from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.run.stack.run import run # type: ignore
from squidasm.util.util import create_complete_graph_network # type: ignore

num_nodes = 6
node_names = [f"Node_{i}" for i in range(num_nodes)]

cfg = create_complete_graph_network(
    node_names,
    link_typ="perfect",
    link_cfg=PerfectQLinkConfig(state_delay=100),
    clink_typ="default",
    clink_cfg=DefaultCLinkConfig(delay=100)
)

programs = {name: GHZProgram(name, node_names) for name in node_names}

num_iters = np.arange(20, 21, 20)
exp_vals = []

for iterations in num_iters:
    results = run(config=cfg, programs=programs, num_times=iterations)
    measurements = []

    for k in range(iterations):
        reference_result = results[0][k]["result"]
        for j in range(num_nodes):
            node_result = results[j][k]["result"]
            assert node_result == reference_result # All nodes should measure the same result
            #print(f"Iteration {k}: Node {j} measures {node_result}")
        measurements.append(reference_result)

    #print(measurements)
    count_1 = sum(measurements)
    count_0 = iterations - count_1
    # Get Z eigenvalues corresponding to 0, 1 measurements for each node
    eigenvalues = [(-1)**(1-measurements[i]) for i in range(iterations)]
    exp_val = np.average(eigenvalues)

    # Print measurement results for current simulation
    print(f"Number of nodes: {num_nodes} \nIterations: {iterations}")
    print(f"State |{'0'*num_nodes}> was measured {count_0} times")
    print(f"State |{'1'*num_nodes}> was measured {count_1} times")
    print(f"Expectation value observed: {exp_val}")

    exp_vals.append(exp_val)
    
    if iterations % 100 == 0:
        print(f"Simulation with {iterations} iterations complete.")


""" plt.figure()
plt.plot(num_iters, exp_vals, c='r', ls='--', alpha=0.5, linewidth=2)
plt.scatter(num_iters, exp_vals, c="g")
plt.xlabel("Number of iterations")
plt.ylabel("Average Z eigenvalue measured")
plt.grid(axis="y")
plt.savefig("expval_vs_iterations") """



