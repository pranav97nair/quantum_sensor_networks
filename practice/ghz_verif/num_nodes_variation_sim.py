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
    max_num_nodes = 10
    num_iters = 10
    ntest = 10   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    num_nodes_list = list(range(3, max_num_nodes+1, 1))
    print(num_nodes_list)
    average_failures1 = []
    average_failures2 = []
    average_failures3 = []

    # Simulation for network with optimistic parameters
    print(f"\nRunning simulations for optimistic network parameters")
    for num_nodes in num_nodes_list:
        # Initialize programs
        programs, node_names = init_verification_programs_v2(num_nodes, ntest)

        # Load network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 250
        
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
        average_failures1.append(np.average(failure_rates))
        print(f"Simulation with {num_nodes} nodes complete.")

    # Simulation for optimistic link and perfect device parameters
    print(f"\nRunning simulations for optimistic link and perfect device parameters")
    for num_nodes in num_nodes_list:
        # Initialize programs
        programs, node_names = init_verification_programs_v2(num_nodes, ntest)

        # Load noisy network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # Change device configurations to perfect for all nodes
        new_stack_cfg = configure_qdevice(is_perfect=True, num_qubits=250)
        for stack in network_cfg.stacks:
            stack.qdevice_cfg = new_stack_cfg
        
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
        average_failures2.append(np.average(failure_rates))
        print(f"Simulation with {num_nodes} nodes complete.")

    # Simulation for optimistic device and perfect link parameters
    print(f"\nRunning simulations for optimistic device and perfect link parameters")
    for num_nodes in num_nodes_list:
        # Initialize programs
        programs, node_names = init_verification_programs_v2(num_nodes, ntest)

        # Load noisy network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # Modiy qdevices to be able to hold 250 qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 250

        # Change link configuration to perfect for all nodes
        new_link_cfg = configure_link(link_typ="perfect")
        for link in network_cfg.links:
            link.cfg = new_link_cfg
        
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
        average_failures3.append(np.average(failure_rates))
        print(f"Simulation with {num_nodes} nodes complete.")

    # Print results
    """ print(f"Results 1: {average_failures1}\n")
    print(f"Results 2: {average_failures2}\n")
    print(f"Results 3: {average_failures3}\n") """

    # Plot single data set with scatter plus dashed line plot
    """ plt.plot(num_nodes_list, average_failures, c='r', ls='--', alpha=0.5)
    plt.scatter(num_nodes_list, average_failures, c='g')
    plt.xlabel('Number of nodes in the network')
    plt.ylabel('Average failure rate')
    plt.title('Verification simulation (ntest=10)')
    plt.savefig('failure_rate_vs_num_nodes_optim_highfid_v2.png') """

    # Plot multiple data sets with bar chart
    labels = [str(n) for n in num_nodes_list]
    x = np.arange(len(labels))
    width = 0.25

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width, average_failures1, width, label="Optimistic links and devices")
    rects2 = ax.bar(x, average_failures2, width, label="Optimistic links, perfect devices")
    rects3 = ax.bar(x + width, average_failures3, width, label="Perfect links, optimistic devices")

    ax.set_ylabel("Average failure rate")
    ax.set_xlabel("Number of nodes")
    ax.set_title("Verification simulation (ntest=10)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    fig.tight_layout()
    plt.savefig("failure_rate_comparison_optim_perfect_v2.png")