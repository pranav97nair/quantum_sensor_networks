from utils import *
from utilsIO import *
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    # Simulation parameters
    num_nodes = 4
    num_iters = 1200
    ntest = 3
    f_threshold = 1 / (2 * num_nodes**2)
    state = "ghz"

    num_dishonest = 2
    # Action the dishonest nodes will perform
    #   1 => zero rotation
    #   2 => incorrect measurement
    #   3 => incorrect rotation
    dishonest_action = 3

    sim_num = 3
    seed = 43240
    random.seed(seed)

    # Initialize programs
    if num_dishonest > 1:
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

    phase_averages = []
    running_plus_freq = []
    plus_outcomes = 0

    for k in range(num_iters):
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=1
        )

        # Get phase average
        phases = []
        for j in range(num_nodes):
            phases.append(results[j][0]['local phase'])
        phase_averages.append(np.average(phases))

        # Get parity results from each node
        k_parities = []
        for j in range(num_nodes):
            k_parities.append(results[j][0]["parity"])
        #print(np.array(k_parities))

        # Check +^d outcome, i.e. when all nodes output parity +1
        """ if np.sum(k_parities) == num_nodes:
            plus_outcomes += 1 """
        
        # Check overall parity +1 outcome
        if np.prod(k_parities) == 1:
            plus_outcomes += 1

        # Track running frequency of +^d outcome
        running_plus_freq.append(plus_outcomes / (k+1))

        if (k+1) % 100 == 0:
            print(f"Simulation {k+1} complete.")

    ### Post-processing ###

    phase_average = phase_averages[-1]
    # Calculate expected probability of +^d outcome
    """ exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / (2 ** num_nodes)
    print(f"Expected probability of {'+'*num_nodes} outcome: {exp_prob0}") """

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2
    print(f"Expected probability of overall +1 parity: {exp_prob0}")

    # Get observed outcome probabilities
    prob0 = running_plus_freq[-1]
    #print(f"Final observed frequency of {'+'*num_nodes} outcome: {prob0}")  # for +^d outcome
    print(f"Final observed frequency of overall +1 parity: {prob0}")         # for overall +1 outcome

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
    if num_dishonest >= 1:
        postfix = f"dishonest{num_dishonest}_action{dishonest_action}"
    else:
        postfix = "honest"
    filename = f"data/sim{sim_num}/running_est_{postfix}.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#  num_nodes={num_nodes}, num_iters={num_iters}, ntest={ntest}, seed={seed}\n")
        f.write(f"#  dishonest_nodes={num_dishonest}, dishonest_action={dishonest_action}\n")
        f.write("# columns:\n")
        f.write("#  iteration   running_frequency   running_estimation   average_phase\n")

    write_to_file_multiy(filename=filename,
                         x=x,
                         y1=running_plus_freq,
                         y2=estimations,
                         y3=phase_averages)