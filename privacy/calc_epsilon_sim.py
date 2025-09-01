from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
from plot_bar3D import plot_3d_bar
from kraus_operators import *
from matrix_animation import plot_3d_bar_animation
import numpy as np
import scipy.linalg as sci
import itertools

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

def H_and_M(d, operator='sigma_z', print_matrices:bool=False):
    
    sigma_x = np.array([[0, 1],[1, 0]])
    # sigma_y = np.array([[0, -1j],[1j, 0]])
    sigma_z = np.diag([1, -1])
    id_2 = np.diag([1, 1])
    
    if operator=='sigma_z':
        OP = sigma_z/2
    elif operator=='hadamard':
        OP = sigma_z/2 + sigma_x/2
    elif operator=='sigma_x':
         OP = sigma_x/2
    else:
        print('Operator not yet implemented in function "H_and_M".')
        from sys import exit
        exit()
    
    # Operators:
    H = {}

    for i in range(d):
        H[i] = np.ones((1,1))
        for j in range(d):
            if i==j:
                H[i] = np.kron(H[i], OP)
            else:
                H[i] = np.kron(H[i], id_2)
    
    
    M = {}
    
    for i in range(d-1):
        M[i] = {}
    
    for i in range(d):
        for j in range(i, d):
            if j!=i:
                M[i][j] = H[i] - H[j]
                # Printing:
                if print_matrices:
                    print(f"H{i+1}-H{j+1} = \n{M[i][j]}")
    
    return H, M

def calc_epsilon(rho: np.ndarray, num_nodes):
    H, M = H_and_M(num_nodes)
    C = {}
    for i in range(num_nodes-1):
        C[i] = {}
    
    trace_norms = []
    for i in M.keys():
        for j in M[i].keys():
            C[i][j] = np.matmul(M[i][j], noisy_rho) - np.matmul(noisy_rho, M[i][j])
            trace_norms.append(sum(np.linalg.svd(C[i][j])[1]))
    
    epsilon = max(trace_norms)
    return epsilon


if __name__ == '__main__':
    num_nodes = 4
    ntest = 3
    ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters = 1
    state = "ghz"

    ### Get density matrix ###

    # Initialize programs
    programs, node_names = init_sensing_programs(num_nodes, ntest, send_state=True)

    # Configure network
    network_cfg = configure_perfect_network(node_names)
    """ network_cfg = configure_network(node_names,
                                    use_high_fidelity=True,
                                    use_optimistic=True) """
    
    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/info_{state}.log")

    # Run simulation
    plus_outcomes = 0
    for k in range(num_iters):
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

    # Density matrix of post-encoding state
    rho = results[-1][0]['full state']

    ### Calculate epsilon for different noise types 

    datapoints = 20
    min_eta = 0
    max_eta = 1
    eta_list = np.linspace(min_eta, max_eta, datapoints)

    amp_dam_eps = []
    print('Amplitude damping:')
    for eta in eta_list:
        K_amp_dam = amplitude_damping_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_amp_dam)
        e = calc_epsilon(noisy_rho, num_nodes)
        print(f"eta: {eta}, epsilon: {e}")
        amp_dam_eps.append(e)

    phase_dam_eps = []
    print('\nPhase damping:')
    for eta in eta_list:
        K_phase_dam = phase_damping_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_phase_dam)
        e = calc_epsilon(noisy_rho, num_nodes)
        print(f"eta: {eta}, epsilon: {e}")
        phase_dam_eps.append(e)
    
    dep_noise_eps = []
    print('\nDepolarising noise:') 
    for eta in eta_list:
        K_dep_noise = depolarising_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_dep_noise)
        e = calc_epsilon(noisy_rho, num_nodes)
        print(f"eta: {eta}, epsilon: {e}")
        dep_noise_eps.append(e)
    
    deph_noise_eps = []
    print('\nDephasing noise:')
    for eta in eta_list:
        K_deph_noise = dephasing_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_deph_noise)
        e = calc_epsilon(noisy_rho, num_nodes)
        print(f"eta: {eta}, epsilon: {e}")
        deph_noise_eps.append(e)

    ### Write data to file

    filename = "data/kraus_noise_epsilons.txt"
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, ntest={ntest}, state={state}\n")
        f.write("# columns:\n")
        f.write("#  eta   amp_dam_epsilon    phase_dam_epsilon    dep_noise_epsilon    deph_noise_epsilon\n")

    write_to_file_multiy(filename, 
                         eta_list, 
                         amp_dam_eps, 
                         phase_dam_eps, 
                         dep_noise_eps, 
                         deph_noise_eps)




    







