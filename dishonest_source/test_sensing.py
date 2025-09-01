from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np
from pprint import pprint
import random

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

def avg_estimator(prob0: float, i: int):
    arg = min(1, (prob0*2 - 1))
    if i == 0:                     
        est = np.arccos(arg) / num_nodes
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
    else:
        est = -1 * np.arccos(arg) / num_nodes + np.pi

    return est

def avg_estimator_Zflip(prob0: float, i: int):
    arg = min(1, (1 - prob0*2))
    if i == 0:                     
        est = np.arccos(arg) / num_nodes
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
    else:
        est = -1 * np.arccos(arg) / num_nodes + np.pi

    return est

def diff_estimator(prob0: float, i: int, negative: bool = False):
    arg = min(1, (prob0*2 - 1))
    if i == 0:                     
        est = np.arccos(arg)
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) + 2*np.pi
    else:
        est = -1 * np.arccos(arg) + 4*np.pi

    return (-1)**negative * est

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    f_threshold = 0.1
    num_iters = 100
    network = 'perfect'
    state = "ghz"
    num_dishonest = 1
    if num_dishonest > 0:
        dishonest_action = 0    # 0 = no action, 1 = apply phase flip, 2 = apply bit flip
    bitflip_node = 2

    # Seed random state
    seed = 13579
    random.seed(seed)

    # Initialize programs
    if num_dishonest > 0:
        programs, node_names, dishonest_nodes, phases = init_dishonest_sensing(num_nodes, ntest, copies, f_threshold, num_dishonest, dishonest_action, bitflip_node)
    else:
        programs, node_names, phases = init_sensing_programs(num_nodes, ntest, copies, f_threshold)

    pprint(programs)
    pprint(phases)

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
    
    ### Post-processing ###

    print(f"\nTotal iterations: {total_iters}")
    print(f"Total sensing iterations: {sensing_iters}\n")

    if num_dishonest > 0:
        print(f"Dishonest nodes: {dishonest_nodes}")

    # In case of phase flip or no dishonest nodes
    if num_dishonest == 0 or dishonest_action == 1:
        # The function encoded is the average of the phases
        phase_average = np.average(list(phases.values()))

        exp_prob0 = (1 + (-1)**num_dishonest * np.cos(num_nodes*phase_average)) / 2
        print(f"\nExpected probability of overall +1 parity: {exp_prob0}")

        prob0 = plus_outcomes / sensing_iters
        print(f"Observed frequency of overall +1 parity: {prob0}")

        print("Encoded function - Phase average")
        print(f"Value: {phase_average}")

        # Determine the pi/4 interval containing the phase average value
        i = 0
        while phase_average % ((i+1)*np.pi/4) != phase_average:
            i += 1
        print(f"Interval: [{i*np.pi/4}, {i*np.pi/4 + np.pi/4}]")

        # Estimate average phase from oberserved +1 parity frequency
        if num_dishonest % 2 == 0:
            est = avg_estimator(prob0, i)
        else:
            est = avg_estimator_Zflip(prob0, i)
    
        print(f"Estimate: {est}")

    # In case of bit flip
    else:
        phase_sum = np.sum(list(phases.values()))
        diff = phase_sum

        if bitflip_node > 0:
            bitflip_name = node_names[bitflip_node]
            print(f"Bitflip node: {bitflip_name}")

            bitflip_phase = phases[bitflip_name]
            print(f"Bitflip node's phase: {bitflip_phase}")
        
            diff -= (2 * bitflip_phase)

        if dishonest_action == 2:
            for node in dishonest_nodes:
                diff -= (2 * phases[node])

        print(f"Encoded function - Sum of normal nodes' phases minus bitflip node's phase")
        print(f"Value: {diff}")

        exp_prob0 = (1 + np.cos(diff)) / 2
        print(f"Expected probability of overall +1 parity: {exp_prob0}")
        prob0 = plus_outcomes / sensing_iters
        print(f"Observed frequency of overall +1 parity: {prob0}")

        # Determine the pi-interval containing the difference value
        i = 0
        negative = diff < 0
        while abs(diff) % ((i+1)*np.pi) != abs(diff):
            i += 1
        if negative:
            print(f"Interval: [{i*-np.pi - np.pi}, {i*-np.pi}]")
        else:
            print(f"Interval: [{i*np.pi}, {i*np.pi + np.pi}]")

        # Estimate difference of honest and dishonest phase sums
        est = diff_estimator(prob0, i, negative)
        print(f"Estimate: {est}")


