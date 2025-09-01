import numpy as np
import time as t
import matplotlib.pyplot as plt
from utils import *
from error_comparison_sim import analyze_results

from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Program variables
    num_nodes = 5
    iterations = 100
    use_high_fidelity = False
    use_optimistic = False
    link_typ = "depolarise"

    # Get current qdevice decoherence times
    current_qdevice_cfg = configure_qdevice(use_optimistic=False)
    current_T1 = current_qdevice_cfg.T1

    # Get optimistic qdevice decoherence times
    optim_qdevice_cfg = configure_qdevice(use_optimistic=True)
    optim_T1 = optim_qdevice_cfg.T1

    # Initialize arrays to store error rate statistics
    error_rate_avg = []
    error_rate_var = []

    # Simulate network sweeping over T1 and T2 values:
    T1_range = np.linspace(current_T1, optim_T1, 30)
    for t in T1_range:
        # Initialize GHZ programs and node names
        programs, node_names = init_GHZ_programs(num_nodes)

        # Initialize network configuration
        network_cfg = configure_network(node_names, use_high_fidelity, use_optimistic, link_typ)

        # Update T1 and T2 values for all qdevice configurations
        # Updating them for one stack automatically applies the change for all stacks in the network
        stacks = network_cfg.stacks
        stacks[0].qdevice_cfg.T1 = t
        stacks[0].qdevice_cfg.T2 = t

        # Run simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=iterations
        )

        # Calculate error rates and output the average and variance
        _, error_rates = analyze_results(results, num_nodes, iterations)
        avg_error = np.average(error_rates)*100
        error_rate_avg.append(avg_error)
        var = np.var(error_rates)
        error_rate_var.append(var)

    # Plot average error rate vs decoherence time
    """ t_seconds = [t / 1e9 for t in T1_range]
    plt.plot(t_seconds, error_rate_avg, c='r')
    plt.xlabel("Decoherence time (s)")
    plt.ylabel("Average error rate (%)")
    plt.savefig("error_rate_vs_decoherence_time.png") """

    # Plot both average error rate and variance vs decoherence time
    """ fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel("Decoherence time (s)")
    ax1.set_ylabel("Average error rate (%)", color=color)
    ax1.plot(t_seconds, error_rate_avg, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()

    color = 'tab:blue'
    ax2.set_ylabel("Error rate variance", color=color)
    ax2.plot(t_seconds, error_rate_var, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()
    fig.savefig("avg_error_and_variance_vs_decoherence_time.png") """

    


        
    


