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
    network = sys.argv[3] # 'perfect' or 'optimhf'
    link_fidelity = float(sys.argv[4]) if network == 'optimhf' else 1.0 # number between 0 and 1

    num_copies_list = list(np.arange(min_copies, max_copies+1, 8))
    avg_failures = []

    for num_copies in num_copies_list:
        # Initialize programs        
        ntest = num_copies - 1
        programs, node_names = init_new_verification(num_nodes, ntest, num_copies)

        # Configure network
        if network == 'perfect':
            network_cfg = configure_perfect_network(node_names)
        elif network == 'optimhf':
            network_cfg = configure_network(node_names,
                                            use_high_fidelity=True,
                                            use_optimistic=True)
            # Modify the link configuration
            for link in network_cfg.links:
                link.cfg.fidelity = link_fidelity
        else:
            raise ValueError("The network parameter must have value \'perfect\' or \'optimhf\'")

        # Logging
        LogManager.set_log_level("WARNING")
        # Disable logging to terminal
        logger = LogManager.get_stack_logger()
        logger.handlers = []
        # Enable logging to file
        LogManager.log_to_file(f"logs/num_copies_variation.log")
        
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

        print(f"Simulation with {num_copies} copies complete.")
        print(f"Average failure rate : {avg_failures[-1]}")
    
    # Write data to file
    if network == "optimhf":
        postfix = f"f{int(link_fidelity*1000)}"
    else:
        postfix = network
    filename = f"data/simul_variation_{postfix}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, link_fidelity={link_fidelity}\n")
        f.write("# columns:\n")
        f.write("#   num_copies   avg_failure_rate\n")

    # Output
    write_to_file(
        x=num_copies_list,
        y=avg_failures,
        filename=filename
    )

    print(f"Simulation results stored in {filename}")

    
    