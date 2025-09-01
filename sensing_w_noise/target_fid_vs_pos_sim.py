from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
import scipy.linalg as sci

from squidasm.run.stack.run import run # type: ignore

def calculate_fidelity(ideal_state: np.ndarray, noisy_state: np.ndarray):
    fidelity = np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
    return round(fidelity, 3)

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 100
    ntest = 10   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = True
    use_optimistic = False

    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/target_fid_vs_pos.log")

    # Perfect verification simulation
    programs, node_names = init_verification_programs(num_nodes, ntest)
    netcfg = configure_perfect_network(node_names)
    results = run(
                config=netcfg,
                programs=programs,
                num_times=1
            )
    ideal_state = results[-1][0]["full state"]

    ### Noisy verification simulation ###

    # Initialize programs
    programs, node_names = init_verification_programs(num_nodes, ntest)

    # Load network configuration
    network_cfg = configure_network(node_names, use_highfid, use_optimistic)

    # Run the simulations
    ids_fids = {}
    for k in range(num_iters):
        results = run(
                config=network_cfg,
                programs=programs,
                num_times=1
            )
        idx = results[0][0]["target index"]
        rho = results[-1][0]["full state"]
        fid = calculate_fidelity(ideal_state, rho)
        ids_fids[idx] = fid

    # Write data to file
    filename = "data/fid_vs_pos_current_highfid_x100.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, ntest={ntest}, use_optimistic={use_optimistic}, use_highfid={use_highfid}\n")
        f.write("# columns:\n")
        f.write("#  target_position    target_fidelity\n")

    # Output
    positions = list(ids_fids.keys())
    fidelities = list(ids_fids.values())
    write_to_file(
        x=positions,
        y=fidelities,
        filename=filename
    )

    pprint(ids_fids)

