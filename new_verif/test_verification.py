from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    num_iters = 1
    state = "ghz"

    # Initialize programs
    """ programs, node_names = init_verification_programs(num_nodes, 
                                                      ntest, 
                                                      select=num_nodes) """
    
    programs, node_names = init_new_verification(num_nodes, ntest, copies)

    # Configure network
    network_cfg = configure_perfect_network(node_names)
    """ network_cfg = configure_network(node_names,
                                    use_high_fidelity=True,
                                    use_optimistic=True) """

    # Logging
    LogManager.set_log_level("ERROR")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/test_new_verif.log")

    results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters
        )
    
    failure_rates = []
    for k in range(num_iters):
        failure_rate = results[0][k]['average failure rate']
        #print(f"Failure rate - Round {k+1} : {failure_rate}")
        failure_rates.append(failure_rate)

        """ density_mat = results[-1][k]['full state']
        print(f"Target state: \n{density_mat}\n") """

    print(f"Average failure rate : {np.mean(failure_rates)}")
    