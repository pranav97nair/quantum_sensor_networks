import numpy as np
import time as t
import matplotlib.pyplot as plt
from utils import *
from error_comparison_sim import *

from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Program variables
    num_nodes = 5
    iterations = 100
    use_high_fidelity = False
    use_optimistic = False
    link_typ = 'depolarise'

    # Get current link fidelity    
    current_fidelity = configure_link(use_high_fidelity=False, use_optimistic=False).fidelity

    # Get optimistic max link fidelity
    optim_high_fidelity = configure_link(use_high_fidelity=True, use_optimistic=True).fidelity

    # Initialize arrays to store error rate statistics
    avg_error_rates = []
    var_error_rates = []

    # Simulate network sweeping over fidelity values
    fidelity_range = np.linspace(current_fidelity, optim_high_fidelity, 30)
    for fidelity in fidelity_range:
        # Initialize GHZ programs and node names
        programs, node_names = init_GHZ_programs(num_nodes)

        # Initialize network configuration
        network_cfg = configure_network(node_names, use_high_fidelity, use_optimistic, link_typ)
        
        # Update network with optimistic qdevices (links unchanged)
        new_stack_cfg = configure_qdevice(use_optimistic=True)
        for stack in network_cfg.stacks:
            stack.qdevice_cfg = new_stack_cfg

        # Update fidelity for all link configurations
        # Updating it for one link automatically applies the change for all links in the network
        network_cfg.links[0].cfg.fidelity = fidelity

        # Run simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=iterations
        )

        # Calculate error rates and output the average and variance
        _, error_rates = analyze_results(results, num_nodes, iterations)
        avg_error = np.average(error_rates)*100
        avg_error_rates.append(avg_error)
        var_error = np.var(error_rates)
        var_error_rates.append(var_error)


    # Plot average error rate vs fidelity
    """ plt.plot(fidelity_range, avg_error_rates, c='b')
    plt.ylabel("Average error rate (%)")
    plt.xlabel("EPR link fidelity")
    plt.savefig("error_rate_vs_fidelity.png") """
    
    # Plot both average error rate and variance vs decoherence time
    fig, ax1 = plt.subplots()
    color = 'tab:blue'
    ax1.set_xlabel("EPR link fidelity")
    ax1.set_ylabel("Average error rate (%)", color=color)
    ax1.plot(fidelity_range, avg_error_rates, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:red'
    ax2.set_ylabel("Error rate variance", color=color)
    ax2.plot(fidelity_range, var_error_rates, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    fig.savefig("avg_error_and_variance_vs_fidelity_w_optim_qdevice.png")




        




       
