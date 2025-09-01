from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 10
    ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters = 10
    state = "ghz"

    #ntest_list = list(range(1, max_ntest+1))
    average_failure_rates = []

    # Initialize programs
    programs, node_names = init_verification_programs(num_nodes, ntest, state)

    # Configure network
    network_cfg = configure_perfect_network(node_names)
    """ network_cfg = configure_network(node_names,
                                    use_high_fidelity=False,
                                    use_optimistic=False) """
    
    if state == "bell":
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 200
    
    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/info_{state}.log")

    failure_rates = []
    # Run simulation
    for k in range(num_iters):
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

        """ for j in range(num_nodes):
            pprint(results[j][0]["target qubit"]) """

        f = results[0][0]['average failure rate']
        #print(f"Average failure rate : {f}")
        failure_rates.append(f)

    avg_failure = np.average(failure_rates)
    print(f"Average failure rate over {num_iters} iterations: {avg_failure}")


