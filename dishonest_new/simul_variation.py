from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np
import sys

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    min_copies = int(sys.argv[1])
    max_copies = int(sys.argv[2])
    num_iters = 10
    state = "ghz"

    # Parameters for network configuration with noise
    network = sys.argv[3] # 'perfect', 'optimhf', or 'optim'

    # Parameters for dishonest part behavior
    num_dishonest = int(sys.argv[4])        # Between 1 and num_nodes-1, inclusive
    dishonest_action = int(sys.argv[5])     # 1 = apply phase flip, 2 = apply bit flip

    num_copies_list = list(np.arange(min_copies, max_copies+1, 5))
    avg_failures = []

    for copies in num_copies_list:
        # Initialize programs        
        ntest = copies - 1

        if num_dishonest >= 1:
            programs, node_names, dishonest_nodes = init_dishonest_verification(num_nodes, ntest, copies, num_dishonest, dishonest_action)
            #pprint(programs)
        else:
            programs, node_names = init_new_verification(num_nodes, ntest, copies)

        # Configure network
        if network == 'perfect':
            network_cfg = configure_perfect_network(node_names)
        elif network == 'optimhf':
            network_cfg = configure_network(node_names,
                                            use_high_fidelity=True,
                                            use_optimistic=True)
        elif network == 'optim':
            network_cfg = configure_network(node_names,
                                            use_high_fidelity=False,
                                            use_optimistic=True)
        else:
            raise ValueError("The network parameter must have value \'perfect\', \'optim\' or \'optimhf\'.")

        # Logging
        LogManager.set_log_level("ERROR")
        # Disable logging to terminal
        logger = LogManager.get_stack_logger()
        logger.handlers = []
        # Enable logging to file
        LogManager.log_to_file(f"logs/simul_variation.log")
        
        failure_rates = []
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1
            )
            failure_rate = results[0][0]['average failure rate']
            #print(f"Failure rate - Round {k+1} : {failure_rate}")
            failure_rates.append(failure_rate)

        avg_failures.append(np.mean(failure_rates))

        print(f"Simulation with {copies} copies complete.")
        print(f"Average failure rate : {avg_failures[-1]}")
    
    # Write data to file
    postfix = f"dishonest{num_dishonest}_action{dishonest_action}"
    filename = f"data/simul_variation_{network}_{postfix}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, num_dishonest={num_dishonest}, dishonest_action={dishonest_action}\n")
        f.write("# columns:\n")
        f.write("#   num_copies   avg_failure_rate\n")

    # Output
    write_to_file(
        x=num_copies_list,
        y=avg_failures,
        filename=filename
    )

    print(f"Simulation results stored in {filename}")