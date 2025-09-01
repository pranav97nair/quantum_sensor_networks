from utils import *
import numpy as np
from verification_programs import GHZProgram_verifier, GHZProgram_member
from squidasm.run.stack.run import run # type: ignore

def init_verification_programs(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZProgram_verifier(verifier, node_names, n_test)}
    programs.update({name: GHZProgram_member(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 3
    num_iters = 1
    n_test = 3
    n_total = 2*num_nodes*n_test
    use_highfid = False
    use_optimistic = True

    # Initialize programs
    programs, node_names = init_verification_programs(num_nodes, n_test)

    # Load the network configuration
    #network_cfg = configure_perfect_network(node_names)
    network_cfg = configure_network(node_names, use_highfid, use_optimistic)

    # Run the simulation
    results = run(
        config=network_cfg,
        programs=programs,
        num_times=num_iters,
    )

    for k in range(num_iters):
        print(f"Iteration {k+1}")
        pprint(results[0][k])