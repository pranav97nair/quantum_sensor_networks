from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
import scipy.linalg as sci

from squidasm.run.stack.run import run # type: ignore

def calculate_fidelity(ideal_state: np.ndarray, noisy_state: np.ndarray):
    fidelity = np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
    return fidelity

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 20
    ntest = 10   # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = True
    use_optimistic = True

    # Retrieve parameters for the default depolarizing quantum link
    default_link_cfg = configure_link(use_highfid, use_optimistic)
    starting_fidelity = default_link_cfg.fidelity
    datapoints = 50
    fidelity_list = np.linspace(starting_fidelity, 1.0, datapoints)

    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/link_variation.log")

    # Perfect verification simulation
    programs, node_names = init_verification_programs(num_nodes, ntest)
    netcfg = configure_perfect_network(node_names)
    results = run(
                config=netcfg,
                programs=programs,
                num_times=1
            )
    ideal_state = results[-1][0]["full state"]
            
    # Run simulation varying the link fidelity
    avg_failures = []
    target_fidelities = []
    for fidelity in fidelity_list:
        if (list(fidelity_list).index(fidelity)+1) % 5 == 0:
            print(f"Fidelity simulation {list(fidelity_list).index(fidelity)+1}.")

        # Initialize programs
        programs, node_names = init_verification_programs(num_nodes, ntest)

        # Load network configuration
        network_cfg = configure_network(node_names, use_highfid, use_optimistic)

        # If needed, we can modify the configuration to increase num_qubits
        """ for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 100 """

        # Modify the link configuration
        for link in network_cfg.links:
            link.cfg.fidelity = fidelity

        # Run the simulation
        failure_rates = []
        target_fids = []
        for k in range(num_iters):
            #print(f"Iteration {k+1}")
            fid = np.nan
            attempt = 1
            while np.isnan(fid):
                #if attempt > 1: print(f"Trying again")
                results = run(
                    config=network_cfg,
                    programs=programs,
                    num_times=1
                )
                f = round(results[0][0]["average failure rate"], 5)
                m = results[-1][0]["full state"]
                #print(f"Average failure rate for iteration {k+1}: {f}")
                fid = round(calculate_fidelity(ideal_state, m), 5)
                attempt += 1
            #print(f"Verification failure rate: {f} \tTarget copy fidelity: {fid}")
            failure_rates.append(f)
            target_fids.append(fid)
            
            
        # Get average failure rate and target fidelity over all simulation iterations
        avg_failures.append(np.average(failure_rates))
        target_fidelities.append(np.average(target_fids))
        
    # Write data to file
    filename = "data/link_variation_multi_fom_x50_(2).txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest}\n")
        f.write("# columns:\n")
        f.write("#  link_fidelity   avg_failure_rate    avg_target_fidelity\n")

    # Output
    write_to_file_multiy(
        x=fidelity_list,
        y1=avg_failures, 
        y2=target_fidelities,
        filename=filename
    )