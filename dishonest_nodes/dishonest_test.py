from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    # Simulation parameters
    num_nodes = 4
    num_iters = 100
    ntest = 3
    f_threshold = 1 / (2 * num_nodes**2)
    state = "ghz"

    num_dishonest = 1
    #dishonest_action = 1 # zero rotation
    #dishonest_action = 2 # Z measurement
    dishonest_action = 3 # incorrect rotation

    random.seed(8600)

    # Initialize programs
    if num_dishonest >= 1:
        programs, node_names, dishonest_nodes = init_dishonest_programs(num_nodes, ntest, f_threshold, num_dishonest, dishonest_action)
    else:
        programs, node_names = init_sensing_programs(num_nodes, ntest, f_threshold)

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
    LogManager.log_to_file(f"logs/dishonest_test_{state}.log")

    ### Run simulation ###

    plus_outcomes = 0
    phase_average = np.nan

    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters
    )

    for k in range(num_iters):
        # Get parity results from each node
        k_parities = []
        for j in range(num_nodes):
            k_parities.append(results[j][k]["parity"])
        # Track overall parity +1 outcomes
        if np.prod(k_parities) == 1:
            plus_outcomes += 1
        # Get phase average
        phases = []
        for j in range(num_nodes):
            phases.append(results[j][k]['local phase'])
        phase_average = np.average(phases)
    
    ### Post-processing ###

    print(f"Total iterations: {num_iters}")

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")

    try:
        prob0 = plus_outcomes / num_iters
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

    

    

    
    
