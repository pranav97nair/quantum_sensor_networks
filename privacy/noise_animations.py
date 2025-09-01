from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
from plot_bar3D import plot_3d_bar
from kraus_operators import *
from matrix_animation import plot_3d_bar_animation
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

    ### Apply nosie operators and generate density matrices

    datapoints = 32
    min_eta = 0
    max_eta = 1
    eta_list = np.linspace(min_eta, max_eta, datapoints)

    amp_dam_mats = []
    phase_dam_mats = []
    dep_noise_mats = []
    deph_noise_mats = []

    # Amplitude damping
    for eta in eta_list:
        K_amp_dam = amplitude_damping_Kraus_operators(num_nodes, eta)
        #print(len(K_amp_dam))
        noisy_rho = apply_noise(rho, num_nodes, K_amp_dam)
        amp_dam_mats.append(np.real(noisy_rho))

    # Phase damping
    """ for eta in eta_list:
        K_phase_dam = phase_damping_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_phase_dam)
        phase_dam_mats.append(np.real(noisy_rho)) """
    
    # Depolarising noise
    """ for eta in eta_list:
        K_dep_noise = depolarising_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_dep_noise)
        dep_noise_mats.append(np.real(noisy_rho)) """
    
    # Dephasing noise
    """ for eta in eta_list:
        K_deph_noise = dephasing_Kraus_operators(num_nodes, eta)
        noisy_rho = apply_noise(rho, num_nodes, K_deph_noise)
        deph_noise_mats.append(np.real(noisy_rho)) """

    ### Generate animation
    
    plot_3d_bar_animation(matrices=amp_dam_mats, 
                          title="Amplitude Damping",
                          filename="animations/amp_dam_animation_n5.gif", 
                          fps=8,
                          min_eta=min_eta,
                          max_eta=max_eta)