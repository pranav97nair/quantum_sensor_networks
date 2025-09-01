from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    min_num_nodes = 3
    max_num_nodes = 7
    num_iters = 10
    ntest = 10   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    num_nodes_list = list(range(min_num_nodes, max_num_nodes+1, 1))
    print(num_nodes_list)
    average_failures1 = []
    average_failures2 = []
    average_failures3 = []
    average_failures4 = []

    # Simulation for network with optimistic parameters
    print(f"\nRunning simulations for optimistic network parameters")
    for num_nodes in num_nodes_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

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
        programs, node_names = init_verification_programs(num_nodes, ntest)

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
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load noisy network configuration
        # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
        #           On 'current' settings, max qubits allowed = 2 so verification is not possible
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # Modify qdevices to be able to hold 250 qubits
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

    # Simulation for perfect network parameters
    print(f"\nRunning simulations for perfect network parameters")
    for num_nodes in num_nodes_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load perfect network configuration
        network_cfg = configure_perfect_network(node_names)

        # Modiy qdevices to be able to hold 250 qubits
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
        average_failures4.append(np.average(failure_rates))
        print(f"Simulation with {num_nodes} nodes complete.")

    filename = "data/failure_rate_comparison_optim_perfect_v2_n8-10.txt"

    # Write parameter information and output data identifiers to file
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  min_num_nodes={min_num_nodes}, max_num_nodes={max_num_nodes}, num_iters={num_iters}, ntest={ntest}\n")
        f.write("# columns:\n")
        f.write("#  num_nodes   f_noisy_network    f_noisy_links_perfect_devices f_perfect_links_noisy_devices  f_perfect_network\n")
    
    # Write output data to file
    write_to_file_multiy(
        filename, 
        x=num_nodes_list,
        y1=average_failures1,
        y2=average_failures2,
        y3=average_failures3,
        y4=average_failures4
    )