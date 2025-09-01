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

def local_estimator(dishonest_phase: float, estimates: List[float]):
    coeff_matrix = np.array([
        [1, 1, 1],
        [1, -1, 1],
        [1, 1, -1]
    ])

    rhs = np.array([est - dishonest_phase for est in estimates])
    print(rhs)
    solution = np.linalg.solve(coeff_matrix, rhs)
    return solution

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    f_threshold = 0.1
    num_iters = 20
    network = 'perfect'
    state = "ghz"

    # For local estimation we will set one dishonestnode that does not apply any local flip operation
    num_dishonest = 1
    dishonest_action = 0    # 0 = no action, 1 = apply phase flip, 2 = apply bit flip

    # Seed random state
    seed = 13579
    random.seed(seed)

    # Initialize standard programs with no bitflip
    programs, node_names, dishonest_nodes, phases = init_dishonest_sensing(num_nodes, ntest, copies, f_threshold, num_dishonest, dishonest_action)

    dishonest_node_id = node_names.index(dishonest_nodes[0])

    # Initialize bitflip programs for local estimation
    bitflip_programs1 = init_dishonest_sensing_given(node_names, ntest, copies, f_threshold, dishonest_node_id, bitflip_node=1, phases=phases)
    
    # Initialize bitflip programs for local estimation
    bitflip_programs2 = init_dishonest_sensing_given(node_names, ntest, copies, f_threshold, dishonest_node_id, bitflip_node=2, phases=phases)

    # Store defined programs in a hashmap
    program_dict = {
        0 : programs,
        1 : bitflip_programs1,
        2 : bitflip_programs2
    }

    # Configure network
    if network == 'perfect':
            network_cfg = configure_perfect_network(node_names)
    elif network == 'optimhf':
        network_cfg = configure_network(node_names,
                                        use_high_fidelity=True,
                                        use_optimistic=True)

    # Logging
    LogManager.set_log_level("ERROR")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"logs/local_estimation.log")

    # Run simulation
    plus_outcomes = [0] * 3
    program_runs = []
    program_counts = [0] * 3

    total_iters = 0
    sensing_iters = 0

    while sensing_iters < num_iters:
        # Randomly select one of the three defined programs to run
        program_id = random.randint(0, 2)
        results = run(
            config=network_cfg,
            programs=program_dict[program_id],
            num_times=1
        )
        program_runs.append(program_id)
        program_counts[program_id] += 1

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
            plus_outcomes[program_id] += 1
    
    ### Post-processing ###

    print(f"\nTotal iterations: {total_iters}")
    print(f"Total sensing iterations: {sensing_iters}\n")
    print(f"Iterations with standard programs: {program_counts[0]}")
    print(f"Iterations with bitflip1 programs: {program_counts[1]}")
    print(f"Iterations with bitflip2 programs: {program_counts[2]}")

    print(f"Dishonest nodes: {dishonest_nodes}\n")

    estimates = []

    print("No bitflip")
    phase_sum = np.sum(list(phases.values()))
    diff = phase_sum
    print(f"Sum of all phases: {diff}")
    
    ## Estimate phase sum ##
    exp_prob0 = (1 + np.cos(diff)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")
    prob0 = plus_outcomes[0] / program_counts[0]
    print(f"Observed frequency of overall +1 parity: {prob0}")

    # Determine the pi-interval
    i = 0
    negative = diff < 0
    while abs(diff) % ((i+1)*np.pi) != abs(diff):
        i += 1

    # Estimate
    est = diff_estimator(prob0, i, negative)
    estimates.append(est)
    print(f"Estimate: {est}\n")

    ## Estimate other two functions of phases

    for bitflip_node in range(1, 3):
        diff = phase_sum
        bitflip_name = node_names[bitflip_node]
        print(f"Bitflip node: {bitflip_name}")

        bitflip_phase = phases[bitflip_name]
        diff -= (2 * bitflip_phase)

        print(f"Encoded function - Sum of normal nodes' phases minus bitflip node's phase")
        print(f"Value: {diff}")

        exp_prob0 = (1 + np.cos(diff)) / 2
        print(f"Expected probability of overall +1 parity: {exp_prob0}")
        prob0 = plus_outcomes[bitflip_node] / program_counts[bitflip_node]
        print(f"Observed frequency of overall +1 parity: {prob0}")

        # Determine pi-interval
        i = 0
        negative = diff < 0
        while abs(diff) % ((i+1)*np.pi) != abs(diff):
            i += 1

        # Estimate
        est = diff_estimator(prob0, i, negative)
        print(f"Estimate: {est}\n")
        estimates.append(est)

    estimates = [1.303522044091468*4, 4.146422452705186, 0.5598623057342861]

    local_estimates = local_estimator(phases[dishonest_nodes[0]], estimates)
    print(f"Phases: {[phases[name] for name in node_names]}")
    print(f"Local estimates: {local_estimates}")

