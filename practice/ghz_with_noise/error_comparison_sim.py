from typing import List
import numpy as np
import matplotlib.pyplot as plt
from application import GHZProgram
from utils import *

from squidasm.run.stack.run import run # type: ignore

###
#   Function to optimistically calculate error rate based on a binary array of measurement outcomes.
#   Calculates and returns the error rate based on the number of deviations from the majority outcome.
###
def calculate_error_rate(num_nodes, outcomes: List[int]) -> float:
    distance_from_1 = num_nodes - abs(sum(outcomes))
    distance_from_0 = abs(sum(outcomes))

    state_guess = 1 if distance_from_1 < distance_from_0 else 0
    error_count = sum([1 for outcome in outcomes if outcome != state_guess])

    #print(f"Error count: {error_count}")
    error_rate = error_count / len(outcomes)
    return error_rate

###
#   Function to analyze simulation results given the results dataset, number of nodes, and iterations.
#   Returns a list of measurement outcomes and error rates for each iteration.
###
def analyze_results(results, num_nodes, iterations):
    outcomes = []
    error_rates = []
    for k in range(iterations):
        reference_result = results[0][k]["result"]
        k_outcomes = []
        for j in range(num_nodes):
            node_result = results[j][k]["result"]
            k_outcomes.append(node_result)
        outcomes.append(k_outcomes)
        error_rates.append(calculate_error_rate(num_nodes, k_outcomes))
    return outcomes, error_rates

###
#   Function to plot error rates.
###
def plot_error_rates(filename, iterations, error_rates_1, error_rates_2=None, error_rates_3=None, error_rates_4=None, label1:str=None, label2:str=None, label3:str=None, label4:str=None):
    # Initialize iterations array
    iters = np.arange(1, iterations+1)
    # Plot error rates with corresponding labels
    plt.plot(iters, error_rates_1, c='g', alpha=0.5, linewidth=2, label=label1)
    if error_rates_2 is not None:
        plt.plot(iters, error_rates_2, c='b', alpha=0.5, linewidth=2, label=label2)
    if error_rates_3 is not None:
        plt.plot(iters, error_rates_3, c='r', alpha=0.5, linewidth=2, label=label3)
    if error_rates_4 is not None:
        plt.plot(iters, error_rates_4, c='black', alpha=0.5, linewidth=2, label=label4)
    # Plot configuration
    plt.ylabel("Error rate")
    plt.xlabel("Iteration")
    plt.legend()
    plt.grid(axis="y")
    plt.savefig(f"{filename}.png")

# Main function
if __name__ == "__main__":
    num_nodes = 5

    # Initialize GHZ programs for all nodes in network
    programs, node_names = init_GHZ_programs(num_nodes)

    # Configure networks
    depolarise_link_network_cfg = configure_network(
        node_names, 
        use_high_fidelity=False, 
        use_optimistic=False, 
        link_typ="depolarise")
    
    perfect_link_network_cfg = configure_network(
        node_names, 
        use_high_fidelity=False, 
        use_optimistic=False, 
        link_typ="perfect")
    
    depo_optim_network_cfg = configure_network(
        node_names,
        use_high_fidelity=False,
        use_optimistic=True,
        link_typ="depolarise"
    )

    depo_highfid_network_cfg = configure_network(
        node_names,
        use_high_fidelity=True,
        use_optimistic=False,
        link_typ="depolarise"
    )

    depo_optim_highfid_network_cfg = configure_network(
        node_names,
        use_high_fidelity=True,
        use_optimistic=False,
        link_typ="depolarise"
    )

    # Run simulations
    iterations = 20
    dlink_results = run(
        config=depolarise_link_network_cfg,
        programs=programs,
        num_times=iterations
    )

    """ plink_results = run(
        config=perfect_link_network_cfg,
        programs=programs,
        num_times=iterations
    ) """

    dlink_optim_results = run(
        config=depo_optim_network_cfg,
        programs=programs,
        num_times=iterations
    )

    dlink_highfid_results = run(
        config=depo_highfid_network_cfg,
        programs=programs,
        num_times=iterations
    )

    dlink_optim_highfid_results = run(
        config=depo_optim_highfid_network_cfg,
        programs=programs,
        num_times=iterations
    )

    _, error_rates_1 = analyze_results(dlink_results, num_nodes, iterations)
    #plink_outcomes, error_rates_2 = analyze_results(plink_results, num_nodes, iterations)
    _, error_rates_2 = analyze_results(dlink_optim_results, num_nodes, iterations) 
    _, error_rates_3 = analyze_results(dlink_highfid_results, num_nodes, iterations)
    _, error_rates_4 = analyze_results(dlink_optim_highfid_results, num_nodes, iterations)

    """ plot_error_rates(
        "error_rate_comparison_depolarise", 
        iterations, 
        error_rates_1, 
        error_rates_2, 
        error_rates_3, 
        error_rates_4, 
        "Current", 
        "Optimistic", 
        "High fidelity", 
        "Optimistic with high fidelity"
    ) """




