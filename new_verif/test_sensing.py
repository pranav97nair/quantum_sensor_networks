from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np
from pprint import pprint
import random

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    f_threshold = 0.05
    num_iters = 100
    network = 'optimhf'
    state = "ghz"


    # Initialize programs
    random.seed(7200)
    programs, node_names = init_sensing_programs(num_nodes, ntest, copies, f_threshold)

    # Configure network
    if network == 'perfect':
            network_cfg = configure_perfect_network(node_names)
    elif network == 'optimhf':
        network_cfg = configure_network(node_names,
                                        use_high_fidelity=True,
                                        use_optimistic=True)

    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/test_sensing.log")

    # Run simulation
    plus_outcomes = 0
    total_iters = 0
    sensing_iters = 0
    phase_average = np.nan

    while sensing_iters < num_iters:
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

        # Increment total iteration count
        total_iters += 1

        # If verification failed, move on to next iteration
        if results[0][0]["status"] == 1:
            continue

        # Otherwise sensing was implemented, increment sensing iteration count
        sensing_iters += 1

        # Get parity results from each node
        parities = []
        for j in range(num_nodes):
            parities.append(results[j][0]["parity"])

        # Track overall parity +1 outcomes
        if np.prod(parities) == 1:
            plus_outcomes += 1
            
        # Get phase average
        phases = []
        for j in range(num_nodes):
            phases.append(results[j][0]['local phase'])
        phase_average = np.average(phases)
    
    ### Post-processing ###

    print(f"Total iterations: {total_iters}")
    print(f"Total sensing iterations: {sensing_iters}")

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")

    try:
        prob0 = plus_outcomes / sensing_iters
    except ZeroDivisionError:
        print("Zero sensing iterations attempted.")
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
    
