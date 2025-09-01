from utils import *
import numpy as np
from application import *
import random
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 3
    num_iters = 1
    ntest = 1
    ntotal = 2*num_nodes*ntest
    use_highfid = False
    use_optimistic = False

    # Initialize programs
    copies = range(ntotal)
    measure_copies = random.sample(copies, ntest)
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    programs = {name: GHZProgram_subroutines(name, node_names, measure_copies) for name in node_names}

    # Load the network configuration
    network_cfg = configure_perfect_network(node_names)
    #network_cfg = configure_network(node_names, use_highfid, use_optimistic)

    # Run the simulation
    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters,
    )

    error_rates = []

    """ for k in range(num_iters):
        print("Iteration", k+1)
        node_results = []
        for j in range(num_nodes):
            node_result = results[j][k]['measurements']
            node_results.append(node_result)

        node_results = np.array(node_results)
        print(node_results)

        sums = node_results.sum(axis=0)
        errors = list(
            1 if (sum % 2) != 0 else 0
            for sum in sums
        )
        print(errors)
        error_rate = sum(errors)/len(errors)
        #print(error_rate)
        error_rates.append(error_rate)

    print(f"Average error rate over {num_iters} iterations: {np.average(error_rates)}") """
        