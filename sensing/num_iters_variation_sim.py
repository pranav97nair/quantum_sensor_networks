from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 3
    ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters_list = np.arange(100, 501, 50)
    state = "ghz"
    
    # Initialize programs
    programs, node_names = init_sensing_programs(num_nodes, ntest)

    # Configure network
    network_cfg = configure_perfect_network(node_names)
    """ network_cfg = configure_network(node_names,
                                    use_high_fidelity=False,
                                    use_optimistic=False) """

    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/num_iters_variation_{state}.log")

    phase_averages = []
    plus_outcome_rates = []
    estimations = []

    # Run simulation for varying number of iterations
    for num_iters in num_iters_list:
        plus_outcomes = 0
        # Run simulation num_iters times
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1
            )

            # Get parity results from each node
            k_parities = []
            for j in range(num_nodes):
                k_parities.append(results[j][0]["parity"])

            # A +^d outcome corresponds to the case when all nodes output parity +1
            if np.sum(k_parities) == num_nodes:
                plus_outcomes += 1

        # Get phase average
        phases = []
        for j in range(num_nodes):
            phases.append(results[j][0]['local phase'])
        phase_averages.append(np.average(phases))

        # Get plus outcome rate
        prob0 = plus_outcomes / num_iters
        plus_outcome_rates.append(prob0)

        # Estimate average phase
        arg = min(1, (prob0 * (2**num_nodes) - 1))
        est = np.arccos(arg) / num_nodes
        estimations.append(est)

        print(f"Simulation wih {num_iters} iterations complete.")
        
    # Write data to file
    filename = "data/num_iters_variation_perfect.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, ntest={ntest}, state={state}\n")
        f.write("# columns:\n")
        f.write("#  simulation_iterations   plus_outcome_rate   estimation   average_phase\n")
    
    write_to_file_multiy(filename=filename,
                        x=num_iters_list,
                        y1=plus_outcome_rates,
                        y2=estimations,
                        y3=phase_averages)

    