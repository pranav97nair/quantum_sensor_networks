from matplotlib import pyplot as plt
from utils import *
import numpy as np

from verification_programs import GHZProgram_verifier, GHZProgram_member
from verification_programs_v2 import GHZVerifierNode_v2, GHZMemberNode_v2
from squidasm.run.stack.run import run # type: ignore

def init_verification_programs(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZProgram_verifier(verifier, node_names, n_test)}
    programs.update({name: GHZProgram_member(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

def init_verification_programs_v2(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZVerifierNode_v2(verifier, node_names, n_test)}
    programs.update({name: GHZMemberNode_v2(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    max_num_iters = 50
    ntest = 10    # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = True
    use_optimistic = True

    num_iters_list = list(range(5, max_num_iters+1, 5))
    average_failures = []

    for num_iters in num_iters_list:
        programs, node_names = init_verification_programs_v2(num_nodes, ntest)

        # Load network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        #           For 'perfect' network, max qubits allowed = 100
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)
        
        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100

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
        print(f"Simulation with {num_iters} iterations complete.")

    plt.plot(num_iters_list, average_failures, c='r', ls='--', alpha=0.5, linewidth=2)
    plt.scatter(num_iters_list, average_failures, c='g')
    plt.xlabel('Number of simulation iterations')
    plt.ylabel('Average failure rate')
    plt.ylim(0,1)
    plt.title('Verification simulation (n=4, ntest=10)')
    plt.savefig('figures/failure_rate_vs_num_iters_optim_v2_n4.png')