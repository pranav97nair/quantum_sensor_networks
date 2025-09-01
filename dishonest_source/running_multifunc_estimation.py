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
    num_iters = 250
    network = 'optimhf'
    state = "ghz"

    # For local estimation we will set one dishonest node that does not apply any local flip operation
    num_dishonest = 1
    dishonest_action = 0    # 0 = no action, 1 = apply phase flip, 2 = apply bit flip

    # Seed random state
    seed = 13579
    random.seed(seed)

    # Initialize standard programs with no bitflip
    programs, node_names, dishonest_nodes, phases = init_dishonest_sensing(num_nodes, ntest, copies, f_threshold, num_dishonest, dishonest_action)

    # Get dishonest node location, for now it is the fourth node
    dishonest_node_id = node_names.index(dishonest_nodes[0])

    # Initialize programs with bitflip on the second node
    bitflip_programs1 = init_dishonest_sensing_given(node_names, ntest, copies, f_threshold, dishonest_node_id, bitflip_node=1, phases=phases)
    
    # Initialize programs with bitflip on the third node
    bitflip_programs2 = init_dishonest_sensing_given(node_names, ntest, copies, f_threshold, dishonest_node_id, bitflip_node=2, phases=phases)

    pprint(phases)

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
    LogManager.log_to_file(f"logs/running_multifunc_estimation.log")

    # Run simulation
    plus_outcomes = [0] * 3
    running_plus_freq = [[] for i in range(3)]
    running_estimations = [[] for i in range(3)]
    program_runs = []
    program_counts = [0] * 3

    total_iters = 0
    sensing_iters = 0

    # Run simulation until total iteration count is reached
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

        # Update running parity +1 frequencies for each program
        for id in range(3):
            if program_counts[id] > 0:
                running_plus_freq[id].append(plus_outcomes[id] / program_counts[id])
            else:
                running_plus_freq[id].append(0)
        
        if sensing_iters % 20 == 0:
            print(f"Iteration {sensing_iters} complete.")
    
    ### Post-processing ###

    ## Estimate phase sum
    phase_sum = np.sum(list(phases.values()))
    funcs = [phase_sum] * 3

    # Determine the pi-interval
    i = 0
    negative = funcs[0] < 0
    while abs(funcs[0]) % ((i+1)*np.pi) != abs(funcs[0]):
        i += 1
    
    # Running estimate
    for prob0 in running_plus_freq[0]:
        est = diff_estimator(prob0, i, negative)
        running_estimations[0].append(est / num_nodes)

    ## Estimate other two functions of phases

    for bitflip_node in [1, 2]:
        bitflip_name = node_names[bitflip_node]
        bitflip_phase = phases[bitflip_name]
        funcs[bitflip_node] -= (2 * bitflip_phase)

        # Determine pi-interval
        i = 0
        negative = funcs[bitflip_node] < 0
        while abs(funcs[bitflip_node]) % ((i+1)*np.pi) != abs(funcs[bitflip_node]):
            i += 1
        
        # Running estimate
        for prob0 in running_plus_freq[bitflip_node]:
            est = diff_estimator(prob0, i, negative)
            running_estimations[bitflip_node].append(est)

    # Write data to file
    filename = f"data/running_multifunc_estimation/s{seed}_{network}_{num_iters}_iters.txt"

    # Parameter information and output data identifiers
    with open(filename, 'w') as f:
        f.write("# parameters:\n")
        f.write(f"#     num_nodes={num_nodes}, num_iters={num_iters}, dishonest_node=Node_4, bitflip_nodes=[Node_2, Node_3]\n")
        f.write(f"# phases={phases}\n")
        f.write(f"# phase_average = {phase_sum / num_nodes}\n")
        f.write(f"# alt_function1 = {funcs[1]}\n")
        f.write(f"# alt_function2 = {funcs[2]}\n")
        f.write("# columns:\n")
        f.write("#      iteration   running_est0   running_est1   running_est2\n")

    # Output
    write_to_file_multiy(
        x=list(range(1,num_iters+1)),
        y1=running_estimations[0],
        y2=running_estimations[1],
        y3=running_estimations[2],
        filename=filename
    )

    print(f"Simulation results stored in {filename}")


