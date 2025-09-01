from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np
import scipy.linalg as sci
import sys

from squidasm.run.stack.run import run # type: ignore

def calculate_fidelity(ideal_state: np.ndarray, noisy_state: np.ndarray):
    fidelity = np.trace(np.abs(sci.sqrtm(ideal_state).dot(sci.sqrtm(noisy_state))))
    return fidelity

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 10
    max_ntest = 20
    # Parameters for network configuration with noise
    network = sys.argv[1] # 'perfect' or 'optimhf'
    link_fidelity = float(sys.argv[2]) # number between 0 and 1, disregarded if network=perfect
    stabset = sys.argv[3] # 'full', 'gen' or 'select'
    if stabset == 'select':
        select = int(sys.argv[4]) # number of stabilizers to measure (int b/w 1 and 2^num_nodes)

    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/ntest_variation.log")

    # Perfect verification simulation
    programs, node_names = init_verification_programs(num_nodes, n_test=1)
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

    ntest_list = range(1, max_ntest+1)
    for ntest in ntest_list:
        # Initialize programs
        if stabset == 'full':
            programs, node_names = init_verification_programs(num_nodes, ntest, full=True)
        elif stabset == 'gen':
            programs, node_names = init_verification_programs(num_nodes, ntest)
        else:
            programs, node_names = init_verification_programs(num_nodes, ntest, select=select)

        # Load network configuration
        if network == "perfect":
            network_cfg = configure_perfect_network(node_names)
        elif network == "optimhf":
            network_cfg = configure_network(node_names, use_high_fidelity=True, use_optimistic=True)
            # Modify the link configuration
            for link in network_cfg.links:
                link.cfg.fidelity = link_fidelity
        else:
            raise ValueError("Network argument must be \'perfect\' or \'optimhf\'")

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

        print(f"Simulation with {ntest} test copies complete.")
            
            
        # Get average failure rate and target fidelity over all simulation iterations
        avg_failures.append(np.average(failure_rates))
        target_fidelities.append(np.average(target_fids))
    
    # Write data to file
    if network == "optimhf":
        postfix = f"f{int(link_fidelity*1000)}"
    else:
        postfix = network
    filename = f"data/ntest_variation_{stabset}_set_{postfix}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, link_fidelity={link_fidelity}\n")
        f.write("# columns:\n")
        f.write("#  ntest   avg_failure_rate    avg_target_fidelity\n")

    # Output
    write_to_file_multiy(
        x=ntest_list,
        y1=avg_failures, 
        y2=target_fidelities,
        filename=filename
    )

    print(f"Simulation results stored in {filename}")