from matplotlib import pyplot as plt
from utils import *
import numpy as np
from verification_programs_v2 import GHZVerifierNode_v2, GHZMemberNode_v2
from squidasm.run.stack.run import run # type: ignore

###
#   Function to initialize programs for the network such that
#   the first node runs the GHZVerifier program
#   and all the other nodes run the GHZMember program
###
def init_verification_programs(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZVerifierNode_v2(verifier, node_names, n_test)}
    programs.update({name: GHZMemberNode_v2(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 5
    num_iters = 10
    max_ntest = 15     # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = False

    ntest_list = list(range(1, max_ntest+1))
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
        average_failure_rates.append(np.average(failure_rates))
        print(f"Simulation with {ntest} test copies complete.")
    
    plt.plot(ntest_list, average_failure_rates)
    plt.xlabel('Number of tests per stabilizer')
    plt.ylabel('Average failure rate')
    plt.title('Verification simulation (n=5)')
    plt.savefig('failure_rate_vs_ntest_perfect_v2.png')

        