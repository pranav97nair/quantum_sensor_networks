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
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    # Retrieve parameters for the default depolarizing quantum link
    default_link_cfg = configure_link(use_highfid, use_optimistic)
    starting_fidelity = default_link_cfg.fidelity
    starting_psuccess = default_link_cfg.prob_success
    starting_tcycle = default_link_cfg.t_cycle

    # Perfect t_cycle is calculated by dividing the link length d=50km by the speed of light in fiber c=200,000km/s and then converted to nanoseconds
    perfect_tcycle = (50 / 2e5) * 1e9

    fidelity_list = np.linspace(starting_fidelity, 1.0, 5)
    psuccess_list = np.linspace(starting_psuccess, 1.0, 5)
    tcycle_list = np.linspace(starting_tcycle, perfect_tcycle, 5)

    """ print(f"Fidelity list: {fidelity_list}")
    print(f"Probability of success list: {psuccess_list}") """

    #avg_failures = []
    avg_failures1 = []
    avg_failures2 = []

    # Run simulation varying the link fidelity
    for fidelity in fidelity_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load network configuration
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100

        # Modify the link configuration
        for link in network_cfg.links:
            link.cfg.fidelity = fidelity

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
        avg_failures1.append(np.average(failure_rates))
        if (list(fidelity_list).index(fidelity)+1) % 5 == 0:
            print(f"Fidelity simulation {list(fidelity_list).index(fidelity)+1} complete.")
    
    # Run simulation varying the link probability of success
    """ for psuccess in psuccess_list:
        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load network configuration
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100

        # Modify the link configuration
        for link in network_cfg.links:
            link.cfg.prob_success = psuccess

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
        avg_failures2.append(np.average(failure_rates))
        print(f"Psuccess simulation {list(psuccess_list).index(psuccess)+1} complete.") """
    
    # Run simulation varying link fidelity, probability of success and tcycle
    """ for i in range(len(fidelity_list)):
        fidelity = fidelity_list[i]
        psuccess = psuccess_list[i]
        tcycle = tcycle_list[i]

        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load network configuration
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100

        # Modify the link configuration
        for link in network_cfg.links:
            link.cfg.fidelity = fidelity
            link.cfg.prob_success = psuccess
            link.cfg.t_cycle = tcycle

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
        if (i+1) % 5 == 0:
            print(f"Link variation simulation {i+1} complete.") """

    # Write data to file for fidelity variation
    filename1 = "data/failure_rate_vs_link_fidelity_optim_v2.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest}\n")
        f.write("# columns:\n")
        f.write("#  fidelity   failure_rate\n")

    # Output
    write_to_file(
        x=fidelity_list,
        y=avg_failures1, 
        filename=filename1
    )

    # Write data to file for psuccess variation
    """ filename2 = "data/failure_rate_vs_link_psuccess_optim_v2.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest}\n")
        f.write("# columns:\n")
        f.write("#  psuccess   failure_rate\n")

    # Output
    write_to_file(
        x=psuccess_list,
        y=avg_failures2, 
        filename=filename2
    ) """

    """ # Write data to file for combined link variation
    filename = "data/failure_rate_vs_link_params_combined_optim_v2.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest}\n")
        f.write("# columns:\n")
        f.write("#  fidelity    psuccess   failure_rate\n")

    # Output
    write_to_file2x(
        x1=fidelity_list,
        x2=psuccess_list,
        filename=filename
    ) """
