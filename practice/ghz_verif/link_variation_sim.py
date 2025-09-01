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
    num_iters = 10
    ntest = 10   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    default_link_cfg = configure_link(use_highfid, use_optimistic)
    starting_fidelity = default_link_cfg.fidelity
    starting_psuccess = default_link_cfg.prob_success
    starting_tcycle = default_link_cfg.t_cycle
    perfect_tcycle = (50 / 2e5) * 1e9

    fidelity_list = np.linspace(starting_fidelity, 1.0, 40)
    psuccess_list = np.linspace(starting_psuccess, 1.0, 40)
    tcycle_list = np.linspace(starting_tcycle, perfect_tcycle, 40)

    """ print(f"Fidelity list: {fidelity_list}")
    print(f"Probability of success list: {psuccess_list}") """

    avg_failures = []
    """ avg_failures1 = []
    avg_failures2 = [] """

    """ # Run simulation varying the link fidelity
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
        print(f"Fidelity simulation {list(fidelity_list).index(fidelity)+1} complete.")
    
    # Run simulation varying the link probability of success
    for psuccess in psuccess_list:
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
    for i in range(len(fidelity_list)):
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
        if (i+1) % 4 == 0:
            print(f"Link variation simulation {i+1} complete.")

    print(f"Average failure rates: {avg_failures}")

    # Plot separate fidelity and psuccess simulation results
    """ fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('Link Fidelity', color=color)
    ax1.set_ylabel('Average Failure Rate')
    ax1.plot(fidelity_list, avg_failures1, color=color)
    ax1.tick_params(axis='x', labelcolor=color)
    ax1.set_ylim(0, 1)

    ax2 = ax1.twiny()
    color = 'tab:blue'
    ax2.set_xlabel('Link Probability of Success', color=color)
    ax2.plot(psuccess_list, avg_failures2, color=color)
    ax2.tick_params(axis='x', labelcolor=color)
    
    fig.tight_layout()
    fig.savefig("failure_rate_vs_link_params_optim_v2.png") """

    # Plot combined fidelity and psuccess simulation results
    fig, ax1 = plt.subplots()
    ax1.set_xlabel('Link Fidelity')
    ax1.set_ylabel('Average Failure Rate')
    ax1.plot(fidelity_list, avg_failures, color='tab:red')
    ax1.set_ylim(-0.05, 1)

    ax2 = ax1.twiny()
    ax2.set_xlabel('Link Probability of Success')
    ax2.scatter(psuccess_list, avg_failures, marker='x',color='tab:green')

    fig.tight_layout()
    fig.savefig("failure_rate_vs_link_params_combined_optim_v2.png")