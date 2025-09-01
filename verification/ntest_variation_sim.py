from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 10
    max_ntest = 10     # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = False

    ntest_list = list(range(1, max_ntest+1))
    print(ntest_list)
    average_failure_rates = []

    for ntest in ntest_list:
        # Initialize verification programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        #           For 'perfect' network, max qubits allowed = 100
        network_cfg = configure_perfect_network(node_names)
        #network_cfg = configure_network(node_names, use_highfid, use_optimistic)
        
        # If needed, we can modify the configuration to increase num_qubits
        """ for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 200 """

        # Run the simulation
        failure_rates = []
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1,
            )
            f = results[0][0]["average failure rate"]
            #print(f"Average failure rate for iteration {k+1}: {f}")
            failure_rates.append(f)
        
        # Get average failure rate over all simulation iterations
        average_failure_rates.append(np.average(failure_rates))
        print(f"Simulation with {ntest} test copies complete.")
        print(f"Average failure rate: {np.average(failure_rates)}")
    
    filename = f"data/ntest_variation_perfect.txt"

    # Write parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, max_ntest={max_ntest}\n")
        f.write("# columns:\n")
        f.write("#  ntest   failure_rates\n")
    
    write_to_file(x=ntest_list, 
                  y=average_failure_rates,
                  filename=filename)

        