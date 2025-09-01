from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np
from pprint import pprint
import random
import sys

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    f_threshold = float(sys.argv[1])
    num_iters = int(sys.argv[2])
    network = sys.argv[3]   # 'perfect' or 'optimhf'
    state = "ghz"

    # Initialize programs
    seed = 7200
    random.seed(seed)
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

    ### Run simulation ###

    plus_outcomes = 0
    running_plus_freq = []
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

        # Check overall parity +1 outcome
        if np.prod(parities) == 1:
            plus_outcomes += 1

        # Track running frequency of +^d outcome
        running_plus_freq.append(plus_outcomes / (sensing_iters))

        # Get phase average
        if sensing_iters == num_iters:
            phases = []
            for j in range(num_nodes):
                phases.append(results[j][0]['local phase'])
            phase_average = np.average(phases)

        if (sensing_iters) % (num_iters/20) == 0:
            print(f"Simulation {sensing_iters} complete.")

    ### Post-processing ###

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")

    # Get observed outcome probabilities
    prob0 = running_plus_freq[-1]
    print(f"Final observed frequency of overall +1 parity: {prob0}")

    # Identify interval
    i = 0
    while phase_average % ((i+1)*np.pi/4) != phase_average:
         i += 1

    # Estimate phase average
    estimations = []
    for p in running_plus_freq:
        #arg = min(1, (p * (2**num_nodes) - 1))      # for +^d outcome
        arg = min(1, (p*2 - 1))                      # for overall +1 outcome
        if i == 0:                     
            est = np.arccos(arg) / num_nodes
        elif i < 3:
            est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
        else:
            est = -1 * np.arccos(arg) / num_nodes + np.pi
        estimations.append(est)

    print(f"Average phase: {phase_average}")
    print(f"Final estimated average phase: {estimations[-1]}")

    x = list(range(1, num_iters+1))

    # Write data to file
    threshold_postfix = str(f_threshold)[2:]
    filename = f"data/t{threshold_postfix}/{num_iters}_iteration_sim_{network}_{seed}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, total_iters={total_iters}, ntest={ntest}, copies={copies}\n")
        f.write(f"#  phase_average={phase_average}, failure_threshold={f_threshold}\n")
        f.write("# columns:\n")
        f.write("#  iteration   running_frequency   running_estimation\n")

    write_to_file_multiy(filename=filename,
                         x=x,
                         y1=running_plus_freq,
                         y2=estimations)