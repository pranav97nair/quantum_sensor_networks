from matplotlib import pyplot as plt
from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 3
    ntotal = 2 * num_nodes * ntest
    #print(f"Total copies: {ntotal}")
    num_iters = 10
    state = "ghz"

    #ntest_list = list(range(1, max_ntest+1))
    average_failure_rates = []

    # Set verification failure trheshold
    #f_threshold = 1 / (2 * num_nodes**2)
    f_threshold = 0.1

    # Initialize programs
    programs, node_names = init_sensing_programs(num_nodes, ntest, f_threshold)

    # Configure network
    #network_cfg = configure_perfect_network(node_names)
    network_cfg = configure_network(node_names,
                                    use_high_fidelity=True,
                                    use_optimistic=True)
    
    if state == "bell":
        for stack in network_cfg.stacks:
            stack.qdevice_cfg.num_qubits = 200
    
    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/info_{state}.log")

    ### Run simulation ###

    plus_outcomes = 0
    rejections = 0
    phase_average = np.nan
    for k in range(num_iters):
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

        if results[0][0]['status'] == 0:
            # Get parity results from each node
            k_parities = []
            for j in range(num_nodes):
                k_parities.append(results[j][0]["parity"])
            # Track overall parity +1 outcomes
            if np.prod(k_parities) == 1:
                plus_outcomes += 1
            # Get phase average
            phases = []
            for j in range(num_nodes):
                phases.append(results[j][0]['local phase'])
            phase_average = np.average(phases)
        else:
            rejections += 1
        if (k+1) % 50 == 0:
            print(f"Iteration {k+1} complete.")
    
    ### Post-processing ###

    print(f"Total iterations: {num_iters}")
    print(f"Verification rejections: {rejections}")
    print(f"Sensing attempts: {num_iters-rejections}\n")

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")

    try:
        prob0 = plus_outcomes / (num_iters - rejections)
    except ZeroDivisionError:
        print("All iterations were rejected, so no sensing was attempted.")
    else:
        print(f"Observed frequency of overall +1 parity: {prob0}")
        print(f"Average phase: {phase_average}")
        i = 0
        while phase_average % ((i+1)*np.pi/4) != phase_average:
            i += 1
        print(f"Interval: [{i*np.pi/4}, {i*np.pi/4 + np.pi/4}]")

        # Estimate average phase from oberserved +1 parity frequency
        arg = min(1, (prob0*2 - 1))
        if i == 0:                     
            est = np.arccos(arg) / num_nodes
        elif i < 3:
            est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
        else:
            est = -1 * np.arccos(arg) / num_nodes + np.pi
        print(f"Estimate: {est}")
