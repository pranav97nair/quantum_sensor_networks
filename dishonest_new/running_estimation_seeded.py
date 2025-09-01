from utils import *
from verification_programs_full import GHZVerifierNode_full, GHZMemberNode_full
from utilsIO import *
import numpy as np
from pprint import pprint
import random
import sys

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
    num_iters = int(sys.argv[1])
    network = sys.argv[2]                  # 'perfect' or 'optimhf'
    state = "ghz"
    num_dishonest = int(sys.argv[3])       # between 1 and num_nodes-1 
    dishonest_action = int(sys.argv[4])    # 1 = apply phase flip, 2 = apply bit flip
    seed = 24680
    random.seed(seed)

    # Initialize programs
    if num_dishonest >= 1:
        programs, node_names, dishonest_nodes = init_dishonest_sensing(num_nodes, ntest, copies, f_threshold, num_dishonest, dishonest_action)
        #pprint(programs)
    else:
        programs, node_names = init_sensing_programs(num_nodes, ntest, copies, f_threshold)

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
    LogManager.log_to_file(f"logs/running_estimation.log")

    # Run simulation
    plus_outcomes = 0
    total_iters = 0
    sensing_iters = 0
    running_plus_freq = []
    phases = {}
    estimations = []

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

        # Track running frequency of +1 parity outcome
        running_plus_freq.append(plus_outcomes / sensing_iters)
            
        # Get phase average
        if sensing_iters == num_iters:
            for j in range(num_nodes):
                node_name = results[j][0]['name']
                phase = results[j][0]['local phase']
                phases[node_name] = phase
        
        if sensing_iters % 20 == 0:
            print(f"Iteration {sensing_iters} complete.")
    
    ### Post-processing ###

    print(f"\nTotal iterations: {total_iters}")
    print(f"Total sensing iterations: {sensing_iters}")

    print(f"Phases: {phases}")
    print(f"Dishonest nodes: {dishonest_nodes}\n")
    
    # In case of phase flip or no dishonest action:
    if dishonest_action == 1 or num_dishonest == 0:
        # The function encoded is the average of the phases
        phase_average = np.average(list(phases.values()))

        exp_prob0 = (1 + (-1)**num_dishonest * np.cos(num_nodes*phase_average)) / 2
        print(f"Expected probability of overall +1 parity: {exp_prob0}")

        prob0 = plus_outcomes / sensing_iters
        print(f"Observed frequency of overall +1 parity: {prob0}")

        print("Encoded function - Phase average")
        print(f"Value: {phase_average}")

        # Determine the pi/4 interval containing the phase average value
        i = 0
        while phase_average % ((i+1)*np.pi/4) != phase_average:
            i += 1
        print(f"Interval: [{i*np.pi/4}, {i*np.pi/4 + np.pi/4}]")

        # Running estimate of average phase from oberserved +1 parity frequency
        for prob0 in running_plus_freq:
            if num_dishonest % 2 == 0:
                est = avg_estimator(prob0, i)
            else:
                est = avg_estimator_Zflip(prob0, i)
            estimations.append(est)
    
        print(f"Final estimate: {est}")

    # In case of bit flip
    else:
        phase_sum = np.sum(list(phases.values()))
        honest_sum = phase_sum
        for node in dishonest_nodes:
            honest_sum -= phases[node]
        honest_avg = honest_sum / (num_nodes-num_dishonest)
        dishonest_avg = (phase_sum - honest_sum) / num_dishonest
        dishonest_sum = phase_sum - honest_sum
        diff = honest_sum - dishonest_sum

        print(f"Honest nodes' phase sum: {honest_sum}")
        print(f"Dishonest nodes' phase sum: {dishonest_sum}\n")
        print(f"Encoded function - Difference of honest and dishonest sums")
        print(f"Value: {diff}")

        exp_prob0 = (1 + np.cos(diff)) / 2
        print(f"Expected probability of overall +1 parity: {exp_prob0}")
        prob0 = plus_outcomes / sensing_iters
        print(f"Observed frequency of overall +1 parity: {prob0}")

        # Determine the pi/4 interval containing the difference value
        i = 0
        negative = diff < 0
        while abs(diff) % ((i+1)*np.pi) != abs(diff):
            i += 1
        if negative:
            print(f"Interval: [{i*-np.pi - np.pi}, {i*-np.pi}]")
        else:
            print(f"Interval: [{i*np.pi}, {i*np.pi + np.pi}]")

        # Running estimation of difference of honest and dishonest phase sums
        for prob0 in running_plus_freq:
            est = diff_estimator(prob0, i, negative)
            estimations.append(est)

        print(f"Final estimate: {est}")

    # Write data to file
    postfix = f"dishonest{num_dishonest}_action{dishonest_action}"
    filename = f"data/running_estimation/s{seed}_{network}_{postfix}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#     num_nodes={num_nodes}, num_iters={num_iters}, num_dishonest={num_dishonest}, dishonest_action={dishonest_action}\n")
        f.write(f"# dishonest_nodes={dishonest_nodes}\n")
        f.write(f"# phases={phases}\n")
        if 'phase_average' in locals():
            f.write(f"# phase_average={phase_average}\n")
        elif diff:
            f.write(f"# difference={diff}\n")
        f.write("# columns:\n")
        f.write("#      iteration   running_frequency   running_estimation\n")

    # Output
    write_to_file_multiy(
        x=list(range(1,num_iters+1)),
        y1=running_plus_freq,
        y2=estimations,
        filename=filename
    )

    print(f"Simulation results stored in {filename}")


