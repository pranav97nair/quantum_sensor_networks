from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

from verification_programs import GHZProgram_verifier, GHZProgram_member
from verification_programs_v2 import GHZVerifierNode_v2, GHZMemberNode_v2
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 10
    max_ntest = 20   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    ntest_list = list(range(1, max_ntest+1))
    print(ntest_list)
    average_failures = [] 
    average_failures_v2 = []

    # Simulate original verification protocol
    for ntest in ntest_list:
        # Initialize verification programs
        programs, node_names = init_verification_programs(num_nodes, ntest, version=1)

        # Load network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        #           For 'perfect' network, max qubits allowed = 100
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)
        
        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 200

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
        average_failures.append(np.average(failure_rates))
        
        print(f"Simulation 1 with {ntest} test copies complete.")
    
    # Simulate modified verification protocol
    for ntest in ntest_list:
        # Initialize verification programs
        programs, node_names = init_verification_programs(num_nodes, ntest, version=2)

        # Load network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        #           For 'perfect' network, max qubits allowed = 100
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

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
        average_failures_v2.append(np.average(failure_rates))
        print(f"Simulation 2 with {ntest} test copies complete.")

    filename = "data/protocol_comparison_optim.txt"

    # Write parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, max_ntest={max_ntest}\n")
        f.write("# columns:\n")
        f.write("#  ntest   failure_rates_v1    failure_rates_v2\n")

    # Write output data to file
    write_to_file_multiy(filename, 
                         x=ntest_list, 
                         y1=average_failures, 
                         y2=average_failures_v2)
