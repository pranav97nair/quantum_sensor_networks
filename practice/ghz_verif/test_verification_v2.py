from matplotlib import pyplot as plt
from utils import *
import numpy as np
from verification_programs_v2 import GHZVerifierNode_v2, GHZMemberNode_v2
from squidasm.run.stack.run import run # type: ignore

###
#   Function to initialize programs for the network such that
#   the first node runs the GHZVerifier program
#   and all the other nodes run the GHZMember program
###
def init_verification_programs(num_nodes: int, n_test: int):
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    programs = {verifier: GHZVerifierNode_v2(verifier, node_names, n_test)}
    programs.update({name: GHZMemberNode_v2(name, node_names, n_test) 
                     for name in node_names if name != verifier})
    return programs, node_names

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 4
    num_iters = 1
    ntest = 3     # n_total = 2*num_nodes*n_test
    # Parameters for network configuration with noise
    use_highfid = False
    use_optimistic = True

    # Initialize verification programs
    programs, node_names = init_verification_programs(num_nodes, ntest)
    #pprint(programs)

    # Load perfect network configuration (max qubits allowed per node = 100)
    #network_cfg = configure_perfect_network(node_names)

    # Load noisy network configuration
    # Warning:  On 'optimistic' settings, max qubits allowed per node = 20
    #           On 'current' settings, max qubits allowed = 2 so verification is not possible
    network_cfg = configure_network(node_names, use_highfid, use_optimistic)
    #pprint([link.cfg for link in network_cfg.links])
    pprint([stack.qdevice_cfg for stack in network_cfg.stacks])

    new_stack_cfg = configure_qdevice(is_perfect=True, num_qubits=200)
    for stack in network_cfg.stacks:
        stack.qdevice_cfg = new_stack_cfg
    
    pprint([stack.qdevice_cfg for stack in network_cfg.stacks])
    
    """ new_link_cfg = configure_link(link_typ="perfect")
    for link in network_cfg.links:
        link.cfg = new_link_cfg

    pprint([link.cfg for link in network_cfg.links]) """


    # Run the simulation
    results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters,
        )

    for j in range(num_nodes):
        print(results[j][0]['target qubit'])
        
    
    
    


            

    
