from sensing_sans_verif import GHZSensingProgram
from utils import *
from utilsIO import *
import numpy as np
import sys

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

def prob_plus(theta: float, d: int):
    p = (1 + np.cos(d*theta)) / 2
    return p

def likelihood(theta: int, d: int, n: int, k: int):
    p = prob_plus(theta, d)
    return (p**k)*(1-p)**(n-k)

def log_likelihood(theta: int, d: int,  n: int, k: int):
    p = prob_plus(theta, d)
    return k*np.log2(p) + (n-k)*np.log2(1-p)

def max_likelihood_estimate(d: int, n: int, k: int, start: float, stop: float, grid_size: int=1000):
    theta_range = np.linspace(start, stop, grid_size, endpoint=False)
    likelihood_dict = {likelihood(theta, d, n, k): theta 
                       for theta in theta_range}
    
    maximum = max(likelihood_dict.keys())
    #print(f"Max value of likelihood function: {maximum}")
    est = likelihood_dict[maximum]
    return est

def inverse_cos_estimate(d: int, n: int, k: int, start: float):
    prob0 = k / n
    i = start / (np.pi/d)
    # Estimate average phase from oberserved +1 parity frequency
    arg = min(1, (prob0*2 - 1))
    if i == 0:                     
        est = np.arccos(arg) / d
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) / d + np.pi/2
    else:
        est = -1 * np.arccos(arg) / d + np.pi
    
    return est


if __name__ == '__main__':
    num_nodes = 4
    num_iters = 1000
    state = "ghz"
    pwd = "/home/pgnair/stage/estimation_dist/"
    params = sys.argv[1] # 'perfect' or 'optimhf'

    # Initialize programs
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    programs = {name: GHZSensingProgram(name, node_names) 
                for name in node_names}

    # Configure network
    # Load network configuration
    if params == "perfect":
        network_cfg = configure_perfect_network(node_names)
    elif params == "optimhf":
        network_cfg = configure_network(node_names, use_high_fidelity=True, use_optimistic=True)
    else:
        raise ValueError("Network argument must be \'perfect\' or \'optimhf\'")
    
    # Logging
    LogManager.set_log_level("WARNING")
    # Disable logging to terminal
    logger = LogManager.get_stack_logger()
    logger.handlers = []
    # Enable logging to file
    LogManager.log_to_file(f"{pwd}logs/info_{state}.log")

    ### Run simulation ###

    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters
    )
    
    ### Post-processing ###

    plus_outcomes = 0
    phase_average = np.nan
    # For each iteration
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

    # Determine interval for the phase average
    i = 0
    d = num_nodes
    while phase_average % ((i+1)*np.pi/d) != phase_average:
        i += 1
    interval_start = i*np.pi/d
    interval_stop = i*np.pi/d + np.pi/d

    # Calculate expected probability of overall +1 outcome
    exp_prob0 = (1 + np.cos(num_nodes*phase_average)) / 2

    est = inverse_cos_estimate(d=num_nodes,
                               n=num_iters,
                               k=plus_outcomes,
                               start=interval_start)
    
    mle = max_likelihood_estimate(d=num_nodes,
                         n=num_iters,
                         k=plus_outcomes,
                         start=interval_start,
                         stop=interval_stop)

    # Write output to existing file
    filename = f"{pwd}data/estimation_x1000_{params}.txt"
    with open(filename, 'a') as f:
        f.write(f"{phase_average} {est} {mle}\n")

