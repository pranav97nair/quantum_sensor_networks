import numpy as np
import scipy.linalg as sci
import matplotlib.pyplot as plt
from application_v2 import GHZProgram_send_full_state
from utils import configure_perfect_network

from netsquid_netbuilder.modules.clinks.default import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.run.stack.run import run # type: ignore
from squidasm.util.util import create_complete_graph_network # type: ignore
from squidasm.util.util import get_qubit_state # type: ignore

if __name__ == '__main__':
    num_nodes = 3
    num_iters = 1

    # Initialize programs
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    programs = {name: GHZProgram_send_full_state(name, node_names) for name in node_names}

    # Configure network
    network_cfg = configure_perfect_network(node_names)

    # Run simulation
    results = run(
        config=network_cfg, 
        programs=programs, 
        num_times=num_iters
    )

    ideal_state = results[num_nodes-1][0]["state"]

    print(f"Ideal GHZ state between {num_nodes} nodes: \n{ideal_state}")
    print(f"Dimensions: {len(ideal_state)}x{len(ideal_state[0])}")
