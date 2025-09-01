from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 10
    ntest = 10   # n_total = 2*num_nodes*n_test
    state = "bell"
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = False

    # Retrieve parameters for the default depolarizing quantum link
    default_link_cfg = configure_link(use_highfid, use_optimistic)
    starting_fidelity = default_link_cfg.fidelity

    fidelity_list = np.linspace(starting_fidelity, 1.0, 40)
    print(f"Fidelity list: {fidelity_list}")

    avg_failures = []

    # Run simulation varying the link fidelity
    for fidelity in fidelity_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest, state)

        # Load network configuration
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        """ for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100 """

        # Modify the link configuration
        for link in network_cfg.links:
            link.cfg.fidelity = fidelity

        # Handle logging
        LogManager.set_log_level("WARNING")
        # Disable logging to terminal and enable logging to file
        logger = LogManager.get_stack_logger()
        logger.handlers = []
        LogManager.log_to_file(f"logs/fidelity_variation_{state}.log")

        # Run the simulation
        failure_rates = []
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1
            )
            f = results[0][0]["average failure rate"]
            #print(f"Average failure rate for iteration {k+1}: {f}")
            failure_rates.append(f)
        
        # Get average failure rate over all simulation iterations
        avg_failures.append(np.average(failure_rates))
        if (list(fidelity_list).index(fidelity)+1) % 5 == 0:
            print(f"Fidelity simulation {list(fidelity_list).index(fidelity)+1} complete.")
    

    # Write data to file for fidelity variation
    filename = f"data/fidelity_variation_{state}_current.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest},   state={state}\n")
        f.write("# columns:\n")
        f.write("#  fidelity   failure_rate\n")

    # Output
    write_to_file(
        x=fidelity_list,
        y=avg_failures, 
        filename=filename
    )