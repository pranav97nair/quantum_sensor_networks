from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    max_ntest = 20
    #ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters = 10
    state = "plus"
    use_highfid = False
    use_optimistic = False

    ntest_list = list(range(1, max_ntest+1))
    print(ntest_list)
    average_failure_rates = []

    for ntest in ntest_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest, state)

        # Configure network
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)
        
        if state == "bell":
            for stack in network_cfg.stacks:
                stack.qdevice_cfg.num_qubits = 200
        
        # Logging
        LogManager.set_log_level("WARNING")
        # Disable logging to terminal and enable logging to file
        logger = LogManager.get_stack_logger()
        logger.handlers = []
        LogManager.log_to_file(f"logs/ntest_variation_{state}.log")

        failure_rates = []
        # Run simulation
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1
            )
            f = results[0][0]['average failure rate']
            failure_rates.append(f)

        avg_failure = np.average(failure_rates)
        average_failure_rates.append(avg_failure)

        print(f"Simulation with {ntest} test copies complete.")
        print(f"Average failure rate: {avg_failure}")
    
    filename = f"data/ntest_variation_{state}_current.txt"

    # Write parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, max_ntest={max_ntest}\n")
        f.write("# columns:\n")
        f.write("#  ntest   failure_rates\n")
    
    write_to_file(x=ntest_list, 
                  y=average_failure_rates,
                  filename=filename)