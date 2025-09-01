import numpy as np
import scipy.linalg as sci
import matplotlib.pyplot as plt
from utils import *

from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.run.stack.run import run # type: ignore

### 
#   Function to simulate a GHZ state distributed over a network with perfect quantum links and devices.
#   The function takes as input the number of nodes in the network
#   and the number of iterations to run the simulation, which is by default 1
#   The function returns the density matrix of the full entangled state for the network.
###
def simulate_perfect_network(num_nodes: int, num_iters: int=1):
    # Initialize programs and configure network
    programs, node_names = init_GHZ_programs(num_nodes, measure_qubits=False, full_state=True)
    cfg = configure_perfect_network(node_names)

    # Run simulation
    results = run(config=cfg, 
                  programs=programs, 
                  num_times=num_iters)

    # Return the density matrix for the full network
    density_mats = [results[num_nodes-1][k]["state"] for k in range(num_iters)]

    return density_mats

### 
#   Function to simulate a GHZ state distributed over a network with noisy quantum links and devices.
#   The function takes as input the number of nodes in the network,
#   and the number of iterations to run the simulation.
#   The function also takes as input two boolean flags that specify the network configuration options.
#   The function returns the density matrix of the full entangled state for the network.
###
def simulate_noisy_network(num_nodes: int, num_iters: int, use_high_fidelity: bool, use_optimistic: bool):
    # Initialize programs and configure network
    programs, node_names = init_GHZ_programs(num_nodes, measure_qubits=False, full_state=True)
    cfg = configure_network(node_names, use_high_fidelity, use_optimistic)
    
    # Run simulation
    density_mats = []
    for k in range(num_iters):
        #print(f"Iteration: {k+1}")
        results = run(config=cfg, programs=programs)        
        # Get the density matrix of the full entanged state for the network
        full_state = results[num_nodes-1][0]["state"]
        density_mats.append(full_state)
    
    return density_mats

def calculate_distances(ideal_state: np.ndarray, noisy_states: List[np.ndarray]):
    distances = (
        0.5 * np.trace(np.abs(ideal_state - noisy_state))
        for noisy_state in noisy_states
    )
    return distances

def calculate_fidelities(ideal_state: np.ndarray, noisy_states: List[np.ndarray]):
    fidelities = (
        np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
        for noisy_state in noisy_states
    )
    return fidelities

if __name__ == '__main__':
    # Program variables
    #num_nodes = 5
    num_iters = 100

    num_nodes_list = [num for num in range(2, 11)]
    """ avg_distances_current = []
    avg_distances_highfid = []
    avg_distances_optim = []
    avg_distances_optim_highfid = [] """

    avg_fid_current = []
    avg_fid_highfid = []
    """ avg_fid_optim = []
    avg_fid_optim_highfid = [] """

    print("Simulating network with current parameters")
    # Simulate network with current parameters
    for num_nodes in num_nodes_list:
        print(f"Number of nodes: {num_nodes}")
        # Simulate perfect network and obtain density matrix for ideal GHZ state
        rho_ideal = simulate_perfect_network(num_nodes)[0]

        # Simulate network with current parameters
        noisy_states = simulate_noisy_network(
            num_nodes, 
            num_iters, 
            use_high_fidelity=False, 
            use_optimistic=False)

        #avg_distance = np.average(list(calculate_distances(rho_ideal, noisy_states)))
        #print(f"Average distance from ideal GHZ: {avg_distance}")
        #avg_distances_current.append(avg_distance)

        avg_fidelity = np.average(list(calculate_fidelities(rho_ideal, noisy_states)))
        avg_fid_current.append(avg_fidelity)

    print("Simulating network with current, high-fidelity parameters")
    # Simulate network with high fidelity parameters
    for num_nodes in num_nodes_list:
        print(f"Number of nodes: {num_nodes}")
        # Simulate perfect network and obtain density matrix for ideal GHZ state
        rho_ideal = simulate_perfect_network(num_nodes)[0]

        # Simulate network with high fidelity parameters
        noisy_states = simulate_noisy_network(
            num_nodes, 
            num_iters, 
            use_high_fidelity=True, 
            use_optimistic=False)

        #avg_distance = np.average(list(calculate_distances(rho_ideal, noisy_states)))
        #print(f"Average distance from ideal GHZ: {avg_distance}")
        #avg_distances_highfid.append(avg_distance)

        avg_fidelity = np.average(list(calculate_fidelities(rho_ideal, noisy_states)))
        avg_fid_highfid.append(avg_fidelity)

    """ print("Simulating network with optimistic parameters")
    # Simulate network with optimistic parameters
    for num_nodes in num_nodes_list:
        print(f"Number of nodes: {num_nodes}")
        # Simulate perfect network and obtain density matrix for ideal GHZ state
        rho_ideal = simulate_perfect_network(num_nodes)[0]

        # Simulate network with optimistic parameters
        noisy_states = simulate_noisy_network(
            num_nodes, 
            num_iters, 
            use_high_fidelity=False, 
            use_optimistic=True)

        #avg_distance = np.average(list(calculate_distances(rho_ideal, noisy_states)))
        #print(f"Average distance from ideal GHZ: {avg_distance}")
        #avg_distances_optim.append(avg_distance)

        avg_fidelity = np.average(list(calculate_fidelities(rho_ideal, noisy_states)))
        avg_fid_optim.append(avg_fidelity) """

    """ print("Simulating network with optimistic, high-fidelity parameters")
    # Simulate network with optimistic and high fidelity parameters
    for num_nodes in num_nodes_list:
        print(f"Number of nodes: {num_nodes}")
        # Simulate perfect network and obtain density matrix for ideal GHZ state
        rho_ideal = simulate_perfect_network(num_nodes)[0]

        # Simulate network with optimistic and high fidelity parameters
        noisy_states = simulate_noisy_network(
            num_nodes, 
            num_iters, 
            use_high_fidelity=True, 
            use_optimistic=True)

        #avg_distance = np.average(list(calculate_distances(rho_ideal, noisy_states)))
        #print(f"Average distance from ideal GHZ: {avg_distance}")
        #avg_distances_optim_highfid.append(avg_distance)

        avg_fidelity = np.average(list(calculate_fidelities(rho_ideal, noisy_states)))
        avg_fid_optim_highfid.append(avg_fidelity) """

    plt.plot(num_nodes_list, avg_fid_current, c='r', label="Current")
    plt.plot(num_nodes_list, avg_fid_highfid, c='b', label="High fidelity")
    """ plt.plot(num_nodes_list, avg_fid_optim, c='g', label="Optimistic")
    plt.plot(num_nodes_list, avg_fid_optim_highfid, c='black', label="Optimistic and high fidelity") """
    plt.xlabel("Number of nodes in the network")
    plt.ylabel("Fidelity to the ideal GHZ state")
    plt.legend(loc='lower left')
    plt.savefig("figures/fidelity_vs_num_nodes_comparison_current.png")


    

    
    

    
