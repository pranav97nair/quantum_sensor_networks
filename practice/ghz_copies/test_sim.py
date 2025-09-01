from utils import *
import numpy as np
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 3
    num_iters = 1
    n_test = 2
    n_total = 2*num_nodes*n_test

    use_highfid = True
    use_optimistic = True

    # Initialize the multiple copy GHZ programs
    programs, node_names = init_GHZ_programs(
        num_nodes=num_nodes,
        measure_qubits=True,
        full_state=False,
        num_copies=n_total
    )

    # Load the network configuration
    network_cfg = configure_perfect_network(node_names)
    #network_cfg = configure_network(node_names, use_highfid, use_optimistic)

    # Run the simulation
    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters,
    )

    # Read results and calculate error rate
    error_rates = []
    for k in range(num_iters):
        node_results = []
        for j in range(num_nodes):
            node_result = results[j][k]['measurements']
            node_results.append(node_result)

        node_results = np.array(node_results)
        pprint(node_results)
        
        sums = node_results.sum(axis=0)
        errors = list(
            1 if (sum % num_nodes) != 0 else 0
            for sum in sums
        )
        #print(errors)
        error_rate = sum(errors)/len(errors)
        #print(error_rate)
        error_rates.append(error_rate)

    print(f"Average error rate over {num_iters} iterations: {np.average(error_rates)}")

        