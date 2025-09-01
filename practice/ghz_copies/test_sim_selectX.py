from utils import *
import numpy as np
from application import GHZProgram_select_measureX
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 3
    num_iters = 2
    n_test = 1
    n_total = 2*num_nodes*n_test
    use_highfid = False
    use_optimistic = False

    # Initialize programs
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    programs = {name: GHZProgram_select_measureX(name, node_names, n_test) for name in node_names}

    # Load the network configuration
    network_cfg = configure_perfect_network(node_names)

    # Run the simulation
    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters,
    )

    for k in range(num_iters):
        print("Iteration", k+1)
        node_qubits = []
        node_results = []
        for j in range(num_nodes):
            qubit = results[j][k]['qubits']
            node_qubits.append(qubit)
            node_result = results[j][k]['measurements']
            node_results.append(node_result)

        node_qubits = np.array(node_qubits)
        pprint(node_qubits)
        node_results = np.array(node_results)
        pprint(node_results)
        print(f"Unmeasured qubits per node: {len(node_qubits[0])}")
