from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
from plot_bar3D import plot_3d_bar
from kraus_operators import *
import numpy as np
import scipy.linalg as sci

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

def calculate_fidelity(ideal_state: np.ndarray, noisy_state: np.ndarray):
    fidelity = np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
    return fidelity

if __name__ == '__main__':
    num_nodes = 4
    ntest = 3
    ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters = 1
    state = "ghz"

    # Initialize programs
    programs, node_names = init_sensing_programs(num_nodes, ntest, send_state=True)

    # Configure network
    network_cfg = configure_perfect_network(node_names)
    """ network_cfg = configure_network(node_names,
                                    use_high_fidelity=False,
                                    use_optimistic=False) """
    
    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/info_{state}.log")

    ### Run simulation ###

    plus_outcomes = 0
    for k in range(num_iters):
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

    rho = results[-1][0]['full state']
    #print(rho)

    ### Apply noise operators and calculate fidelities

    datapoints = 100
    min_eta = 0
    max_eta = 1
    eta_list = np.linspace(min_eta, max_eta, datapoints)

    amp_dam_fids = []
    #print('Amplitude damping:')
    for eta in eta_list:
        K_amp_dam = amplitude_damping_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_amp_dam)
        fid = calculate_fidelity(rho, noisy_rho)
        #print(f"eta: {eta}, fidelity: {fid}")
        amp_dam_fids.append(fid)

    phase_dam_fids = []
    #print('\nPhase damping:')
    for eta in eta_list:
        K_phase_dam = phase_damping_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_phase_dam)
        fid = calculate_fidelity(rho, noisy_rho)
        #print(f"eta: {eta}, fidelity: {fid}")
        phase_dam_fids.append(fid)
    
    dep_noise_fids = []
    #print('\nDepolarising noise:') 
    for eta in eta_list:
        K_dep_noise = depolarising_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_dep_noise)
        fid = calculate_fidelity(rho, noisy_rho)
        #print(f"eta: {eta}, fidelity: {fid}")
        dep_noise_fids.append(fid)
    
    deph_noise_fids = []
    #print('\nDephasing noise:')
    for eta in eta_list:
        K_deph_noise = dephasing_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_deph_noise)
        fid = calculate_fidelity(rho, noisy_rho)
        #print(f"eta: {eta}, fidelity: {fid}")
        deph_noise_fids.append(fid)

    ### Write data to file

    filename = "data/kraus_noise_fidelities.txt"
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, ntest={ntest}, state={state}\n")
        f.write("# columns:\n")
        f.write("#  eta   amp_dam_fidelity    phase_dam_fidelity    dep_noise_fidelity    deph_noise_fidelity\n")

    write_to_file_multiy(filename, 
                         eta_list, 
                         amp_dam_fids, 
                         phase_dam_fids, 
                         dep_noise_fids, 
                         deph_noise_fids)