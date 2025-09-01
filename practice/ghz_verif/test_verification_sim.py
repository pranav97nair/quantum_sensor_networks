from matplotlib import pyplot as plt
from utils import *
import numpy as np
from verification_programs import GHZProgram_verifier, GHZProgram_member
from squidasm.run.stack.run import run # type: ignore

def init_verification_programs(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZProgram_verifier(verifier, node_names, n_test)}
    programs.update({name: GHZProgram_member(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 3
    num_iters = 10
    max_ntest = 5     # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    avg_failures = []
    ntest_list = list(range(max_ntest, max_ntest+1, 2))
    print(ntest_list)
    for ntest in ntest_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)
        #print(programs)

        # Load perfect network configuration (max qubits allowed per node = 100)
        #network_cfg = configure_perfect_network(node_names)

        # Load noisy network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 200
        # Print qdevice configuration info for all nodes
        #pprint([stack.__dict__ for stack in network_cfg.stacks])
        
        # Run the simulation    
        failure_rates = []
        # Display average failure rates
        for k in range(num_iters):
            results = run(
                config=network_cfg,
                programs=programs,
                num_times=1,
            )
            avg_failure_rate = results[0][0]['average failure rate']
            failure_rates.append(avg_failure_rate)
            print(f"Iteration {k+1}, Average failure rate: {avg_failure_rate}")
        
        """ avg_failures.append(np.mean(failure_rates))
        print(f"Simulation for ntest={ntest} completed") """
    
    # Plot the results
    """ plt.plot(ntest_list, avg_failures)
    plt.xlabel('Number of tests per stabilizer')
    plt.ylabel('Average failure rate')
    plt.title('Verification simulation (n=3)')
    plt.savefig('failure_rate_vs_ntest_optim_highfid_n3.png') """
        